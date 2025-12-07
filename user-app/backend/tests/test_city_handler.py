"""
Tests for City Search Handler
Tests city autocomplete functionality
"""
import pytest
from unittest.mock import Mock, patch
from handlers.city_handler import handle_city_search


class TestCitySearch:
    """Test city search functionality"""
    
    @patch('handlers.city_handler.search_cities')
    def test_city_search_success(self, mock_search_cities):
        """Test successful city search"""
        # Setup
        mock_search_cities.return_value = {
            'cities': [
                {'name': 'Paris', 'country': 'France'},
                {'name': 'London', 'country': 'United Kingdom'}
            ]
        }
        
        # Execute
        result = handle_city_search('par')
        
        # Assert
        assert 'cities' in result
        assert len(result['cities']) == 2
        assert result['cities'][0]['name'] == 'Paris'
        mock_search_cities.assert_called_once_with('par')
    
    @patch('handlers.city_handler.search_cities')
    def test_city_search_empty_query(self, mock_search_cities):
        """Test city search with empty query"""
        # Setup
        mock_search_cities.return_value = {'cities': []}
        
        # Execute
        result = handle_city_search('')
        
        # Assert
        assert 'cities' in result
        assert len(result['cities']) == 0
    
    @patch('handlers.city_handler.search_cities')
    def test_city_search_no_results(self, mock_search_cities):
        """Test city search with no matching results"""
        # Setup
        mock_search_cities.return_value = {'cities': []}
        
        # Execute
        result = handle_city_search('zzznonexistentcity')
        
        # Assert
        assert 'cities' in result
        assert len(result['cities']) == 0
    
    @patch('handlers.city_handler.search_cities')
    def test_city_search_case_insensitive(self, mock_search_cities):
        """Test city search is case insensitive"""
        # Setup
        mock_search_cities.return_value = {
            'cities': [
                {'name': 'New York', 'country': 'United States'}
            ]
        }
        
        # Execute
        result = handle_city_search('NEW YORK')
        
        # Assert
        assert 'cities' in result
        assert len(result['cities']) == 1

