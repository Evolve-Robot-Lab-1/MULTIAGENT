"""
Unit tests for validators.
"""
import pytest

from app.utils.validators import (
    validate_email_address, validate_filename, validate_url,
    validate_uuid, validate_page_params, sanitize_html
)
from app.core.exceptions import ValidationError, FileSizeLimitError


class TestValidators:
    """Test validation functions."""
    
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@email.com",
            "123@test.org"
        ]
        
        for email in valid_emails:
            result = validate_email_address(email)
            assert result  # Should return normalized email
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            ""
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                validate_email_address(email)
            assert exc_info.value.field == 'email'
    
    def test_validate_filename_valid(self):
        """Test valid filenames."""
        valid_filenames = [
            "document.pdf",
            "test_file.docx",
            "report-2024.txt",
            "data.csv"
        ]
        
        for filename in valid_filenames:
            result = validate_filename(filename)
            assert result == filename
    
    def test_validate_filename_invalid(self):
        """Test invalid filenames."""
        invalid_filenames = [
            "../../../etc/passwd",  # Path traversal
            "file/with/slashes.txt",
            "file\\with\\backslashes.doc",
            "",
            "file with spaces.pdf"  # Invalid characters
        ]
        
        for filename in invalid_filenames:
            with pytest.raises(ValidationError) as exc_info:
                validate_filename(filename)
            assert exc_info.value.field == 'filename'
    
    def test_validate_filename_with_extensions(self):
        """Test filename validation with allowed extensions."""
        allowed = ['pdf', 'docx', 'txt']
        
        # Valid
        assert validate_filename("doc.pdf", allowed) == "doc.pdf"
        assert validate_filename("test.docx", allowed) == "test.docx"
        
        # Invalid extension
        with pytest.raises(ValidationError) as exc_info:
            validate_filename("image.jpg", allowed)
        assert "Invalid file extension" in str(exc_info.value.reason)
    
    def test_validate_url_valid(self):
        """Test valid URLs."""
        valid_urls = [
            "http://example.com",
            "https://www.example.com/path",
            "https://example.com:8080/api",
            "http://localhost:3000",
            "https://192.168.1.1"
        ]
        
        for url in valid_urls:
            result = validate_url(url)
            assert result == url
    
    def test_validate_url_invalid(self):
        """Test invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Only http/https allowed
            "//example.com",
            "http://",
            ""
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                validate_url(url)
            assert exc_info.value.field == 'url'
    
    def test_validate_uuid_valid(self):
        """Test valid UUIDs."""
        valid_uuids = [
            "12345678-1234-5678-1234-567812345678",
            "ABCDEF12-3456-7890-ABCD-EF1234567890",
            "a0b1c2d3-e4f5-6789-0123-456789abcdef"
        ]
        
        for uuid_str in valid_uuids:
            result = validate_uuid(uuid_str)
            assert result == uuid_str.lower()
    
    def test_validate_uuid_invalid(self):
        """Test invalid UUIDs."""
        invalid_uuids = [
            "not-a-uuid",
            "12345678-1234-5678-1234",  # Too short
            "12345678-1234-5678-1234-567812345678-extra",  # Too long
            "12345678_1234_5678_1234_567812345678",  # Wrong separator
            ""
        ]
        
        for uuid_str in invalid_uuids:
            with pytest.raises(ValidationError) as exc_info:
                validate_uuid(uuid_str)
            assert exc_info.value.field == 'uuid'
    
    def test_validate_page_params_valid(self):
        """Test valid pagination parameters."""
        page, per_page = validate_page_params(1, 20)
        assert page == 1
        assert per_page == 20
        
        page, per_page = validate_page_params(5, 50, max_per_page=100)
        assert page == 5
        assert per_page == 50
    
    def test_validate_page_params_invalid(self):
        """Test invalid pagination parameters."""
        # Page < 1
        with pytest.raises(ValidationError) as exc_info:
            validate_page_params(0, 20)
        assert exc_info.value.field == 'page'
        
        # Per page < 1
        with pytest.raises(ValidationError) as exc_info:
            validate_page_params(1, 0)
        assert exc_info.value.field == 'per_page'
        
        # Per page > max
        with pytest.raises(ValidationError) as exc_info:
            validate_page_params(1, 150, max_per_page=100)
        assert exc_info.value.field == 'per_page'
    
    def test_sanitize_html(self):
        """Test HTML sanitization."""
        # Safe HTML
        safe_html = '<p>Hello <strong>world</strong></p>'
        assert sanitize_html(safe_html) == safe_html
        
        # Remove dangerous tags
        dangerous_html = '<p>Hello</p><script>alert("XSS")</script>'
        cleaned = sanitize_html(dangerous_html)
        assert '<script>' not in cleaned
        assert '<p>Hello</p>' in cleaned
        
        # Remove dangerous attributes
        html_with_events = '<p onclick="alert()">Click me</p>'
        cleaned = sanitize_html(html_with_events)
        assert 'onclick' not in cleaned
        assert '<p>Click me</p>' in cleaned
        
        # Preserve allowed attributes
        html_with_href = '<a href="https://example.com">Link</a>'
        cleaned = sanitize_html(html_with_href)
        assert 'href="https://example.com"' in cleaned