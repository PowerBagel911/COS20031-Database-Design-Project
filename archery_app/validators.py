# archery_app/validators.py

import re
from datetime import date, datetime
import streamlit as st

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_integer(value, field_name="Value", min_value=None, max_value=None, allow_none=False):
    """
    Validate that a value is an integer within specified range.
    
    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        allow_none: Whether None values are allowed
        
    Returns:
        int: The validated integer
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{field_name} cannot be empty.")
    
    try:
        # Try to convert to integer
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer.")
    
    # Check range if specified
    if min_value is not None and int_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}.")
    if max_value is not None and int_value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}.")
    
    return int_value

def validate_string(value, field_name="Value", min_length=None, max_length=None, 
                   pattern=None, pattern_description=None, allow_none=False):
    """
    Validate that a value is a string matching specified criteria.
    
    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        pattern: Regular expression pattern the string must match
        pattern_description: Description of the pattern (for error messages)
        allow_none: Whether None/empty values are allowed
        
    Returns:
        str: The validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None or value == "":
        if allow_none:
            return None
        raise ValidationError(f"{field_name} cannot be empty.")
    
    # Ensure it's a string
    if not isinstance(value, str):
        try:
            value = str(value)
        except:
            raise ValidationError(f"{field_name} must be a valid string.")
    
    # Check length if specified
    if min_length is not None and len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters.")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters.")
    
    # Check pattern if specified
    if pattern is not None and not re.match(pattern, value):
        error_msg = f"{field_name} is not in a valid format."
        if pattern_description:
            error_msg += f" {pattern_description}"
        raise ValidationError(error_msg)
    
    return value

def validate_date(value, field_name="Date", min_date=None, max_date=None, allow_none=False):
    """
    Validate that a value is a valid date within specified range.
    
    Args:
        value: The value to validate (date object or string in YYYY-MM-DD format)
        field_name: Name of the field (for error messages)
        min_date: Minimum allowed date
        max_date: Maximum allowed date
        allow_none: Whether None values are allowed
        
    Returns:
        date: The validated date
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(f"{field_name} cannot be empty.")
    
    # Convert to date if it's not already
    if not isinstance(value, date):
        try:
            if isinstance(value, str):
                # Try to parse as YYYY-MM-DD
                parts = value.split('-')
                if len(parts) != 3:
                    raise ValueError("Invalid format")
                year, month, day = map(int, parts)
                value = date(year, month, day)
            else:
                raise ValueError("Not a string or date")
        except Exception as e:
            raise ValidationError(f"{field_name} must be a valid date in YYYY-MM-DD format.")
    
    # Check range if specified
    if min_date is not None and value < min_date:
        raise ValidationError(f"{field_name} cannot be earlier than {min_date.strftime('%Y-%m-%d')}.")
    if max_date is not None and value > max_date:
        raise ValidationError(f"{field_name} cannot be later than {max_date.strftime('%Y-%m-%d')}.")
    
    return value

def sanitize_input(value, input_type='string'):
    """
    Sanitize user input to prevent SQL injection and other attacks.
    
    Args:
        value: The input to sanitize
        input_type: Type of input ('string', 'integer', 'date')
        
    Returns:
        The sanitized input
    """
    if value is None:
        return None
    
    if input_type == 'integer':
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    elif input_type == 'date':
        if isinstance(value, date):
            return value
        
        try:
            if isinstance(value, str):
                # Remove any potentially harmful characters
                sanitized = re.sub(r'[^\d-]', '', value)
                # Validate format
                if re.match(r'^\d{4}-\d{2}-\d{2}$', sanitized):
                    parts = sanitized.split('-')
                    year, month, day = map(int, parts)
                    return date(year, month, day)
            return None
        except:
            return None
    
    else:  # string
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                return None
        
        # Remove potentially dangerous characters
        # This removes SQL command characters and common injection patterns
        sanitized = re.sub(r'[\'"\\;]', '', value)
        
        # Remove any inline comments
        sanitized = re.sub(r'--.*', '', sanitized)
        
        # Remove any script tags
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL)
        
        return sanitized

def validate_username(value, field_name="Username"):
    """Validate a username with specific requirements."""
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    pattern_desc = "Username must contain only letters, numbers, and underscores."
    return validate_string(value, field_name, min_length=3, max_length=50, 
                          pattern=pattern, pattern_description=pattern_desc)

def validate_password(value, field_name="Password"):
    """Validate a password with specific requirements."""
    # At least 8 characters with at least one digit, one uppercase, and one special character
    pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>])[a-zA-Z0-9!@#$%^&*(),.?":{}|<>]{8,}$'
    pattern_desc = "Password must be at least 8 characters with at least one digit, one uppercase letter, and one special character."
    return validate_string(value, field_name, min_length=8, 
                          pattern=pattern, pattern_description=pattern_desc)

def validate_form_input(form_data, validation_rules):
    """
    Validate a dictionary of form data according to specified rules.
    
    Args:
        form_data (dict): Dictionary of form field values
        validation_rules (dict): Dictionary mapping field names to validation functions
        
    Returns:
        dict: Dictionary with validated and sanitized values
        list: List of error messages, empty if validation succeeded
    """
    errors = []
    validated_data = {}
    
    for field, validator in validation_rules.items():
        if field not in form_data:
            errors.append(f"Field '{field}' is missing")
            continue
            
        try:
            validated_data[field] = validator(form_data[field])
        except ValidationError as e:
            errors.append(str(e))
    
    return validated_data, errors

# Helper function to display validation errors in Streamlit
def display_validation_errors(errors):
    """Display validation errors in Streamlit."""
    if errors:
        error_message = "Please correct the following errors:"
        for error in errors:
            error_message += f"\n• {error}"
        st.error(error_message)
        return True
    return False