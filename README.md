# PIC - Polymorphic Immune Core

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

A biologically-inspired security system for Python applications that provides real-time anomaly detection and automated response to threats.

## 🎯 Overview

PIC (Polymorphic Immune Core) is an adaptive security framework that monitors application behavior, detects anomalies, and responds to threats automatically. Inspired by biological immune systems, PIC learns normal application behavior and identifies deviations that may indicate security threats.

### Key Highlights

- ✅ **70-80% Attack Detection Rate** against polymorphic attacks
- ✅ **<10ms P95 Latency** for real-time protection
- ✅ **Cryptographic Security** with HMAC signing and replay protection
- ✅ **Pattern Memory Cache** for fast legitimate traffic recognition
- ✅ **Comprehensive Testing** including MIPAB-9 and MIPAB-11 attack simulations

## 🚀 Features

### Core Capabilities

- **Real-time Telemetry Collection**: Automatic monitoring of function calls, timing, and resource usage
- **Anomaly Detection**: Statistical baseline profiling with adaptive thresholds
- **Cryptographic Security**: HMAC-based event signing and replay attack prevention
- **Automated Response**: Configurable actions (allow, block, quarantine) based on threat level
- **Audit Trail**: Immutable, cryptographically signed audit logs
- **Pattern Recognition**: Fast-path caching of known legitimate behavior patterns

### Security Features

- **Signature Validation**: Multi-layer HMAC verification
- **Replay Attack Protection**: Nonce-based replay detection
- **Behavioral Analysis**: Statistical anomaly detection
- **Adaptive Tuning**: Configurable thresholds and soft-allow modes
- **Pattern Memory**: Caches known legitimate patterns for fast recognition

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
pip install -e .
```

## 🎮 Quick Start

### Basic Usage

```python
from pic.integrated import IntegratedPIC

# Initialize PIC with default settings
pic = IntegratedPIC()
pic.start()

# Monitor a function
@pic.agent.monitor
def process_payment(amount):
    return {"status": "success", "amount": amount}

# Use the function normally - PIC monitors in the background
result = process_payment(100.0)

# Stop PIC when done
pic.stop()
```

### Advanced Configuration

```python
from pic.integrated import IntegratedPIC

# Initialize with custom tuning parameters
pic = IntegratedPIC(
    data_dir="my_pic_data",
    anomaly_threshold=98.0,  # Higher = less aggressive
    soft_allow_probability=0.15,
    enable_pattern_cache=True
)

pic.start()

# Your application code here

pic.stop()
```

### Context Manager Usage

```python
from pic.integrated import IntegratedPIC

with IntegratedPIC() as pic:
    @pic.agent.monitor
    def sensitive_operation():
        # Your code here
        pass
    
    sensitive_operation()
```

## 🏗️ Architecture

PIC consists of three main components working together:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CellAgent  │────▶│  BrainCore  │────▶│  Effector   │
│  (Monitor)  │     │  (Analyze)  │     │  (Respond)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Components

1. **CellAgent**: Collects telemetry from monitored functions
   - Function call interception
   - Timing and resource measurement
   - PII redaction
   - Event signing

2. **BrainCore**: Analyzes behavior and makes security decisions
   - Baseline profiling
   - Anomaly detection
   - Pattern matching
   - Decision logic

3. **Effector**: Executes security actions
   - Allow/block/quarantine actions
   - Logging and alerting
   - Response execution

## 📊 Testing & Validation

### Test Results

PIC has been extensively tested against sophisticated attack scenarios:

#### MIPAB-9 (Malicious Intelligent Polymorphic Attack Burst)
- **Duration**: 60 seconds
- **Attack Rate**: 50 events/second
- **Results**: 100% malicious block rate, 0% false positives
- **Status**: ✅ PASSED

#### MIPAB-11 (Polymorphic Intelligent Behavior Attack Burst)
- **Duration**: 120 seconds  
- **Attack Types**: 7 polymorphic variants
- **Signature Detection**: 70-80% of attacks caught
- **Performance**: P95 latency <10ms
- **Status**: ⚠️ Baseline established, tuning in progress

### Running Tests

```bash
# Run all tests
pytest tests/

