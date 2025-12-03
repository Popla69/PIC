"""PII redaction engine for telemetry data."""

import re
from typing import Any, Dict
from pic.crypto import CryptoCore


class PIIRedactor:
    """Redact personally identifiable information from telemetry data.
    
    Supports:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - SSN/Tax IDs
    - IP addresses
    """
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b')
    CC_PATTERN = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b')
    SSN_PATTERN = re.compile(r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b')
    IP_PATTERN = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    
    def __init__(self):
        """Initialize PIIRedactor."""
        pass
    
    def redact_string(self, text: str) -> str:
        """Redact PII from a string.
        
        Args:
            text: String potentially containing PII
            
        Returns:
            String with PII replaced by redaction tokens
        """
        if not isinstance(text, str):
            return text
        
        # Redact email addresses
        text = self.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
        
        # Redact phone numbers
        text = self.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
        
        # Redact credit card numbers
        text = self.CC_PATTERN.sub('[CC_REDACTED]', text)
        
        # Redact SSN
        text = self.SSN_PATTERN.sub('[ID_REDACTED]', text)
        
        # Redact IP addresses (zero out last octet)
        text = self.IP_PATTERN.sub(lambda m: '.'.join(m.group().split('.')[:-1] + ['0']), text)
        
        return text
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from dictionary values.
        
        Args:
            data: Dictionary potentially containing PII
            
        Returns:
            Dictionary with PII redacted
        """
        redacted = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.redact_string(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [self.redact_string(v) if isinstance(v, str) else v for v in value]
            else:
                redacted[key] = value
        return redacted
    
    @staticmethod
    def hash_argument(arg: Any) -> str:
        """Hash an argument value using SHA-256.
        
        Args:
            arg: Argument value to hash
            
        Returns:
            SHA-256 hash of the argument
        """
        if arg is None:
            return CryptoCore.sha256_hash_string("None")
        
        # Convert to string representation
        arg_str = str(arg)
        return CryptoCore.sha256_hash_string(arg_str)
    
    def redact_and_hash_args(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Redact PII and hash function arguments.
        
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Dictionary with argument metadata (hashed)
        """
        arg_hashes = []
        arg_types = []
        
        # Hash positional arguments
        for arg in args:
            arg_hashes.append(self.hash_argument(arg))
            arg_types.append(type(arg).__name__)
        
        # Hash keyword arguments
        kwarg_hashes = {}
        for key, value in kwargs.items():
            kwarg_hashes[key] = self.hash_argument(value)
        
        return {
            "arg_count": len(args) + len(kwargs),
            "arg_types": arg_types,
            "arg_hashes": arg_hashes,
            "kwarg_hashes": kwarg_hashes
        }
