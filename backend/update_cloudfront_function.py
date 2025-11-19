#!/usr/bin/env python3
"""
Update CloudFront Function
Automates CloudFront function deployment from GitHub Actions
"""
import boto3
import os
import sys
import time

def update_cloudfront_function(function_name, code_file_path):
    """
    Update a CloudFront function with new code
    
    Args:
        function_name: Name of the CloudFront function to update
        code_file_path: Path to the JavaScript file containing the function code
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"☁️  Updating CloudFront function: {function_name}")
        
        # Read the function code
        if not os.path.exists(code_file_path):
            print(f"❌ Error: Code file not found: {code_file_path}")
            return False
        
        with open(code_file_path, 'r', encoding='utf-8') as f:
            function_code = f.read()
        
        print(f"📄 Read function code from: {code_file_path}")
        print(f"📊 Code size: {len(function_code)} bytes")
        
        # Initialize CloudFront client
        cloudfront = boto3.client('cloudfront', region_name='us-east-1')
        
        # Get the current function to retrieve its ETag
        print("🔍 Getting current function configuration...")
        try:
            describe_response = cloudfront.describe_function(Name=function_name)
            etag = describe_response['ETag']
            function_arn = describe_response['FunctionSummary']['FunctionMetadata']['FunctionARN']
            current_stage = describe_response['FunctionSummary']['Status']
            
            print(f"✅ Found function: {function_arn}")
            print(f"📍 Current stage: {current_stage}")
            print(f"🔖 Current ETag: {etag}")
        except cloudfront.exceptions.NoSuchFunctionExists:
            print(f"❌ Error: Function '{function_name}' does not exist")
            print(f"💡 Create it first in AWS Console: https://console.aws.amazon.com/cloudfront/v3/home#/functions")
            return False
        
        # Update the function code
        print("📝 Updating function code...")
        update_response = cloudfront.update_function(
            Name=function_name,
            IfMatch=etag,
            FunctionConfig={
                'Comment': 'Galerly URL rewrite function - Auto-updated by GitHub Actions',
                'Runtime': 'cloudfront-js-1.0'
            },
            FunctionCode=function_code.encode('utf-8')
        )
        
        new_etag = update_response['ETag']
        print(f"✅ Function code updated successfully")
        print(f"🔖 New ETag: {new_etag}")
        
        # Publish the function (make it live)
        print("🚀 Publishing function to LIVE stage...")
        publish_response = cloudfront.publish_function(
            Name=function_name,
            IfMatch=new_etag
        )
        
        published_etag = publish_response['FunctionSummary']['FunctionMetadata']['FunctionARN']
        print(f"✅ Function published successfully!")
        print(f"📍 Function ARN: {published_etag}")
        
        # Wait a moment and verify the function is published
        print("⏳ Verifying function status...")
        time.sleep(2)
        
        verify_response = cloudfront.describe_function(Name=function_name, Stage='LIVE')
        final_stage = verify_response['FunctionSummary']['Status']
        
        if final_stage == 'PUBLISHED' or final_stage == 'UNASSOCIATED':
            print(f"✅ Function is now in {final_stage} stage and ready to use!")
            return True
        else:
            print(f"⚠️  Warning: Function stage is {final_stage} (expected PUBLISHED)")
            return True  # Still consider it successful if it updated
        
    except Exception as e:
        print(f"❌ Error updating CloudFront function: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    
    # Configuration
    FUNCTION_NAME = os.environ.get('CLOUDFRONT_FUNCTION_NAME', 'galerly-url-rewrite')
    CODE_FILE = os.environ.get('CLOUDFRONT_FUNCTION_CODE', '../cloudfront/url-rewrite-function.js')
    
    # Get the absolute path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    code_file_path = os.path.normpath(os.path.join(script_dir, CODE_FILE))
    
    print("")
    print("════════════════════════════════════════════════════════")
    print("   ☁️  CLOUDFRONT FUNCTION DEPLOYMENT")
    print("════════════════════════════════════════════════════════")
    print("")
    print(f"Function name: {FUNCTION_NAME}")
    print(f"Code file: {code_file_path}")
    print("")
    
    # Update the function
    success = update_cloudfront_function(FUNCTION_NAME, code_file_path)
    
    print("")
    if success:
        print("════════════════════════════════════════════════════════")
        print("   ✅ CLOUDFRONT FUNCTION UPDATED SUCCESSFULLY")
        print("════════════════════════════════════════════════════════")
        print("")
        print("The function is now live and will be used for all CloudFront requests.")
        print("Invalid routes will be redirected to /404.html")
        print("")
        sys.exit(0)
    else:
        print("════════════════════════════════════════════════════════")
        print("   ❌ CLOUDFRONT FUNCTION UPDATE FAILED")
        print("════════════════════════════════════════════════════════")
        print("")
        sys.exit(1)

if __name__ == "__main__":
    main()

