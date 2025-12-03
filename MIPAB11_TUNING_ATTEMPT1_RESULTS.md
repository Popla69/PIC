# MIPAB-11 Tuning Attempt #1 Results

## Changes Made
1. **Lowered anomaly threshold**: 95 → 65 percentile
2. **Added pattern memory cache**: Fast-path for known legitimate patterns
3. **Implemented soft-allow mode**: 15% probability for borderline cases (65-75 percentile)

## Test Results

### Baseline (Untuned)
- Legitimate Acceptance: 71.7%
- Malicious Block Rate: 71.6%
- False Positive Rate: 28.3%
- P95 Latency: 7.4ms

### After Tuning Attempt #1
- Legitimate Acceptance: **24.2%** ❌ (WORSE - down from 71.7%)
- Malicious Block Rate: **80.5%** ✅ (improved from 71.6%)
- False Positive Rate: **75.8%** ❌ (MUCH WORSE - up from 28.3%)
- P95 Latency: **7.9ms** ✅ (maintained)

```json
{
  "duration_s": 120.71,
  "total_events": 1200,
  "legit_events": 120,
  "legit_allowed": 29,
  "malicious_events": 1080,
  "malicious_blocked": 869,
  "false_positives": 91,
  "false_negatives": 211,
  "p50_latency_ms": 1.58,
  "p95_latency_ms": 7.92,
  "p99_latency_ms": 13.86,
  "peak_throughput_eps": 9.94,
  "backpressure_time_fraction": 0.0,
  "nonce_replays_detected": 180,
  "signature_errors": 9
}
```

## Analysis

### What Went Wrong

**Critical Error**: Lowering the anomaly threshold from 95 to 65 made the system MORE aggressive, not less.

**Why**: The anomaly score is a percentile ranking:
- Score of 50 = median (normal)
- Score of 95 = 95th percentile (very anomalous)
- **Lowering threshold to 65 means blocking anything above 65th percentile**
- This is TOO aggressive - we're blocking events that are only slightly above median

**Result**: 
- False positives skyrocketed from 28.3% to 75.8%
- 91 out of 120 legitimate events were incorrectly blocked
- System became unusable for legitimate users

### What Worked

1. **Pattern Cache**: Not utilized effectively because most events were blocked before reaching cache
2. **Soft-Allow Mode**: Helped slightly but couldn't overcome the overly aggressive threshold
3. **Performance**: P95 latency remained excellent at 7.9ms

### Root Cause

The tuning recommendations were based on a misunderstanding of the scoring system:
- **Recommendation said**: "Lower anomaly threshold from 0.85 → 0.65"
- **What we did**: Lowered from 95 → 65 (percentile scale)
- **What we should have done**: The threshold needs to be RAISED, not lowered, OR we need to change how the threshold is interpreted

## Next Steps

### Option 1: Invert the Threshold Logic
Instead of "block if score > threshold", use "block if score < threshold" where threshold represents "confidence in legitimacy"

### Option 2: Raise the Threshold
- Increase threshold from 65 back to 95 or even higher (98-99)
- This makes the system less aggressive
- Only block truly extreme outliers

### Option 3: Change Scoring System
- Normalize scores to 0.0-1.0 range where:
  - 0.0 = definitely normal
  - 1.0 = definitely anomalous
- Then threshold of 0.65 makes sense

### Option 4: Use Confidence Scoring
- Instead of percentile, use confidence that event is legitimate
- Threshold of 0.65 means "block if confidence < 65%"

## Recommendation

**Immediate Fix**: Raise the anomaly threshold to 98-99 percentile to make the system less aggressive. This will:
- Reduce false positives dramatically
- Still catch extreme outliers
- Allow pattern cache to build up legitimate patterns
- Let soft-allow mode work on truly borderline cases

**Long-term Fix**: Redesign the scoring system to use confidence-based scoring (0.0-1.0) where the threshold interpretation is more intuitive.

## Lessons Learned

1. **Understand the scoring system before tuning**: Percentile-based scoring is counter-intuitive
2. **Test incrementally**: Should have tested with threshold=98 first, then adjusted
3. **Monitor both metrics**: Improving malicious block rate while destroying legitimate acceptance is not a win
4. **Pattern cache needs time**: Can't evaluate cache effectiveness when everything is blocked

## Status

**FAILED** - Tuning attempt made the system significantly worse. Need to reverse changes and try again with correct threshold direction.
