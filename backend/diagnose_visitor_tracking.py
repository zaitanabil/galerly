#!/usr/bin/env python3
"""
Diagnose Visitor Tracking Issues
Checks DynamoDB table, Lambda permissions, and test the endpoint
"""
import boto3
import json
import os
from botocore.exceptions import ClientError

# Configuration
REGION = os.environ.get('AWS_REGION', 'us-east-1')
TABLE_NAME = 'galerly-visitor-tracking'
LAMBDA_NAME = os.environ.get('LAMBDA_FUNCTION_NAME', 'galerly-api')

# Initialize clients
dynamodb = boto3.client('dynamodb', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
logs = boto3.client('logs', region_name=REGION)


def check_dynamodb_table():
    """Check if the visitor tracking table exists and is active"""
    print("═══════════════════════════════════════════════════════════════")
    print("1️⃣  CHECKING DYNAMODB TABLE")
    print("═══════════════════════════════════════════════════════════════")
    
    try:
        response = dynamodb.describe_table(TableName=TABLE_NAME)
        table_status = response['Table']['TableStatus']
        item_count = response['Table']['ItemCount']
        
        if table_status == 'ACTIVE':
            print(f"✅ Table '{TABLE_NAME}' exists and is ACTIVE")
            print(f"   Item count: {item_count}")
            
            # Check indexes
            gsi = response['Table'].get('GlobalSecondaryIndexes', [])
            print(f"   Global Secondary Indexes: {len(gsi)}")
            for index in gsi:
                print(f"      • {index['IndexName']}: {index['IndexStatus']}")
            
            return True
        else:
            print(f"⚠️  Table exists but status is: {table_status}")
            return False
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Table '{TABLE_NAME}' does NOT exist!")
            print("   Run: python setup_dynamodb.py create")
        else:
            print(f"❌ Error checking table: {str(e)}")
        return False


def check_lambda_permissions():
    """Check if Lambda has permission to access DynamoDB"""
    print("\n═══════════════════════════════════════════════════════════════")
    print("2️⃣  CHECKING LAMBDA PERMISSIONS")
    print("═══════════════════════════════════════════════════════════════")
    
    try:
        # Get Lambda function config
        response = lambda_client.get_function_configuration(FunctionName=LAMBDA_NAME)
        role_arn = response['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"✅ Lambda function: {LAMBDA_NAME}")
        print(f"   IAM Role: {role_name}")
        
        # Get role policies
        try:
            attached_policies = iam.list_attached_role_policies(RoleName=role_name)
            print(f"   Attached policies: {len(attached_policies['AttachedPolicies'])}")
            
            has_dynamodb = False
            for policy in attached_policies['AttachedPolicies']:
                policy_name = policy['PolicyName']
                print(f"      • {policy_name}")
                
                if 'Dynamo' in policy_name or 'DynamoDB' in policy_name:
                    has_dynamodb = True
            
            if not has_dynamodb:
                print("   ⚠️  No DynamoDB policy found in attached policies")
                print("      Checking inline policies...")
                
                inline_policies = iam.list_role_policies(RoleName=role_name)
                if inline_policies['PolicyNames']:
                    print(f"      Inline policies: {', '.join(inline_policies['PolicyNames'])}")
                else:
                    print("      ❌ No inline policies found")
            else:
                print("   ✅ DynamoDB policy attached")
            
            return True
            
        except ClientError as e:
            print(f"   ⚠️  Cannot check role policies: {str(e)}")
            return True  # Continue anyway
            
    except ClientError as e:
        print(f"❌ Error checking Lambda: {str(e)}")
        return False


def check_lambda_environment():
    """Check Lambda environment variables"""
    print("\n═══════════════════════════════════════════════════════════════")
    print("3️⃣  CHECKING LAMBDA ENVIRONMENT VARIABLES")
    print("═══════════════════════════════════════════════════════════════")
    
    try:
        response = lambda_client.get_function_configuration(FunctionName=LAMBDA_NAME)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        print(f"✅ Environment variables: {len(env_vars)}")
        
        # Check required variables
        required = ['AWS_REGION', 'FRONTEND_URL', 'JWT_SECRET']
        for var in required:
            if var in env_vars:
                value = env_vars[var]
                # Mask sensitive values
                if 'SECRET' in var or 'KEY' in var:
                    value = '*' * len(value)
                print(f"   ✅ {var}: {value}")
            else:
                print(f"   ⚠️  {var}: NOT SET")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error checking environment: {str(e)}")
        return False


def check_recent_logs():
    """Check CloudWatch Logs for recent errors"""
    print("\n═══════════════════════════════════════════════════════════════")
    print("4️⃣  CHECKING CLOUDWATCH LOGS (Last 10 minutes)")
    print("═══════════════════════════════════════════════════════════════")
    
    log_group = f'/aws/lambda/{LAMBDA_NAME}'
    
    try:
        # Get log streams
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        if not streams['logStreams']:
            print("⚠️  No log streams found")
            return False
        
        print(f"✅ Found {len(streams['logStreams'])} recent log streams")
        
        # Get events from most recent stream
        latest_stream = streams['logStreams'][0]['logStreamName']
        print(f"   Latest stream: {latest_stream}")
        
        # Get logs from last 10 minutes (600000 ms)
        import time
        start_time = int((time.time() - 600) * 1000)
        
        events = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=latest_stream,
            startTime=start_time,
            limit=50
        )
        
        error_count = 0
        visitor_tracking_errors = []
        
        for event in events['events']:
            message = event['message']
            
            # Look for errors
            if 'ERROR' in message or 'Traceback' in message or '500' in message:
                error_count += 1
                
            # Look for visitor tracking specific errors
            if 'visitor' in message.lower() or 'track' in message.lower():
                visitor_tracking_errors.append(message)
        
        if error_count > 0:
            print(f"\n   ⚠️  Found {error_count} errors in recent logs")
            
            if visitor_tracking_errors:
                print("\n   📋 Visitor Tracking Related Logs:")
                for msg in visitor_tracking_errors[:5]:  # Show first 5
                    print(f"      {msg.strip()[:200]}")
        else:
            print("   ✅ No errors found in recent logs")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Log group '{log_group}' not found")
            print("   Lambda may not have been invoked yet")
        else:
            print(f"❌ Error checking logs: {str(e)}")
        return False


def test_visitor_tracking_locally():
    """Test the visitor tracking handler locally"""
    print("\n═══════════════════════════════════════════════════════════════")
    print("5️⃣  TESTING HANDLER LOCALLY")
    print("═══════════════════════════════════════════════════════════════")
    
    try:
        # Import the handler
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from handlers.visitor_tracking_handler import handle_track_event
        
        # Test payload
        test_body = {
            'session_id': 'test-session-12345',
            'visitor_id': 'test-visitor-67890',
            'event_type': 'diagnostic_test',
            'event_category': 'testing',
            'event_label': 'Diagnostic script test',
            'page_url': 'https://galerly.com/test'
        }
        
        print("🧪 Sending test event...")
        response = handle_track_event(test_body)
        
        status_code = response.get('statusCode')
        body = json.loads(response.get('body', '{}'))
        
        if status_code == 200:
            print(f"✅ Handler works! Response:")
            print(f"   {json.dumps(body, indent=2)}")
            return True
        else:
            print(f"❌ Handler returned error {status_code}:")
            print(f"   {json.dumps(body, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic checks"""
    print("\n🔍 VISITOR TRACKING DIAGNOSTICS")
    print("═══════════════════════════════════════════════════════════════")
    print(f"Region: {REGION}")
    print(f"Table: {TABLE_NAME}")
    print(f"Lambda: {LAMBDA_NAME}")
    print()
    
    results = {
        'dynamodb': check_dynamodb_table(),
        'permissions': check_lambda_permissions(),
        'environment': check_lambda_environment(),
        'logs': check_recent_logs(),
        'local_test': test_visitor_tracking_locally()
    }
    
    print("\n═══════════════════════════════════════════════════════════════")
    print("📊 DIAGNOSTIC SUMMARY")
    print("═══════════════════════════════════════════════════════════════")
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ All checks passed!")
        print("\n💡 If you're still seeing CORS errors, the issue is likely:")
        print("   1. Browser caching old responses (try hard refresh)")
        print("   2. API Gateway custom domain needs CORS configuration")
        print("   3. CloudFront cache needs invalidation")
    else:
        print("\n❌ Some checks failed. Fix the issues above and try again.")
    
    print()


if __name__ == '__main__':
    main()

