"""Unit tests for PICConfig."""

import os
import tempfile
import pytest
from pathlib import Path

from pic.config import PICConfig


def test_default_config():
    """Test loading default configuration."""
    config = PICConfig.load(config_path="/nonexistent/path.yaml")
    
    assert config.get("cellagent.sampling_rate") == 0.1
    assert config.get("baseline.min_samples") == 20
    assert config.get("effector.default_action") == "allow"


def test_yaml_config_loading():
    """Test loading configuration from YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
cellagent:
  sampling_rate: 0.2
  buffer_size: 5000
baseline:
  min_samples: 30
""")
        config_path = f.name
    
    try:
        config = PICConfig.load(config_path=config_path)
        
        assert config.get("cellagent.sampling_rate") == 0.2
        assert config.get("cellagent.buffer_size") == 5000
        assert config.get("baseline.min_samples") == 30
        # Default values should still be present
        assert config.get("effector.default_action") == "allow"
    finally:
        os.unlink(config_path)


def test_env_var_override():
    """Test environment variable override."""
    os.environ["PIC_CELLAGENT_SAMPLING_RATE"] = "0.3"
    os.environ["PIC_BASELINE_MIN_SAMPLES"] = "40"
    
    try:
        config = PICConfig.load(config_path="/nonexistent/path.yaml")
        
        assert config.get("cellagent.sampling_rate") == 0.3
        assert config.get("baseline.min_samples") == 40
    finally:
        del os.environ["PIC_CELLAGENT_SAMPLING_RATE"]
        del os.environ["PIC_BASELINE_MIN_SAMPLES"]


def test_cli_args_override():
    """Test CLI arguments override."""
    cli_args = {
        "cellagent": {"sampling_rate": 0.5},
        "baseline": {"min_samples": 50}
    }
    
    config = PICConfig.load(config_path="/nonexistent/path.yaml", cli_args=cli_args)
    
    assert config.get("cellagent.sampling_rate") == 0.5
    assert config.get("baseline.min_samples") == 50


def test_priority_order():
    """Test that CLI > env > file > defaults."""
    # Create YAML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("cellagent:\n  sampling_rate: 0.2\n")
        config_path = f.name
    
    # Set env var
    os.environ["PIC_CELLAGENT_SAMPLING_RATE"] = "0.3"
    
    # Set CLI arg
    cli_args = {"cellagent": {"sampling_rate": 0.4}}
    
    try:
        config = PICConfig.load(config_path=config_path, cli_args=cli_args)
        
        # CLI should win
        assert config.get("cellagent.sampling_rate") == 0.4
    finally:
        os.unlink(config_path)
        del os.environ["PIC_CELLAGENT_SAMPLING_RATE"]


def test_get_with_default():
    """Test get method with default value."""
    config = PICConfig.load(config_path="/nonexistent/path.yaml")
    
    assert config.get("nonexistent.key", "default_value") == "default_value"
    assert config.get("cellagent.nonexistent", 999) == 999


def test_set_value():
    """Test setting configuration values."""
    config = PICConfig.load(config_path="/nonexistent/path.yaml")
    
    config.set("cellagent.sampling_rate", 0.7)
    assert config.get("cellagent.sampling_rate") == 0.7
    
    config.set("new.nested.key", "value")
    assert config.get("new.nested.key") == "value"


def test_to_dict():
    """Test converting config to dictionary."""
    config = PICConfig.load(config_path="/nonexistent/path.yaml")
    
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "cellagent" in config_dict
    assert config_dict["cellagent"]["sampling_rate"] == 0.1


def test_type_conversion():
    """Test environment variable type conversion."""
    os.environ["PIC_TEST_BOOL_TRUE"] = "true"
    os.environ["PIC_TEST_BOOL_FALSE"] = "false"
    os.environ["PIC_TEST_INT"] = "42"
    os.environ["PIC_TEST_FLOAT"] = "3.14"
    os.environ["PIC_TEST_STRING"] = "hello"
    
    try:
        config = PICConfig.load(config_path="/nonexistent/path.yaml")
        
        # PIC_TEST_BOOL_TRUE becomes test.bool_true (not test.bool.true)
        assert config.get("test.bool_true") is True
        assert config.get("test.bool_false") is False
        assert config.get("test.int") == 42
        assert config.get("test.float") == 3.14
        assert config.get("test.string") == "hello"
    finally:
        for key in ["PIC_TEST_BOOL_TRUE", "PIC_TEST_BOOL_FALSE", "PIC_TEST_INT", 
                    "PIC_TEST_FLOAT", "PIC_TEST_STRING"]:
            if key in os.environ:
                del os.environ[key]
