"""PIC v1 Demo Script - 5-minute demonstration."""

import time
import random
from datetime import datetime
from pic.cellagent import CellAgent
from pic.testing.generators import TestDataGenerator

print("=" * 60)
print("PIC v1 (Popla Immune Core) - Demo")
print("=" * 60)
print()

# Initialize agent
print("[1/5] Initializing CellAgent...")
agent = CellAgent(sampling_rate=1.0)  # 100% sampling for demo
print("✓ Agent initialized")
print()

# Create monitored function
@agent.monitor
def process_transaction(amount: float, user_id: str) -> dict:
    """Simulated transaction processing."""
    time.sleep(amount / 1000)  # Simulate processing time
    return {"status": "success", "amount": amount, "user": user_id}

# Generate test data
print("[2/5] Generating test data...")
generator = TestDataGenerator(seed=42)
benign_events = generator.generate_benign_events(count=100)
malicious_events = generator.generate_malicious_events(pattern="spike", count=20)
print(f"✓ Generated {len(benign_events)} benign + {len(malicious_events)} malicious events")
print()

# Training phase
print("[3/5] Training baseline (20 samples)...")
for i in range(20):
    amount = 50.0 + random.gauss(0, 10)
    process_transaction(amount, f"user{i}")
    if i % 5 == 0:
        print(f"  Training: {i+1}/20 samples")
print("✓ Baseline trained")
print()

# Normal operation
print("[4/5] Processing normal transactions...")
normal_count = 0
for i in range(30):
    amount = 50.0 + random.gauss(0, 10)
    result = process_transaction(amount, f"user{i+20}")
    normal_count += 1
    if i % 10 == 0:
        print(f"  Processed: {i+1}/30 transactions")
print(f"✓ {normal_count} normal transactions processed")
print()

# Anomalous operation
print("[5/5] Injecting anomalous transactions...")
blocked_count = 0
for i in range(10):
    # Anomalous: 10x normal duration
    amount = 500.0 + random.gauss(0, 50)
    try:
        result = process_transaction(amount, f"attacker{i}")
        if result is None:
            blocked_count += 1
    except Exception:
        blocked_count += 1
    if i % 5 == 0:
        print(f"  Tested: {i+1}/10 anomalous transactions")
print(f"✓ {blocked_count}/10 anomalous transactions blocked")
print()

# Summary
print("=" * 60)
print("Demo Complete!")
print("=" * 60)
print(f"Training samples: 20")
print(f"Normal transactions: {normal_count}")
print(f"Anomalous transactions: 10")
print(f"Blocked: {blocked_count}")
print(f"Detection rate: {blocked_count/10*100:.1f}%")
print()
print("Next steps:")
print("  - Start SentinelBrain: pic start")
print("  - View metrics: curl http://localhost:8443/metrics")
print("  - Export logs: pic logs export")
print("=" * 60)
