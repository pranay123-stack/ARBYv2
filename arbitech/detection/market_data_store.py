"""
Market Data Store - High-performance storage system for market data.

This module provides a comprehensive storage system with caching, compression,
efficient retrieval, and persistence for market data from multiple sources.
"""

import asyncio
import json
import pickle
import gzip
import sqlite3
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Iterator, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import logging
import hashlib
from collections import defaultdict, OrderedDict
import weakref
import threading
from pathlib import Path

try:
    # Try relative imports first (when used as part of arbitech package)
    from .data_aggregator import AggregatedEvent, MarketData, MarketOdds
    from .data_synchronizer import SyncEvent, SyncEventType
    from ..utils.logger import get_logger
except ImportError:
    # Fall back to absolute imports (when used standalone)
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    from data_aggregator import AggregatedEvent, MarketData, MarketOdds
    from data_synchronizer import SyncEvent, SyncEventType
    
    try:
        from utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)


logger = get_logger(__name__)


class StorageType(str, Enum):
    """Types of storage backends."""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE_SYSTEM = "file_system"
    DISTRIBUTED = "distributed"


class CompressionType(str, Enum):
    """Types of compression supported."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


class CacheStrategy(str, Enum):
    """Cache management strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live


@dataclass
class StorageMetrics:
    """Performance and usage metrics for storage."""
    total_reads: int = 0
    total_writes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_ratio: float = 0.0
    avg_read_time_ms: float = 0.0
    avg_write_time_ms: float = 0.0
    storage_size_bytes: int = 0
    cache_size_bytes: int = 0
    last_cleanup: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total_requests = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_requests) if total_requests > 0 else 0.0
    
    @property
    def throughput_ops_per_sec(self) -> float:
        """Calculate operations per second."""
        total_ops = self.total_reads + self.total_writes
        time_diff = (datetime.utcnow() - self.last_cleanup).total_seconds()
        return total_ops / max(time_diff, 1.0)


@dataclass
class DataRecord:
    """Individual data record in storage."""
    key: str
    value: Any
    data_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    compression: str = "none"
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.size_bytes:
            self.size_bytes = self._calculate_size()
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_size(self) -> int:
        """Calculate the size of the data in bytes."""
        try:
            serialized = pickle.dumps(self.value)
            return len(serialized)
        except Exception:
            return 0
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for data integrity."""
        try:
            serialized = pickle.dumps(self.value)
            return hashlib.md5(serialized).hexdigest()
        except Exception:
            return ""
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if record is expired based on TTL."""
        if ttl_seconds <= 0:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > ttl_seconds


class LRUCache:
    """Thread-safe LRU cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, DataRecord] = OrderedDict()
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[DataRecord]:
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                record = self.cache.pop(key)
                self.cache[key] = record
                record.access_count += 1
                record.last_accessed = datetime.utcnow()
                self.hit_count += 1
                return record
            else:
                self.miss_count += 1
                return None
    
    def put(self, key: str, record: DataRecord):
        """Put item in cache."""
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
            
            self.cache[key] = record
    
    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_ratio': self.hit_count / max(total_requests, 1.0),
                'total_requests': total_requests
            }


class TTLCache:
    """TTL-based cache with automatic expiration."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.default_ttl = default_ttl
        self.cache: Dict[str, DataRecord] = {}
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[DataRecord]:
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                record = self.cache[key]
                if not record.is_expired(self.default_ttl):
                    record.access_count += 1
                    record.last_accessed = datetime.utcnow()
                    self.hit_count += 1
                    return record
                else:
                    # Remove expired record
                    del self.cache[key]
            
            self.miss_count += 1
            return None
    
    def put(self, key: str, record: DataRecord):
        """Put item in cache."""
        with self.lock:
            self.cache[key] = record
    
    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def cleanup_expired(self):
        """Remove expired items from cache."""
        with self.lock:
            expired_keys = [
                key for key, record in self.cache.items()
                if record.is_expired(self.default_ttl)
            ]
            for key in expired_keys:
                del self.cache[key]
    
    def size(self) -> int:
        """Get cache size."""
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            return {
                'size': len(self.cache),
                'default_ttl': self.default_ttl,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_ratio': self.hit_count / max(total_requests, 1.0),
                'total_requests': total_requests
            }


