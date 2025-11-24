"""
Tests for billing_handler.py endpoints.
Tests cover: get subscription, cancel subscription, change plan, reactivate subscription.
"""
import pytest
from unittest.mock import Mock, patch
import json

@pytest.fixture
def mock_billing_dependencies():
    """Mock all billing handler dependencies."""
    with patch('handlers.billing_handler.subscriptions_table') as mock_subs, \
         patch('handlers.billing_handler.users_table') as mock_users, \
         patch('handlers.billing_handler.stripe') as mock_stripe:
        yield {
            'subscriptions': mock_subs,
            'users': mock_users,
            'stripe': mock_stripe
        }

# Test: handle_get_subscription
class TestHandleGetSubscription:
    """Tests for handle_get_subscription endpoint."""
    
    def test_get_subscription_active(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Get active subscription successfully."""
        from handlers.billing_handler import handle_get_subscription
        
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [sample_subscription]
        }
        
        result = handle_get_subscription(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['plan'] == 'pro'
        assert body['status'] == 'active'
        assert body['is_canceled'] is False
    
    def test_get_subscription_canceled(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Get canceled subscription."""
        from handlers.billing_handler import handle_get_subscription
        
        canceled_sub = {**sample_subscription, 'cancel_at_period_end': True, 'pending_plan': 'free'}
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [canceled_sub]
        }
        
        result = handle_get_subscription(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['is_canceled'] is True
        assert body['pending_plan'] == 'free'
    
    def test_get_subscription_no_subscription(self, sample_user, mock_billing_dependencies):
        """Get subscription when user has no subscription."""
        from handlers.billing_handler import handle_get_subscription
        
        mock_billing_dependencies['subscriptions'].query.return_value = {'Items': []}
        
        result = handle_get_subscription(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['plan'] == 'free'
        assert body['status'] == 'none'

# Test: handle_cancel_subscription
class TestHandleCancelSubscription:
    """Tests for handle_cancel_subscription endpoint."""
    
    def test_cancel_subscription_success(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Cancel active subscription successfully."""
        from handlers.billing_handler import handle_cancel_subscription
        
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [sample_subscription]
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': sample_subscription
        }
        mock_billing_dependencies['stripe'].Subscription.modify.return_value = Mock(
            cancel_at_period_end=True
        )
        
        result = handle_cancel_subscription(sample_user)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'canceled' in body['message'].lower()
        
        # Verify Stripe API was called
        mock_billing_dependencies['stripe'].Subscription.modify.assert_called_once()
    
    def test_cancel_subscription_free_plan(self, sample_user, mock_billing_dependencies):
        """Cancel subscription fails for free plan."""
        from handlers.billing_handler import handle_cancel_subscription
        
        free_user = {**sample_user, 'plan': 'free'}
        mock_billing_dependencies['subscriptions'].query.return_value = {'Items': []}
        
        result = handle_cancel_subscription(free_user)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'free plan' in body['error'].lower()
    
    def test_cancel_subscription_already_canceled(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Cancel subscription fails when already canceled."""
        from handlers.billing_handler import handle_cancel_subscription
        
        canceled_sub = {**sample_subscription, 'cancel_at_period_end': True}
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [canceled_sub]
        }
        
        result = handle_cancel_subscription(sample_user)
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'already canceled' in body['error'].lower()

# Test: handle_change_plan
class TestHandleChangePlan:
    """Tests for handle_change_plan endpoint."""
    
    def test_change_plan_upgrade_success(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Upgrade plan successfully."""
        from handlers.billing_handler import handle_change_plan
        
        starter_sub = {**sample_subscription, 'plan': 'starter'}
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [starter_sub]
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': starter_sub
        }
        
        with patch('handlers.billing_handler.PRICE_IDS', {'pro': 'price_pro', 'starter': 'price_starter'}):
            mock_billing_dependencies['stripe'].Subscription.retrieve.return_value = Mock(
                items=Mock(data=[Mock(price=Mock(id='price_starter'))])
            )
            mock_billing_dependencies['stripe'].Subscription.modify.return_value = Mock(
                id='sub_stripe123'
            )
            
            body = {'new_plan': 'pro'}
            result = handle_change_plan(sample_user, body)
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'upgraded' in response_body['message'].lower() or 'changed' in response_body['message'].lower()
    
    def test_change_plan_downgrade_creates_checkout(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Downgrade plan creates Stripe checkout session."""
        from handlers.billing_handler import handle_change_plan
        
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [sample_subscription]  # pro plan
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': sample_subscription
        }
        
        with patch('handlers.billing_handler.PRICE_IDS', {'starter': 'price_starter', 'pro': 'price_pro'}):
            mock_billing_dependencies['stripe'].Subscription.retrieve.return_value = Mock(
                items=Mock(data=[Mock(price=Mock(id='price_pro'))])
            )
            mock_billing_dependencies['stripe'].checkout.Session.create.return_value = Mock(
                url='https://checkout.stripe.com/test'
            )
            
            body = {'new_plan': 'starter'}
            result = handle_change_plan(sample_user, body)
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'checkout_url' in response_body
    
    def test_change_plan_reactivate_same_plan(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Reactivate canceled subscription to same plan."""
        from handlers.billing_handler import handle_change_plan
        
        canceled_sub = {
            **sample_subscription,
            'cancel_at_period_end': True,
            'pending_plan': 'free'
        }
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [canceled_sub]
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': canceled_sub
        }
        
        with patch('handlers.billing_handler.PRICE_IDS', {'pro': 'price_pro'}):
            mock_billing_dependencies['stripe'].Subscription.retrieve.return_value = Mock(
                items=Mock(data=[Mock(price=Mock(id='price_pro'))])
            )
            mock_billing_dependencies['stripe'].Subscription.modify.return_value = Mock(
                cancel_at_period_end=False
            )
            
            body = {'new_plan': 'pro'}  # Same plan as current
            result = handle_change_plan(sample_user, body)
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'reactivated' in response_body['message'].lower()
            
            # Verify Stripe was called to remove cancellation
            mock_billing_dependencies['stripe'].Subscription.modify.assert_called_once()
    
    def test_change_plan_reactivate_different_plan(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Reactivate and change to different plan creates checkout."""
        from handlers.billing_handler import handle_change_plan
        
        canceled_sub = {
            **sample_subscription,
            'plan': 'starter',
            'cancel_at_period_end': True,
            'pending_plan': 'free'
        }
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [canceled_sub]
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': canceled_sub
        }
        
        with patch('handlers.billing_handler.PRICE_IDS', {'pro': 'price_pro', 'starter': 'price_starter'}):
            mock_billing_dependencies['stripe'].checkout.Session.create.return_value = Mock(
                url='https://checkout.stripe.com/test'
            )
            
            body = {'new_plan': 'pro'}  # Different plan
            result = handle_change_plan(sample_user, body)
            
            assert result['statusCode'] == 200
            response_body = json.loads(result['body'])
            assert 'checkout_url' in response_body
    
    def test_change_plan_already_on_plan(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Change plan fails when already on that plan."""
        from handlers.billing_handler import handle_change_plan
        
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [sample_subscription]  # pro plan
        }
        mock_billing_dependencies['subscriptions'].get_item.return_value = {
            'Item': sample_subscription
        }
        
        with patch('handlers.billing_handler.PRICE_IDS', {'pro': 'price_pro'}):
            mock_billing_dependencies['stripe'].Subscription.retrieve.return_value = Mock(
                items=Mock(data=[Mock(price=Mock(id='price_pro'))])
            )
            
            body = {'new_plan': 'pro'}
            result = handle_change_plan(sample_user, body)
            
            assert result['statusCode'] == 400
            response_body = json.loads(result['body'])
            assert 'already on this plan' in response_body['error'].lower()
    
    def test_change_plan_missing_new_plan(self, sample_user, mock_billing_dependencies):
        """Change plan fails when new_plan not provided."""
        from handlers.billing_handler import handle_change_plan
        
        body = {}
        result = handle_change_plan(sample_user, body)
        
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'new_plan' in response_body['error'].lower()
    
    def test_change_plan_invalid_plan(self, sample_user, mock_billing_dependencies):
        """Change plan fails for invalid plan name."""
        from handlers.billing_handler import handle_change_plan
        
        body = {'new_plan': 'invalid_plan'}
        result = handle_change_plan(sample_user, body)
        
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'invalid' in response_body['error'].lower()

# Test: Stripe Webhook - checkout.session.completed
class TestStripeWebhookCheckoutCompleted:
    """Tests for Stripe webhook handling."""
    
    def test_webhook_checkout_completed_cancels_old_subscription(self, sample_user, sample_subscription, mock_billing_dependencies):
        """Webhook cancels old Stripe subscription when new one is created."""
        from handlers.billing_handler import handle_stripe_webhook
        
        # Simulate existing subscription
        old_sub = {**sample_subscription, 'stripe_subscription_id': 'sub_old123'}
        mock_billing_dependencies['subscriptions'].query.return_value = {
            'Items': [old_sub]
        }
        
        with patch('handlers.billing_handler.stripe.Webhook.construct_event') as mock_construct:
            # Mock webhook event
            mock_event = {
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'customer': 'cus_test123',
                        'subscription': 'sub_new123',
                        'client_reference_id': 'user_123',
                        'metadata': {'plan': 'pro'}
                    }
                }
            }
            mock_construct.return_value = mock_event
            
            # Mock Stripe cancel
            mock_billing_dependencies['stripe'].Subscription.delete.return_value = Mock()
            
            result = handle_stripe_webhook({'body': 'webhook_payload', 'headers': {}})
            
            # Verify old subscription was canceled
            mock_billing_dependencies['stripe'].Subscription.delete.assert_called_with('sub_old123')

# Test: Subscription validation
class TestSubscriptionValidation:
    """Tests for subscription validation logic."""
    
    def test_validate_cancel_prevents_double_cancel(self, sample_subscription):
        """Validation prevents canceling already canceled subscription."""
        from utils.subscription_validator import SubscriptionState
        
        canceled_sub = {**sample_subscription, 'cancel_at_period_end': True}
        state = SubscriptionState(canceled_sub)
        
        is_valid, error = state.validate_cancel()
        
        assert is_valid is False
        assert 'already canceled' in error.lower()
    
    def test_validate_reactivate_allows_canceled_sub(self, sample_subscription):
        """Validation allows reactivating canceled subscription."""
        from utils.subscription_validator import SubscriptionState
        
        canceled_sub = {
            **sample_subscription,
            'cancel_at_period_end': True,
            'pending_plan': 'free'
        }
        state = SubscriptionState(canceled_sub)
        
        is_valid, error = state.validate_reactivate()
        
        assert is_valid is True
        assert error is None

