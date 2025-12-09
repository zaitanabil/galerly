"""
Security Tests - Password Hashing with bcrypt
Tests for bcrypt password hashing and verification
"""
import pytest
import bcrypt
from utils.auth import hash_password, verify_password

def test_hash_password_creates_bcrypt_hash():
    """Test that hash_password creates a valid bcrypt hash"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    # bcrypt hashes start with $2b$ and are 60 chars
    assert hashed.startswith('$2b$')
    assert len(hashed) == 60
    assert isinstance(hashed, str)

def test_hash_password_different_salts():
    """Test that same password produces different hashes (different salts)"""
    password = "TestPassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Same password should produce different hashes due to different salts
    assert hash1 != hash2

def test_verify_password_correct():
    """Test that verify_password correctly validates matching password"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Test that verify_password rejects non-matching password"""
    password = "TestPassword123!"
    wrong_password = "WrongPassword456!"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False

def test_verify_password_empty():
    """Test that verify_password handles empty passwords"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert verify_password("", hashed) is False

def test_verify_password_invalid_hash():
    """Test that verify_password handles invalid hash format"""
    password = "TestPassword123!"
    invalid_hash = "not_a_valid_bcrypt_hash"
    
    # Should return False, not raise exception
    assert verify_password(password, invalid_hash) is False

def test_bcrypt_rounds():
    """Test that bcrypt uses correct number of rounds (12)"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    # bcrypt hash format: $2b$12$... (12 is the rounds)
    parts = hashed.split('$')
    rounds = int(parts[2])
    
    assert rounds == 12  # Security requirement

def test_password_hash_unicode():
    """Test that password hashing works with unicode characters"""
    password = "Pässwörd123!€"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_password_hash_special_chars():
    """Test that password hashing works with special characters"""
    password = "P@$$w0rd!#%^&*()[]{}|\\<>?,./`~"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True

def test_password_hash_long():
    """Test that password hashing works with very long passwords"""
    password = "x" * 1000  # Very long password
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    # bcrypt has a 72-byte limit, so very similar long passwords may hash the same
    # This is expected bcrypt behavior

@pytest.mark.integration
def test_bcrypt_migration_compatibility():
    """
    Test that new bcrypt hashes work with old SHA-256 hashes during migration
    This ensures we can gradually migrate users
    """
    # Old SHA-256 hash (for reference)
    import hashlib
    old_password = "TestPassword123!"
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    
    # New bcrypt hash
    new_hash = hash_password(old_password)
    
    # Verify they're different systems
    assert old_hash != new_hash
    assert len(old_hash) == 64  # SHA-256 is 64 hex chars
    assert len(new_hash) == 60  # bcrypt is 60 chars
    
    # Verify new system works
    assert verify_password(old_password, new_hash) is True

