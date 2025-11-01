"""
VLM Configuration Management

This module provides configuration classes and utilities for the Qwen-VL Vision
Language Model integration, including model parameters, performance settings, and
validation utilities.
"""

import os
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import time


class ModelStatus(Enum):
    """Model loading and status enumeration"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    TIMEOUT = "timeout"


class ModelPrecision(Enum):
    """Model precision options"""
    FP16 = "fp16"
    FP32 = "fp32"
    INT8 = "int8"
    INT4 = "int4"


class DeviceType(Enum):
    """Device type options for model execution"""
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon


@dataclass
class ModelParameters:
    """Model parameters configuration"""
    # Model identification
    model_name: str = "Qwen/Qwen2-VL-2B-Instruct"
    model_path: Optional[str] = None
    trust_remote_code: bool = True
    
    # Device and precision
    device: DeviceType = DeviceType.AUTO
    precision: ModelPrecision = ModelPrecision.FP16
    
    # Generation parameters
    max_new_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    
    # Image processing
    image_size: int = 224
    patch_size: int = 14
    
    # Context and memory
    max_length: int = 2048
    cache_size: int = 1024
    
    # Model loading
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    device_map: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, 'value'):  # Handle enums
                result[key] = value.value
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelParameters':
        """Create parameters from dictionary"""
        # Convert enum values back to enums
        if 'device' in data and isinstance(data['device'], str):
            data['device'] = DeviceType(data['device'])
        if 'precision' in data and isinstance(data['precision'], str):
            data['precision'] = ModelPrecision(data['precision'])
        
        return cls(**data)


@dataclass
class PerformanceConfig:
    """Performance and optimization settings"""
    # Batch processing
    batch_size: int = 1
    max_batch_size: int = 4
    
    # Memory management
    max_memory_per_gpu: Optional[str] = None
    cpu_offload: bool = False
    
    # Streaming
    use_streaming: bool = True
    stream_interval: float = 0.1
    
    # Caching
    use_cache: bool = True
    cache_dir: str = ".cache/vlm"
    
    # Worker threads
    num_workers: int = 4
    max_queue_size: int = 100
    
    # Timeout settings
    model_load_timeout: int = 300  # 5 minutes
    inference_timeout: int = 30    # 30 seconds
    
    # Rate limiting
    requests_per_minute: int = 60
    burst_limit: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in self.__dict__.items()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""
    # Performance monitoring
    enable_performance_monitoring: bool = True
    metrics_interval: float = 60.0  # seconds
    
    # Memory monitoring
    monitor_memory_usage: bool = True
    memory_threshold: float = 0.8  # 80%
    
    # Error tracking
    track_errors: bool = True
    error_threshold: int = 10  # errors per hour
    
    # Logging
    enable_detailed_logging: bool = True
    log_file: Optional[str] = None
    
    # Health checks
    enable_health_checks: bool = True
    health_check_interval: float = 300.0  # 5 minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class VLMConfig:
    """Main VLM configuration class"""
    # Model configuration
    model: ModelParameters = field(default_factory=ModelParameters)
    
    # Performance settings
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Monitoring settings
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "enable_image_processing": True,
        "enable_batch_processing": False,
        "enable_caching": True,
        "enable_async_inference": True,
        "enable_error_recovery": True,
        "enable_metrics_collection": True
    })
    
    # Paths
    cache_dir: str = ".cache/vlm"
    model_cache_dir: str = ".cache/models"
    log_dir: str = "logs/vlm"
    
    # Validation
    validate_on_load: bool = True
    strict_validation: bool = True
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        if self.validate_on_load:
            validate_config(self)
        
        # Ensure directories exist
        for dir_path in [self.cache_dir, self.model_cache_dir, self.log_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "model": self.model.to_dict(),
            "performance": self.performance.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "features": self.features.copy(),
            "cache_dir": self.cache_dir,
            "model_cache_dir": self.model_cache_dir,
            "log_dir": self.log_dir,
            "validate_on_load": self.validate_on_load,
            "strict_validation": self.strict_validation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VLMConfig':
        """Create configuration from dictionary"""
        model_data = data.get('model', {})
        performance_data = data.get('performance', {})
        monitoring_data = data.get('monitoring', {})
        
        model = ModelParameters.from_dict(model_data) if model_data else ModelParameters()
        performance = PerformanceConfig.from_dict(performance_data) if performance_data else PerformanceConfig()
        monitoring = MonitoringConfig.from_dict(monitoring_data) if monitoring_data else MonitoringConfig()
        
        return cls(
            model=model,
            performance=performance,
            monitoring=monitoring,
            features=data.get('features', {}),
            cache_dir=data.get('cache_dir', '.cache/vlm'),
            model_cache_dir=data.get('model_cache_dir', '.cache/models'),
            log_dir=data.get('log_dir', 'logs/vlm'),
            validate_on_load=data.get('validate_on_load', True),
            strict_validation=data.get('strict_validation', True)
        )
    
    def get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with environment overrides"""
        config_dict = self.to_dict()
        
        # Apply environment variable overrides
        env_overrides = self._get_env_overrides()
        config_dict.update(env_overrides)
        
        return config_dict
    
    def _get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Model parameters
        if os.getenv('ARBITECH_VLM_MODEL_NAME'):
            overrides['model'] = overrides.get('model', {})
            overrides['model']['model_name'] = os.getenv('ARBITECH_VLM_MODEL_NAME')
        
        if os.getenv('ARBITECH_VLM_DEVICE'):
            overrides['model'] = overrides.get('model', {})
            overrides['model']['device'] = os.getenv('ARBITECH_VLM_DEVICE')
        
        if os.getenv('ARBITECH_VLM_PRECISION'):
            overrides['model'] = overrides.get('model', {})
            overrides['model']['precision'] = os.getenv('ARBITECH_VLM_PRECISION')
        
        # Performance settings
        if os.getenv('ARBITECH_VLM_BATCH_SIZE'):
            overrides['performance'] = overrides.get('performance', {})
            overrides['performance']['batch_size'] = int(os.getenv('ARBITECH_VLM_BATCH_SIZE'))
        
        if os.getenv('ARBITECH_VLM_TIMEOUT'):
            overrides['performance'] = overrides.get('performance', {})
            overrides['performance']['inference_timeout'] = int(os.getenv('ARBITECH_VLM_TIMEOUT'))
        
        # Paths
        if os.getenv('ARBITECH_VLM_CACHE_DIR'):
            overrides['cache_dir'] = os.getenv('ARBITECH_VLM_CACHE_DIR')
        
        if os.getenv('ARBITECH_VLM_LOG_DIR'):
            overrides['log_dir'] = os.getenv('ARBITECH_VLM_LOG_DIR')
        
        return overrides
    
    def update_from_config(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        # Update model parameters
        if 'model' in config_dict:
            model_dict = config_dict['model']
            for key, value in model_dict.items():
                if hasattr(self.model, key):
                    if hasattr(value, 'value'):  # Handle enums
                        setattr(self.model, key, type(getattr(self.model, key))(value))
                    else:
                        setattr(self.model, key, value)
        
        # Update performance settings
        if 'performance' in config_dict:
            perf_dict = config_dict['performance']
            for key, value in perf_dict.items():
                if hasattr(self.performance, key):
                    setattr(self.performance, key, value)
        
        # Update monitoring settings
        if 'monitoring' in config_dict:
            mon_dict = config_dict['monitoring']
            for key, value in mon_dict.items():
                if hasattr(self.monitoring, key):
                    setattr(self.monitoring, key, value)
        
        # Update other settings
        for key in ['features', 'cache_dir', 'model_cache_dir', 'log_dir']:
            if key in config_dict:
                setattr(self, key, config_dict[key])
        
        # Validate after update
        if self.validate_on_load:
            validate_config(self)


def get_default_config() -> VLMConfig:
    """Get default VLM configuration"""
    return VLMConfig()


def validate_config(config: VLMConfig) -> bool:
    """Validate VLM configuration"""
    logger = logging.getLogger(__name__)
    errors = []
    
    # Validate model parameters
    model = config.model
    
    if not model.model_name:
        errors.append("Model name is required")
    
    if model.max_new_tokens <= 0:
        errors.append("max_new_tokens must be positive")
    
    if not 0 <= model.temperature <= 2:
        errors.append("temperature must be between 0 and 2")
    
    if not 0 < model.top_p <= 1:
        errors.append("top_p must be between 0 and 1")
    
    if model.top_k <= 0:
        errors.append("top_k must be positive")
    
    # Validate performance settings
    performance = config.performance
    
    if performance.batch_size <= 0:
        errors.append("batch_size must be positive")
    
    if performance.inference_timeout <= 0:
        errors.append("inference_timeout must be positive")
    
    if performance.requests_per_minute <= 0:
        errors.append("requests_per_minute must be positive")
    
    # Validate paths
    required_dirs = [config.cache_dir, config.model_cache_dir, config.log_dir]
    for dir_path in required_dirs:
        if not dir_path:
            errors.append(f"Required path: {dir_path}")
    
    # Memory validation
    if performance.max_memory_per_gpu:
        try:
            # Basic format validation for memory strings like "8GB"
            memory_str = performance.max_memory_per_gpu.upper()
            if not any(memory_str.endswith(unit) for unit in ['MB', 'GB', 'TB']):
                errors.append("max_memory_per_gpu must have valid format (e.g., '8GB')")
        except Exception:
            errors.append("Invalid max_memory_per_gpu format")
    
    # Report validation results
    if errors:
        error_msg = "VLM configuration validation failed:\n" + "\n".join(f"- {err}" for err in errors)
        if config.strict_validation:
            raise ValueError(error_msg)
        else:
            logger.warning(error_msg)
            return False
    
    logger.info("VLM configuration validation passed")
    return True


def load_config_from_file(file_path: str) -> VLMConfig:
    """Load configuration from YAML file"""
    import yaml
    
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return VLMConfig.from_dict(data)


def save_config_to_file(config: VLMConfig, file_path: str) -> None:
    """Save configuration to YAML file"""
    import yaml
    
    with open(file_path, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)


def create_config_from_env() -> VLMConfig:
    """Create configuration from environment variables"""
    config = get_default_config()
    
    # Apply environment overrides
    env_overrides = config._get_env_overrides()
    config.update_from_config(env_overrides)
    
    return config


def get_optimal_device_config() -> Dict[str, Any]:
    """Get optimal device configuration based on system capabilities"""
    try:
        import torch
    except ImportError:
        return {
            "device": "cpu",
            "precision": "fp32",
            "load_in_8bit": False,
            "load_in_4bit": False,
            "cpu_offload": False
        }
    
    config = {
        "device": "auto",
        "precision": "fp16",
        "load_in_8bit": False,
        "load_in_4bit": False,
        "cpu_offload": False
    }
    
    # Check for CUDA availability
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_memory = [torch.cuda.get_device_properties(i).total_memory for i in range(gpu_count)]
        
        # Use 8-bit quantization for GPUs with less than 8GB memory
        if gpu_memory and min(gpu_memory) < 8 * 1024**3:  # 8GB in bytes
            config["load_in_8bit"] = True
            config["precision"] = "int8"
        
        config["device"] = "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        # Apple Silicon
        config["device"] = "mps"
        config["precision"] = "fp16"
    else:
        # CPU only
        config["device"] = "cpu"
        config["precision"] = "fp32"
        config["load_in_8bit"] = True  # Enable quantization for CPU
    
    return config
