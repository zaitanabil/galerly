"""
Subscription audit logging for compliance and dispute resolution
"""
import uuid
from datetime import datetime
from utils.config import dynamodb, get_required_env

# Initialize audit log table
audit_table = dynamodb.Table(get_required_env('DYNAMODB_TABLE_AUDIT_LOG'))


def log_subscription_change(user_id, action, from_plan, to_plan, effective_at=None, metadata=None):
    """
    Log subscription state changes for audit trail and dispute resolution
    
    Args:
        user_id: User ID
        action: Action type ('upgrade', 'downgrade_scheduled', 'reactivation', 
                'cancellation', 'checkout_completed', 'refund_requested', 'refund_approved', 'refund_rejected')
        from_plan: Previous plan (or None for new subscriptions)
        to_plan: New plan
        effective_at: Unix timestamp when change becomes effective (for scheduled changes)
        metadata: Additional context (dict)
    
    Example:
        log_subscription_change(
            user_id='user123',
            action='upgrade',
            from_plan='plus',
            to_plan='pro',
            metadata={'stripe_subscription_id': 'sub_123', 'prorated': True}
        )
    """
    try:
        audit_entry = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': action,
            'from_plan': from_plan or 'none',
            'to_plan': to_plan,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'effective_at': effective_at,
            'metadata': metadata or {}
        }
        
        audit_table.put_item(Item=audit_entry)
        print(f"✅ Audit Log: {action} | {from_plan} → {to_plan} | User: {user_id}")
        
    except Exception as e:
        # Don't fail the main operation if logging fails
        # Just log the error and continue
        print(f"⚠️  Error logging audit entry: {str(e)}")
        import traceback
        print(traceback.format_exc())


def get_user_subscription_history(user_id, limit=50):
    """
    Get subscription change history for a user
    
    Args:
        user_id: User ID
        limit: Maximum number of entries to return
    
    Returns:
        List of audit entries sorted by timestamp (most recent first)
    """
    try:
        response = audit_table.query(
            IndexName='UserIdTimestampIndex',
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        print(f"⚠️  Error retrieving subscription history: {str(e)}")
        return []


def log_refund_action(user_id, refund_id, action, from_status, to_status, metadata=None):
    """
    Log refund request state changes
    
    Args:
        user_id: User ID
        refund_id: Refund request ID
        action: Action type ('refund_requested', 'refund_approved', 'refund_rejected', 'refund_processed')
        from_status: Previous status
        to_status: New status
        metadata: Additional context (dict)
    """
    try:
        audit_entry = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': action,
            'from_plan': from_status,
            'to_plan': to_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'effective_at': None,
            'metadata': metadata or {'refund_id': refund_id}
        }
        
        audit_table.put_item(Item=audit_entry)
        print(f"✅ Audit Log: {action} | {from_status} → {to_status} | Refund: {refund_id} | User: {user_id}")
        
    except Exception as e:
        print(f"⚠️  Error logging refund action: {str(e)}")
        import traceback
        print(traceback.format_exc())


def analyze_subscription_patterns(user_id):
    """
    Analyze subscription change patterns for a user to detect potential abuse
    
    Returns:
        Dict with pattern analysis
    """
    try:
        history = get_user_subscription_history(user_id, limit=100)
        
        # Count actions
        action_counts = {}
        for entry in history:
            action = entry.get('action')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Check for rapid changes (more than 3 changes in 24 hours)
        from datetime import timedelta
        now = datetime.utcnow()
        recent_changes = [
            e for e in history 
            if (now - datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00').replace('+00:00', ''))).total_seconds() < 86400
        ]
        
        # Flags
        flags = []
        if len(recent_changes) > 3:
            flags.append(f'rapid_changes_{len(recent_changes)}_in_24h')
        
        if action_counts.get('refund_requested', 0) > 2:
            flags.append(f'multiple_refund_requests_{action_counts["refund_requested"]}')
        
        upgrade_count = action_counts.get('upgrade', 0)
        downgrade_count = action_counts.get('downgrade_scheduled', 0) + action_counts.get('cancellation', 0)
        if upgrade_count > 0 and downgrade_count > upgrade_count * 0.5:
            flags.append(f'frequent_upgrades_and_downgrades')
        
        return {
            'total_changes': len(history),
            'action_counts': action_counts,
            'recent_changes_24h': len(recent_changes),
            'flags': flags,
            'risk_score': len(flags)  # Simple risk scoring
        }
        
    except Exception as e:
        print(f"⚠️  Error analyzing subscription patterns: {str(e)}")
        return {
            'total_changes': 0,
            'action_counts': {},
            'recent_changes_24h': 0,
            'flags': [],
            'risk_score': 0
        }

