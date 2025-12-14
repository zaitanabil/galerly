"""
Centralized Plan Enforcement Middleware
Provides reusable decorators and utilities for consistent plan enforcement
"""
from functools import wraps
from utils.response import create_response
from utils.plan_monitoring import track_feature_violation, track_role_violation


def get_user_features(user):
    """
    Lazy import to prevent circular dependency.
    Import get_user_features from subscription_handler when needed.
    """
    from handlers.subscription_handler import get_user_features as _get_user_features
    return _get_user_features(user)


def require_plan(min_plan=None, feature=None):
    """
    Decorator to enforce plan requirements on handler functions
    
    Args:
        min_plan: Minimum plan required ('starter', 'plus', 'pro', 'ultimate')
        feature: Specific feature required (e.g., 'raw_support', 'client_invoicing')
    
    Usage:
        @require_plan(feature='raw_vault')
        def handle_archive_to_vault(user, body):
            # Only executed if user has raw_vault feature
            ...
        
        @require_plan(min_plan='pro')
        def handle_advanced_feature(user, body):
            # Only executed if user has Pro or Ultimate plan
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from arguments
            user = None
            for arg in args:
                if isinstance(arg, dict) and 'id' in arg and 'email' in arg:
                    user = arg
                    break
            
            if not user:
                return create_response(401, {'error': 'Authentication required'})
            
            # Get user features
            features, plan_id, plan_name = get_user_features(user)
            
            # Check feature requirement
            if feature:
                if not features.get(feature):
                    # Track violation
                    track_feature_violation(user, feature, get_required_plan_for_feature(feature))
                    
                    return create_response(403, {
                        'error': f'{feature.replace("_", " ").title()} is not available on your plan',
                        'upgrade_required': True,
                        'current_plan': plan_id,
                        'feature': feature,
                        'message': f'Upgrade to {get_required_plan_for_feature(feature)} to access this feature'
                    })
            
            # Check minimum plan requirement
            if min_plan:
                plan_hierarchy = {'free': 0, 'starter': 1, 'plus': 2, 'pro': 3, 'ultimate': 4}
                user_plan_level = plan_hierarchy.get(plan_id, 0)
                required_level = plan_hierarchy.get(min_plan, 0)
                
                if user_plan_level < required_level:
                    track_feature_violation(user, f'min_plan_{min_plan}', min_plan)
                    
                    return create_response(403, {
                        'error': f'This feature requires {min_plan.title()} plan or higher',
                        'upgrade_required': True,
                        'current_plan': plan_id,
                        'required_plan': min_plan
                    })
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role):
    """
    Decorator to enforce role requirements
    
    Args:
        role: Required role ('photographer', 'client', 'admin')
    
    Usage:
        @require_role('photographer')
        def handle_create_gallery(user, body):
            # Only photographers can create galleries
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from arguments
            user = None
            for arg in args:
                if isinstance(arg, dict) and 'id' in arg and 'role' in arg:
                    user = arg
                    break
            
            if not user:
                return create_response(401, {'error': 'Authentication required'})
            
            user_role = user.get('role', 'client')
            
            if user_role != role:
                # Track violation
                action = func.__name__.replace('handle_', '').replace('_', ' ')
                track_role_violation(user, action, role)
                
                return create_response(403, {
                    'error': f'This action requires {role} role',
                    'current_role': user_role,
                    'required_role': role
                })
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_feature(*features):
    """
    Decorator to require multiple features (any one of them)
    
    Usage:
        @require_feature('email_templates', 'email_automation')
        def handle_send_custom_email(user, body):
            # Requires either email_templates OR email_automation
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = None
            for arg in args:
                if isinstance(arg, dict) and 'id' in arg and 'email' in arg:
                    user = arg
                    break
            
            if not user:
                return create_response(401, {'error': 'Authentication required'})
            
            user_features, plan_id, _ = get_user_features(user)
            
            # Check if user has any of the required features
            has_feature = any(user_features.get(f) for f in features)
            
            if not has_feature:
                track_feature_violation(user, '|'.join(features), 'unknown')
                
                return create_response(403, {
                    'error': 'This feature is not available on your plan',
                    'upgrade_required': True,
                    'required_features': list(features),
                    'current_plan': plan_id
                })
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_required_plan_for_feature(feature):
    """Map feature to minimum required plan"""
    feature_to_plan = {
        'remove_branding': 'Starter',
        'client_favorites': 'Starter',
        'edit_requests': 'Starter',
        'custom_domain': 'Plus',
        'watermarking': 'Plus',
        'analytics_advanced': 'Plus',
        'raw_support': 'Pro',
        'client_invoicing': 'Pro',
        'email_templates': 'Pro',
        'seo_tools': 'Pro',
        'analytics_pro': 'Pro',
        'raw_vault': 'Ultimate',
        'scheduler': 'Ultimate',
        'e_signatures': 'Ultimate'
    }
    return feature_to_plan.get(feature, 'Pro')


# Convenience functions for checking plans inline

def check_plan_feature(user, feature):
    """
    Check if user has a specific feature
    Returns: (has_feature: bool, error_response: dict or None)
    
    Usage:
        has_feature, error = check_plan_feature(user, 'raw_support')
        if not has_feature:
            return error
    """
    features, plan_id, _ = get_user_features(user)
    
    if not features.get(feature):
        track_feature_violation(user, feature, get_required_plan_for_feature(feature))
        
        return False, create_response(403, {
            'error': f'{feature.replace("_", " ").title()} is not available on your plan',
            'upgrade_required': True,
            'current_plan': plan_id,
            'feature': feature
        })
    
    return True, None


def check_user_role(user, required_role):
    """
    Check if user has required role
    Returns: (has_role: bool, error_response: dict or None)
    
    Usage:
        has_role, error = check_user_role(user, 'photographer')
        if not has_role:
            return error
    """
    user_role = user.get('role', 'client')
    
    if user_role != required_role:
        track_role_violation(user, 'action', required_role)
        
        return False, create_response(403, {
            'error': f'This action requires {required_role} role',
            'current_role': user_role,
            'required_role': required_role
        })
    
    return True, None


def check_min_plan(user, min_plan):
    """
    Check if user has minimum plan level
    Returns: (has_plan: bool, error_response: dict or None)
    
    Usage:
        has_plan, error = check_min_plan(user, 'pro')
        if not has_plan:
            return error
    """
    features, plan_id, _ = get_user_features(user)
    
    plan_hierarchy = {'free': 0, 'starter': 1, 'plus': 2, 'pro': 3, 'ultimate': 4}
    user_plan_level = plan_hierarchy.get(plan_id, 0)
    required_level = plan_hierarchy.get(min_plan, 0)
    
    if user_plan_level < required_level:
        track_feature_violation(user, f'min_plan_{min_plan}', min_plan)
        
        return False, create_response(403, {
            'error': f'This feature requires {min_plan.title()} plan or higher',
            'upgrade_required': True,
            'current_plan': plan_id,
            'required_plan': min_plan
        })
    
    return True, None


# Migration examples for existing handlers:

"""
BEFORE (manual checks):
def handle_create_invoice(user, body):
    # Check role
    if user.get('role') != 'photographer':
        return create_response(403, {'error': 'Only photographers...'})
    
    # Check plan
    features, _, _ = get_user_features(user)
    if not features.get('client_invoicing'):
        return create_response(403, {'error': 'Requires Pro...'})
    
    # ... rest of handler

AFTER (with middleware):
@require_role('photographer')
@require_plan(feature='client_invoicing')
def handle_create_invoice(user, body):
    # Clean handler logic - enforcement automatic
    # ... rest of handler
"""

"""
INLINE USAGE (for complex logic):
def handle_complex_operation(user, body):
    # Check multiple conditions
    has_feature, error = check_plan_feature(user, 'advanced_feature')
    if not has_feature:
        return error
    
    has_role, error = check_user_role(user, 'photographer')
    if not has_role:
        return error
    
    # Continue with logic...
"""
