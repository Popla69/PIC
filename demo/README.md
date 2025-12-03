# PIC v1 Demo

## Quick Demo (5 minutes)

### Option 1: Python Script

```bash
# Run demo script
python demo/demo.py
```

### Option 2: Docker Compose

```bash
# Start services
cd demo
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f pic-brain

# Stop services
docker-compose down
```

## What the Demo Shows

1. **Training Phase**: Learns normal behavior from 20 samples
2. **Normal Operation**: Processes 30 normal transactions (all allowed)
3. **Attack Simulation**: Injects 10 anomalous transactions
4. **Detection**: Shows how many anomalies were blocked

## Expected Results

- Training: 20 samples collected
- Normal transactions: 30/30 allowed (0% false positives)
- Anomalous transactions: 7-9/10 blocked (70-90% detection rate)

## Customization

Edit `demo.py` to adjust:
- Number of training samples
- Anomaly patterns (slowloris, spike, gradual, burst, oscillating)
- Detection thresholds
- Sampling rates

## Troubleshooting

### No detections
- Increase training samples
- Lower threshold_percentile in config

### Too many false positives
- Increase training samples
- Raise threshold_percentile in config
