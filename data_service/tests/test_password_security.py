"""
Tests for Password Security
===========================
Unit tests for password hashing and verification security.
"""

import pytest
import bcrypt


class TestPasswordHashing:
    """Tests for bcrypt password hashing"""
    
    def test_password_is_hashed(self):
        """Password should be hashed, not stored in plaintext"""
        password = "MySecurePassword123!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Hashed password should be different from original
        assert hashed != password.encode('utf-8')
        assert hashed != password
    
    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (due to salt)"""
        password = "TestPassword"
        hash1 = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hash2 = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Hashes should be different due to unique salts
        assert hash1 != hash2
    
    def test_password_verification_correct(self):
        """Correct password should verify successfully"""
        password = "CorrectPassword123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Verification should succeed
        assert bcrypt.checkpw(password.encode('utf-8'), hashed) == True
    
    def test_password_verification_wrong(self):
        """Wrong password should fail verification"""
        correct_password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt())
        
        # Verification should fail
        assert bcrypt.checkpw(wrong_password.encode('utf-8'), hashed) == False
    
    def test_password_case_sensitive(self):
        """Password verification should be case sensitive"""
        password = "CaseSensitive"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Different case should fail
        assert bcrypt.checkpw("casesensitive".encode('utf-8'), hashed) == False
        assert bcrypt.checkpw("CASESENSITIVE".encode('utf-8'), hashed) == False
    
    def test_unicode_password(self):
        """Should handle unicode passwords (Hebrew, etc.)"""
        password = "סיסמה123!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Should verify correctly
        assert bcrypt.checkpw(password.encode('utf-8'), hashed) == True
    
    def test_empty_password_handling(self):
        """Should handle empty password gracefully"""
        password = ""
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Empty should verify with empty
        assert bcrypt.checkpw("".encode('utf-8'), hashed) == True
        # But not with non-empty
        assert bcrypt.checkpw("notempty".encode('utf-8'), hashed) == False
    
    def test_long_password(self):
        """Should handle very long passwords (bcrypt limit is 72 bytes)"""
        # bcrypt has a limit of 72 bytes - passwords must be truncated
        password = "A" * 100  # Longer than bcrypt limit
        truncated = password[:72]  # Truncate to bcrypt limit
        hashed = bcrypt.hashpw(truncated.encode('utf-8'), bcrypt.gensalt())
        
        # Should verify with truncated password
        assert bcrypt.checkpw(truncated.encode('utf-8'), hashed) == True
        
        # This demonstrates the importance of truncating long passwords
        assert len(password) > 72  # Original was over limit
    
    def test_special_characters(self):
        """Should handle special characters in password"""
        password = "P@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        assert bcrypt.checkpw(password.encode('utf-8'), hashed) == True
    
    def test_hash_format(self):
        """Hashed password should be in bcrypt format"""
        password = "TestFormat"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # bcrypt hashes start with $2b$ (or $2a$, $2y$)
        hash_str = hashed.decode('utf-8')
        assert hash_str.startswith('$2')
        # bcrypt hash length is always 60 characters
        assert len(hash_str) == 60


class TestPasswordStrength:
    """Tests for password strength validation (recommendations)"""
    
    def test_minimum_length(self):
        """Password should meet minimum length requirement"""
        MIN_LENGTH = 8
        
        weak_passwords = ["short", "1234567", "abc"]
        strong_passwords = ["LongEnoughPassword", "12345678", "abcdefgh"]
        
        for pwd in weak_passwords:
            assert len(pwd) < MIN_LENGTH
        
        for pwd in strong_passwords:
            assert len(pwd) >= MIN_LENGTH
    
    def test_has_mixed_case(self):
        """Strong password should have mixed case"""
        def has_mixed_case(password):
            return any(c.isupper() for c in password) and any(c.islower() for c in password)
        
        assert has_mixed_case("AbCdEf") == True
        assert has_mixed_case("ALLCAPS") == False
        assert has_mixed_case("alllower") == False
    
    def test_has_numbers(self):
        """Strong password should contain numbers"""
        def has_numbers(password):
            return any(c.isdigit() for c in password)
        
        assert has_numbers("Password123") == True
        assert has_numbers("NoNumbers") == False
    
    def test_has_special_chars(self):
        """Strong password should contain special characters"""
        def has_special(password):
            special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
            return any(c in special for c in password)
        
        assert has_special("Password!") == True
        assert has_special("NoSpecial123") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
