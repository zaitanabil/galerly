"""
IP Geolocation Service
Converts IP addresses to approximate geographic coordinates
Privacy: Returns city/region level data, never stores exact IPs
"""
import os
import requests
from functools import lru_cache


def get_geolocation_api_url():
    """Get geolocation API URL from environment"""
    return os.environ.get('GEOLOCATION_API_URL', 'http://ip-api.com/json')


@lru_cache(maxsize=1000)
def get_location_from_ip(ip_address):
    """
    Get approximate location from IP address
    Returns city, region, country, and coordinates
    Caches results to reduce API calls
    
    Args:
        ip_address: Client IP address
        
    Returns:
        dict: {
            'city': str,
            'region': str,
            'country': str,
            'country_code': str,
            'latitude': float,
            'longitude': float,
            'timezone': str
        }
        
    Note: Privacy-focused - only returns approximate city/region level data
    """
    try:
        # Skip private/local IPs
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            return {
                'city': 'Local',
                'region': 'Development',
                'country': 'Local',
                'country_code': 'XX',
                'latitude': 0.0,
                'longitude': 0.0,
                'timezone': 'UTC'
            }
        
        # Use ip-api.com (free, no API key required, 45 requests/minute limit)
        # For production, consider upgrading to ipapi.co or ipgeolocation.io
        api_url = get_geolocation_api_url()
        
        # Request specific fields for privacy and performance
        response = requests.get(
            f"{api_url}/{ip_address}",
            params={
                'fields': 'status,message,country,countryCode,region,regionName,city,lat,lon,timezone'
            },
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', 'XX'),
                    'latitude': float(data.get('lat', 0.0)),
                    'longitude': float(data.get('lon', 0.0)),
                    'timezone': data.get('timezone', 'UTC')
                }
        
        # Fallback for failed lookups
        return {
            'city': 'Unknown',
            'region': 'Unknown',
            'country': 'Unknown',
            'country_code': 'XX',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'UTC'
        }
        
    except Exception as e:
        print(f"Error getting geolocation for IP: {str(e)}")
        # Return default location on error
        return {
            'city': 'Unknown',
            'region': 'Unknown',
            'country': 'Unknown',
            'country_code': 'XX',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'UTC'
        }


def get_ip_from_request(event):
    """
    Extract client IP from API Gateway event
    Handles both direct IPs and proxied requests
    
    Args:
        event: API Gateway event dict
        
    Returns:
        str: Client IP address
    """
    try:
        # Try to get real IP from headers (for proxied requests)
        request_context = event.get('requestContext', {})
        identity = request_context.get('identity', {})
        
        # Check X-Forwarded-For header first (most common for proxied requests)
        headers = event.get('headers', {})
        forwarded_for = headers.get('X-Forwarded-For') or headers.get('x-forwarded-for')
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one (client IP)
            return forwarded_for.split(',')[0].strip()
        
        # Fall back to sourceIp from API Gateway
        source_ip = identity.get('sourceIp')
        if source_ip:
            return source_ip
        
        # Last resort: try to get from headers
        return headers.get('X-Real-IP') or headers.get('x-real-ip') or '127.0.0.1'
        
    except Exception as e:
        print(f"Error extracting IP from request: {str(e)}")
        return '127.0.0.1'
