"""
Priority support level indicator
Adds support priority based on subscription tier
"""
from utils.response import create_response
from handlers.subscription_handler import get_user_features


# Support level definitions by plan
SUPPORT_LEVELS = {
    'free': {
        'level': 'priority',
        'response_time': '24-48 hours',
        'channels': ['email'],
        'description': 'Email support with priority response'
    },
    'starter': {
        'level': 'priority',
        'response_time': '24-48 hours',
        'channels': ['email'],
        'description': 'Email support with priority response'
    },
    'plus': {
        'level': 'priority',
        'response_time': '12-24 hours',
        'channels': ['email', 'chat'],
        'description': 'Faster email response + live chat'
    },
    'pro': {
        'level': 'priority-plus',
        'response_time': '6-12 hours',
        'channels': ['email', 'chat', 'video'],
        'description': 'Priority+ support with video calls'
    },
    'ultimate': {
        'level': 'vip',
        'response_time': '2-6 hours',
        'channels': ['email', 'chat', 'video', 'phone'],
        'description': 'VIP support with dedicated assistance'
    }
}


def get_support_level(user):
    """
    Get support level information for a user
    Returns support tier details based on subscription plan
    """
    features, plan_id, plan_name = get_user_features(user)
    
    support_info = SUPPORT_LEVELS.get(plan_id, SUPPORT_LEVELS['free'])
    
    return {
        'plan': plan_id,
        'plan_name': plan_name,
        **support_info
    }


def handle_get_support_info(user):
    """
    API endpoint to get support information
    """
    try:
        support_info = get_support_level(user)
        return create_response(200, support_info)
    except Exception as e:
        print(f"Error getting support info: {str(e)}")
        return create_response(500, {'error': 'Failed to get support information'})

