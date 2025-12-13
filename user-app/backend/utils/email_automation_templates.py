"""
Pre-built Email Automation Templates
Ready-to-use workflow templates for common photography scenarios
"""
from typing import Dict, List, Any


def get_automation_templates() -> List[Dict[str, Any]]:
    """
    Get pre-built email automation workflow templates
    
    Returns:
        List of workflow templates
    """
    
    templates = [
        {
            'id': 'client_onboarding',
            'name': 'Client Onboarding',
            'description': 'Welcome new clients and guide them through viewing their gallery',
            'category': 'Client Communication',
            'icon': 'users',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'gallery_shared',
                        'description': 'When you share a gallery with a client'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'gallery_ready',
                        'subject': 'Your photos are ready to view!',
                        'delay_minutes': 0
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 3,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'no_activity',
                        'description': 'If client has not viewed gallery yet'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'view_reminder',
                        'subject': 'Have you seen your photos yet?',
                        'delay_minutes': 0
                    }
                }
            ]
        },
        {
            'id': 'selection_followup',
            'name': 'Selection Follow-up',
            'description': 'Remind clients to select their favorite photos',
            'category': 'Client Actions',
            'icon': 'heart',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'gallery_viewed',
                        'description': 'When client views gallery'
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 7,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'no_favorites',
                        'description': 'If client has not favorited any photos'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'selection_reminder',
                        'subject': 'Please select your favorite photos',
                        'delay_minutes': 0
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 7,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'no_favorites',
                        'description': 'If still no favorites'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'final_selection_reminder',
                        'subject': 'Last chance to select your favorites',
                        'delay_minutes': 0
                    }
                }
            ]
        },
        {
            'id': 'download_followup',
            'name': 'Download Follow-up',
            'description': 'Ensure clients download their photos',
            'category': 'Client Actions',
            'icon': 'download',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'favorites_submitted',
                        'description': 'When client submits favorite selections'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'download_ready',
                        'subject': 'Your selected photos are ready to download',
                        'delay_minutes': 0
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 5,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'no_downloads',
                        'description': 'If client has not downloaded yet'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'download_reminder',
                        'subject': 'Your photos are waiting for download',
                        'delay_minutes': 0
                    }
                }
            ]
        },
        {
            'id': 'review_request',
            'name': 'Review Request',
            'description': 'Ask satisfied clients for testimonials',
            'category': 'Marketing',
            'icon': 'star',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'photos_downloaded',
                        'description': 'When client downloads photos'
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 14,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'review_request',
                        'subject': 'How was your experience?',
                        'delay_minutes': 0
                    }
                }
            ]
        },
        {
            'id': 'engagement_recovery',
            'name': 'Re-engagement',
            'description': 'Win back inactive clients',
            'category': 'Client Retention',
            'icon': 'refresh',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'no_activity_30_days',
                        'description': 'Client has not engaged for 30 days'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'reengagement',
                        'subject': 'We miss you! Check out your gallery',
                        'delay_minutes': 0
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 14,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'still_inactive',
                        'description': 'If still no activity'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'final_reminder',
                        'subject': 'Your photos will expire soon',
                        'delay_minutes': 0
                    }
                }
            ]
        },
        {
            'id': 'booking_followup',
            'name': 'Booking Follow-up',
            'description': 'Follow up with leads who requested quotes',
            'category': 'Sales',
            'icon': 'calendar',
            'steps': [
                {
                    'type': 'trigger',
                    'config': {
                        'trigger': 'lead_captured',
                        'description': 'When someone submits a contact form'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'quote_sent',
                        'subject': 'Your photography quote',
                        'delay_minutes': 30
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 3,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'not_booked',
                        'description': 'If lead has not booked yet'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'followup',
                        'subject': 'Any questions about your photography session?',
                        'delay_minutes': 0
                    }
                },
                {
                    'type': 'delay',
                    'config': {
                        'delay_days': 7,
                        'delay_hours': 0
                    }
                },
                {
                    'type': 'condition',
                    'config': {
                        'condition': 'not_booked',
                        'description': 'If still not booked'
                    }
                },
                {
                    'type': 'email',
                    'config': {
                        'template': 'last_chance',
                        'subject': 'Limited availability remaining',
                        'delay_minutes': 0
                    }
                }
            ]
        }
    ]
    
    return templates


def get_template_by_id(template_id: str) -> Dict[str, Any]:
    """
    Get a specific automation template by ID
    
    Args:
        template_id: Template identifier
    
    Returns:
        Template dict or None if not found
    """
    templates = get_automation_templates()
    for template in templates:
        if template['id'] == template_id:
            return template
    return None


def get_templates_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get automation templates grouped by category
    
    Returns:
        Dict with category as key and list of templates as value
    """
    templates = get_automation_templates()
    categorized = {}
    
    for template in templates:
        category = template.get('category', 'General')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(template)
    
    return categorized