class DataCompressor:
    """Handles data compression and decompression."""
    
    @staticmethod
    def compress(data: Any, compression_type: CompressionType = CompressionType.GZIP) -> bytes:
        """Compress data using specified compression."""
        try:
            serialized = pickle.dumps(data)
            
            if compression_type == CompressionType.NONE:
                return serialized
            
            elif compression_type == CompressionType.GZIP:
                return gzip.compress(serialized)
            
            # Add other compression types as needed
            else:
                return serialized
        
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return pickle.dumps(data)
    
    @staticmethod
    def decompress(compressed_data: bytes, compression_type: CompressionType = CompressionType.GZIP) -> Any:
        """Decompress data using specified compression."""
        try:
            if compression_type == CompressionType.NONE:
                return pickle.loads(compressed_data)
            
            elif compression_type == CompressionType.GZIP:
                decompressed = gzip.decompress(compressed_data)
                return pickle.loads(decompressed)
            
            # Add other compression types as needed
            else:
                return pickle.loads(compressed_data)
        
        except Exception as e:
            logger.warning(f"Decompression failed: {e}")
            return pickle.loads(compressed_data)


class SQLiteStorage:
    """SQLite-based persistent storage."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    data_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    size_bytes INTEGER DEFAULT 0,
                    compression TEXT DEFAULT 'none',
                    checksum TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed 
                ON market_data(last_accessed)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON market_data(created_at)
            """)
            
            conn.commit()
    
    def store(self, key: str, record: DataRecord) -> bool:
        """Store data record in SQLite."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    serialized_value = DataCompressor.compress(
                        record.value, CompressionType(record.compression)
                    )
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO market_data 
                        (key, value, data_type, created_at, updated_at, 
                         access_count, last_accessed, size_bytes, 
                         compression, checksum, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        key,
                        serialized_value,
                        record.data_type,
                        record.created_at.isoformat(),
                        record.updated_at.isoformat(),
                        record.access_count,
                        record.last_accessed.isoformat(),
                        record.size_bytes,
                        record.compression,
                        record.checksum,
                        json.dumps(record.metadata)
                    ))
                    
                    conn.commit()
                    return True
        
        except Exception as e:
            logger.error(f"SQLite store failed for {key}: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[DataRecord]:
        """Retrieve data record from SQLite."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value, data_type, created_at, updated_at,
                               access_count, last_accessed, size_bytes,
                               compression, checksum, metadata
                        FROM market_data WHERE key = ?
                    """, (key,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    # Decompress and deserialize value
                    compressed_value, data_type, created_at, updated_at, \
                    access_count, last_accessed, size_bytes, \
                    compression, checksum, metadata = row
                    
                    value = DataCompressor.decompress(
                        compressed_value, CompressionType(compression)
                    )
                    
                    return DataRecord(
                        key=key,
                        value=value,
                        data_type=data_type,
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at),
                        access_count=access_count,
                        last_accessed=datetime.fromisoformat(last_accessed),
                        size_bytes=size_bytes,
                        compression=compression,
                        checksum=checksum,
                        metadata=json.loads(metadata or '{}')
                    )
        
        except Exception as e:
            logger.error(f"SQLite retrieve failed for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete data record from SQLite."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM market_data WHERE key = ?", (key,))
                    conn.commit()
                    return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"SQLite delete failed for {key}: {e}")
            return False
    
    def list_keys(self, prefix: str = "", limit: int = 1000) -> List[str]:
        """List keys in SQLite storage."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    if prefix:
                        cursor = conn.execute("""
                            SELECT key FROM market_data 
                            WHERE key LIKE ? 
                            ORDER BY last_accessed DESC 
                            LIMIT ?
                        """, (f"{prefix}%", limit))
                    else:
                        cursor = conn.execute("""
                            SELECT key FROM market_data 
                            ORDER BY last_accessed DESC 
                            LIMIT ?
                        """, (limit,))
                    
                    return [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"SQLite list_keys failed: {e}")
            return []
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """Cleanup old records from SQLite."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM market_data 
                        WHERE created_at < ? AND access_count = 0
                    """, (cutoff_date.isoformat(),))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    return deleted_count
        
        except Exception as e:
            logger.error(f"SQLite cleanup failed: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(size_bytes) as total_size,
                            AVG(size_bytes) as avg_size
                        FROM market_data
                    """)
                    
                    stats = cursor.fetchone()
                    total_records, total_size, avg_size = stats
                    
                    return {
                        'total_records': total_records or 0,
                        'total_size_bytes': total_size or 0,
                        'average_size_bytes': avg_size or 0,
                        'database_path': self.db_path
                    }
        
        except Exception as e:
            logger.error(f"SQLite stats failed: {e}")
            return {}


class MarketDataStore:
    """High-performance market data storage system."""
    
    def __init__(self, 
                 storage_type: StorageType = StorageType.MEMORY,
                 cache_strategy: CacheStrategy = CacheStrategy.LRU,
                 max_cache_size: int = 10000,
                 cache_ttl: int = 300,
                 compression: CompressionType = CompressionType.GZIP,
                 db_path: str = "data/market_data.db"):
        
        self.logger = get_logger(__name__)
        
        # Storage configuration
        self.storage_type = storage_type
        self.cache_strategy = cache_strategy
        self.compression = compression
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        
        # Initialize components
        self.metrics = StorageMetrics()
        
        # Cache
        if cache_strategy == CacheStrategy.LRU:
            self.cache = LRUCache(max_cache_size)
        elif cache_strategy == CacheStrategy.TTL:
            self.cache = TTLCache(cache_ttl)
        else:
            self.cache = LRUCache(max_cache_size)
        
        # Persistent storage
        if storage_type == StorageType.SQLITE:
            self.persistent_storage = SQLiteStorage(db_path)
        else:
            self.persistent_storage = None
        
        # In-memory storage
        self.memory_storage: Dict[str, DataRecord] = {}
        
        # Performance monitoring
        self.read_times: List[float] = []
        self.write_times: List[float] = []
        self.max_time_history = 1000
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.compression_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self.store_callbacks: List[Callable] = []
        self.retrieve_callbacks: List[Callable] = []
        
        # Control flags
        self.store_active = False
    
    async def initialize(self):
        """Initialize the market data store."""
        try:
            # Start background tasks
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.compression_task = asyncio.create_task(self._compression_loop())
            
            self.store_active = True
            self.logger.info(f"Market data store initialized with {self.storage_type.value} storage")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize market data store: {e}")
            raise
    
    async def store_event_data(self, event: AggregatedEvent, key: Optional[str] = None) -> bool:
        """Store aggregated event data."""
        start_time = time.time()
        
        try:
            if not key:
                key = f"event:{event.event_id}"
            
            record = DataRecord(
                key=key,
                value=event,
                data_type="AggregatedEvent",
                compression=self.compression.value,
                metadata={
                    'sport': event.sport.value,
                    'event_name': event.event_name,
                    'start_time': event.start_time.isoformat(),
                    'markets_count': len(event.markets),
                    'source_count': event.source_count
                }
            )
            
            success = await self._store_record(key, record)
            
            # Update metrics
            write_time = (time.time() - start_time) * 1000
            self._update_write_time(write_time)
            self.metrics.total_writes += 1
            
            # Notify callbacks
            for callback in self.store_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback('store_event', key, record)
                    else:
                        callback('store_event', key, record)
                except Exception as e:
                    self.logger.warning(f"Store callback failed: {e}")
            
            return success
        
        except Exception as e:
            self.logger.error(f"Store event data failed: {e}")
            return False
    
    async def retrieve_event_data(self, event_id: str) -> Optional[AggregatedEvent]:
        """Retrieve aggregated event data."""
        start_time = time.time()
        
        try:
            key = f"event:{event_id}"
            record = await self._retrieve_record(key)
            
            if record and isinstance(record.value, AggregatedEvent):
                # Update metrics
                read_time = (time.time() - start_time) * 1000
                self._update_read_time(read_time)
                self.metrics.total_reads += 1
                
                # Notify callbacks
                for callback in self.retrieve_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback('retrieve_event', key, record)
                        else:
                            callback('retrieve_event', key, record)
                    except Exception as e:
                        self.logger.warning(f"Retrieve callback failed: {e}")
                
                return record.value
            else:
                self.metrics.cache_misses += 1
                return None
        
        except Exception as e:
            self.logger.error(f"Retrieve event data failed: {e}")
            return None
    
    async def store_market_data(self, market: MarketData, key: Optional[str] = None) -> bool:
        """Store market data."""
        start_time = time.time()
        
        try:
            if not key:
                key = f"market:{market.market_id}"
            
            record = DataRecord(
                key=key,
                value=market,
                data_type="MarketData",
                compression=self.compression.value,
                metadata={
                    'event_id': market.event_id,
                    'market_type': market.market_type,
                    'sport': market.sport.value,
                    'odds_count': len(market.odds),
                    'source_count': market.source_count
                }
            )
            
            success = await self._store_record(key, record)
            
            # Update metrics
            write_time = (time.time() - start_time) * 1000
            self._update_write_time(write_time)
            self.metrics.total_writes += 1
            
            return success
        
        except Exception as e:
            self.logger.error(f"Store market data failed: {e}")
            return False
    
    async def retrieve_market_data(self, market_id: str) -> Optional[MarketData]:
        """Retrieve market data."""
        start_time = time.time()
        
        try:
            key = f"market:{market_id}"
            record = await self._retrieve_record(key)
            
            if record and isinstance(record.value, MarketData):
                # Update metrics
                read_time = (time.time() - start_time) * 1000
                self._update_read_time(read_time)
                self.metrics.total_reads += 1
                
                return record.value
            else:
                self.metrics.cache_misses += 1
                return None
        
        except Exception as e:
            self.logger.error(f"Retrieve market data failed: {e}")
            return None
    
    async def store_sync_event(self, sync_event: SyncEvent) -> bool:
        """Store synchronization event."""
        try:
            key = f"sync_event:{sync_event.event_id}:{sync_event.timestamp.isoformat()}"
            
            record = DataRecord(
                key=key,
                value=sync_event,
                data_type="SyncEvent",
                compression=self.compression.value,
                metadata={
                    'event_type': sync_event.event_type,
                    'event_id': sync_event.event_id,
                    'source': sync_event.source
                }
            )
            
            return await self._store_record(key, record)
        
        except Exception as e:
            self.logger.error(f"Store sync event failed: {e}")
            return False
    
    async def _store_record(self, key: str, record: DataRecord) -> bool:
        """Store data record using configured storage."""
        try:
            # Store in memory
            self.memory_storage[key] = record
            
            # Store in cache
            if hasattr(self.cache, 'put'):
                self.cache.put(key, record)
                self.metrics.cache_hits += 1
            
            # Store persistently if configured
            if self.persistent_storage:
                persistent_success = self.persistent_storage.store(key, record)
                if not persistent_success:
                    self.logger.warning(f"Persistent storage failed for {key}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Store record failed for {key}: {e}")
            return False
    
    async def _retrieve_record(self, key: str) -> Optional[DataRecord]:
        """Retrieve data record using configured storage."""
        try:
            # Try cache first
            cached_record = self.cache.get(key)
            if cached_record:
                self.metrics.cache_hits += 1
                return cached_record
            
            # Try memory storage
            if key in self.memory_storage:
                record = self.memory_storage[key]
                # Update cache
                if hasattr(self.cache, 'put'):
                    self.cache.put(key, record)
                self.metrics.cache_hits += 1
                return record
            
            # Try persistent storage
            if self.persistent_storage:
                record = self.persistent_storage.retrieve(key)
                if record:
                    # Store in memory and cache
                    self.memory_storage[key] = record
                    if hasattr(self.cache, 'put'):
                        self.cache.put(key, record)
                    self.metrics.cache_hits += 1
                    return record
            
            self.metrics.cache_misses += 1
            return None
        
        except Exception as e:
            self.logger.error(f"Retrieve record failed for {key}: {e}")
            self.metrics.cache_misses += 1
            return None
    
    def _update_read_time(self, read_time_ms: float):
        """Update read time metrics."""
        self.read_times.append(read_time_ms)
        if len(self.read_times) > self.max_time_history:
            self.read_times.pop(0)
        
        if self.metrics.avg_read_time_ms == 0:
            self.metrics.avg_read_time_ms = read_time_ms
        else:
            self.metrics.avg_read_time_ms = (
                self.metrics.avg_read_time_ms * 0.8 + read_time_ms * 0.2
            )
    
    def _update_write_time(self, write_time_ms: float):
        """Update write time metrics."""
        self.write_times.append(write_time_ms)
        if len(self.write_times) > self.max_time_history:
            self.write_times.pop(0)
        
        if self.metrics.avg_write_time_ms == 0:
            self.metrics.avg_write_time_ms = write_time_ms
        else:
            self.metrics.avg_write_time_ms = (
                self.metrics.avg_write_time_ms * 0.8 + write_time_ms * 0.2
            )
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.store_active:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._perform_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _compression_loop(self):
        """Background compression optimization loop."""
        while self.store_active:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                await self._optimize_compression()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Compression loop error: {e}")
                await asyncio.sleep(300)  # Wait before retrying
    
    async def _perform_cleanup(self):
        """Perform storage cleanup."""
        try:
            # Clean up expired cache entries
            if hasattr(self.cache, 'cleanup_expired'):
                self.cache.cleanup_expired()
            
            # Clean up old memory storage entries (older than 24 hours and not accessed)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            expired_keys = [
                key for key, record in self.memory_storage.items()
                if record.last_accessed < cutoff_time and record.access_count < 2
            ]
            
            for key in expired_keys:
                del self.memory_storage[key]
            
            # Clean up persistent storage
            if self.persistent_storage:
                cleaned_count = self.persistent_storage.cleanup_old_records(30)
                if cleaned_count > 0:
                    self.logger.info(f"Cleaned up {cleaned_count} old records")
            
            # Update metrics
            self.metrics.last_cleanup = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    async def _optimize_compression(self):
        """Optimize storage compression."""
        try:
            if not self.persistent_storage:
                return
            
            # Get storage stats
            storage_stats = self.persistent_storage.get_storage_stats()
            total_size = storage_stats.get('total_size_bytes', 0)
            
            # Calculate compression ratio
            total_uncompressed = sum(
                record.size_bytes for record in self.memory_storage.values()
            )
            
            if total_uncompressed > 0:
                self.metrics.compression_ratio = total_size / total_uncompressed
            
            # Adjust compression strategy based on usage
            if self.metrics.compression_ratio > 0.8:
                # High compression ratio, consider using stronger compression
                self.logger.info("High compression ratio detected")
            
        except Exception as e:
            self.logger.error(f"Compression optimization failed: {e}")
    
    async def search_events(self, 
                           sport: Optional[str] = None,
                           start_time_range: Optional[Tuple[datetime, datetime]] = None,
                           min_quality_score: Optional[float] = None,
                           limit: int = 100) -> List[AggregatedEvent]:
        """Search for events based on criteria."""
        try:
            events = []
            
            # Get all event keys
            all_keys = []
            if self.persistent_storage:
                all_keys.extend(self.persistent_storage.list_keys("event:"))
            all_keys.extend([key for key in self.memory_storage.keys() if key.startswith("event:")])
            
            # Filter and retrieve events
            for key in all_keys[:limit * 2]:  # Get more than needed for filtering
                record = await self._retrieve_record(key)
                if record and isinstance(record.value, AggregatedEvent):
                    event = record.value
                    
                    # Apply filters
                    if sport and event.sport.value != sport:
                        continue
                    
                    if (start_time_range and 
                        not (start_time_range[0] <= event.start_time <= start_time_range[1])):
                        continue
                    
                    if (min_quality_score and 
                        event.overall_quality_score < min_quality_score):
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
            
            return events
        
        except Exception as e:
            self.logger.error(f"Search events failed: {e}")
            return []
    
    async def get_events_by_sport(self, sport: str, limit: int = 50) -> List[AggregatedEvent]:
        """Get events for a specific sport."""
        return await self.search_events(sport=sport, limit=limit)
    
    async def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[AggregatedEvent]:
        """Get events from recent time period."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        return await self.search_events(
            start_time_range=(start_time, end_time),
            limit=limit
        )
    
    def get_storage_metrics(self) -> StorageMetrics:
        """Get current storage metrics."""
        # Update cache metrics
        cache_stats = self.cache.get_stats()
        self.metrics.cache_hits = cache_stats.get('hit_count', 0)
        self.metrics.cache_misses = cache_stats.get('miss_count', 0)
        
        # Update storage size
        total_size = sum(record.size_bytes for record in self.memory_storage.values())
        self.metrics.storage_size_bytes = total_size
        self.metrics.cache_size_bytes = self.cache.size() * 1000  # Rough estimate
        
        return self.metrics
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        return self.cache.get_stats()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        metrics = self.get_storage_metrics()
        
        return {
            'storage_metrics': asdict(metrics),
            'cache_stats': self.get_cache_statistics(),
            'performance': {
                'avg_read_time_ms': self.metrics.avg_read_time_ms,
                'avg_write_time_ms': self.metrics.avg_write_time_ms,
                'read_times_sample': self.read_times[-10:],  # Last 10 read times
                'write_times_sample': self.write_times[-10:]  # Last 10 write times
            },
            'storage_usage': {
                'memory_storage_size': len(self.memory_storage),
                'cache_size': self.cache.size(),
                'total_estimated_size_mb': self.metrics.storage_size_bytes / (1024 * 1024)
            }
        }
    
    def add_store_callback(self, callback: Callable):
        """Add callback for store operations."""
        self.store_callbacks.append(callback)
    
    def add_retrieve_callback(self, callback: Callable):
        """Add callback for retrieve operations."""
        self.retrieve_callbacks.append(callback)
    
    async def export_data(self, export_path: str, format: str = "json") -> bool:
        """Export stored data to file."""
        try:
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'format': format,
                'events': [],
                'markets': [],
                'sync_events': []
            }
            
            # Export events
            for key, record in self.memory_storage.items():
                if record.data_type == "AggregatedEvent":
                    export_data['events'].append({
                        'key': key,
                        'data': asdict(record.value),
                        'metadata': record.metadata
                    })
                elif record.data_type == "MarketData":
                    export_data['markets'].append({
                        'key': key,
                        'data': asdict(record.value),
                        'metadata': record.metadata
                    })
                elif record.data_type == "SyncEvent":
                    export_data['sync_events'].append({
                        'key': key,
                        'data': asdict(record.value),
                        'metadata': record.metadata
                    })
            
            # Write to file
            if format.lower() == "json":
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                # Default to JSON
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Data exported to {export_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the market data store."""
        self.logger.info("Shutting down market data store...")
        
        self.store_active = False
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.compression_task:
            self.compression_task.cancel()
            try:
                await self.compression_task
            except asyncio.CancelledError:
                pass
        
        # Log final statistics
        stats = self.get_performance_stats()
        self.logger.info(f"Final storage stats: {stats}")
        
        self.logger.info("Market data store shutdown complete")


# Global instance
_market_data_store: Optional[MarketDataStore] = None


async def get_market_data_store() -> MarketDataStore:
    """Get global market data store instance."""
    global _market_data_store
    
    if _market_data_store is None:
        _market_data_store = MarketDataStore()
        await _market_data_store.initialize()
    
    return _market_data_store


async def shutdown_market_data_store():
    """Shutdown global market data store."""
    global _market_data_store
    
    if _market_data_store:
        await _market_data_store.shutdown()
        _market_data_store = None