"""
Security Monitoring and Alerting
CloudWatch alarms and SNS notifications for security events
"""
import boto3
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
sns = boto3.client('sns', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# SNS topic for security alerts
SECURITY_ALERT_TOPIC_ARN = os.environ.get('SECURITY_ALERT_TOPIC_ARN', '')

# Security event types
SECURITY_EVENTS = {
    'failed_login_attempt': {
        'severity': 'medium',
        'threshold': 5,
        'window_minutes': 5
    },
    'rate_limit_exceeded': {
        'severity': 'medium',
        'threshold': 10,
        'window_minutes': 5
    },
    'invalid_csrf_token': {
        'severity': 'high',
        'threshold': 3,
        'window_minutes': 5
    },
    'webhook_signature_failure': {
        'severity': 'high',
        'threshold': 3,
        'window_minutes': 5
    },
    'unauthorized_access_attempt': {
        'severity': 'high',
        'threshold': 5,
        'window_minutes': 5
    },
    'sql_injection_attempt': {
        'severity': 'critical',
        'threshold': 1,
        'window_minutes': 1
    },
    'xss_attempt': {
        'severity': 'critical',
        'threshold': 1,
        'window_minutes': 1
    },
}

def log_security_event(event_type: str, details: Dict[str, Any], user_id: str = None, ip_address: str = None):
    """
    Log security event to CloudWatch and trigger alerts
    
    Args:
        event_type: Type of security event
        details: Additional details about the event
        user_id: User ID if applicable
        ip_address: Source IP address
    """
    try:
        # Create CloudWatch metric
        dimensions = []
        
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        if ip_address:
            dimensions.append({'Name': 'SourceIP', 'Value': ip_address})
        
        dimensions.append({'Name': 'EventType', 'Value': event_type})
        
        # Put metric data
        cloudwatch.put_metric_data(
            Namespace='Galerly/Security',
            MetricData=[{
                'MetricName': event_type,
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.now(timezone.utc),
                'Dimensions': dimensions
            }]
        )
        
        # Check if alert should be triggered
        event_config = SECURITY_EVENTS.get(event_type, {})
        severity = event_config.get('severity', 'low')
        
        if severity in ['critical', 'high']:
            send_security_alert(event_type, details, severity, user_id, ip_address)
        
        print(f"🔒 Security event logged: {event_type} (severity: {severity})")
        
    except Exception as e:
        print(f"Error logging security event: {str(e)}")

def send_security_alert(event_type: str, details: Dict[str, Any], severity: str, user_id: str = None, ip_address: str = None):
    """
    Send security alert via SNS
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Severity level
        user_id: User ID if applicable
        ip_address: Source IP address
    """
    if not SECURITY_ALERT_TOPIC_ARN:
        print("⚠️  SECURITY_ALERT_TOPIC_ARN not configured - alert not sent")
        return
    
    try:
        alert_message = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'severity': severity.upper(),
            'details': details,
            'user_id': user_id,
            'ip_address': ip_address,
            'environment': os.environ.get('ENVIRONMENT', 'unknown')
        }
        
        subject = f"🚨 SECURITY ALERT: {event_type} ({severity.upper()})"
        
        sns.publish(
            TopicArn=SECURITY_ALERT_TOPIC_ARN,
            Subject=subject,
            Message=json.dumps(alert_message, indent=2)
        )
        
        print(f"🚨 Security alert sent: {event_type}")
        
    except Exception as e:
        print(f"Error sending security alert: {str(e)}")

def monitor_failed_logins(user_email: str, ip_address: str):
    """Monitor and alert on failed login attempts"""
    log_security_event(
        'failed_login_attempt',
        {'email': user_email},
        ip_address=ip_address
    )

def monitor_rate_limit_exceeded(endpoint: str, ip_address: str):
    """Monitor rate limit exceeded events"""
    log_security_event(
        'rate_limit_exceeded',
        {'endpoint': endpoint},
        ip_address=ip_address
    )

def monitor_csrf_failure(user_id: str, ip_address: str):
    """Monitor CSRF token failures"""
    log_security_event(
        'invalid_csrf_token',
        {'user_id': user_id},
        user_id=user_id,
        ip_address=ip_address
    )

def monitor_webhook_signature_failure(webhook_type: str, ip_address: str):
    """Monitor webhook signature verification failures"""
    log_security_event(
        'webhook_signature_failure',
        {'webhook_type': webhook_type},
        ip_address=ip_address
    )

def monitor_injection_attempt(attack_type: str, payload: str, ip_address: str):
    """Monitor SQL injection or XSS attempts"""
    event_type = f"{attack_type}_attempt"
    
    # Truncate payload for logging
    truncated_payload = payload[:100] if len(payload) > 100 else payload
    
    log_security_event(
        event_type,
        {
            'attack_type': attack_type,
            'payload_preview': truncated_payload,
            'payload_length': len(payload)
        },
        ip_address=ip_address
    )

