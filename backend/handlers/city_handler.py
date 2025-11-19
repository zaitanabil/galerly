"""
City search handler
"""
from utils.cities import search_cities

def handle_city_search(query):
    """Handle city search endpoint"""
    return search_cities(query)

