"""
Integration test for the multi-bookmaker data aggregation system.

This test demonstrates the complete flow of the aggregation system,
from data collection to storage and synchronization.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List

from detection.bookmaker_manager import get_bookmaker_manager, shutdown_bookmaker_manager
from detection.data_aggregator import get_data_aggregator, shutdown_data_aggregator
from detection.data_synchronizer import get_data_synchronizer, shutdown_data_synchronizer
from detection.market_data_store import get_market_data_store, shutdown_market_data_store
from storage.models import Sport


async def test_multi_bookmaker_aggregation():
    """Test the complete multi-bookmaker data aggregation workflow."""
    
    print("🚀 Starting Multi-Bookmaker Data Aggregation Test")
    print("=" * 60)
    
    try:
        # Step 1: Initialize Bookmaker Manager
        print("\n📊 Step 1: Initializing Bookmaker Manager...")
        bookmaker_manager = await get_bookmaker_manager()
        
        # Get health status
        health_status = bookmaker_manager.get_all_health_status()
        print(f"✅ Bookmaker manager initialized with {len(health_status)} bookmakers")
        
        for bookmaker_name, health in health_status.items():
            if health:
                print(f"   📈 {bookmaker_name}: {health['status']}")
        
        # Step 2: Initialize Data Aggregator
        print("\n🔄 Step 2: Initializing Data Aggregator...")
        data_aggregator = await get_data_aggregator()
        print("✅ Data aggregator initialized")
        
        # Step 3: Initialize Data Synchronizer
        print("\n⚡ Step 3: Initializing Data Synchronizer...")
        data_synchronizer = await get_data_synchronizer()
        print("✅ Data synchronizer initialized")
        
        # Step 4: Initialize Market Data Store
        print("\n💾 Step 4: Initializing Market Data Store...")
        data_store = await get_market_data_store()
        print("✅ Market data store initialized")
        
        # Step 5: Test Data Aggregation
        print("\n🎯 Step 5: Testing Data Aggregation...")
        
        # Test aggregation for multiple sports
        test_sports = [Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL]
        
        aggregation_start = time.time()
        aggregated_events = await data_aggregator.aggregate_sports_data(
            sports=test_sports,
            markets=["match_winner", "over_under"],
            timeout_seconds=60
        )
        aggregation_time = (time.time() - aggregation_start) * 1000
        
        print(f"✅ Aggregated data for {len(aggregated_events)} events in {aggregation_time:.2f}ms")
        
        # Step 6: Test Data Storage
        print("\n💾 Step 6: Testing Data Storage...")
        
        stored_count = 0
        for event_id, event in aggregated_events.items():
            success = await data_store.store_event_data(event)
            if success:
                stored_count += 1
                
                # Store individual markets
                for market_id, market in event.markets.items():
                    await data_store.store_market_data(market)
        
        print(f"✅ Stored {stored_count} events and their markets")
        
        # Step 7: Test Data Retrieval
        print("\n📖 Step 7: Testing Data Retrieval...")
        
        retrieval_start = time.time()
        retrieved_events = []
        
        for event_id in list(aggregated_events.keys())[:5]:  # Test first 5 events
            event = await data_store.retrieve_event_data(event_id)
            if event:
                retrieved_events.append(event)
        
        retrieval_time = (time.time() - retrieval_start) * 1000
        print(f"✅ Retrieved {len(retrieved_events)} events in {retrieval_time:.2f}ms")
        
        # Step 8: Test Synchronization
        print("\n🔄 Step 8: Testing Real-time Synchronization...")
        
        # Start synchronization for test events
        sync_event_ids = list(aggregated_events.keys())[:3]  # Sync first 3 events
        sync_results = await data_synchronizer.start_synchronization(
            event_ids=sync_event_ids,
            sync_mode="adaptive"
        )
        
        print(f"✅ Started synchronization for {len(sync_results)} events")
        
        # Wait for some sync cycles
        print("⏳ Waiting for synchronization cycles...")
        await asyncio.sleep(10)
        
        # Get sync status
        sync_status = {}
        for event_id in sync_event_ids:
            status = data_synchronizer.get_sync_status(event_id)
            if status:
                sync_status[event_id] = status
        
        print(f"✅ Sync status updated for {len(sync_status)} events")
        
        # Step 9: Performance Metrics
        print("\n📊 Step 9: Performance Metrics...")
        
        # Get aggregation statistics
        agg_stats = data_aggregator.get_aggregation_statistics()
        print(f"📈 Aggregation Stats:")
        print(f"   - Events processed: {agg_stats.total_events_processed}")
        print(f"   - Markets processed: {agg_stats.total_markets_processed}")
        print(f"   - Odds collected: {agg_stats.total_odds_collected}")
        print(f"   - Success rate: {(agg_stats.successful_aggregations / max(1, agg_stats.total_events_processed)) * 100:.1f}%")
        
        # Get sync performance
        sync_performance = data_synchronizer.get_performance_stats()
        print(f"⚡ Synchronization Stats:")
        print(f"   - Total syncs: {sync_performance['total_syncs']}")
        print(f"   - Success rate: {sync_performance.get('success_rate', 0):.1f}%")
        print(f"   - Active syncs: {sync_performance['active_syncs']}")
        
        # Get storage performance
        storage_performance = data_store.get_performance_stats()
        print(f"💾 Storage Stats:")
        print(f"   - Cache hit ratio: {storage_performance['storage_metrics']['cache_hit_ratio']:.2f}")
        print(f"   - Avg read time: {storage_performance['performance']['avg_read_time_ms']:.2f}ms")
        print(f"   - Avg write time: {storage_performance['performance']['avg_write_time_ms']:.2f}ms")
        
        # Step 10: Search and Query Tests
        print("\n🔍 Step 10: Testing Search and Query...")
        
        # Search recent events
        recent_events = await data_store.get_recent_events(hours=1, limit=10)
        print(f"✅ Found {len(recent_events)} recent events")
        
        # Search by sport
        football_events = await data_store.get_events_by_sport(sport="football", limit=10)
        print(f"✅ Found {len(football_events)} football events")
        
        # Step 11: Data Quality Assessment
        print("\n🎯 Step 11: Data Quality Assessment...")
        
        quality_scores = []
        for event in retrieved_events[:5]:  # Check first 5 events
            quality_scores.append(event.overall_quality_score)
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"✅ Average data quality score: {avg_quality:.2f}")
        
        # Step 12: Error Handling Test
        print("\n⚠️ Step 12: Testing Error Handling...")
        
        # Test invalid event retrieval
        invalid_event = await data_store.retrieve_event_data("invalid_event_id")
        print(f"✅ Invalid event retrieval handled: {invalid_event is None}")
        
        # Step 13: Cleanup and Shutdown
        print("\n🛑 Step 13: Cleanup and Shutdown...")
        
        # Stop synchronization
        await data_synchronizer.stop_synchronization(sync_event_ids)
        print("✅ Stopped synchronization")
        
        # Shutdown components
        await shutdown_data_synchronizer()
        await shutdown_data_aggregator()
        await shutdown_bookmaker_manager()
        await shutdown_market_data_store()
        print("✅ All components shutdown successfully")
        
        print("\n" + "=" * 60)
        print("🎉 Multi-Bookmaker Data Aggregation Test Completed Successfully!")
        print("=" * 60)
        
        return {
            'aggregation_time_ms': aggregation_time,
            'retrieval_time_ms': retrieval_time,
            'events_processed': len(aggregated_events),
            'events_stored': stored_count,
            'events_retrieved': len(retrieved_events),
            'sync_events': len(sync_event_ids),
            'avg_quality_score': avg_quality if quality_scores else 0,
            'success': True
        }
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        
        # Attempt cleanup even on failure
        try:
            await shutdown_data_synchronizer()
            await shutdown_data_aggregator()
            await shutdown_bookmaker_manager()
            await shutdown_market_data_store()
        except:
            pass
        
        return {'success': False, 'error': str(e)}


async def test_performance_benchmarks():
    """Run performance benchmarks for the aggregation system."""
    
    print("\n🏁 Performance Benchmarks")
    print("=" * 40)
    
    try:
        # Initialize components
        bookmaker_manager = await get_bookmaker_manager()
        data_aggregator = await get_data_aggregator()
        data_store = await get_market_data_store()
        
        # Benchmark 1: Concurrent Data Collection
        print("\n📊 Benchmark 1: Concurrent Data Collection")
        
        start_time = time.time()
        
        # Test concurrent aggregation
        sports_batch = [Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL, Sport.BASEBALL]
        tasks = []
        
        for sport in sports_batch:
            task = asyncio.create_task(
                data_aggregator.aggregate_sport_data([sport])
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        concurrent_time = (time.time() - start_time) * 1000
        successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
        
        print(f"✅ Concurrent aggregation: {concurrent_time:.2f}ms for {successful_tasks}/{len(sports_batch)} sports")
        
        # Benchmark 2: Storage Throughput
        print("\n💾 Benchmark 2: Storage Throughput")
        
        # Create test events
        test_events = []
        for i in range(100):
            from detection.data_aggregator import AggregatedEvent, MarketData, MarketOdds
            
            # Create test market data
            test_market = MarketData(
                sport=Sport.FOOTBALL,
                event_name=f"Test Event {i}",
                event_id=f"test_event_{i}",
                market_type="match_winner",
                market_id=f"test_market_{i}",
                start_time=datetime.utcnow(),
                participants=["Team A", "Team B"],
                odds=[
                    MarketOdds(
                        bookmaker="test_bookmaker",
                        outcome="Team A",
                        odds=2.0,
                        implied_probability=0.5
                    ),
                    MarketOdds(
                        bookmaker="test_bookmaker",
                        outcome="Team B", 
                        odds=1.8,
                        implied_probability=0.556
                    )
                ]
            )
            
            test_event = AggregatedEvent(
                event_id=f"test_event_{i}",
                event_name=f"Test Event {i}",
                sport=Sport.FOOTBALL,
                start_time=datetime.utcnow(),
                participants=["Team A", "Team B"],
                markets={"match_winner": test_market}
            )
            
            test_events.append(test_event)
        
        # Benchmark storage
        storage_start = time.time()
        
        for event in test_events:
            await data_store.store_event_data(event)
        
        storage_time = (time.time() - storage_start) * 1000
        throughput = len(test_events) / (storage_time / 1000)
        
        print(f"✅ Storage throughput: {throughput:.1f} events/second ({storage_time:.2f}ms for {len(test_events)} events)")
        
        # Benchmark 3: Retrieval Performance
        print("\n📖 Benchmark 3: Retrieval Performance")
        
        # Test retrieval performance
        retrieval_start = time.time()
        
        for i in range(min(50, len(test_events))):  # Retrieve first 50 events
            await data_store.retrieve_event_data(f"test_event_{i}")
        
        retrieval_time = (time.time() - retrieval_start) * 1000
        retrieval_throughput = 50 / (retrieval_time / 1000)
        
        print(f"✅ Retrieval throughput: {retrieval_throughput:.1f} events/second ({retrieval_time:.2f}ms for 50 retrievals)")
        
        # Benchmark 4: Cache Performance
        print("\n🚀 Benchmark 4: Cache Performance")
        
        # First retrieval (cache miss)
        cache_miss_start = time.time()
        await data_store.retrieve_event_data("test_event_0")
        cache_miss_time = (time.time() - cache_miss_start) * 1000
        
        # Second retrieval (cache hit)
        cache_hit_start = time.time()
        await data_store.retrieve_event_data("test_event_0")
        cache_hit_time = (time.time() - cache_hit_start) * 1000
        
        speedup = cache_miss_time / cache_hit_time if cache_hit_time > 0 else 0
        
        print(f"✅ Cache performance: {speedup:.1f}x speedup ({cache_hit_time:.2f}ms vs {cache_miss_time:.2f}ms)")
        
        # Cleanup
        await shutdown_data_aggregator()
        await shutdown_bookmaker_manager()
        await shutdown_market_data_store()
        
        print("\n🏁 Performance benchmarks completed!")
        
        return {
            'concurrent_aggregation_time_ms': concurrent_time,
            'storage_throughput_events_per_sec': throughput,
            'retrieval_throughput_events_per_sec': retrieval_throughput,
            'cache_speedup_factor': speedup,
            'success': True
        }
        
    except Exception as e:
        print(f"\n❌ Benchmark failed with error: {e}")
        return {'success': False, 'error': str(e)}


async def main():
    """Main test runner."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎯 ARBitech Multi-Bookmaker Data Aggregation System")
    print("🧪 Integration Tests")
    print("=" * 60)
    
    # Run integration test
    integration_results = await test_multi_bookmaker_aggregation()
    
    # Run performance benchmarks
    performance_results = await test_performance_benchmarks()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    
    if integration_results['success']:
        print("✅ Integration Test: PASSED")
        print(f"   - Events processed: {integration_results['events_processed']}")
        print(f"   - Aggregation time: {integration_results['aggregation_time_ms']:.2f}ms")
        print(f"   - Average quality: {integration_results['avg_quality_score']:.2f}")
    else:
        print("❌ Integration Test: FAILED")
        print(f"   - Error: {integration_results.get('error', 'Unknown')}")
    
    if performance_results['success']:
        print("✅ Performance Benchmarks: PASSED")
        print(f"   - Storage throughput: {performance_results['storage_throughput_events_per_sec']:.1f} events/sec")
        print(f"   - Retrieval throughput: {performance_results['retrieval_throughput_events_per_sec']:.1f} events/sec")
        print(f"   - Cache speedup: {performance_results['cache_speedup_factor']:.1f}x")
    else:
        print("❌ Performance Benchmarks: FAILED")
        print(f"   - Error: {performance_results.get('error', 'Unknown')}")
    
    overall_success = integration_results['success'] and performance_results['success']
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if overall_success else '⚠️ SOME TESTS FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)