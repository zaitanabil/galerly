"""
Database Query Optimization Guide
Replaces inefficient scan operations with GSI queries
"""

# PROBLEM: Many handlers use scan() which is slow and expensive
# SOLUTION: Use Query with Global Secondary Indexes (GSI)

"""
Required GSI Configuration for DynamoDB Tables:

1. galleries_table:
   - Primary Key: user_id (HASH), id (RANGE)
   - GSI: GalleryIdIndex
     * Key: id (HASH)
     * Projection: ALL
   
2. photos_table:
   - Primary Key: id (HASH)
   - GSI: GalleryIdIndex
     * Key: gallery_id (HASH), created_at (RANGE)
     * Projection: ALL
   - GSI: UserIdIndex
     * Key: user_id (HASH), created_at (RANGE)
     * Projection: ALL

3. users_table:
   - Primary Key: email (HASH)
   - GSI: UserIdIndex
     * Key: id (HASH)
     * Projection: ALL
   - GSI: EmailIndex (if using id as primary)
     * Key: email (HASH)
     * Projection: ALL

4. analytics_table:
   - Primary Key: id (HASH)
   - GSI: GalleryIdIndex
     * Key: gallery_id (HASH), timestamp (RANGE)
     * Projection: ALL
   - GSI: UserIdIndex
     * Key: user_id (HASH), timestamp (RANGE)
     * Projection: ALL

5. client_favorites_table:
   - Primary Key: client_email (HASH), photo_id (RANGE)
   - GSI: PhotoIdIndex
     * Key: photo_id (HASH)
     * Projection: ALL
   - GSI: GalleryIdIndex
     * Key: gallery_id (HASH), created_at (RANGE)
     * Projection: ALL
"""

# BEFORE (SLOW - uses scan):
def get_gallery_by_id_SLOW(gallery_id):
    """
    ❌ BAD: Scans entire table
    Cost: High read capacity, slow with large datasets
    """
    from utils.config import galleries_table
    response = galleries_table.scan(
        FilterExpression='id = :gid',
        ExpressionAttributeValues={':gid': gallery_id}
    )
    return response.get('Items', [])[0] if response.get('Items') else None


# AFTER (FAST - uses GSI):
def get_gallery_by_id_FAST(gallery_id):
    """
    ✅ GOOD: Uses GalleryIdIndex GSI
    Cost: Minimal read capacity, fast at any scale
    """
    from utils.config import galleries_table
    from boto3.dynamodb.conditions import Key
    
    response = galleries_table.query(
        IndexName='GalleryIdIndex',
        KeyConditionExpression=Key('id').eq(gallery_id),
        Limit=1
    )
    return response.get('Items', [])[0] if response.get('Items') else None


# OPTIMIZATION 1: Get gallery owner without scan
def get_gallery_owner_optimized(gallery_id):
    """
    Find gallery owner using GSI instead of scan
    Used in analytics, bulk download, client access
    """
    from utils.config import galleries_table
    from boto3.dynamodb.conditions import Key
    
    try:
        response = galleries_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('id').eq(gallery_id),
            ProjectionExpression='user_id, id, #name',
            ExpressionAttributeNames={'#name': 'name'},
            Limit=1
        )
        
        if response.get('Items'):
            return response['Items'][0]
        return None
    except Exception as e:
        print(f"Error getting gallery owner: {str(e)}")
        return None


# OPTIMIZATION 2: Get user by ID without scan
def get_user_by_id_optimized(user_id):
    """
    Find user by ID using UserIdIndex GSI
    Used throughout the application
    """
    from utils.config import users_table
    from boto3.dynamodb.conditions import Key
    
    try:
        response = users_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('id').eq(user_id),
            Limit=1
        )
        
        if response.get('Items'):
            return response['Items'][0]
        return None
    except Exception as e:
        print(f"Error getting user by ID: {str(e)}")
        return None


# OPTIMIZATION 3: Get photos by gallery efficiently
def get_gallery_photos_optimized(gallery_id, limit=None):
    """
    Get all photos in a gallery using GalleryIdIndex
    Sorted by created_at (newest first)
    """
    from utils.config import photos_table
    from boto3.dynamodb.conditions import Key
    
    try:
        query_params = {
            'IndexName': 'GalleryIdIndex',
            'KeyConditionExpression': Key('gallery_id').eq(gallery_id),
            'ScanIndexForward': False  # Descending order (newest first)
        }
        
        if limit:
            query_params['Limit'] = limit
        
        response = photos_table.query(**query_params)
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting gallery photos: {str(e)}")
        return []


# OPTIMIZATION 4: Get analytics by gallery efficiently
def get_gallery_analytics_optimized(gallery_id, start_date, end_date):
    """
    Get analytics events for gallery using GalleryIdIndex
    With time range filtering
    """
    from utils.config import analytics_table
    from boto3.dynamodb.conditions import Key
    
    try:
        response = analytics_table.query(
            IndexName='GalleryIdIndex',
            KeyConditionExpression=Key('gallery_id').eq(gallery_id) & 
                                   Key('timestamp').between(start_date, end_date)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting gallery analytics: {str(e)}")
        return []


# USAGE EXAMPLES - Replace these patterns in handlers:

# Pattern 1: In analytics_handler.py, realtime_viewers_handler.py
# BEFORE:
"""
gallery_response = galleries_table.scan(
    FilterExpression='id = :gid',
    ExpressionAttributeValues={':gid': gallery_id}
)
"""
# AFTER:
"""
gallery = get_gallery_by_id_optimized(gallery_id)
if gallery:
    owner_user_id = gallery['user_id']
"""

# Pattern 2: In client_favorites_handler.py
# BEFORE:
"""
photographer_response = users_table.scan(
    FilterExpression='id = :uid',
    ExpressionAttributeValues={':uid': photographer_id},
    Limit=1
)
"""
# AFTER:
"""
photographer = get_user_by_id_optimized(photographer_id)
if photographer:
    features, _, _ = get_user_features(photographer)
"""

# Pattern 3: In subscription_handler.py
# BEFORE:
"""
resp = users_table.query(
    IndexName='UserIdIndex', 
    KeyConditionExpression=Key('id').eq(user_id)
)
"""
# AFTER (already optimized, but ensure GSI exists)
"""
# This is already correct - keep using UserIdIndex
"""


# Migration script to update all handlers:
def migrate_handlers_to_use_gsi():
    r"""
    Steps to migrate existing handlers:
    
    1. Identify all scan() operations:
       grep -r "\.scan\(" handlers/ --include="*.py"
    
    2. For each scan, determine what it's looking for:
       - Gallery by ID -> use get_gallery_by_id_optimized()
       - User by ID -> use get_user_by_id_optimized()
       - Photos by gallery -> use get_gallery_photos_optimized()
    
    3. Replace with optimized query
    
    4. Test thoroughly to ensure behavior unchanged
    
    5. Monitor CloudWatch metrics:
       - ConsumedReadCapacityUnits should decrease significantly
       - Query latency should improve
    """
    pass


# Performance comparison:
"""
SCENARIO: Find gallery with specific ID in table with 100,000 galleries

Scan method:
- Reads: 100,000 items scanned
- Time: ~10-30 seconds
- Cost: ~$0.50 per query (assuming 1KB items)
- Scales: Linearly worse with more data

Query with GSI:
- Reads: 1 item read
- Time: ~50-100ms
- Cost: ~$0.000005 per query
- Scales: Constant time regardless of table size

RESULT: 100,000x more efficient!
"""
