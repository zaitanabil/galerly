"""
Admin Plan Override Handler
Allows platform admins to grant/revoke features for specific users
"""
import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from utils.config import user_features_table, users_table
from utils.response import create_response


def handle_grant_feature(admin_user, body):
    """
    Grant a specific feature to a user (admin only)
    
    POST /api/v1/admin/users/{user_id}/features
    Body: {
        "feature_id": "raw_vault",
        "reason": "Trial extension for photographer",
        "expires_at": "2025-12-31T23:59:59Z" (optional)
    }
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        user_id = body.get('user_id')
        feature_id = body.get('feature_id')
        reason = body.get('reason', '')
        expires_at = body.get('expires_at')
        
        if not user_id or not feature_id:
            return create_response(400, {'error': 'user_id and feature_id required'})
        
        # Verify user exists
        user_response = users_table.scan(
            FilterExpression='id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=1
        )
        
        if not user_response.get('Items'):
            return create_response(404, {'error': 'User not found'})
        
        # Create feature override
        override_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        feature_override = {
            'id': override_id,
            'user_id': user_id,
            'feature_id': feature_id,
            'granted_by': admin_user['id'],
            'reason': reason,
            'granted_at': timestamp,
            'expires_at': expires_at,
            'status': 'active'
        }
        
        user_features_table.put_item(Item=feature_override)
        
        print(f"✅ Admin {admin_user['id']} granted {feature_id} to {user_id}")
        
        return create_response(200, {
            'message': 'Feature granted successfully',
            'override': feature_override
        })
        
    except Exception as e:
        print(f"Error granting feature: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to grant feature'})


def handle_revoke_feature(admin_user, user_id, feature_id):
    """
    Revoke a feature override (admin only)
    
    DELETE /api/v1/admin/users/{user_id}/features/{feature_id}
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        # Find and remove feature override
        response = user_features_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        overrides = response.get('Items', [])
        removed = False
        
        for override in overrides:
            if override.get('feature_id') == feature_id:
                user_features_table.delete_item(Key={
                    'user_id': user_id,
                    'id': override['id']
                })
                removed = True
                print(f"✅ Admin {admin_user['id']} revoked {feature_id} from {user_id}")
        
        if removed:
            return create_response(200, {'message': 'Feature revoked successfully'})
        else:
            return create_response(404, {'error': 'Feature override not found'})
            
    except Exception as e:
        print(f"Error revoking feature: {str(e)}")
        return create_response(500, {'error': 'Failed to revoke feature'})


def handle_list_user_overrides(admin_user, user_id):
    """
    List all feature overrides for a user (admin only)
    
    GET /api/v1/admin/users/{user_id}/features
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        response = user_features_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        overrides = response.get('Items', [])
        
        # Check for expired overrides
        current_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        for override in overrides:
            expires_at = override.get('expires_at')
            if expires_at and expires_at < current_time:
                override['status'] = 'expired'
        
        return create_response(200, {
            'user_id': user_id,
            'overrides': overrides
        })
        
    except Exception as e:
        print(f"Error listing overrides: {str(e)}")
        return create_response(500, {'error': 'Failed to list overrides'})


def handle_upgrade_user_plan(admin_user, body):
    """
    Change user's subscription plan (admin only)
    
    POST /api/v1/admin/users/{user_id}/plan
    Body: {
        "user_id": "user123",
        "plan": "pro",
        "reason": "Customer support upgrade",
        "duration_days": 30 (optional - for trials)
    }
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        user_id = body.get('user_id')
        new_plan = body.get('plan')
        reason = body.get('reason', '')
        duration_days = body.get('duration_days')
        
        if not user_id or not new_plan:
            return create_response(400, {'error': 'user_id and plan required'})
        
        # Validate plan
        from handlers.billing_handler import PLANS
        if new_plan not in PLANS:
            return create_response(400, {'error': f'Invalid plan: {new_plan}'})
        
        # Get user
        user_response = users_table.scan(
            FilterExpression='id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=1
        )
        
        if not user_response.get('Items'):
            return create_response(404, {'error': 'User not found'})
        
        user = user_response['Items'][0]
        old_plan = user.get('plan', 'free')
        
        # Update user plan
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET plan = :plan, updated_at = :time',
            ExpressionAttributeValues={
                ':plan': new_plan,
                ':time': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        # Log the change
        print(f"✅ Admin {admin_user['id']} changed {user_id} plan from {old_plan} to {new_plan}")
        print(f"   Reason: {reason}")
        
        # If duration specified, set expiration
        if duration_days:
            from datetime import timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).replace(tzinfo=None).isoformat() + 'Z'
            print(f"   Trial expires: {expires_at}")
        
        return create_response(200, {
            'message': 'Plan updated successfully',
            'user_id': user_id,
            'old_plan': old_plan,
            'new_plan': new_plan
        })
        
    except Exception as e:
        print(f"Error updating user plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update plan'})


def handle_get_plan_violations(admin_user, query_params=None):
    """
    Get plan violation reports (admin only)
    
    GET /api/v1/admin/violations?days=7
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        from utils.plan_monitoring import get_violation_summary
        
        days = int(query_params.get('days', 7)) if query_params else 7
        
        summary = get_violation_summary(days)
        
        return create_response(200, summary)
        
    except Exception as e:
        print(f"Error getting violations: {str(e)}")
        return create_response(500, {'error': 'Failed to get violations'})


def handle_get_user_violations(admin_user, user_id, query_params=None):
    """
    Get violation history for specific user (admin only)
    
    GET /api/v1/admin/users/{user_id}/violations?days=30
    """
    try:
        # Verify admin role
        if admin_user.get('role') != 'admin':
            return create_response(403, {'error': 'Admin access required'})
        
        from utils.plan_monitoring import get_user_violations
        
        days = int(query_params.get('days', 30)) if query_params else 30
        
        violations = get_user_violations(user_id, days)
        
        return create_response(200, violations)
        
    except Exception as e:
        print(f"Error getting user violations: {str(e)}")
        return create_response(500, {'error': 'Failed to get user violations'})
