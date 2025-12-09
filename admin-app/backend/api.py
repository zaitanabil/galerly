"""
Galerly Admin API
Admin dashboard backend for monitoring and managing the platform
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv()

app = Flask(__name__)

# Secure CORS configuration from environment
allowed_origins = os.environ.get('ADMIN_CORS_ORIGINS', 'http://localhost:3001').split(',')
CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     max_age=3600  # Cache preflight requests for 1 hour
)

# DynamoDB setup with LocalStack support
endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
dynamodb_config = {
    'service_name': 'dynamodb',
    'region_name': os.environ.get('AWS_REGION', 'us-east-1')
}

if endpoint_url:
    dynamodb_config['endpoint_url'] = endpoint_url
    dynamodb_config['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
    dynamodb_config['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
    print(f"🔧 Admin Backend - LocalStack Mode")
    print(f"   Endpoint: {endpoint_url}")

dynamodb = boto3.resource(**dynamodb_config)

# Tables
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'galerly-users-local'))
galleries_table = dynamodb.Table(os.environ.get('GALLERIES_TABLE', 'galerly-galleries-local'))
photos_table = dynamodb.Table(os.environ.get('PHOTOS_TABLE', 'galerly-photos-local'))
subscriptions_table = dynamodb.Table(os.environ.get('SUBSCRIPTIONS_TABLE', 'galerly-subscriptions-local'))
billing_table = dynamodb.Table(os.environ.get('BILLING_TABLE', 'galerly-billing-local'))
audit_log_table = dynamodb.Table(os.environ.get('AUDIT_LOG_TABLE', 'galerly-audit-log-local'))
analytics_table = dynamodb.Table(os.environ.get('ANALYTICS_TABLE', 'galerly-analytics-local'))


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive overview statistics for admin dashboard"""
    try:
        # Get total users
        users_response = users_table.scan(Select='COUNT')
        total_users = users_response['Count']
        
        # Get users with detailed breakdown
        all_users = users_table.scan()
        users_list = all_users.get('Items', [])
        
        # User stats by role
        photographers_count = sum(1 for u in users_list if u.get('role') == 'photographer')
        clients_count = total_users - photographers_count
        
        # User stats by plan
        users_by_plan = {}
        for user in users_list:
            plan = user.get('plan', 'free')
            users_by_plan[plan] = users_by_plan.get(plan, 0) + 1
        
        # Get total galleries
        galleries_response = galleries_table.scan(Select='COUNT')
        total_galleries = galleries_response['Count']
        
        # Get total photos
        photos_response = photos_table.scan(Select='COUNT')
        total_photos = photos_response['Count']
        
        # Get all subscriptions with full details
        subscriptions_response = subscriptions_table.scan()
        all_subscriptions = subscriptions_response.get('Items', [])
        
        # Subscription breakdown by status
        active_subscriptions = [s for s in all_subscriptions if s.get('status') == 'active']
        canceled_subscriptions = [s for s in all_subscriptions if s.get('status') == 'canceled']
        
        # Subscription breakdown by plan
        subs_by_plan = {}
        active_by_plan = {}
        canceled_by_plan = {}
        
        for sub in all_subscriptions:
            plan = sub.get('plan', 'free')
            status = sub.get('status', 'unknown')
            
            subs_by_plan[plan] = subs_by_plan.get(plan, 0) + 1
            
            if status == 'active':
                active_by_plan[plan] = active_by_plan.get(plan, 0) + 1
            elif status == 'canceled':
                canceled_by_plan[plan] = canceled_by_plan.get(plan, 0) + 1
        
        # Subscription breakdown by billing interval (only count active subscriptions)
        monthly_subs = []
        annual_subs = []
        
        for sub in active_subscriptions:
            interval = sub.get('interval', 'month')  # Default to month if not set
            if interval in ['month', 'monthly']:
                monthly_subs.append(sub)
            elif interval in ['year', 'annual', 'yearly']:
                annual_subs.append(sub)
        
        monthly_by_plan = {}
        annual_by_plan = {}
        
        for sub in monthly_subs:
            plan = sub.get('plan', 'free')
            monthly_by_plan[plan] = monthly_by_plan.get(plan, 0) + 1
        
        for sub in annual_subs:
            plan = sub.get('plan', 'free')
            annual_by_plan[plan] = annual_by_plan.get(plan, 0) + 1
        
        # Calculate MRR and ARR
        plan_prices_monthly = {
            'starter': 12,
            'plus': 29,
            'pro': 59,
            'ultimate': 119
        }
        
        plan_prices_annual = {
            'starter': 99,
            'plus': 249,
            'pro': 499,
            'ultimate': 999
        }
        
        mrr = 0
        arr = 0
        
        # MRR from monthly subscriptions
        for sub in monthly_subs:
            plan = sub.get('plan', 'free')
            mrr += plan_prices_monthly.get(plan, 0)
        
        # Add annualized monthly from annual subscriptions
        for sub in annual_subs:
            plan = sub.get('plan', 'free')
            annual_price = plan_prices_annual.get(plan, 0)
            mrr += annual_price / 12  # Convert annual to monthly
            arr += annual_price
        
        # Total ARR (annualize all subscriptions)
        arr = mrr * 12
        
        # Get billing data for revenue trends
        billing_response = billing_table.scan()
        billing_records = billing_response.get('Items', [])
        
        # Revenue by month (last 12 months)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        monthly_revenue = {}
        
        for i in range(12):
            month_date = now - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            monthly_revenue[month_key] = 0
        
        for record in billing_records:
            created_at = record.get('created_at', '')
            if created_at:
                month_key = created_at[:7]
                if month_key in monthly_revenue:
                    monthly_revenue[month_key] += float(record.get('amount', 0))
        
        # Get recent activity count (last 24 hours) - handle if table doesn't exist
        recent_activity_count = 0
        try:
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
            recent_activity = audit_log_table.scan(
                FilterExpression=Attr('timestamp').gt(yesterday),
                Select='COUNT'
            )
            recent_activity_count = recent_activity['Count']
        except Exception as e:
            print(f"Note: Audit log table not available: {str(e)}")
            recent_activity_count = 0
        
        return jsonify({
            # User metrics
            'total_users': total_users,
            'total_photographers': photographers_count,
            'total_clients': clients_count,
            'users_by_plan': users_by_plan,
            
            # Content metrics
            'total_galleries': total_galleries,
            'total_photos': total_photos,
            'avg_photos_per_gallery': round(total_photos / total_galleries) if total_galleries > 0 else 0,
            
            # Subscription metrics
            'total_subscriptions': len(all_subscriptions),
            'active_subscriptions': len(active_subscriptions),
            'canceled_subscriptions': len(canceled_subscriptions),
            'subscriptions_by_plan': subs_by_plan,
            'active_by_plan': active_by_plan,
            'canceled_by_plan': canceled_by_plan,
            
            # Billing interval breakdown
            'monthly_subscriptions': len(monthly_subs),
            'annual_subscriptions': len(annual_subs),
            'monthly_by_plan': monthly_by_plan,
            'annual_by_plan': annual_by_plan,
            
            # Revenue metrics
            'monthly_recurring_revenue': round(mrr, 2),
            'annual_recurring_revenue': round(arr, 2),
            'monthly_revenue_trend': monthly_revenue,
            
            # Activity
            'recent_activity_24h': recent_activity_count
        }), 200
        
    except Exception as e:
        print(f"Error getting dashboard stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with pagination and filtering"""
    try:
        # Get query parameters
        role = request.args.get('role')
        plan = request.args.get('plan')
        limit = int(request.args.get('limit', 50))
        
        scan_params = {}
        filter_expressions = []
        
        if role:
            filter_expressions.append(Attr('role').eq(role))
        
        if plan:
            filter_expressions.append(Attr('plan').eq(plan))
        
        if filter_expressions:
            from functools import reduce
            scan_params['FilterExpression'] = reduce(lambda a, b: a & b, filter_expressions)
        
        scan_params['Limit'] = limit
        
        response = users_table.scan(**scan_params)
        
        # Remove sensitive data
        users = []
        for user in response['Items']:
            users.append({
                'id': user.get('id'),
                'email': user.get('email'),
                'name': user.get('name'),
                'role': user.get('role'),
                'plan': user.get('plan', 'free'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login'),
                'gallery_count': user.get('gallery_count', 0),
                'photo_count': user.get('photo_count', 0)
            })
        
        return jsonify({
            'users': users,
            'count': len(users),
            'last_evaluated_key': response.get('LastEvaluatedKey')
        }), 200
        
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    try:
        # Get user
        users = users_table.scan(FilterExpression=Attr('id').eq(user_id))
        if not users.get('Items'):
            return jsonify({'error': 'User not found'}), 404
        
        user = users['Items'][0]
        
        # Get user's galleries
        galleries = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        # Get user's subscriptions (use scan instead of query with index)
        subscription_response = subscriptions_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )
        subscription = subscription_response.get('Items', [{}])[0] if subscription_response.get('Items') else None
        
        # Get user's billing history (use scan instead of query with index)
        billing_response = billing_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )
        billing_history = sorted(
            billing_response.get('Items', []),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )[:10]
        
        # Get recent activity (use scan instead of query with index)
        activity_response = audit_log_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )
        recent_activity = sorted(
            activity_response.get('Items', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:20]
        
        return jsonify({
            'user': {
                'id': user.get('id'),
                'email': user.get('email'),
                'name': user.get('name'),
                'role': user.get('role'),
                'plan': user.get('plan', 'free'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login'),
                'city': user.get('city'),
                'bio': user.get('bio'),
                'account_status': user.get('account_status', 'active')
            },
            'galleries': galleries.get('Items', []),
            'subscription': subscription,
            'billing_history': billing_history,
            'recent_activity': recent_activity
        }), 200
        
    except Exception as e:
        print(f"Error getting user details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/activity', methods=['GET'])
def get_recent_activity():
    """Get recent platform activity"""
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 100))
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z'
        
        response = audit_log_table.scan(
            FilterExpression=Attr('timestamp').gt(since),
            Limit=limit
        )
        
        # Sort by timestamp descending
        activities = sorted(
            response['Items'],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return jsonify({
            'activities': activities,
            'count': len(activities)
        }), 200
        
    except Exception as e:
        print(f"Error getting activity: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/revenue', methods=['GET'])
def get_revenue_stats():
    """Get revenue statistics with enhanced details"""
    try:
        # Get all billing records
        response = billing_table.scan()
        records = response['Items']
        
        # Calculate totals
        total_revenue = sum(float(r.get('amount', 0)) for r in records)
        
        # Revenue by month
        monthly_revenue = {}
        for record in records:
            created_at = record.get('created_at', '')
            if created_at:
                month = created_at[:7]  # YYYY-MM
                monthly_revenue[month] = monthly_revenue.get(month, 0) + float(record.get('amount', 0))
        
        # Revenue by plan with transaction count
        plan_revenue = {}
        plan_transactions = {}
        for record in records:
            plan = record.get('plan', 'unknown')
            amount = float(record.get('amount', 0))
            plan_revenue[plan] = plan_revenue.get(plan, 0) + amount
            plan_transactions[plan] = plan_transactions.get(plan, 0) + 1
        
        # Enrich billing records with user validation
        orphaned_revenue = 0
        for record in records:
            user_id = record.get('user_id')
            if user_id:
                user_response = users_table.scan(
                    FilterExpression=Attr('id').eq(user_id),
                    Limit=1
                )
                if not user_response.get('Items'):
                    orphaned_revenue += float(record.get('amount', 0))
        
        return jsonify({
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'revenue_by_plan': plan_revenue,
            'transactions_by_plan': plan_transactions,
            'total_transactions': len(records),
            'health_issues': {
                'orphaned_revenue': orphaned_revenue,
                'orphaned_transactions': sum(1 for r in records if not users_table.scan(FilterExpression=Attr('id').eq(r.get('user_id')), Limit=1).get('Items'))
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting revenue stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/subscriptions', methods=['GET'])
def get_subscriptions():
    """Get all subscriptions with enhanced details"""
    try:
        status = request.args.get('status')
        
        if status:
            response = subscriptions_table.scan(
                FilterExpression=Attr('status').eq(status)
            )
        else:
            response = subscriptions_table.scan()
        
        subscriptions = response['Items']
        
        # Enrich subscriptions with user data and validation
        enriched_subscriptions = []
        orphaned_count = 0
        duplicate_emails = {}
        
        for sub in subscriptions:
            user_id = sub.get('user_id')
            email = sub.get('user_email', 'N/A')
            
            # Check if user exists
            user_exists = False
            user_name = None
            if user_id:
                user_response = users_table.scan(
                    FilterExpression=Attr('id').eq(user_id),
                    Limit=1
                )
                if user_response.get('Items'):
                    user_exists = True
                    user_name = user_response['Items'][0].get('name')
            
            # Track duplicates by email
            if email != 'N/A':
                if email not in duplicate_emails:
                    duplicate_emails[email] = []
                duplicate_emails[email].append(sub.get('id'))
            
            # Add enriched data
            enriched_sub = dict(sub)
            enriched_sub['user_exists'] = user_exists
            enriched_sub['user_name'] = user_name
            enriched_sub['is_orphaned'] = not user_exists
            
            if not user_exists:
                orphaned_count += 1
            
            enriched_subscriptions.append(enriched_sub)
        
        # Identify duplicate emails (more than one subscription per email)
        duplicate_email_list = {email: ids for email, ids in duplicate_emails.items() if len(ids) > 1}
        
        # Group by plan
        by_plan = {}
        by_status = {}
        for sub in subscriptions:
            plan = sub.get('plan', 'free')
            status_val = sub.get('status', 'unknown')
            by_plan[plan] = by_plan.get(plan, 0) + 1
            by_status[status_val] = by_status.get(status_val, 0) + 1
        
        return jsonify({
            'subscriptions': enriched_subscriptions,
            'count': len(subscriptions),
            'by_plan': by_plan,
            'by_status': by_status,
            'orphaned_count': orphaned_count,
            'duplicate_emails': duplicate_email_list,
            'health_issues': {
                'orphaned_subscriptions': orphaned_count,
                'duplicate_email_count': len(duplicate_email_list)
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting subscriptions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/data-health', methods=['GET'])
def get_data_health():
    """Get comprehensive data health and integrity report"""
    try:
        issues = []
        
        # Check for orphaned subscriptions
        subs_response = subscriptions_table.scan()
        subscriptions = subs_response['Items']
        
        orphaned_subs = []
        for sub in subscriptions:
            user_id = sub.get('user_id')
            if user_id:
                user_response = users_table.scan(
                    FilterExpression=Attr('id').eq(user_id),
                    Limit=1
                )
                if not user_response.get('Items'):
                    orphaned_subs.append({
                        'subscription_id': sub.get('id'),
                        'stripe_subscription_id': sub.get('stripe_subscription_id'),
                        'user_id': user_id,
                        'user_email': sub.get('user_email'),
                        'plan': sub.get('plan'),
                        'status': sub.get('status'),
                        'created_at': sub.get('created_at')
                    })
        
        if orphaned_subs:
            issues.append({
                'type': 'orphaned_subscriptions',
                'severity': 'high',
                'count': len(orphaned_subs),
                'description': 'Subscriptions exist without corresponding user accounts',
                'items': orphaned_subs
            })
        
        # Check for duplicate email subscriptions
        email_groups = {}
        for sub in subscriptions:
            email = sub.get('user_email', 'N/A')
            if email != 'N/A':
                if email not in email_groups:
                    email_groups[email] = []
                email_groups[email].append(sub)
        
        duplicate_emails = []
        for email, subs in email_groups.items():
            if len(subs) > 1:
                duplicate_emails.append({
                    'email': email,
                    'count': len(subs),
                    'subscriptions': [{
                        'id': s.get('id'),
                        'user_id': s.get('user_id'),
                        'plan': s.get('plan'),
                        'status': s.get('status'),
                        'stripe_subscription_id': s.get('stripe_subscription_id')
                    } for s in subs]
                })
        
        if duplicate_emails:
            issues.append({
                'type': 'duplicate_email_subscriptions',
                'severity': 'medium',
                'count': len(duplicate_emails),
                'description': 'Multiple subscriptions found for the same email address',
                'items': duplicate_emails
            })
        
        # Check for orphaned billing records
        billing_response = billing_table.scan()
        billing_records = billing_response['Items']
        
        orphaned_billing = []
        for record in billing_records:
            user_id = record.get('user_id')
            if user_id:
                user_response = users_table.scan(
                    FilterExpression=Attr('id').eq(user_id),
                    Limit=1
                )
                if not user_response.get('Items'):
                    orphaned_billing.append({
                        'billing_id': record.get('id'),
                        'user_id': user_id,
                        'amount': float(record.get('amount', 0)),
                        'plan': record.get('plan'),
                        'stripe_invoice_id': record.get('stripe_invoice_id'),
                        'created_at': record.get('created_at')
                    })
        
        if orphaned_billing:
            issues.append({
                'type': 'orphaned_billing_records',
                'severity': 'medium',
                'count': len(orphaned_billing),
                'description': 'Billing records exist without corresponding user accounts',
                'items': orphaned_billing
            })
        
        # Summary
        health_score = 100 - (len(orphaned_subs) * 10 + len(duplicate_emails) * 5 + len(orphaned_billing) * 3)
        health_score = max(0, min(100, health_score))
        
        return jsonify({
            'health_score': health_score,
            'total_issues': len(issues),
            'issues': issues,
            'summary': {
                'orphaned_subscriptions': len(orphaned_subs),
                'duplicate_emails': len(duplicate_emails),
                'orphaned_billing': len(orphaned_billing)
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting data health: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    """Suspend a user account"""
    try:
        body = request.get_json() or {}
        reason = body.get('reason', 'Suspended by administrator')
        
        # Find user by ID
        users = users_table.scan(FilterExpression=Attr('id').eq(user_id))
        if not users.get('Items'):
            return jsonify({'error': 'User not found'}), 404
        
        user = users['Items'][0]
        
        # Update user status
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET account_status = :status, suspended_at = :now, suspension_reason = :reason',
            ExpressionAttributeValues={
                ':status': 'suspended',
                ':now': datetime.utcnow().isoformat() + 'Z',
                ':reason': reason
            }
        )
        
        # Log to audit
        audit_log_table.put_item(Item={
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'account_suspended',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'details': {'reason': reason}
        })
        
        return jsonify({'message': 'User suspended successfully'}), 200
        
    except Exception as e:
        print(f"Error suspending user: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/unsuspend', methods=['POST'])
def unsuspend_user(user_id):
    """Unsuspend a user account"""
    try:
        # Find user by ID
        users = users_table.scan(FilterExpression=Attr('id').eq(user_id))
        if not users.get('Items'):
            return jsonify({'error': 'User not found'}), 404
        
        user = users['Items'][0]
        
        # Update user status
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET account_status = :status REMOVE suspended_at, suspension_reason',
            ExpressionAttributeValues={
                ':status': 'active'
            }
        )
        
        # Log to audit
        audit_log_table.put_item(Item={
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'account_unsuspended',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return jsonify({'message': 'User unsuspended successfully'}), 200
        
    except Exception as e:
        print(f"Error unsuspending user: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user account and all associated data"""
    try:
        # Find user by ID
        users = users_table.scan(FilterExpression=Attr('id').eq(user_id))
        if not users.get('Items'):
            return jsonify({'error': 'User not found'}), 404
        
        user = users['Items'][0]
        user_email = user['email']
        
        # Delete user's galleries
        galleries = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        for gallery in galleries.get('Items', []):
            galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery['id']})
        
        # Delete user's photos
        photos = photos_table.scan(FilterExpression=Attr('user_id').eq(user_id))
        for photo in photos.get('Items', []):
            photos_table.delete_item(Key={'id': photo['id']})
        
        # Delete user's subscriptions
        subs = subscriptions_table.scan(FilterExpression=Attr('user_id').eq(user_id))
        for sub in subs.get('Items', []):
            subscriptions_table.delete_item(Key={'id': sub['id']})
        
        # Delete user
        users_table.delete_item(Key={'email': user_email})
        
        # Log to audit
        audit_log_table.put_item(Item={
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'account_deleted_by_admin',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'details': {'email': user_email}
        })
        
        return jsonify({'message': 'User and all associated data deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/galleries', methods=['GET'])
def get_user_galleries(user_id):
    """Get all galleries for a specific user"""
    try:
        response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        galleries = response.get('Items', [])
        
        # Sort by created date descending
        galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'galleries': galleries,
            'count': len(galleries)
        }), 200
        
    except Exception as e:
        print(f"Error getting user galleries: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/galleries', methods=['GET'])
def get_all_galleries():
    """Get all galleries across all users with pagination"""
    try:
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '').lower()
        
        response = galleries_table.scan(Limit=limit)
        galleries = response.get('Items', [])
        
        # Enrich with user info
        enriched_galleries = []
        for gallery in galleries:
            user_id = gallery.get('user_id')
            if user_id:
                user_response = users_table.scan(
                    FilterExpression=Attr('id').eq(user_id),
                    Limit=1
                )
                if user_response.get('Items'):
                    gallery['user'] = {
                        'email': user_response['Items'][0].get('email'),
                        'name': user_response['Items'][0].get('name'),
                        'role': user_response['Items'][0].get('role')
                    }
            
            # Apply search filter
            if search:
                if (search in gallery.get('name', '').lower() or
                    search in gallery.get('client_name', '').lower() or
                    search in gallery.get('user', {}).get('email', '').lower()):
                    enriched_galleries.append(gallery)
            else:
                enriched_galleries.append(gallery)
        
        # Sort by created date
        enriched_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'galleries': enriched_galleries,
            'count': len(enriched_galleries),
            'total': len(galleries)
        }), 200
        
    except Exception as e:
        print(f"Error getting galleries: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/galleries/<gallery_id>', methods=['DELETE'])
def delete_gallery(gallery_id):
    """Delete a gallery and its photos"""
    try:
        # Get gallery
        galleries = galleries_table.scan(
            FilterExpression=Attr('id').eq(gallery_id)
        )
        
        if not galleries.get('Items'):
            return jsonify({'error': 'Gallery not found'}), 404
        
        gallery = galleries['Items'][0]
        user_id = gallery['user_id']
        
        # Delete photos
        photos = photos_table.scan(FilterExpression=Attr('gallery_id').eq(gallery_id))
        for photo in photos.get('Items', []):
            photos_table.delete_item(Key={'id': photo['id']})
        
        # Delete gallery
        galleries_table.delete_item(Key={'user_id': user_id, 'id': gallery_id})
        
        # Log to audit
        audit_log_table.put_item(Item={
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'gallery_deleted_by_admin',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'details': {'gallery_id': gallery_id, 'gallery_name': gallery.get('name')}
        })
        
        return jsonify({'message': 'Gallery deleted successfully'}), 200
        
    except Exception as e:
        print(f"Error deleting gallery: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/create', methods=['POST'])
def create_user():
    """Create a new user account"""
    try:
        body = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'name', 'password', 'role']
        for field in required_fields:
            if field not in body:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        email = body['email'].lower()
        name = body['name']
        password = body['password']
        role = body['role']
        plan = body.get('plan', 'free')
        
        # Check if user exists
        existing = users_table.get_item(Key={'email': email})
        if existing.get('Item'):
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create user
        import uuid as uuid_lib
        import bcrypt
        
        def hash_password(password):
            """Hash password using bcrypt"""
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        
        user_id = str(uuid_lib.uuid4())
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Generate username
        username = email.split('@')[0]
        counter = 1
        while True:
            check = users_table.scan(
                FilterExpression=Attr('username').eq(username),
                Limit=1
            )
            if not check.get('Items'):
                break
            username = f"{email.split('@')[0]}{counter}"
            counter += 1
        
        user = {
            'id': user_id,
            'email': email,
            'name': name,
            'password_hash': hash_password(password),
            'role': role,
            'plan': plan,
            'username': username,
            'email_verified': True,  # Admin-created accounts are pre-verified
            'account_status': 'active',
            'created_at': current_time,
            'updated_at': current_time,
            'created_by_admin': True
        }
        
        users_table.put_item(Item=user)
        
        # Log to audit
        audit_log_table.put_item(Item={
            'id': str(uuid_lib.uuid4()),
            'user_id': user_id,
            'action': 'account_created_by_admin',
            'timestamp': current_time,
            'details': {'email': email, 'role': role}
        })
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({'user': user}), 201
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'galerly-admin-api'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)

