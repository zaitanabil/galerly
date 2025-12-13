"""
CloudWatch Monitoring Dashboard Setup
Creates comprehensive monitoring dashboard for new features
"""
import json
import boto3
import os
from datetime import datetime

# AWS clients
cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

# Configuration
DASHBOARD_NAME = os.environ.get('CLOUDWATCH_DASHBOARD_NAME', 'Galerly-NewFeatures-Dashboard')
LAMBDA_FUNCTION_NAME = os.environ.get('LAMBDA_FUNCTION_NAME', 'galerly-api')
API_GATEWAY_NAME = os.environ.get('API_GATEWAY_NAME', 'galerly-api')


def create_dashboard():
    """
    Create CloudWatch dashboard for monitoring new features
    """
    
    dashboard_body = {
        "widgets": [
            # Header
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": "# Galerly New Features Monitoring Dashboard\nMonitoring SEO, Analytics, Email Automation, Gallery Statistics, and Client Selection"
                }
            },
            
            # Lambda Metrics Row 1
            {
                "type": "metric",
                "x": 0,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Invocations", { "stat": "Sum", "label": "Total Invocations" } ],
                        [ ".", "Errors", { "stat": "Sum", "label": "Errors", "color": "#d62728" } ],
                        [ ".", "Throttles", { "stat": "Sum", "label": "Throttles", "color": "#ff7f0e" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "Lambda Function Health",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0
                        }
                    }
                }
            },
            
            {
                "type": "metric",
                "x": 12,
                "y": 1,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/Lambda", "Duration", { "stat": "Average", "label": "Avg Duration" } ],
                        [ "...", { "stat": "Maximum", "label": "Max Duration", "color": "#d62728" } ],
                        [ ".", ".", { "stat": "p99", "label": "P99 Duration", "color": "#ff7f0e" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "Lambda Duration (ms)",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "label": "Milliseconds"
                        }
                    }
                }
            },
            
            # API Gateway Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 7,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "Count", { "stat": "Sum", "label": "Total Requests" } ],
                        [ ".", "4XXError", { "stat": "Sum", "label": "4XX Errors", "color": "#ff7f0e" } ],
                        [ ".", "5XXError", { "stat": "Sum", "label": "5XX Errors", "color": "#d62728" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "API Gateway Requests & Errors",
                    "period": 300
                }
            },
            
            {
                "type": "metric",
                "x": 8,
                "y": 7,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "Latency", { "stat": "Average", "label": "Avg Latency" } ],
                        [ "...", { "stat": "p95", "label": "P95 Latency", "color": "#ff7f0e" } ],
                        [ ".", ".", { "stat": "p99", "label": "P99 Latency", "color": "#d62728" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "API Gateway Latency (ms)",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "label": "Milliseconds"
                        }
                    }
                }
            },
            
            {
                "type": "metric",
                "x": 16,
                "y": 7,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/ApiGateway", "CacheHitCount", { "stat": "Sum", "label": "Cache Hits" } ],
                        [ ".", "CacheMissCount", { "stat": "Sum", "label": "Cache Misses", "color": "#ff7f0e" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "API Gateway Cache Performance",
                    "period": 300
                }
            },
            
            # DynamoDB Metrics
            {
                "type": "metric",
                "x": 0,
                "y": 13,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", { "stat": "Sum", "label": "Read Capacity (client_selections)" }, { "TableName": "client_selections" } ],
                        [ ".", "ConsumedWriteCapacityUnits", { "stat": "Sum", "label": "Write Capacity (client_selections)" }, { "TableName": "client_selections" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "DynamoDB - client_selections Table",
                    "period": 300
                }
            },
            
            {
                "type": "metric",
                "x": 12,
                "y": 13,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "AWS/DynamoDB", "UserErrors", { "stat": "Sum", "label": "User Errors", "color": "#ff7f0e" }, { "TableName": "client_selections" } ],
                        [ ".", "SystemErrors", { "stat": "Sum", "label": "System Errors", "color": "#d62728" }, { "TableName": "client_selections" } ],
                        [ ".", "ThrottledRequests", { "stat": "Sum", "label": "Throttled", "color": "#9467bd" }, { "TableName": "client_selections" } ]
                    ],
                    "view": "timeSeries",
                    "stacked": false,
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "title": "DynamoDB Errors & Throttling",
                    "period": 300
                }
            },
            
            # Custom Metrics (Log-based)
            {
                "type": "log",
                "x": 0,
                "y": 19,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{LAMBDA_FUNCTION_NAME}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "stacked": false,
                    "title": "Recent Errors",
                    "view": "table"
                }
            },
            
            # Feature-specific metrics
            {
                "type": "text",
                "x": 0,
                "y": 25,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": "## Feature-Specific Metrics"
                }
            },
            
            {
                "type": "log",
                "x": 0,
                "y": 26,
                "width": 8,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{LAMBDA_FUNCTION_NAME}'\n| fields @timestamp\n| filter @message like /\\/seo\\/recommendations/\n| stats count() by bin(5m)",
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "stacked": false,
                    "title": "SEO Recommendations Requests",
                    "view": "timeSeries"
                }
            },
            
            {
                "type": "log",
                "x": 8,
                "y": 26,
                "width": 8,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{LAMBDA_FUNCTION_NAME}'\n| fields @timestamp\n| filter @message like /\\/analytics\\/export\\/excel/\n| stats count() by bin(5m)",
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "stacked": false,
                    "title": "Excel Export Requests",
                    "view": "timeSeries"
                }
            },
            
            {
                "type": "log",
                "x": 16,
                "y": 26,
                "width": 8,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{LAMBDA_FUNCTION_NAME}'\n| fields @timestamp\n| filter @message like /\\/selections\\//\n| stats count() by bin(5m)",
                    "region": os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                    "stacked": false,
                    "title": "Selection Workflow Requests",
                    "view": "timeSeries"
                }
            },
            
            # Alarms Summary
            {
                "type": "text",
                "x": 0,
                "y": 32,
                "width": 24,
                "height": 1,
                "properties": {
                    "markdown": "## Active Alarms"
                }
            },
            
            {
                "type": "alarm",
                "x": 0,
                "y": 33,
                "width": 24,
                "height": 3,
                "properties": {
                    "title": "Alarm Status",
                    "alarms": [
                        f"arn:aws:cloudwatch:{os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:alarm:galerly-lambda-errors",
                        f"arn:aws:cloudwatch:{os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:alarm:galerly-lambda-duration",
                        f"arn:aws:cloudwatch:{os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID', '123456789012')}:alarm:galerly-api-5xx"
                    ]
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"✓ Dashboard created successfully: {DASHBOARD_NAME}")
        print(f"  Dashboard ARN: {response.get('DashboardValidationMessages', [])}")
        print(f"\nView dashboard at:")
        print(f"https://console.aws.amazon.com/cloudwatch/home?region={os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}#dashboards:name={DASHBOARD_NAME}")
        
        return response
        
    except Exception as e:
        print(f"✗ Error creating dashboard: {str(e)}")
        raise


def create_alarms():
    """
    Create CloudWatch alarms for monitoring
    """
    
    alarms = [
        {
            'AlarmName': 'galerly-lambda-errors',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 1,
            'MetricName': 'Errors',
            'Namespace': 'AWS/Lambda',
            'Period': 300,
            'Statistic': 'Sum',
            'Threshold': 5.0,
            'ActionsEnabled': True,
            'AlarmDescription': 'Alert when Lambda function errors exceed threshold',
            'Dimensions': [
                {
                    'Name': 'FunctionName',
                    'Value': LAMBDA_FUNCTION_NAME
                }
            ],
            'TreatMissingData': 'notBreaching'
        },
        {
            'AlarmName': 'galerly-lambda-duration',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 2,
            'MetricName': 'Duration',
            'Namespace': 'AWS/Lambda',
            'Period': 300,
            'Statistic': 'Average',
            'Threshold': 10000.0,  # 10 seconds
            'ActionsEnabled': True,
            'AlarmDescription': 'Alert when Lambda duration is high',
            'Dimensions': [
                {
                    'Name': 'FunctionName',
                    'Value': LAMBDA_FUNCTION_NAME
                }
            ],
            'TreatMissingData': 'notBreaching'
        },
        {
            'AlarmName': 'galerly-api-5xx',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 1,
            'MetricName': '5XXError',
            'Namespace': 'AWS/ApiGateway',
            'Period': 300,
            'Statistic': 'Sum',
            'Threshold': 10.0,
            'ActionsEnabled': True,
            'AlarmDescription': 'Alert on API Gateway 5xx errors',
            'Dimensions': [
                {
                    'Name': 'ApiName',
                    'Value': API_GATEWAY_NAME
                }
            ],
            'TreatMissingData': 'notBreaching'
        },
        {
            'AlarmName': 'galerly-dynamodb-throttles',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 1,
            'MetricName': 'ThrottledRequests',
            'Namespace': 'AWS/DynamoDB',
            'Period': 300,
            'Statistic': 'Sum',
            'Threshold': 5.0,
            'ActionsEnabled': True,
            'AlarmDescription': 'Alert on DynamoDB throttling',
            'Dimensions': [
                {
                    'Name': 'TableName',
                    'Value': 'client_selections'
                }
            ],
            'TreatMissingData': 'notBreaching'
        }
    ]
    
    created_alarms = []
    
    for alarm in alarms:
        try:
            cloudwatch.put_metric_alarm(**alarm)
            print(f"✓ Created alarm: {alarm['AlarmName']}")
            created_alarms.append(alarm['AlarmName'])
        except Exception as e:
            print(f"✗ Error creating alarm {alarm['AlarmName']}: {str(e)}")
    
    return created_alarms


def main():
    """
    Main setup function
    """
    print("\n" + "="*60)
    print("CloudWatch Monitoring Setup")
    print("="*60 + "\n")
    
    # Create dashboard
    print("Creating CloudWatch dashboard...")
    dashboard = create_dashboard()
    
    print("\nCreating CloudWatch alarms...")
    alarms = create_alarms()
    
    print("\n" + "="*60)
    print("Setup Complete")
    print("="*60)
    print(f"\nDashboard: {DASHBOARD_NAME}")
    print(f"Alarms created: {len(alarms)}")
    print("\nNext steps:")
    print("1. Configure SNS topic for alarm notifications")
    print("2. Add SNS topic ARN to alarms")
    print("3. Subscribe email/SMS to SNS topic")
    print("4. Test alarms by triggering thresholds")
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()