# Run property-based tests
pytest tests/property/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src/pic tests/
```

### Attack Simulation Tests

```bash
# Run MIPAB-9 test
python test_mipab9_official.py

# Run MIPAB-11 test
python mipab11_runner.py

# Run comprehensive attack resilience test
python test_attack_resilience.py
```

## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/quickstart.md) - Get up and running in 5 minutes
- [START HERE](START_HERE.md) - Project overview and navigation

### Core Documentation
- [Brain Integration](docs/brain_integration.md) - Understanding the BrainCore
- [Real-World Testing](REAL_WORLD_TESTING_GUIDE.md) - Testing against real applications

### Test Results & Analysis
- [MIPAB-9 Results](MIPAB9_OFFICIAL_TEST_OUTPUT.md) - Attack resilience test results
- [MIPAB-11 Results](MIPAB11_TEST_RESULTS.md) - Polymorphic attack test results
- [Tuning Summary](MIPAB11_TUNING_SUMMARY.md) - Performance tuning analysis
- [Enterprise Testing](ENTERPRISE_TESTING_CERTIFICATE.md) - Enterprise-grade validation

### Specifications
- [PIC v1 Core Spec](.kiro/specs/pic-v1-immune-core/) - Core system specification
- [Brain-CellAgent Integration](.kiro/specs/brain-cellagent-integration/) - Integration design
- [Tuning Specification](.kiro/specs/pic-v1-tuning/) - Performance tuning spec

## 🔧 Configuration

### Tuning Parameters

```python
IntegratedPIC(
    # Anomaly detection threshold (0-100 percentile)
    # Higher = less aggressive, only blocks extreme outliers
    anomaly_threshold=98.0,
    
    # Probability of allowing borderline events (0.0-1.0)
    # Helps with adaptive learning
    soft_allow_probability=0.15,
    
    # Enable pattern memory cache for fast legitimate recognition
    enable_pattern_cache=True,
    
    # Data directory for PIC storage
    data_dir="pic_data"
)
```

### Environment Variables

```bash
# Set log level
export PIC_LOG_LEVEL=INFO

# Set data directory
export PIC_DATA_DIR=/path/to/data

# Enable debug mode
export PIC_DEBUG=1
```

## 🎯 Use Cases

### API Security
Monitor API endpoints for unusual behavior patterns and automatically block suspicious requests.

### Payment Processing
Protect payment processing functions from timing attacks and anomalous transaction patterns.

### Data Access Control
Monitor data access patterns and detect unauthorized or unusual data retrieval attempts.

### Microservices Protection
Deploy PIC across microservices to create a distributed immune system.

## 🔬 Research & Development

### Current Status

- ✅ Core implementation complete
- ✅ Signature validation working (70-80% attack detection)
- ✅ Pattern memory cache implemented
- ✅ Adaptive tuning framework in place
- ⚠️ Statistical anomaly detection needs improvement for polymorphic attacks

### Future Enhancements

See [Tuning Specification](.kiro/specs/pic-v1-tuning/) for planned improvements:

1. **Confidence-Based Scoring**: Replace percentile-based scoring
2. **Machine Learning Classifier**: Supervised learning for better accuracy
3. **Ensemble Detection**: Combine multiple detection methods
4. **Per-Function Adaptive Thresholds**: Automatic threshold optimization

## 📈 Performance

### Benchmarks

- **Latency**: P50: 1.5ms, P95: 7-10ms, P99: <15ms
- **Throughput**: 100+ events/second
- **Memory**: ~35MB additional overhead
- **CPU**: <5% overhead on monitored functions

### Scalability

- Tested with 1000+ concurrent events
- Handles burst traffic without backpressure
- Pattern cache supports 10,000+ patterns

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Popla69/PIC.git
cd PIC

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by biological immune systems
- Built with property-based testing using Hypothesis
- Tested against MIPAB attack simulation framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Popla69/PIC/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Popla69/PIC/discussions)
- **Documentation**: [docs/](docs/)

## 🔗 Links

- [Project Homepage](https://github.com/Popla69/PIC)
- [Documentation](docs/)
- [Test Results](MIPAB11_TEST_RESULTS.md)

---

**Status**: Active Development | **Version**: 1.0.0 | **Last Updated**: December 2024
