"""
Secure Handler Decorator
Wraps handlers to sanitize errors and add security features
"""
from functools import wraps
from utils.error_sanitizer import safe_error_response, log_error_safely

def secure_handler(handler_func):
    """
    Decorator that wraps handlers to:
    1. Catch and sanitize all exceptions
    2. Log errors safely
    3. Return sanitized error responses
    
    Usage:
        @secure_handler
        def handle_something(user, body):
            # handler code
    """
    @wraps(handler_func)
    def wrapper(*args, **kwargs):
        try:
            return handler_func(*args, **kwargs)
        except ValueError as e:
            # User input errors (4xx)
            log_error_safely(e, f"{handler_func.__name__} - Validation Error")
            return safe_error_response(400, e)
        except PermissionError as e:
            # Authorization errors (403)
            log_error_safely(e, f"{handler_func.__name__} - Permission Error")
            return safe_error_response(403, e)
        except KeyError as e:
            # Missing required fields (400)
            log_error_safely(e, f"{handler_func.__name__} - Missing Field")
            return safe_error_response(400, f"Missing required field: {e}")
        except Exception as e:
            # All other errors - sanitize heavily (500)
            log_error_safely(e, f"{handler_func.__name__} - Internal Error")
            return safe_error_response(500, e)
    
    return wrapper

def auth_required(handler_func):
    """
    Decorator that ensures user is authenticated
    Must be applied after secure_handler
    
    Usage:
        @secure_handler
        @auth_required
        def handle_something(user, body):
            # user is guaranteed to exist
    """
    @wraps(handler_func)
    def wrapper(user=None, *args, **kwargs):
        if not user:
            from utils.response import create_response
            return create_response(401, {'error': 'Authentication required'})
        return handler_func(user, *args, **kwargs)
    
    return wrapper

def plan_required(required_plans):
    """
    Decorator that checks if user has required subscription plan
    
    Args:
        required_plans: List of allowed plan names or single plan string
    
    Usage:
        @secure_handler
        @auth_required
        @plan_required(['pro', 'ultimate'])
        def handle_something(user, body):
            # user is guaranteed to have pro or ultimate plan
    """
    if isinstance(required_plans, str):
        required_plans = [required_plans]
    
    def decorator(handler_func):
        @wraps(handler_func)
        def wrapper(user, *args, **kwargs):
            user_plan = user.get('plan', 'free')
            if user_plan not in required_plans:
                from utils.response import create_response
                return create_response(403, {
                    'error': 'This feature requires a higher subscription plan',
                    'required_plans': required_plans,
                    'current_plan': user_plan
                })
            return handler_func(user, *args, **kwargs)
        
        return wrapper
    return decorator

