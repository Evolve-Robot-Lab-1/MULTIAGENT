"""
Input validation utilities.
"""
import re
from typing import Optional, List, Any
from pathlib import Path
from pydantic import validator, BaseModel
from email_validator import validate_email, EmailNotValidError

from app.core.exceptions import ValidationError


# Common regex patterns
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URL_REGEX = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)
FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
UUID_REGEX = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def validate_email_address(email: str) -> str:
    """
    Validate email address.
    
    Args:
        email: Email address to validate
        
    Returns:
        Normalized email address
        
    Raises:
        ValidationError: If email is invalid
    """
    try:
        # Validate and normalize
        validation = validate_email(email, check_deliverability=False)
        return validation.email
    except EmailNotValidError as e:
        raise ValidationError('email', str(e))


def validate_filename(filename: str, allowed_extensions: Optional[List[str]] = None) -> str:
    """
    Validate filename.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['pdf', 'docx'])
        
    Returns:
        Validated filename
        
    Raises:
        ValidationError: If filename is invalid
    """
    if not filename:
        raise ValidationError('filename', 'Filename cannot be empty')
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError('filename', 'Invalid filename - path traversal detected')
    
    # Check filename format
    if not FILENAME_REGEX.match(filename):
        raise ValidationError('filename', 'Invalid filename format')
    
    # Check extension if specified
    if allowed_extensions:
        ext = Path(filename).suffix.lower().lstrip('.')
        if ext not in allowed_extensions:
            raise ValidationError(
                'filename', 
                f'Invalid file extension. Allowed: {", ".join(allowed_extensions)}'
            )
    
    return filename


def validate_url(url: str) -> str:
    """
    Validate URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError('url', 'URL cannot be empty')
    
    if not URL_REGEX.match(url):
        raise ValidationError('url', 'Invalid URL format')
    
    return url


def validate_uuid(uuid_str: str) -> str:
    """
    Validate UUID string.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        Validated UUID string
        
    Raises:
        ValidationError: If UUID is invalid
    """
    if not uuid_str:
        raise ValidationError('uuid', 'UUID cannot be empty')
    
    if not UUID_REGEX.match(uuid_str.lower()):
        raise ValidationError('uuid', 'Invalid UUID format')
    
    return uuid_str.lower()


def validate_page_params(page: int, per_page: int, max_per_page: int = 100) -> tuple:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number
        per_page: Items per page
        max_per_page: Maximum allowed items per page
        
    Returns:
        Tuple of (page, per_page)
        
    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError('page', 'Page must be >= 1')
    
    if per_page < 1:
        raise ValidationError('per_page', 'Items per page must be >= 1')
    
    if per_page > max_per_page:
        raise ValidationError('per_page', f'Items per page cannot exceed {max_per_page}')
    
    return page, per_page


# Pydantic validators for common fields
class EmailValidator:
    """Pydantic validator for email fields."""
    
    @validator('email')
    def validate_email(cls, v):
        return validate_email_address(v)


class FilenameValidator:
    """Pydantic validator for filename fields."""
    
    @validator('filename')
    def validate_filename(cls, v):
        return validate_filename(v)


class URLValidator:
    """Pydantic validator for URL fields."""
    
    @validator('url')
    def validate_url(cls, v):
        return validate_url(v)


class UUIDValidator:
    """Pydantic validator for UUID fields."""
    
    @validator('id', 'user_id', 'document_id', 'session_id')
    def validate_uuid(cls, v):
        if v:
            return validate_uuid(v)
        return v


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML content to prevent XSS.
    
    Args:
        html: HTML content to sanitize
        
    Returns:
        Sanitized HTML
    """
    import bleach
    
    # Allowed tags and attributes
    allowed_tags = [
        'p', 'br', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'strong', 'em', 'u', 'strike', 'sub', 'sup',
        'ul', 'ol', 'li', 'a', 'img', 'table', 'tr', 'td', 'th',
        'blockquote', 'code', 'pre'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
        'div': ['class', 'id'],
        'span': ['class', 'style'],
        'p': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }
    
    # Clean HTML
    cleaned = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return cleaned


def validate_json(data: Any, schema: dict) -> Any:
    """
    Validate JSON data against a schema.
    
    Args:
        data: Data to validate
        schema: JSON schema
        
    Returns:
        Validated data
        
    Raises:
        ValidationError: If validation fails
    """
    import jsonschema
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        return data
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError('json', str(e))


def validate_file_size(size: int, max_size: int) -> int:
    """
    Validate file size.
    
    Args:
        size: File size in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        Validated size
        
    Raises:
        ValidationError: If size exceeds limit
    """
    if size > max_size:
        from app.core.exceptions import FileSizeLimitError
        raise FileSizeLimitError(size, max_size)
    
    return size