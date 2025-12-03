# Vulnerable Applications for PIC Testing

⚠️ **WARNING: INTENTIONALLY INSECURE APPLICATIONS** ⚠️

These applications contain deliberate security vulnerabilities for testing PIC's detection capabilities. **DO NOT** deploy these to production or expose them to the internet.

## Purpose

These vulnerable applications are designed to test PIC's ability to detect real-world attack patterns in a safe, controlled environment. Each application simulates common security vulnerabilities that PIC should detect and respond to.

## Applications

### 1. Flask Vulnerable Web App (`flask_vulnerable.py`)

A Flask-based web application with multiple intentional vulnerabilities:

**Vulnerabilities:**
- **SQL Injection** (`/search`) - Direct string interpolation in SQL queries
- **Timing Attacks** (`/login`) - Character-by-character password comparison
- **Server-Side Template Injection** (`/render`) - Unsafe template rendering
- **Slowloris Attack** (`/slow`) - No timeout protection
- **Unrestricted File Upload** (`/upload`) - No file validation
- **Code Injection** (`/eval`) - Direct eval() of user input

**PIC Should Detect:**
- Unusual string patterns and high entropy in SQL injection attempts
- Abnormal timing patterns in authentication
- Suspicious template patterns
- Abnormal execution duration
- Unusual file sizes and patterns
- Code injection patterns

**Running:**
```bash
python examples/vulnerable_apps/flask_vulnerable.py
```

Access at: http://127.0.0.1:5000

### 2. FastAPI Microservices (`fastapi_microservices.py`)

Three microservices demonstrating distributed system vulnerabilities:

**Services:**

1. **Auth Service** (Port 8001)
   - Vulnerable login with timing attacks
   - No rate limiting on failed attempts
   - Timing leaks reveal user existence

2. **Billing Service** (Port 8002)
   - No validation on transaction amounts
   - Timing leaks based on transaction size
   - No authentication required

3. **API Gateway** (Port 8000)
   - No rate limiting
   - Information disclosure in health checks
   - No authentication on critical endpoints

**PIC Should Detect:**
- Login failure spikes
- Brute force patterns
- Unusual transaction patterns
- Abnormal amounts
- Suspicious transaction rates
- CPU correlation with operations

**Running:**

Run each service in a separate terminal:

```bash
# Terminal 1 - Auth Service
python examples/vulnerable_apps/fastapi_microservices.py auth

# Terminal 2 - Billing Service
python examples/vulnerable_apps/fastapi_microservices.py billing

# Terminal 3 - API Gateway
python examples/vulnerable_apps/fastapi_microservices.py gateway
```

## Testing with PIC

### Basic Testing

1. **Wrap the application with PIC:**

```python
from pic.cellagent import CellAgent
from flask_vulnerable import app

# Initialize PIC
agent = CellAgent(sampling_rate=1.0)

# Wrap Flask routes
@agent.monitor
def wrapped_search():
    return app.view_functions['search']()

# Run application with PIC monitoring
```

2. **Generate attack traffic:**

```bash
# SQL Injection
curl "http://localhost:5000/search?q=' OR '1'='1"

# Timing Attack
for i in {1..100}; do
  curl -X POST http://localhost:5000/login \
    -d "username=admin&password=wrong$i"
done

# Slowloris
curl "http://localhost:5000/slow?delay=10"
```

3. **Monitor PIC detection:**

Check PIC logs and audit trail for:
- Anomaly scores above threshold
- Effector responses
- Forensic data collection

### Advanced Testing with Real-World Test Suite

Use the PIC Real-World Test Suite for comprehensive testing:

```bash
# Run all tests against vulnerable apps
pic-realworld run-webservice

# Run specific attack simulations
pic-realworld run-vulnerable

# Generate comprehensive report
pic-realworld run-all --output-dir ./results
```

## Attack Scenarios

### Scenario 1: SQL Injection Detection

**Attack:**
```bash
curl "http://localhost:5000/search?q=' UNION SELECT * FROM users--"
```

**Expected PIC Behavior:**
- Detect unusual string patterns
- High entropy score
- Anomaly score > 0.7
- Log forensic data

### Scenario 2: Brute Force Detection

**Attack:**
```python
import requests

for i in range(1000):
    requests.post('http://localhost:5000/login', data={
        'username': 'admin',
        'password': f'attempt{i}'
    })
```

**Expected PIC Behavior:**
- Detect login failure spike
- Identify brute force pattern
- Trigger effector response after threshold
- Block or rate-limit requests

### Scenario 3: Slowloris Attack

**Attack:**
```python
import requests
import concurrent.futures

def slow_request():
    requests.get('http://localhost:5000/slow?delay=30')

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(slow_request) for _ in range(50)]
```

**Expected PIC Behavior:**
- Detect abnormal execution duration
- Identify resource exhaustion pattern
- Monitor system stability
- Apply sampling if needed

### Scenario 4: Transaction Fraud Detection

**Attack:**
```python
import requests

# Unusual transaction patterns
requests.post('http://localhost:8002/transaction', json={
    'user_id': 1,
    'amount': -1000000,  # Negative amount
    'description': 'Fraudulent withdrawal'
})

requests.post('http://localhost:8002/transaction', json={
    'user_id': 1,
    'amount': 999999999,  # Extremely large amount
    'description': 'Suspicious transaction'
})
```

**Expected PIC Behavior:**
- Detect unusual transaction patterns
- Flag abnormal amounts
- Correlate with user behavior
- Generate alerts

## Safety Guidelines

1. **Network Isolation:**
   - Run only on localhost (127.0.0.1)
   - Never expose to external networks
   - Use firewall rules if needed

2. **Environment Isolation:**
   - Run in dedicated test environment
   - Use Docker containers for isolation
   - Clean up test data after testing

3. **Monitoring:**
   - Always run with PIC monitoring active
   - Review logs and audit trails
   - Validate safety constraints

4. **Cleanup:**
   - Remove test databases after testing
   - Clear temporary files
   - Reset application state

## Docker Deployment (Recommended)

For maximum safety, run in Docker containers:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY examples/vulnerable_apps/ .

# Run on localhost only
CMD ["python", "flask_vulnerable.py"]
```

```bash
# Build and run
docker build -t pic-vulnerable-test .
docker run -p 127.0.0.1:5000:5000 pic-vulnerable-test
```

## Troubleshooting

### Application Won't Start

- Check if ports are already in use
- Ensure Python dependencies are installed
- Verify test_data directory permissions

### PIC Not Detecting Attacks

- Verify PIC is properly initialized
- Check sampling rate (should be 1.0 for testing)
- Ensure baseline has been established
- Review anomaly detection thresholds

### Performance Issues

- Reduce concurrent requests
- Increase resource limits
- Use sampling for high-volume tests

## Legal and Ethical Considerations

- ✅ Testing on localhost is legal and safe
- ✅ Using educational vulnerability samples is acceptable
- ✅ Controlled penetration testing of your own systems is permitted
- ❌ Never attack systems you don't own
- ❌ Never expose vulnerable apps to the internet
- ❌ Never use real user data in testing

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PIC Documentation](../../docs/)
- [Real-World Testing Guide](../../docs/realworld_testing.md)

## Support

For questions or issues with these test applications:
1. Check PIC documentation
2. Review test logs and reports
3. Consult the PIC development team

---

**Remember: These applications are tools for improving security, not for causing harm. Use responsibly.**
