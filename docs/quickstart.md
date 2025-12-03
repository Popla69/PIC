# PIC v1 Quick Start Guide

## 5-Minute Tutorial

### Step 1: Install PIC

```bash
pip install pic-immune-core
```

### Step 2: Create Configuration

Create `/etc/pic/config.yaml`:

```yaml
cellagent:
  sampling_rate: 0.1
  buffer_size: 10000

baseline:
  min_samples: 20

anomaly:
  threshold_percentile: 95

storage:
  state_db_path: /var/lib/pic/state.db
  audit_log_path: /var/lib/pic/audit.log
```

### Step 3: Instrument Your Application

```python
from pic.cellagent import CellAgent

# Initialize agent
agent = CellAgent()

# Decorate critical functions
@agent.monitor
def transfer_funds(from_account, to_account, amount):
    # Your business logic
    if amount > 10000:
        # This might trigger anomaly detection
        pass
    return {"status": "success"}
```

### Step 4: Start SentinelBrain

```bash
# Terminal 1: Start detection service
pic start

# Terminal 2: Run your application
python your_app.py
```

### Step 5: Monitor and Respond

```bash
# Check system status
pic status

# View metrics
curl http://localhost:8443/metrics

# Export audit logs
pic logs export
```

## What Happens Next?

1. **Training Phase** (first 20+ samples):
   - PIC learns normal behavior
   - Builds statistical baseline
   - All requests allowed

2. **Detection Phase** (after training):
   - Compares new requests to baseline
   - Calculates anomaly scores
   - Blocks suspicious requests

3. **Continuous Learning**:
   - Baselines updated every 6 hours
   - Adapts to changing patterns
   - Maintains low false positive rate

## Next Steps

- Read [Configuration Guide](configuration.md)
- Explore [API Documentation](api.md)
- Review [Best Practices](best-practices.md)
