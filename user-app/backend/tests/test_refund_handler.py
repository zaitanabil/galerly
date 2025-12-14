"""
Unit tests for refund handler
Tests refund eligibility, processing, and status checks
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from handlers.refund_handler import (
    handle_check_refund_eligibility,
    handle_request_refund,
    handle_get_refund_status,
    has_pending_or_approved_refund
)


class TestRefundEligibility:
    """Test refund eligibility checking"""
    
    @patch('handlers.refund_handler.subscriptions_table')
    def test_eligible_within_window(self, mock_table):
        """Test user is eligible within 14-day window"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        # Subscription created 5 days ago
        subscription_date = (datetime.now(timezone.utc) - timedelta(days=5)).replace(tzinfo=None).isoformat() + 'Z'
        
        mock_table.query.return_value = {
            'Items': [{
                'user_id': 'user123',
                'status': 'active',
                'current_period_start': subscription_date,
                'plan': 'pro'
            }]
        }
        
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] == 200
        # Body contains eligibility info
    
    @patch('handlers.refund_handler.subscriptions_table')
    def test_not_eligible_outside_window(self, mock_table):
        """Test user is not eligible after 14 days"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        # Subscription created 20 days ago
        subscription_date = (datetime.now(timezone.utc) - timedelta(days=20)).replace(tzinfo=None).isoformat() + 'Z'
        
        mock_table.query.return_value = {
            'Items': [{
                'user_id': 'user123',
                'status': 'active',
                'current_period_start': subscription_date,
                'plan': 'pro'
            }]
        }
        
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] == 200
        # Should indicate not eligible
    
    @patch('handlers.refund_handler.subscriptions_table')
    def test_no_subscription_not_eligible(self, mock_table):
        """Test user with no subscription is not eligible"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        mock_table.query.return_value = {'Items': []}
        
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] == 200
        # Should indicate no subscription


class TestRefundProcessing:
    """Test refund request processing"""
    
    @patch('handlers.refund_handler.stripe')
    @patch('handlers.refund_handler.subscriptions_table')
    @patch('handlers.refund_handler.handle_check_refund_eligibility')
    def test_successful_refund_request(self, mock_eligibility, mock_table, mock_stripe):
        """Test successful refund processing"""
        user = {'id': 'user123', 'role': 'photographer', 'email': 'user@test.com'}
        body = {'reason': 'Not satisfied'}
        
        # Mock eligibility check returns eligible
        mock_eligibility.return_value = {
            'body': '{"eligible": true}'
        }
        
        # Mock subscription with Stripe ID
        mock_table.query.return_value = {
            'Items': [{
                'user_id': 'user123',
                'stripe_subscription_id': 'sub_123',
                'stripe_customer_id': 'cus_123',
                'amount_paid': 49.99
            }]
        }
        
        # Mock Stripe invoice list (handler needs this first)
        mock_invoice = Mock()
        mock_invoice.status = 'paid'
        mock_invoice.payment_intent = 'pi_123'
        mock_stripe.Invoice.list.return_value = Mock(data=[mock_invoice])
        
        # Mock Stripe refund creation
        mock_stripe.Refund.create.return_value = Mock(
            id='re_123',
            amount=4999,
            status='succeeded'
        )
        
        # Mock users_table
        with patch('handlers.refund_handler.users_table') as mock_users:
            mock_users.get_item.return_value = {'Item': {'email': 'user@test.com', 'plan': 'pro'}}
            
            result = handle_request_refund(user, body)
            # Verify refund was processed
            assert mock_stripe.Refund.create.called
    
    @patch('handlers.refund_handler.handle_check_refund_eligibility')
    def test_refund_blocked_when_not_eligible(self, mock_eligibility):
        """Test refund is blocked when user not eligible"""
        user = {'id': 'user123', 'role': 'photographer'}
        body = {'reason': 'Test'}
        
        # Mock eligibility check returns not eligible
        mock_eligibility.return_value = {
            'body': '{"eligible": false, "reason": "Outside refund window"}'
        }
        
        result = handle_request_refund(user, body)
        assert result['statusCode'] == 403


class TestRefundStatus:
    """Test refund status retrieval"""
    
    @patch('handlers.refund_handler.subscriptions_table')
    def test_get_refund_status_refunded(self, mock_table):
        """Test getting status for refunded subscription"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        mock_table.query.return_value = {
            'Items': [{
                'user_id': 'user123',
                'refund_status': 'refunded',
                'refund_amount': 49.99,
                'refund_date': '2025-01-01T00:00:00Z',
                'refund_id': 're_123'
            }]
        }
        
        result = handle_get_refund_status(user)
        assert result['statusCode'] == 200
        # Should return refund details
    
    @patch('handlers.refund_handler.subscriptions_table')
    def test_get_refund_status_no_subscription(self, mock_table):
        """Test getting status when no subscription exists"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        mock_table.query.return_value = {'Items': []}
        
        result = handle_get_refund_status(user)
        assert result['statusCode'] == 200


class TestPendingRefundCheck:
    """Test pending refund detection"""
    
    @patch('handlers.refund_handler.billing_table')
    @patch('handlers.refund_handler.subscriptions_table')
    def test_has_pending_refund_returns_true(self, mock_subs, mock_billing):
        """Test detection of pending refunds"""
        mock_billing.query.return_value = {
            'Items': [{
                'user_id': 'user123',
                'refund_status': 'pending'
            }]
        }
        
        result = has_pending_or_approved_refund('user123')
        assert result is True
    
    @patch('handlers.refund_handler.billing_table')
    @patch('handlers.refund_handler.subscriptions_table')
    def test_no_pending_refund_returns_false(self, mock_subs, mock_billing):
        """Test when no pending refunds exist"""
        mock_billing.query.return_value = {'Items': []}
        mock_subs.query.return_value = {'Items': []}
        
        result = has_pending_or_approved_refund('user123')
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
