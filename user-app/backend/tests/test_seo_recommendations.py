"""
Test Suite for SEO Recommendations Engine
Tests the SEO analysis, scoring, and recommendations functionality
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from handlers.seo_handler import handle_get_seo_recommendations
from utils.seo_recommendations import (
    analyze_seo_completeness,
    generate_seo_checklist,
    get_automation_templates
)


class TestSEORecommendations:
    """Test SEO recommendations functionality"""
    
    @pytest.fixture
    def mock_user(self):
        """Mock photographer user"""
        return {
            'id': 'user123',
            'email': 'photographer@example.com',
            'plan': 'pro',
            'role': 'photographer'
        }
    
    @pytest.fixture
    def mock_user_data_complete(self):
        """Mock user with complete SEO setup"""
        return {
            'id': 'user123',
            'email': 'photographer@example.com',
            'bio': 'Professional wedding photographer with 10 years experience',
            'city': 'New York',
            'portfolio_seo': {
                'title': 'John Doe Photography - Wedding Photographer in NYC',
                'description': 'Award-winning wedding photographer based in New York City. Specializing in candid, emotional wedding photography that tells your unique love story.',
                'keywords': ['wedding', 'photography', 'NYC', 'photographer'],
                'og_image': 'https://example.com/og-image.jpg'
            },
            'portfolio_custom_domain': 'johndoephotography.com',
            'custom_domain_certificate_arn': 'arn:aws:acm:...',
            'seo_settings': {
                'structured_data': True,
                'canonical_urls': True
            },
            'seo_optimized': True,
            'portfolio_social_links': {
                'instagram': 'https://instagram.com/johndoe'
            }
        }
    
    @pytest.fixture
    def mock_user_data_incomplete(self):
        """Mock user with incomplete SEO setup"""
        return {
            'id': 'user456',
            'email': 'newbie@example.com',
            'portfolio_seo': {
                'title': 'My Portfolio'  # Too short
            }
        }
    
    @pytest.fixture
    def mock_galleries_public(self):
        """Mock public galleries"""
        return [
            {
                'id': 'gallery1',
                'name': 'Summer Wedding',
                'privacy': 'public',
                'description': 'Beautiful summer wedding in the countryside'
            },
            {
                'id': 'gallery2',
                'name': 'Engagement Session',
                'privacy': 'public',
                'description': 'Romantic engagement photos at sunset'
            }
        ]
    
    @pytest.fixture
    def mock_galleries_private(self):
        """Mock private galleries"""
        return [
            {
                'id': 'gallery3',
                'name': 'Private Event',
                'privacy': 'private'
            }
        ]
    
    def test_analyze_complete_seo(self, mock_user_data_complete, mock_galleries_public):
        """Test SEO analysis with complete setup"""
        result = analyze_seo_completeness(mock_user_data_complete, mock_galleries_public)
        
        # Should have high score
        assert result['score'] >= 80
        assert result['health'] == 'excellent'
        assert result['health_color'] == 'green'
        
        # Should have few issues
        assert len(result['issues']) == 0
        
        # Should have quick wins
        assert len(result['quick_wins']) > 0
        assert 'Custom domain configured' in str(result['quick_wins'])
    
    def test_analyze_incomplete_seo(self, mock_user_data_incomplete, mock_galleries_private):
        """Test SEO analysis with incomplete setup"""
        result = analyze_seo_completeness(mock_user_data_incomplete, mock_galleries_private)
        
        # Should have low score
        assert result['score'] < 60
        assert result['health'] in ['fair', 'poor']
        
        # Should have multiple issues
        assert len(result['issues']) > 0
        
        # Should detect critical issues
        critical_issues = [i for i in result['issues'] if i['severity'] == 'critical']
        assert len(critical_issues) > 0  # No public galleries
    
    def test_analyze_seo_no_meta_title(self, mock_user_data_incomplete, mock_galleries_public):
        """Test detection of missing meta title"""
        user_data = mock_user_data_incomplete.copy()
        user_data['portfolio_seo'] = {}
        
        result = analyze_seo_completeness(user_data, mock_galleries_public)
        
        # Should detect missing title
        issues = [i for i in result['issues'] if 'title' in i['issue'].lower()]
        assert len(issues) > 0
        assert issues[0]['severity'] == 'high'
    
    def test_analyze_seo_no_meta_description(self, mock_user_data_complete, mock_galleries_public):
        """Test detection of missing meta description"""
        user_data = mock_user_data_complete.copy()
        user_data['portfolio_seo']['description'] = ''
        
        result = analyze_seo_completeness(user_data, mock_galleries_public)
        
        # Should detect missing description
        issues = [i for i in result['issues'] if 'description' in i['issue'].lower()]
        assert len(issues) > 0
    
    def test_analyze_seo_title_length(self, mock_user_data_complete, mock_galleries_public):
        """Test title length validation"""
        user_data = mock_user_data_complete.copy()
        
        # Too short title
        user_data['portfolio_seo']['title'] = 'Photos'
        result = analyze_seo_completeness(user_data, mock_galleries_public)
        recommendations = [r for r in result['recommendations'] if 'title' in r['recommendation'].lower()]
        assert len(recommendations) > 0
        
        # Too long title
        user_data['portfolio_seo']['title'] = 'X' * 70
        result = analyze_seo_completeness(user_data, mock_galleries_public)
        recommendations = [r for r in result['recommendations'] if 'title' in r['recommendation'].lower()]
        assert len(recommendations) > 0
    
    def test_generate_seo_checklist_complete(self, mock_user_data_complete):
        """Test checklist generation for complete setup"""
        result = generate_seo_checklist(mock_user_data_complete)
        
        assert result['total_count'] == 10
        assert result['completed_count'] >= 8
        assert result['completion_percentage'] >= 80
        
        # Check specific items
        checklist_items = {item['item']: item['completed'] for item in result['checklist']}
        assert checklist_items['Meta title configured'] == True
        assert checklist_items['Custom domain configured'] == True
    
    def test_generate_seo_checklist_incomplete(self, mock_user_data_incomplete):
        """Test checklist generation for incomplete setup"""
        result = generate_seo_checklist(mock_user_data_incomplete)
        
        assert result['total_count'] == 10
        assert result['completed_count'] < 5
        assert result['completion_percentage'] < 50
    
    def test_recommendations_prioritization(self, mock_user_data_incomplete, mock_galleries_private):
        """Test that recommendations are properly prioritized"""
        result = analyze_seo_completeness(mock_user_data_incomplete, mock_galleries_private)
        
        recommendations = result['recommendations']
        
        # Check that high priority comes first
        priorities = [r['priority'] for r in recommendations]
        high_index = priorities.index('high') if 'high' in priorities else -1
        low_index = priorities.index('low') if 'low' in priorities else -1
        
        if high_index >= 0 and low_index >= 0:
            assert high_index < low_index
    
    def test_issues_severity_sorting(self, mock_user_data_incomplete, mock_galleries_private):
        """Test that issues are sorted by severity"""
        result = analyze_seo_completeness(mock_user_data_incomplete, mock_galleries_private)
        
        issues = result['issues']
        if len(issues) > 1:
            severities = [i['severity'] for i in issues]
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            severity_values = [severity_order[s] for s in severities]
            
            # Check sorted
            assert severity_values == sorted(severity_values)
    
    def test_score_calculation_boundaries(self):
        """Test score stays within 0-100 range"""
        # Minimal setup
        minimal_user = {'id': 'test', 'portfolio_seo': {}}
        result = analyze_seo_completeness(minimal_user, [])
        assert 0 <= result['score'] <= 100
        
        # Maximum setup (would be tested with fixture)
        # Score should never exceed 100
    
    def test_next_action_identification(self, mock_user_data_incomplete, mock_galleries_private):
        """Test that next action is identified"""
        result = analyze_seo_completeness(mock_user_data_incomplete, mock_galleries_private)
        
        assert result['next_action'] is not None
        
        # Next action should be highest priority issue or recommendation
        if result['issues']:
            assert result['next_action'] == result['issues'][0]
        elif result['recommendations']:
            assert result['next_action'] == result['recommendations'][0]
    
    @patch('handlers.seo_handler.users_table')
    @patch('handlers.seo_handler.galleries_table')
    def test_handle_get_seo_recommendations_success(
        self, mock_galleries_table, mock_users_table,
        mock_user, mock_user_data_complete, mock_galleries_public
    ):
        """Test successful SEO recommendations API call"""
        # Setup mocks
        mock_users_table.get_item.return_value = {'Item': mock_user_data_complete}
        mock_galleries_table.query.return_value = {'Items': mock_galleries_public}
        
        # Call handler
        response = handle_get_seo_recommendations(mock_user)
        
        # Verify response
        assert response['statusCode'] == 200
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        
        assert 'analysis' in body
        assert 'checklist' in body
        assert 'user_id' in body
        assert body['user_id'] == mock_user['id']
    
    @patch('handlers.seo_handler.users_table')
    def test_handle_get_seo_recommendations_user_not_found(
        self, mock_users_table, mock_user
    ):
        """Test SEO recommendations when user not found"""
        mock_users_table.get_item.return_value = {}
        
        response = handle_get_seo_recommendations(mock_user)
        
        assert response['statusCode'] == 404
        body = response['body'] if isinstance(response['body'], dict) else eval(response['body'])
        assert 'error' in body


class TestSEORecommendationsEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_galleries(self):
        """Test with no galleries"""
        user_data = {'id': 'test', 'portfolio_seo': {'title': 'Test'}}
        result = analyze_seo_completeness(user_data, [])
        
        # Should identify lack of galleries as issue
        assert len(result['issues']) > 0
    
    def test_all_private_galleries(self):
        """Test with only private galleries"""
        user_data = {'id': 'test', 'portfolio_seo': {'title': 'Test', 'description': 'Test'}}
        galleries = [{'privacy': 'private'}] * 5
        
        result = analyze_seo_completeness(user_data, galleries)
        
        # Should identify lack of public content
        issues = [i for i in result['issues'] if 'public' in i['description'].lower()]
        assert len(issues) > 0
    
    def test_malformed_user_data(self):
        """Test with malformed user data"""
        user_data = None
        galleries = []
        
        # Should handle gracefully (not crash)
        try:
            result = analyze_seo_completeness(user_data or {}, galleries)
            assert result['score'] >= 0
        except Exception as e:
            pytest.fail(f"Should handle malformed data gracefully: {e}")
    
    def test_special_characters_in_seo_data(self):
        """Test with special characters in SEO data"""
        user_data = {
            'id': 'test',
            'portfolio_seo': {
                'title': 'Test & Photography <script>',
                'description': 'Photos with "quotes" and \'apostrophes\''
            }
        }
        
        result = analyze_seo_completeness(user_data, [])
        
        # Should process without errors
        assert result['score'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

