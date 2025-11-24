"""
Tests for refund_handler.py endpoints.
Tests cover: check refund eligibility, request refund, get refund status.
"""
import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

@pytest.fixture
def mock_refund_dependencies():
    """Mock refund dependencies."""
    with patch('handlers.refund_handler.subscriptions_table') as mock_subs, \
         patch('handlers.refund_handler.stripe') as mock_stripe:
        yield {
            'subscriptions': mock_subs,
            'stripe': mock_stripe
        }

class TestCheckRefundEligibility:
    """Tests for handle_check_refund_eligibility endpoint."""
    
    def test_check_eligibility_within_timeframe(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Check eligibility - subscription within refund window."""
        from handlers.refund_handler import handle_check_refund_eligibility
        
        recent_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=5)).isoformat()
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [recent_sub]}
        
        result = handle_check_refund_eligibility(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('eligible') is True
    
    def test_check_eligibility_outside_timeframe(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Check eligibility - subscription outside refund window."""
        from handlers.refund_handler import handle_check_refund_eligibility
        
        old_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=60)).isoformat()
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [old_sub]}
        
        result = handle_check_refund_eligibility(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('eligible') is False
    
    def test_check_eligibility_no_subscription(self, sample_user, mock_refund_dependencies):
        """Check eligibility - no active subscription."""
        from handlers.refund_handler import handle_check_refund_eligibility
        
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': []}
        
        result = handle_check_refund_eligibility(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('eligible') is False
    
    def test_check_eligibility_partial_refund(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Check eligibility for partial refund."""
        from handlers.refund_handler import handle_check_refund_eligibility
        
        mid_period_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=15)).isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=15)).isoformat()
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [mid_period_sub]}
        
        result = handle_check_refund_eligibility(sample_user)
        
        assert result['statusCode'] == 200
    
    def test_check_eligibility_multiple_charges(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Check eligibility with multiple charges."""
        from handlers.refund_handler import handle_check_refund_eligibility
        
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sample_subscription]}
        
        result = handle_check_refund_eligibility(sample_user)
        
        assert result['statusCode'] == 200

class TestRequestRefund:
    """Tests for handle_request_refund endpoint."""
    
    def test_request_refund_success(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Request refund successfully."""
        from handlers.refund_handler import handle_request_refund
        
        recent_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=5)).isoformat(),
            'stripe_payment_intent': 'pi_test123'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [recent_sub]}
        mock_refund_dependencies['stripe'].Refund.create.return_value = Mock(
            id='re_test123',
            status='succeeded'
        )
        
        body = {'reason': 'Not satisfied with service'}
        result = handle_request_refund(sample_user, body)
        
        assert result['statusCode'] in [200, 201]
    
    def test_request_refund_not_eligible(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Request refund when not eligible."""
        from handlers.refund_handler import handle_request_refund
        
        old_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=60)).isoformat()
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [old_sub]}
        
        body = {'reason': 'Test'}
        result = handle_request_refund(sample_user, body)
        
        assert result['statusCode'] == 400
    
    def test_request_refund_missing_reason(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Request refund without reason."""
        from handlers.refund_handler import handle_request_refund
        
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sample_subscription]}
        
        body = {}
        result = handle_request_refund(sample_user, body)
        
        assert result['statusCode'] == 400
    
    def test_request_refund_duplicate(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Request refund when already requested."""
        from handlers.refund_handler import handle_request_refund
        
        sub_with_refund = {
            **sample_subscription,
            'refund_requested': True,
            'refund_id': 're_existing'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sub_with_refund]}
        
        body = {'reason': 'Test'}
        result = handle_request_refund(sample_user, body)
        
        assert result['statusCode'] == 400
    
    def test_request_refund_stripe_processing(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Request refund processes through Stripe."""
        from handlers.refund_handler import handle_request_refund
        
        recent_sub = {
            **sample_subscription,
            'created_at': (datetime.utcnow() - timedelta(days=3)).isoformat(),
            'stripe_payment_intent': 'pi_test123'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [recent_sub]}
        mock_refund_dependencies['stripe'].Refund.create.return_value = Mock(
            id='re_test123',
            status='pending'
        )
        
        body = {'reason': 'Changed my mind'}
        result = handle_request_refund(sample_user, body)
        
        assert result['statusCode'] in [200, 201]
        # Verify Stripe was called
        mock_refund_dependencies['stripe'].Refund.create.assert_called_once()

class TestGetRefundStatus:
    """Tests for handle_get_refund_status endpoint."""
    
    def test_get_refund_status_pending(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Get refund status - pending."""
        from handlers.refund_handler import handle_get_refund_status
        
        sub_with_refund = {
            **sample_subscription,
            'refund_id': 're_test123',
            'refund_status': 'pending'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sub_with_refund]}
        
        result = handle_get_refund_status(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body.get('refund_status') == 'pending' or body.get('status') == 'pending'
    
    def test_get_refund_status_completed(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Get refund status - completed."""
        from handlers.refund_handler import handle_get_refund_status
        
        sub_with_refund = {
            **sample_subscription,
            'refund_id': 're_test123',
            'refund_status': 'succeeded'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sub_with_refund]}
        
        result = handle_get_refund_status(sample_user)
        
        assert result['statusCode'] == 200
    
    def test_get_refund_status_failed(self, sample_user, sample_subscription, mock_refund_dependencies):
        """Get refund status - failed."""
        from handlers.refund_handler import handle_get_refund_status
        
        sub_with_refund = {
            **sample_subscription,
            'refund_id': 're_test123',
            'refund_status': 'failed'
        }
        mock_refund_dependencies['subscriptions'].query.return_value = {'Items': [sub_with_refund]}
        
        result = handle_get_refund_status(sample_user)
        
        assert result['statusCode'] == 200

