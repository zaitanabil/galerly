"""
Authentication utilities for admin operations
"""
import hashlib
import os

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = bytes.fromhex(stored_password[:64])
    stored_pwdhash = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash.hex() == stored_pwdhash
