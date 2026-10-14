from .email_validator import (
    ValidationResult, validate_email, syntax_ok, classify_category, split_email,
)
from .mx import has_mx, dns_available
from .dedup import mark_duplicates, is_duplicate_email

__all__ = [
    "ValidationResult", "validate_email", "syntax_ok", "classify_category",
    "split_email", "has_mx", "dns_available", "mark_duplicates",
    "is_duplicate_email",
]
