"""Intentionally Vulnerable FastAPI Microservices for PIC Testing

WARNING: These services contain intentional security vulnerabilities.
DO NOT deploy to production or expose to the internet.
Use ONLY for testing PIC in controlled environments.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import time
import random
from typing import Optional, Dict, List
import uvicorn

# Auth Service
auth_app = FastAPI(title="Vulnerable Auth Service")

class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str

# Simulated user database
users_db = {
    "admin": {"id": 1, "password": "admin123", "email": "admin@example.com"},
    "user": {"id": 2, "password": "password", "email": "user@example.com"}
}

# Track failed login attempts (for testing spike detection)
failed_attempts: Dict[str, List[float]] = {}


@auth_app.post("/login")
async def login(request: LoginRequest):
    """Vulnerable login endpoint.
    
    PIC should detect:
    - Login failure spikes
    - Brute force patterns
    - Timing attacks
    """
    username = request.username
    password = request.password
    
    # Track failed attempts
    if username not in failed_attempts:
        failed_attempts[username] = []
    
    # VULNERABILITY: Timing attack
    # Different timing for valid vs invalid users
    if username in users_db:
        time.sleep(0.1)  # Simulate database lookup
        
        stored_password = users_db[username]["password"]
        
        # Character-by-character comparison (timing leak)
        for i, (c1, c2) in enumerate(zip(password, stored_password)):
            if c1 != c2:
                failed_attempts[username].append(time.time())
                time.sleep(0.01 * i)
                raise HTTPException(status_code=401, detail="Invalid credentials")
            time.sleep(0.01)
        
        if len(password) == len(stored_password):
            # Clear failed attempts on success
            failed_attempts[username] = []
            return {
                "success": True,
                "user": {
                    "id": users_db[username]["id"],
                    "username": username,
                    "email": users_db[username]["email"]
                }
            }
    
    # Invalid user
    failed_attempts[username].append(time.time())
    time.sleep(0.05)  # Different timing
    raise HTTPException(status_code=401, detail="Invalid credentials")


@auth_app.get("/failed-attempts/{username}")
async def get_failed_attempts(username: str):
    """Get failed login attempts for a user."""
    return {
        "username": username,
        "failed_attempts": len(failed_attempts.get(username, [])),
        "recent_attempts": failed_attempts.get(username, [])[-10:]
    }


# Billing Service
billing_app = FastAPI(title="Vulnerable Billing Service")

class Transaction(BaseModel):
    user_id: int
    amount: float
    description: str

# Simulated transaction database
transactions: List[Dict] = []


@billing_app.post("/transaction")
async def create_transaction(transaction: Transaction):
    """Vulnerable transaction endpoint.
    
    PIC should detect:
    - Unusual transaction patterns
    - Abnormal amounts
    - Suspicious transaction rates
    """
    # VULNERABILITY: No validation on amount
    # Allows negative amounts, extremely large amounts, etc.
    
    tx = {
        "id": len(transactions) + 1,
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "description": transaction.description,
        "timestamp": time.time()
    }
    
    transactions.append(tx)
    
    # Simulate processing time based on amount
    # VULNERABILITY: Timing leak reveals transaction amount
    processing_time = min(abs(transaction.amount) / 1000, 1.0)
    time.sleep(processing_time)
    
    return {"success": True, "transaction": tx}


@billing_app.get("/transactions/{user_id}")
async def get_transactions(user_id: int):
    """Get transactions for a user."""
    user_txs = [tx for tx in transactions if tx["user_id"] == user_id]
    return {"user_id": user_id, "transactions": user_txs}


@billing_app.get("/stats")
async def get_stats():
    """Get transaction statistics."""
    if not transactions:
        return {"total": 0, "average": 0, "max": 0, "min": 0}
    
    amounts = [tx["amount"] for tx in transactions]
    return {
        "total": sum(amounts),
        "average": sum(amounts) / len(amounts),
        "max": max(amounts),
        "min": min(amounts),
        "count": len(transactions)
    }


# API Gateway (combines services)
gateway_app = FastAPI(title="Vulnerable API Gateway")


@gateway_app.get("/")
async def root():
    """Gateway root endpoint."""
    return {
        "message": "Vulnerable Microservices Gateway",
        "services": {
            "auth": "http://localhost:8001",
            "billing": "http://localhost:8002"
        },
        "warning": "This is an intentionally vulnerable application for testing only!"
    }


@gateway_app.post("/api/login")
async def gateway_login(request: LoginRequest):
    """Gateway login endpoint - forwards to auth service."""
    # In real scenario, would forward to auth service
    # For testing, we'll simulate the vulnerable behavior
    
    # VULNERABILITY: No rate limiting
    # Allows unlimited login attempts
    
    username = request.username
    password = request.password
    
    if username in users_db and users_db[username]["password"] == password:
        return {"success": True, "message": "Login successful"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@gateway_app.post("/api/transaction")
async def gateway_transaction(transaction: Transaction):
    """Gateway transaction endpoint - forwards to billing service."""
    # VULNERABILITY: No authentication check
    # Anyone can create transactions
    
    # VULNERABILITY: No input validation
    # Accepts any transaction amount
    
    tx = {
        "id": random.randint(1000, 9999),
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "description": transaction.description,
        "timestamp": time.time()
    }
    
    return {"success": True, "transaction": tx}


@gateway_app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # VULNERABILITY: Reveals internal system information
    return {
        "status": "healthy",
        "services": {
            "auth": "running",
            "billing": "running"
        },
        "system": {
            "python_version": "3.9",
            "framework": "FastAPI",
            "database": "SQLite"
        }
    }


def run_auth_service():
    """Run auth service on port 8001."""
    print("Starting Auth Service on http://127.0.0.1:8001")
    uvicorn.run(auth_app, host="127.0.0.1", port=8001, log_level="info")


def run_billing_service():
    """Run billing service on port 8002."""
    print("Starting Billing Service on http://127.0.0.1:8002")
    uvicorn.run(billing_app, host="127.0.0.1", port=8002, log_level="info")


def run_gateway():
    """Run API gateway on port 8000."""
    print("Starting API Gateway on http://127.0.0.1:8000")
    uvicorn.run(gateway_app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == '__main__':
    import sys
    
    print("="*60)
    print("VULNERABLE MICROSERVICES")
    print("="*60)
    print("WARNING: These services are intentionally insecure!")
    print("DO NOT expose to the internet or use in production!")
    print("Use ONLY for testing PIC in controlled environments.")
    print("="*60)
    print()
    
    if len(sys.argv) > 1:
        service = sys.argv[1]
        if service == "auth":
            run_auth_service()
        elif service == "billing":
            run_billing_service()
        elif service == "gateway":
            run_gateway()
        else:
            print(f"Unknown service: {service}")
            print("Usage: python fastapi_microservices.py [auth|billing|gateway]")
    else:
        print("Usage: python fastapi_microservices.py [auth|billing|gateway]")
        print()
        print("Run each service in a separate terminal:")
        print("  python fastapi_microservices.py auth")
        print("  python fastapi_microservices.py billing")
        print("  python fastapi_microservices.py gateway")
