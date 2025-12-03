"""Property test for PII redaction completeness.

Feature: pic-v1-immune-core, Property 4: PII Redaction Completeness
Validates: Requirements 1.5, 6.2
"""

from hypothesis import given, strategies as st
from pic.cellagent.redaction import PIIRedactor


@given(
    # Use realistic email patterns with ASCII only
    username=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=3, max_size=10),
    domain=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10),
    tld=st.sampled_from(['com', 'org', 'net', 'edu', 'gov']),
    # Use realistic phone patterns
    area_code=st.integers(min_value=200, max_value=999),
    exchange=st.integers(min_value=200, max_value=999),
    number=st.integers(min_value=1000, max_value=9999),
)
def test_pii_redaction_completeness(username, domain, tld, area_code, exchange, number):
    """
    Property 4: PII Redaction Completeness
    
    For any telemetry event containing PII patterns (email, phone, credit card, SSN, IP address),
    all PII shall be replaced with redaction tokens or hashes before transmission.
    """
    redactor = PIIRedactor()
    
    # Create realistic PII
    email = f"{username}@{domain}.{tld}"
    phone = f"{area_code}-{exchange}-{number}"
    
    # Create text with PII
    text_with_pii = f"Contact {email} or call {phone} for support"
    
    # Redact PII
    redacted = redactor.redact_string(text_with_pii)
    
    # Verify: Original PII not in redacted text
    assert email not in redacted
    assert phone not in redacted
    
    # Verify: Redaction tokens present
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted


def test_credit_card_redaction():
    """Test credit card number redaction."""
    redactor = PIIRedactor()
    
    # Test various CC formats
    cc_numbers = [
        "4111111111111111",  # Visa
        "5500000000000004",  # Mastercard
        "340000000000009",   # Amex
    ]
    
    for cc in cc_numbers:
        text = f"Card number: {cc}"
        redacted = redactor.redact_string(text)
        
        assert cc not in redacted
        assert "[CC_REDACTED]" in redacted


def test_ssn_redaction():
    """Test SSN redaction."""
    redactor = PIIRedactor()
    
    ssn = "123-45-6789"
    text = f"SSN: {ssn}"
    redacted = redactor.redact_string(text)
    
    assert ssn not in redacted
    assert "[ID_REDACTED]" in redacted


def test_ip_address_redaction():
    """Test IP address redaction (last octet zeroed)."""
    redactor = PIIRedactor()
    
    ip = "192.168.1.100"
    text = f"IP: {ip}"
    redacted = redactor.redact_string(text)
    
    assert ip not in redacted
    assert "192.168.1.0" in redacted


def test_multiple_pii_types():
    """Test redaction of multiple PII types in one string."""
    redactor = PIIRedactor()
    
    text = "Email: user@example.com, Phone: 555-123-4567, IP: 10.0.0.50"
    redacted = redactor.redact_string(text)
    
    # Verify all PII redacted
    assert "user@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "10.0.0.50" not in redacted
    
    # Verify tokens present
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "10.0.0.0" in redacted
