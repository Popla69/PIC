"""Configuration loader with support for YAML, environment variables, and CLI args."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class PICConfig:
    """Centralized configuration management for PIC.
    
    Loads configuration from multiple sources with priority:
    1. CLI arguments (highest priority)
    2. Environment variables (PIC_* prefix)
    3. YAML config file
    4. Built-in defaults (lowest priority)
    """
    
    DEFAULT_CONFIG = {
        "cellagent": {
            "sampling_rate": 0.1,
            "buffer_size": 10000,
            "batch_size": 100,
            "batch_interval_sec": 5,
            "cpu_threshold": 0.02,
        },
        "baseline": {
            "window_hours": 72,
            "min_samples": 20,
            "retrain_interval_hours": 6,
        },
        "anomaly": {
            "threshold_percentile": 95,
            "candidate_score_threshold": 80,
        },
        "effector": {
            "default_action": "allow",
            "fail_safe_mode": "allow",
        },
        "storage": {
            "state_db_path": "/var/lib/pic/state.db",
            "audit_log_path": "/var/lib/pic/audit.log",
            "trace_buffer_size": 1000,
        },
        "api": {
            "listen_address": "127.0.0.1",
            "listen_port": 8443,
            "metrics_enabled": True,
        },
    }
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize with configuration dictionary."""
        self._config = config_dict
    
    @classmethod
    def load(cls, config_path: Optional[str] = None, cli_args: Optional[Dict[str, Any]] = None) -> "PICConfig":
        """Load configuration from all sources.
        
        Args:
            config_path: Path to YAML config file (default: /etc/pic/config.yaml)
            cli_args: Dictionary of CLI arguments to override config
            
        Returns:
            PICConfig instance with merged configuration
        """
        # Start with defaults
        config = cls._deep_copy(cls.DEFAULT_CONFIG)
        
        # Load from YAML file
        if config_path is None:
            config_path = os.getenv("PIC_CONFIG_PATH", "/etc/pic/config.yaml")
        
        if Path(config_path).exists():
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config = cls._deep_merge(config, yaml_config)
        
        # Override with environment variables
        env_config = cls._load_from_env()
        config = cls._deep_merge(config, env_config)
        
        # Override with CLI arguments
        if cli_args:
            config = cls._deep_merge(config, cli_args)
        
        return cls(config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., "cellagent.sampling_rate")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get("cellagent.sampling_rate")
            0.1
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., "cellagent.sampling_rate")
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def reload(self, config_path: Optional[str] = None) -> None:
        """Reload configuration from sources.
        
        Args:
            config_path: Path to YAML config file
        """
        new_config = self.load(config_path)
        self._config = new_config._config
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._deep_copy(self._config)
    
    @staticmethod
    def _load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables with PIC_ prefix.
        
        Environment variables are converted to nested dict structure:
        PIC_CELLAGENT_SAMPLING_RATE=0.2 -> {"cellagent": {"sampling_rate": 0.2}}
        """
        config: Dict[str, Any] = {}
        
        for key, value in os.environ.items():
            if key.startswith("PIC_"):
                # Remove PIC_ prefix and convert to lowercase
                key_without_prefix = key[4:].lower()
                
                # Split only on first underscore to get section and key
                # PIC_CELLAGENT_SAMPLING_RATE -> cellagent, sampling_rate
                parts = key_without_prefix.split("_", 1)
                
                if len(parts) == 2:
                    section, key_name = parts
                    if section not in config:
                        config[section] = {}
                    config[section][key_name] = PICConfig._convert_value(value)
                else:
                    # Single-level key (no section)
                    config[parts[0]] = PICConfig._convert_value(value)
        
        return config
    
    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    @staticmethod
    def _deep_copy(d: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = PICConfig._deep_copy(value)
            else:
                result[key] = value
        return result
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = PICConfig._deep_copy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = PICConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
