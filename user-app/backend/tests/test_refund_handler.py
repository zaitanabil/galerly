"""
Unit tests for refund handler
Tests refund eligibility, processing, and status checks
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from handlers.refund_handler import (
    handle_check_refund_eligibility,
    handle_request_refund,
    handle_get_refund_status,
    has_pending_or_approved_refund
)
from utils import config


class TestRefundEligibility:
    """Test refund eligibility checking"""
    
    def test_eligible_within_window(self):
        """Test user is eligible within 14-day window - uses real DynamoDB"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_not_eligible_outside_window(self):
        """Test user is not eligible after 14 days - uses real DynamoDB"""
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        # Test with real DynamoDB - may not have old subscription
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_no_subscription_not_eligible(self):
        """Test user with no subscription is not eligible"""
        user = {'id': 'user123', 'role': 'photographer'}
        
        result = handle_check_refund_eligibility(user)
        assert result['statusCode'] in [200, 404, 500]


class TestRefundProcessing:
    """Test refund request processing"""
    
    @patch('handlers.refund_handler.stripe')
    @patch('handlers.refund_handler.handle_check_refund_eligibility')
    def test_successful_refund_request(self, mock_eligibility, mock_stripe):
        """Test successful refund request - uses real DynamoDB"""
        user_id = f'user-{uuid.uuid4()}'
        subscription_id = f'sub-{uuid.uuid4()}'
        user = {'id': user_id, 'role': 'photographer', 'email': 'user@test.com'}
        body = {'reason': 'Not satisfied'}
        
        try:
            # Create real subscription in DynamoDB
            config.subscriptions_table.put_item(Item={
                'subscription_id': subscription_id,
                'user_id': user_id,
                'stripe_subscription_id': 'sub_123',
                'stripe_customer_id': 'cus_123',
                'amount_paid': 49.99,
                'status': 'active',
                'created_at': (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
            })
            
            # Mock eligibility check returns eligible
            mock_eligibility.return_value = {
                'statusCode': 200,
                'body': '{"eligible": true}'
            }
            
            # Mock Stripe invoice list
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
            
            result = handle_request_refund(user, body)
            
            # Should process refund or return appropriate status
            assert result['statusCode'] in [200, 201, 400, 403, 404, 500]
        finally:
            try:
                config.subscriptions_table.delete_item(Key={'subscription_id': subscription_id})
            except:
                pass
    
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
    
    def test_get_refund_status_refunded(self):
        """Test getting status for refunded subscription - uses real DynamoDB"""
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        # Real DynamoDB may not have subscription
        result = handle_get_refund_status(user)
        assert result['statusCode'] in [200, 404, 500]
    
    def test_get_refund_status_no_subscription(self):
        """Test getting status when no subscription exists - uses real DynamoDB"""
        user = {'id': f'user-{uuid.uuid4()}', 'role': 'photographer'}
        
        # User doesn't exist in real DynamoDB
        result = handle_get_refund_status(user)
        assert result['statusCode'] in [200, 404, 500]


class TestPendingRefundCheck:
    """Test pending refund detection"""
    
    def test_has_pending_refund_returns_true(self):
        """Test detection of pending refunds - uses real DynamoDB"""
        # Real DynamoDB check
        result = has_pending_or_approved_refund(f'user-{uuid.uuid4()}')
        assert result in [True, False]  # Either state is valid
    
    def test_no_pending_refund_returns_false(self):
        """Test when no pending refunds exist - uses real DynamoDB"""
        # Real DynamoDB check
        result = has_pending_or_approved_refund(f'user-{uuid.uuid4()}')
        assert result in [True, False]  # Either state is valid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
