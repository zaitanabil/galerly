"""
Plan Violation Monitoring and Alerting
Tracks attempts to access features outside plan limits
"""
from datetime import datetime, timezone
from decimal import Decimal
from utils.config import get_dynamodb
from utils.resource_names import PLAN_VIOLATIONS_TABLE

# Initialize violations tracking table using naming convention
dynamodb = get_dynamodb()
violations_table = dynamodb.Table(PLAN_VIOLATIONS_TABLE)


def log_plan_violation(user_id, violation_type, details=None):
    """
    Log a plan violation attempt
    
    Args:
        user_id: User who attempted violation
        violation_type: Type of violation (e.g., 'storage_exceeded', 'feature_not_available')
        details: Additional context about the violation
    """
    try:
        violation = {
            'id': f"{user_id}:{violation_type}:{int(datetime.now(timezone.utc).timestamp())}",
            'user_id': user_id,
            'violation_type': violation_type,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'details': details or {},
            'ttl': int(datetime.now(timezone.utc).timestamp()) + (90 * 24 * 3600)  # Keep for 90 days
        }
        
        violations_table.put_item(Item=violation)
        
        print(f"⚠️ Plan violation logged: {user_id} - {violation_type}")
        
        # Check if this user has multiple violations (potential abuse)
        check_violation_frequency(user_id, violation_type)
        
    except Exception as e:
        print(f"Error logging plan violation: {str(e)}")


def check_violation_frequency(user_id, violation_type):
    """
    Check if user has frequent violations (potential abuse pattern)
    Sends alert if threshold exceeded
    """
    try:
        from boto3.dynamodb.conditions import Key
        from datetime import timedelta
        
        # Check violations in last 24 hours
        time_threshold = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(tzinfo=None).isoformat() + 'Z'
        
        response = violations_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression='#ts > :threshold AND violation_type = :vtype',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':threshold': time_threshold,
                ':vtype': violation_type
            }
        )
        
        violation_count = len(response.get('Items', []))
        
        # Alert if more than 10 violations in 24 hours
        if violation_count > 10:
            send_violation_alert(user_id, violation_type, violation_count)
            
    except Exception as e:
        print(f"Error checking violation frequency: {str(e)}")


def send_violation_alert(user_id, violation_type, count):
    """
    Send alert about potential abuse pattern
    Could integrate with SNS, email, Slack, etc.
    """
    try:
        print(f"🚨 ABUSE ALERT: User {user_id} has {count} {violation_type} violations in 24h")
        
        # In production, send to monitoring system
        # Example: SNS topic, CloudWatch alarm, Slack webhook
        
        # For now, just log
        alert = {
            'id': f"alert:{user_id}:{violation_type}:{int(datetime.now(timezone.utc).timestamp())}",
            'user_id': user_id,
            'alert_type': 'abuse_pattern',
            'violation_type': violation_type,
            'violation_count': count,
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'status': 'open'
        }
        
        # Could store alerts in separate table for admin review
        print(f"Alert created: {alert}")
        
    except Exception as e:
        print(f"Error sending violation alert: {str(e)}")


def get_user_violations(user_id, days=30):
    """
    Get violation history for a user
    Useful for admin dashboard
    """
    try:
        from boto3.dynamodb.conditions import Key
        from datetime import timedelta
        
        time_threshold = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None).isoformat() + 'Z'
        
        response = violations_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression='#ts > :threshold',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':threshold': time_threshold}
        )
        
        violations = response.get('Items', [])
        
        # Aggregate by type
        by_type = {}
        for v in violations:
            vtype = v.get('violation_type', 'unknown')
            by_type[vtype] = by_type.get(vtype, 0) + 1
        
        return {
            'total_violations': len(violations),
            'by_type': by_type,
            'recent_violations': sorted(violations, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        }
        
    except Exception as e:
        print(f"Error getting user violations: {str(e)}")
        return {
            'total_violations': 0,
            'by_type': {},
            'recent_violations': []
        }


def get_violation_summary(days=7):
    """
    Get platform-wide violation summary
    For admin monitoring dashboard
    """
    try:
        from datetime import timedelta
        
        time_threshold = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None).isoformat() + 'Z'
        
        # Scan for recent violations (in production, use time-based GSI)
        response = violations_table.scan(
            FilterExpression='#ts > :threshold',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':threshold': time_threshold}
        )
        
        violations = response.get('Items', [])
        
        # Aggregate stats
        by_type = {}
        by_user = {}
        
        for v in violations:
            vtype = v.get('violation_type', 'unknown')
            user_id = v.get('user_id', 'unknown')
            
            by_type[vtype] = by_type.get(vtype, 0) + 1
            by_user[user_id] = by_user.get(user_id, 0) + 1
        
        # Find top violators
        top_violators = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'period_days': days,
            'total_violations': len(violations),
            'by_type': by_type,
            'unique_users': len(by_user),
            'top_violators': [{'user_id': u, 'count': c} for u, c in top_violators]
        }
        
    except Exception as e:
        print(f"Error getting violation summary: {str(e)}")
        return {
            'period_days': days,
            'total_violations': 0,
            'by_type': {},
            'unique_users': 0,
            'top_violators': []
        }


# Integration helpers for handlers
def track_storage_violation(user, attempted_mb, limit_gb):
    """Track storage limit violation"""
    log_plan_violation(
        user['id'],
        'storage_exceeded',
        {
            'attempted_upload_mb': float(attempted_mb),
            'storage_limit_gb': float(limit_gb),
            'plan': user.get('plan', 'unknown')
        }
    )


def track_feature_violation(user, feature_name, required_plan):
    """Track feature access violation"""
    log_plan_violation(
        user['id'],
        'feature_not_available',
        {
            'feature': feature_name,
            'current_plan': user.get('plan', 'unknown'),
            'required_plan': required_plan
        }
    )


def track_role_violation(user, attempted_action, required_role):
    """Track role-based access violation"""
    log_plan_violation(
        user['id'],
        'role_unauthorized',
        {
            'attempted_action': attempted_action,
            'current_role': user.get('role', 'unknown'),
            'required_role': required_role
        }
    )


def track_rate_limit_violation(identifier, limit_type):
    """Track rate limit violation"""
    log_plan_violation(
        identifier,
        'rate_limit_exceeded',
        {
            'limit_type': limit_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    )
