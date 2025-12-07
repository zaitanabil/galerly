"""
Scheduled Lambda entry point for periodic tasks
Handles EventBridge/CloudWatch Events triggers
"""
from handlers.scheduled_handler import (
    handle_gallery_expiration_reminders,
    handle_expire_galleries
)

def handler(event, context):
    """
    Main handler for scheduled Lambda functions
    Routes to appropriate scheduled task based on event source
    """
    try:
        # Check event source
        event_source = event.get('source', '')
        detail_type = event.get('detail-type', '')
        
        # EventBridge scheduled event
        if event_source == 'aws.events' or detail_type == 'Scheduled Event':
            # Check which scheduled task to run
            # This can be determined by the rule name or a custom parameter
            rule_name = event.get('resources', [{}])[0].split('/')[-1] if event.get('resources') else ''
            
            if 'expiration-reminder' in rule_name.lower() or 'reminder' in rule_name.lower():
                print("📧 Running gallery expiration reminder task...")
                return handle_gallery_expiration_reminders(event, context)
            elif 'expire-galleries' in rule_name.lower() or 'expire' in rule_name.lower():
                print("🗄️  Running gallery expiration task...")
                return handle_expire_galleries(event, context)
            else:
                # Default: run reminder check
                print("📧 Running default gallery expiration reminder task...")
                return handle_gallery_expiration_reminders(event, context)
        
        # Manual invocation (for testing)
        elif event.get('action'):
            action = event.get('action')
            if action == 'reminder':
                return handle_gallery_expiration_reminders(event, context)
            elif action == 'expire':
                return handle_expire_galleries(event, context)
            else:
                return {
                    'statusCode': 400,
                    'body': {'error': f'Unknown action: {action}'}
                }
        
        # Default: run reminder check
        else:
            print("📧 Running default gallery expiration reminder task...")
            return handle_gallery_expiration_reminders(event, context)
            
    except Exception as e:
        print(f"❌ Error in scheduled Lambda handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }

