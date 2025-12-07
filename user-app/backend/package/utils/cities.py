"""
City search utilities using DynamoDB with GSI for ultra-fast queries
"""
import boto3
from .response import create_response

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
cities_table = dynamodb.Table('galerly-cities')

# In-memory cache for cities (loaded once on cold start)
CITIES_CACHE = []

def search_cities_with_gsi(query):
    """
    Ultra-fast city search using DynamoDB GSI (no memory loading needed).
    
    Uses the search_key-index GSI for instant prefix searches.
    Falls back to in-memory cache for longer/complex queries.
    """
    try:
        if not query or len(query) < 2:
            return create_response(400, {'error': 'Query must be at least 2 characters'})
        
        query_lower = query.lower()
        print(f"🔍 Searching for cities starting with: {query}")
        
        # For 3+ char queries, use the GSI for instant results
        if len(query_lower) >= 3:
            search_prefix = query_lower[:3]
            
            try:
                # Query the GSI (ultra-fast, no memory loading)
                response = cities_table.query(
                    IndexName='search_key-index',
                    KeyConditionExpression='search_key = :prefix',
                    ExpressionAttributeValues={
                        ':prefix': search_prefix
                    },
                    ScanIndexForward=False,  # Sort by population DESC
                    Limit=100  # Get top 100 from this prefix
                )
                
                items = response.get('Items', [])
                
                # Filter results to match full query (not just 3-char prefix)
                matches = []
                for item in items:
                    city_lower = item.get('city_lower', '')
                    if city_lower.startswith(query_lower):
                        matches.append({
                            'city_ascii': item.get('city_ascii', ''),
                            'country': item.get('country', ''),
                            'display': f"{item.get('city_ascii', '')}, {item.get('country', '')}",
                            'population': int(item.get('population', 0)),
                            'lat': float(item.get('lat', 0)),
                            'lng': float(item.get('lng', 0))
                        })
                
                # Already sorted by population, take top 10
                top_matches = matches[:10]
                
                print(f"✅ GSI query found {len(matches)} matches, returning top {len(top_matches)}")
                
                return create_response(200, {
                    'cities': top_matches,
                    'total': len(matches)
                })
                
            except Exception as gsi_error:
                print(f"⚠️  GSI query failed, falling back to cache: {gsi_error}")
                # Fall through to cache-based search
        
        # For short queries (< 3 chars) or GSI fallback, use in-memory cache
        return search_cities_cached(query_lower)
        
    except Exception as e:
        print(f"❌ Error searching cities: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'City search failed'})

def load_cities_from_dynamodb():
    """
    Load all cities from DynamoDB into memory (once on cold start).
    This makes searches instant instead of scanning DynamoDB on every request.
    """
    global CITIES_CACHE
    
    if CITIES_CACHE:
        print(f"✅ Using cached cities: {len(CITIES_CACHE)} in memory")
        return CITIES_CACHE
    
    try:
        print("📥 Loading cities from DynamoDB into memory...")
        
        # Scan entire table with parallel scan for faster loading (done only once on cold start)
        # Using 4 parallel segments for 4x faster initial load
        items = []
        segments = 4
        
        # Parallel scan for faster loading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def scan_segment(segment):
            """Scan a single segment of the table"""
            segment_items = []
            response = cities_table.scan(
                Segment=segment,
                TotalSegments=segments
            )
            segment_items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                response = cities_table.scan(
                    Segment=segment,
                    TotalSegments=segments,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                segment_items.extend(response.get('Items', []))
            
            return segment_items
        
        # Execute parallel scans
        with ThreadPoolExecutor(max_workers=segments) as executor:
            futures = [executor.submit(scan_segment, i) for i in range(segments)]
            for future in as_completed(futures):
                items.extend(future.result())
        
        # Store in cache
        cache = []
        for item in items:
            cache.append({
                'city': item.get('city', ''),
                'city_ascii': item.get('city_ascii', ''),
                'country': item.get('country', ''),
                'lat': float(item.get('lat', 0)),
                'lng': float(item.get('lng', 0)),
                'population': int(item.get('population', 0))
            })
        
        CITIES_CACHE = cache  # Assign to global
        print(f"✅ Loaded {len(CITIES_CACHE)} cities into Lambda memory")
        return CITIES_CACHE
    
    except Exception as e:
        print(f"❌ Error loading cities from DynamoDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def search_cities_cached(query_lower):
    """
    Search cities using in-memory cache (fallback for short queries or GSI failures).
    
    Logic:
    - User can search by either 'city' (e.g., "Béni") or 'city_ascii' (e.g., "Beni")
    - Returns matches that START with the query in either field
    - Always displays results as "city_ascii, country"
    - Sorted by population (largest first)
    - Returns top 10 results
    
    Performance: Instant! Searches in-memory cache (loaded once on cold start)
    """
    # Load cities into memory (only happens once on cold start)
    cities = load_cities_from_dynamodb()
    
    if not cities:
        return create_response(500, {'error': 'Cities database not loaded'})
    
    print(f"🔍 Cache search for: {query_lower}")
    
    # Fast in-memory search
    matches = []
    for city in cities:
        city_name = city['city'].lower()
        city_ascii = city['city_ascii'].lower()
        
        # Check if query matches the start of either field
        if city_name.startswith(query_lower) or city_ascii.startswith(query_lower):
            matches.append({
                'city_ascii': city['city_ascii'],
                'country': city['country'],
                'display': f"{city['city_ascii']}, {city['country']}",  # Always use city_ascii
                'population': city['population'],
                'lat': city['lat'],
                'lng': city['lng']
            })
    
    # Sort by population (largest first) and take top 10
    matches.sort(key=lambda x: x['population'], reverse=True)
    top_matches = matches[:10]
    
    print(f"✅ Found {len(matches)} matches in {len(cities)} cities, returning top {len(top_matches)}")
    
    return create_response(200, {
        'cities': top_matches,
        'total': len(matches)
    })

def search_cities(query):
    """
    Main search function - automatically chooses best strategy.
    Uses GSI for 3+ char queries, cache for shorter queries.
    """
    return search_cities_with_gsi(query)
