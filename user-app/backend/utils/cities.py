"""
City search utilities using DynamoDB with prefix GSIs for ultra-fast queries
"""
import boto3
import os
from .response import create_response

# Configuration
AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL')
IS_LOCAL = AWS_ENDPOINT_URL and ('localhost' in AWS_ENDPOINT_URL or 'localstack' in AWS_ENDPOINT_URL)
AWS_REGION = os.getenv('AWS_REGION')

# DynamoDB setup
if IS_LOCAL:
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    TABLE_NAME = os.getenv('DYNAMODB_TABLE_CITIES')
    print(f"Cities: Using LocalStack at {AWS_ENDPOINT_URL}")
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    TABLE_NAME = os.getenv('DYNAMODB_TABLE_CITIES')
    print(f"Cities: Using AWS DynamoDB")

cities_table = dynamodb.Table(TABLE_NAME)
print(f"Cities table: {TABLE_NAME}")


def search_cities(query):
    """
    Ultra-fast city search using prefix GSIs.
    
    Strategy:
    - 1-2 chars: Use prefix1 or prefix2 index
    - 3+ chars: Use prefix3 index for best performance
    
    All results sorted by population (largest first)
    Returns top 10 matches
    """
    try:
        if not query or len(query) < 1:
            return create_response(400, {'error': 'Query required'})
        
        query_lower = query.lower().strip()
        query_len = len(query_lower)
        
        print(f"Searching cities: '{query}' (length: {query_len})")
        
        # Choose the appropriate index based on query length
        if query_len == 1:
            index_name = 'prefix1-population-index'
            prefix_key = 'prefix1'
            prefix_value = query_lower[0]
        elif query_len == 2:
            index_name = 'prefix2-population-index'
            prefix_key = 'prefix2'
            prefix_value = query_lower[:2]
        else:  # 3+ characters
            index_name = 'prefix3-population-index'
            prefix_key = 'prefix3'
            prefix_value = query_lower[:3]
        
        print(f"Using index: {index_name} with prefix: '{prefix_value}'")
        
        # Query the GSI (sorted by population DESC automatically)
        response = cities_table.query(IndexName=index_name,KeyConditionExpression=f'{prefix_key} = :prefix',ExpressionAttributeValues={':prefix': prefix_value},ScanIndexForward=False,Limit=100)
                
        items = response.get('Items', [])
        print(f"Retrieved {len(items)} cities from index")
                
        # Filter to exact query match (for queries longer than the prefix)
        matches = []
        for item in items:
            city_lower = item.get('city_lower', '')
            
            # Check if city starts with the full query
            if city_lower.startswith(query_lower):
                matches.append({
                    'city_id': item.get('city_id'),
                    'city': item.get('city'),
                    'city_ascii': item.get('city_ascii'),
                    'country': item.get('country'),
                    'admin_name': item.get('admin_name', ''),
                    'display_name': item.get('display_name'),
                    'population': int(item.get('population', 0)),
                    'lat': float(item.get('lat', 0)),
                    'lng': float(item.get('lng', 0))
                })
        
        # Already sorted by population DESC from GSI, take top 10
        top_matches = matches[:10]
        
        print(f"Found {len(matches)} matches, returning top {len(top_matches)}")
        
        # Debug: Print first match to verify structure
        if top_matches:
            print(f"First match structure: {top_matches[0]}")
        
        return create_response(200, {
            'cities': top_matches,
            'total': len(matches),
            'query': query
        })
        
    except Exception as e:
        print(f"Error searching cities: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {
            'error': 'City search failed',
            'message': str(e)
            })
