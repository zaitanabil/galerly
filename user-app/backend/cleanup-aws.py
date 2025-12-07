"""
AWS Resource Cleanup Script
Removes all Galerly resources from AWS account for fresh start

CAUTION: This is a destructive operation. All data will be permanently deleted.
"""
import boto3
import os
import sys
from datetime import datetime


class AWSResourceCleanup:
    """
    Handles safe cleanup of all Galerly AWS resources
    """
    
    def __init__(self):
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize AWS clients
        self.dynamodb = boto3.client('dynamodb', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        self.cloudfront = boto3.client('cloudfront', region_name='us-east-1')
        self.apigateway = boto3.client('apigateway', region_name=self.region)
        self.iam = boto3.client('iam', region_name=self.region)
        
        # Resource name patterns
        self.resource_prefix = os.environ.get('RESOURCE_PREFIX', 'galerly')
        
        # Track deletions
        self.deleted = {
            'dynamodb_tables': [],
            'lambda_functions': [],
            's3_buckets': [],
            'cloudfront_distributions': [],
            'api_gateways': [],
            'iam_roles': []
        }
        
        self.failed = {
            'dynamodb_tables': [],
            'lambda_functions': [],
            's3_buckets': [],
            'cloudfront_distributions': [],
            'api_gateways': [],
            'iam_roles': []
        }
    
    
    def list_all_resources(self):
        """
        List all Galerly resources before deletion
        Returns dictionary with resource counts
        """
        print("\n" + "=" * 60)
        print("SCANNING AWS ACCOUNT FOR GALERLY RESOURCES")
        print("=" * 60 + "\n")
        
        resources = {}
        
        # List DynamoDB tables
        print("Scanning DynamoDB tables...")
        resources['dynamodb_tables'] = self._list_dynamodb_tables()
        print(f"  Found: {len(resources['dynamodb_tables'])} tables")
        
        # List Lambda functions
        print("Scanning Lambda functions...")
        resources['lambda_functions'] = self._list_lambda_functions()
        print(f"  Found: {len(resources['lambda_functions'])} functions")
        
        # List S3 buckets
        print("Scanning S3 buckets...")
        resources['s3_buckets'] = self._list_s3_buckets()
        print(f"  Found: {len(resources['s3_buckets'])} buckets")
        
        # List CloudFront distributions
        print("Scanning CloudFront distributions...")
        resources['cloudfront_distributions'] = self._list_cloudfront_distributions()
        print(f"  Found: {len(resources['cloudfront_distributions'])} distributions")
        
        # List API Gateways
        print("Scanning API Gateway APIs...")
        resources['api_gateways'] = self._list_api_gateways()
        print(f"  Found: {len(resources['api_gateways'])} APIs")
        
        # List IAM roles
        print("Scanning IAM roles...")
        resources['iam_roles'] = self._list_iam_roles()
        print(f"  Found: {len(resources['iam_roles'])} roles")
        
        return resources
    
    
    def _list_dynamodb_tables(self):
        """List all DynamoDB tables matching prefix"""
        try:
            tables = []
            paginator = self.dynamodb.get_paginator('list_tables')
            
            for page in paginator.paginate():
                for table_name in page['TableNames']:
                    if table_name.startswith(self.resource_prefix):
                        tables.append(table_name)
            
            return tables
        except Exception as e:
            print(f"  Error listing DynamoDB tables: {str(e)}")
            return []
    
    
    def _list_lambda_functions(self):
        """List all Lambda functions matching prefix"""
        try:
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    if function['FunctionName'].startswith(self.resource_prefix):
                        functions.append(function['FunctionName'])
            
            return functions
        except Exception as e:
            print(f"  Error listing Lambda functions: {str(e)}")
            return []
    
    
    def _list_s3_buckets(self):
        """List all S3 buckets matching prefix"""
        try:
            buckets = []
            response = self.s3.list_buckets()
            
            for bucket in response['Buckets']:
                if bucket['Name'].startswith(self.resource_prefix):
                    buckets.append(bucket['Name'])
            
            return buckets
        except Exception as e:
            print(f"  Error listing S3 buckets: {str(e)}")
            return []
    
    
    def _list_cloudfront_distributions(self):
        """List all CloudFront distributions matching prefix"""
        try:
            distributions = []
            paginator = self.cloudfront.get_paginator('list_distributions')
            
            for page in paginator.paginate():
                if 'DistributionList' in page and 'Items' in page['DistributionList']:
                    for dist in page['DistributionList']['Items']:
                        # Check if comment or domain contains prefix
                        comment = dist.get('Comment', '')
                        if self.resource_prefix in comment.lower():
                            distributions.append({
                                'id': dist['Id'],
                                'domain': dist['DomainName'],
                                'enabled': dist['Enabled']
                            })
            
            return distributions
        except Exception as e:
            print(f"  Error listing CloudFront distributions: {str(e)}")
            return []
    
    
    def _list_api_gateways(self):
        """List all API Gateway APIs matching prefix"""
        try:
            apis = []
            paginator = self.apigateway.get_paginator('get_rest_apis')
            
            for page in paginator.paginate():
                for api in page['items']:
                    if api['name'].startswith(self.resource_prefix):
                        apis.append({
                            'id': api['id'],
                            'name': api['name']
                        })
            
            return apis
        except Exception as e:
            print(f"  Error listing API Gateways: {str(e)}")
            return []
    
    
    def _list_iam_roles(self):
        """List all IAM roles matching prefix"""
        try:
            roles = []
            paginator = self.iam.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    if role['RoleName'].startswith(self.resource_prefix):
                        roles.append(role['RoleName'])
            
            return roles
        except Exception as e:
            print(f"  Error listing IAM roles: {str(e)}")
            return []
    
    
    def delete_all_resources(self):
        """
        Delete all Galerly resources in correct order
        Handles dependencies automatically
        """
        print("\n" + "=" * 60)
        print("DELETING AWS RESOURCES")
        print("=" * 60 + "\n")
        
        # Order matters: delete dependent resources first
        
        # Step 1: Disable and delete CloudFront distributions
        print("\n[1/6] CloudFront Distributions")
        print("-" * 60)
        resources = self._list_cloudfront_distributions()
        for dist in resources:
            self._delete_cloudfront_distribution(dist)
        
        # Step 2: Delete Lambda functions
        print("\n[2/6] Lambda Functions")
        print("-" * 60)
        resources = self._list_lambda_functions()
        for function_name in resources:
            self._delete_lambda_function(function_name)
        
        # Step 3: Delete API Gateway APIs
        print("\n[3/6] API Gateway APIs")
        print("-" * 60)
        resources = self._list_api_gateways()
        for api in resources:
            self._delete_api_gateway(api)
        
        # Step 4: Empty and delete S3 buckets
        print("\n[4/6] S3 Buckets")
        print("-" * 60)
        resources = self._list_s3_buckets()
        for bucket_name in resources:
            self._delete_s3_bucket(bucket_name)
        
        # Step 5: Delete DynamoDB tables
        print("\n[5/6] DynamoDB Tables")
        print("-" * 60)
        resources = self._list_dynamodb_tables()
        for table_name in resources:
            self._delete_dynamodb_table(table_name)
        
        # Step 6: Delete IAM roles
        print("\n[6/6] IAM Roles")
        print("-" * 60)
        resources = self._list_iam_roles()
        for role_name in resources:
            self._delete_iam_role(role_name)
    
    
    def _delete_cloudfront_distribution(self, dist):
        """Delete CloudFront distribution (disable first if enabled)"""
        try:
            dist_id = dist['id']
            print(f"  Processing: {dist['domain']} ({dist_id})")
            
            # Get current config
            response = self.cloudfront.get_distribution_config(Id=dist_id)
            config = response['DistributionConfig']
            etag = response['ETag']
            
            # Disable if enabled
            if dist['enabled']:
                print(f"    Disabling distribution...")
                config['Enabled'] = False
                self.cloudfront.update_distribution(
                    Id=dist_id,
                    DistributionConfig=config,
                    IfMatch=etag
                )
                print(f"    Distribution disabled (must wait for deployment before deletion)")
                print(f"    Run this script again later to complete deletion")
                return
            
            # Delete disabled distribution
            self.cloudfront.delete_distribution(Id=dist_id, IfMatch=etag)
            self.deleted['cloudfront_distributions'].append(dist_id)
            print(f"    Deleted: {dist_id}")
            
        except Exception as e:
            print(f"    Failed: {str(e)}")
            self.failed['cloudfront_distributions'].append(dist['id'])
    
    
    def _delete_lambda_function(self, function_name):
        """Delete Lambda function (handles Lambda@Edge replicated functions)"""
        try:
            print(f"  Deleting: {function_name}")
            
            # Check if this is a Lambda@Edge function
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
                
                # Lambda@Edge functions cannot be deleted while replicated
                # They must be disassociated from CloudFront first
                if ':lambda-edge:' in function_arn or 'replicated' in str(response).lower():
                    print(f"    Lambda@Edge function detected - cannot delete while replicated")
                    print(f"    Will be auto-deleted after CloudFront disassociation (24-48 hours)")
                    self.deleted['lambda_functions'].append(function_name)
                    return
            except:
                pass
            
            # Regular Lambda function - delete normally
            self.lambda_client.delete_function(FunctionName=function_name)
            self.deleted['lambda_functions'].append(function_name)
            print(f"    Deleted")
        except Exception as e:
            error_msg = str(e)
            if 'replicated function' in error_msg.lower():
                print(f"    Lambda@Edge replicated function - will auto-delete after 24-48 hours")
                self.deleted['lambda_functions'].append(function_name)
            else:
                print(f"    Failed: {error_msg}")
                self.failed['lambda_functions'].append(function_name)
    
    
    def _delete_api_gateway(self, api):
        """Delete API Gateway API (removes custom domain mappings first)"""
        try:
            api_id = api['id']
            api_name = api['name']
            print(f"  Deleting: {api_name} ({api_id})")
            
            # Remove custom domain base path mappings first
            try:
                print(f"    Checking for custom domain mappings...")
                domains_response = self.apigateway.get_domain_names()
                
                for domain in domains_response.get('items', []):
                    domain_name = domain['domainName']
                    try:
                        # Get base path mappings for this domain
                        mappings = self.apigateway.get_base_path_mappings(domainName=domain_name)
                        
                        for mapping in mappings.get('items', []):
                            if mapping.get('restApiId') == api_id:
                                base_path = mapping.get('basePath', '(none)')
                                print(f"    Removing base path mapping: {domain_name}/{base_path}")
                                self.apigateway.delete_base_path_mapping(
                                    domainName=domain_name,
                                    basePath=base_path
                                )
                    except:
                        pass
            except Exception as domain_error:
                print(f"    Warning: Could not check domains: {str(domain_error)}")
            
            # Now delete the API
            self.apigateway.delete_rest_api(restApiId=api_id)
            self.deleted['api_gateways'].append(api_id)
            print(f"    Deleted")
        except Exception as e:
            error_msg = str(e)
            if 'base path mappings' in error_msg.lower():
                print(f"    Failed: Custom domain mappings still exist")
                print(f"    Manual cleanup required for domain: {error_msg.split('domains: ')[-1] if 'domains:' in error_msg else 'unknown'}")
            else:
                print(f"    Failed: {error_msg}")
            self.failed['api_gateways'].append(api['id'])
    
    
    def _delete_s3_bucket(self, bucket_name):
        """Empty and delete S3 bucket"""
        try:
            print(f"  Processing: {bucket_name}")
            
            # Empty bucket first
            print(f"    Emptying bucket...")
            paginator = self.s3.get_paginator('list_object_versions')
            
            delete_count = 0
            for page in paginator.paginate(Bucket=bucket_name):
                objects_to_delete = []
                
                # Add versions
                if 'Versions' in page:
                    for version in page['Versions']:
                        objects_to_delete.append({
                            'Key': version['Key'],
                            'VersionId': version['VersionId']
                        })
                
                # Add delete markers
                if 'DeleteMarkers' in page:
                    for marker in page['DeleteMarkers']:
                        objects_to_delete.append({
                            'Key': marker['Key'],
                            'VersionId': marker['VersionId']
                        })
                
                # Delete objects
                if objects_to_delete:
                    self.s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    delete_count += len(objects_to_delete)
            
            if delete_count > 0:
                print(f"    Deleted {delete_count} objects")
            
            # Delete bucket
            self.s3.delete_bucket(Bucket=bucket_name)
            self.deleted['s3_buckets'].append(bucket_name)
            print(f"    Deleted bucket")
            
        except Exception as e:
            print(f"    Failed: {str(e)}")
            self.failed['s3_buckets'].append(bucket_name)
    
    
    def _delete_dynamodb_table(self, table_name):
        """Delete DynamoDB table"""
        try:
            print(f"  Deleting: {table_name}")
            self.dynamodb.delete_table(TableName=table_name)
            self.deleted['dynamodb_tables'].append(table_name)
            print(f"    Deleted")
        except Exception as e:
            print(f"    Failed: {str(e)}")
            self.failed['dynamodb_tables'].append(table_name)
    
    
    def _delete_iam_role(self, role_name):
        """Delete IAM role (detach policies first)"""
        try:
            print(f"  Processing: {role_name}")
            
            # Detach managed policies
            response = self.iam.list_attached_role_policies(RoleName=role_name)
            for policy in response['AttachedPolicies']:
                self.iam.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Delete inline policies
            response = self.iam.list_role_policies(RoleName=role_name)
            for policy_name in response['PolicyNames']:
                self.iam.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
            
            # Delete role
            self.iam.delete_role(RoleName=role_name)
            self.deleted['iam_roles'].append(role_name)
            print(f"    Deleted")
            
        except Exception as e:
            print(f"    Failed: {str(e)}")
            self.failed['iam_roles'].append(role_name)
    
    
    def print_summary(self):
        """Print deletion summary"""
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY")
        print("=" * 60 + "\n")
        
        # Count totals
        total_deleted = sum(len(v) for v in self.deleted.values())
        total_failed = sum(len(v) for v in self.failed.values())
        
        print(f"Successfully deleted: {total_deleted} resources")
        print(f"Failed to delete: {total_failed} resources\n")
        
        # Detail by resource type
        for resource_type, items in self.deleted.items():
            if items:
                print(f"  {resource_type.replace('_', ' ').title()}: {len(items)}")
        
        if total_failed > 0:
            print("\nFailed deletions:")
            for resource_type, items in self.failed.items():
                if items:
                    print(f"  {resource_type.replace('_', ' ').title()}:")
                    for item in items:
                        print(f"    - {item}")


def main():
    """Main cleanup execution"""
    print("\n" + "=" * 60)
    print("AWS RESOURCE CLEANUP - GALERLY")
    print("=" * 60)
    print("\nWARNING: This will permanently delete ALL Galerly resources")
    print("         from your AWS account. This action CANNOT be undone.")
    print("\nAffected resources:")
    print("  - DynamoDB tables")
    print("  - Lambda functions")
    print("  - S3 buckets and all contents")
    print("  - CloudFront distributions")
    print("  - API Gateway APIs")
    print("  - IAM roles and policies")
    
    # Require confirmation
    print("\n" + "-" * 60)
    response = input("\nType 'DELETE ALL' to confirm: ")
    
    if response != "DELETE ALL":
        print("\nCleanup cancelled.")
        sys.exit(0)
    
    # Execute cleanup
    cleanup = AWSResourceCleanup()
    
    # List resources
    resources = cleanup.list_all_resources()
    total_resources = sum(len(v) for v in resources.values())
    
    if total_resources == 0:
        print("\nNo Galerly resources found. Account is clean.")
        sys.exit(0)
    
    # Final confirmation
    print(f"\nTotal resources to delete: {total_resources}")
    response = input("\nProceed with deletion? (yes/no): ")
    
    if response.lower() != "yes":
        print("\nCleanup cancelled.")
        sys.exit(0)
    
    # Delete resources
    cleanup.delete_all_resources()
    
    # Print summary
    cleanup.print_summary()
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print("\nYour AWS account has been reset.")
    print("You can now run setup scripts to start fresh.\n")


if __name__ == '__main__':
    main()

