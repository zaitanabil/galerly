"""
Subscription State Validation Module

Validates ALL possible subscription state transitions to prevent:
- Race conditions
- Invalid state transitions
- Security exploits
- Data corruption
- Billing fraud attempts

Valid States:
- free (Starter)
- plus (Plus - $12/month)
- pro (Pro - $24/month)

Valid Actions:
- subscribe (new subscription)
- upgrade (immediate, prorated)
- downgrade (scheduled for period end)
- cancel (scheduled for period end)
- reactivate (cancel the cancellation)
- refund (with approval process)
"""

from datetime import datetime
from typing import Dict, Optional, Tuple, List

# Plan hierarchy for upgrade/downgrade logic
PLAN_HIERARCHY = {
    'free': 0,
    'starter': 1,
    'plus': 2,
    'pro': 3,
    'ultimate': 4
}


class SubscriptionState:
    """Represents the current state of a subscription"""
    def __init__(self, subscription_data: Dict, user_data: Dict):
        self.subscription = subscription_data
        self.user = user_data
        
        # Normalize plan names
        raw_plan = user_data.get('plan') or user_data.get('subscription')
        self.current_plan = raw_plan
        
        # State flags
        self.has_stripe_subscription = bool(subscription_data.get('stripe_subscription_id'))
        self.is_active = subscription_data.get('status') == 'active'
        self.is_canceled = subscription_data.get('cancel_at_period_end', False)
        self.has_pending_change = bool(subscription_data.get('pending_plan'))
        self.pending_plan = subscription_data.get('pending_plan')
        self.pending_change_at = subscription_data.get('pending_plan_change_at')
        
        # Processing locks
        self.is_processing = subscription_data.get('processing_change', False)
        
        # Refund status
        self.has_pending_refund = False  # Will be set by caller
        
        # Timestamps
        self.current_time = datetime.utcnow().timestamp()
        self.period_end = subscription_data.get('current_period_end', 0)


class ValidationResult:
    """Result of a validation check"""
    def __init__(self, valid: bool, reason: str = "", error_code: str = ""):
        self.valid = valid
        self.reason = reason
        self.error_code = error_code
    
    def to_dict(self) -> Dict:
        return {
            'valid': self.valid,
            'reason': self.reason,
            'error_code': self.error_code
        }


class SubscriptionValidator:
    """Validates subscription state transitions"""
    
    @staticmethod
    def normalize_plan(plan_id: str) -> str:
        """Normalize plan name"""
        return plan_id
    
    @staticmethod
    def get_plan_level(plan_id: str) -> int:
        """Get plan hierarchy level"""
        normalized = SubscriptionValidator.normalize_plan(plan_id)
        return PLAN_HIERARCHY.get(normalized, -1)
    
    @staticmethod
    def validate_plan_exists(plan_id: str) -> ValidationResult:
        """Validate that a plan ID is valid"""
        normalized = SubscriptionValidator.normalize_plan(plan_id)
        if normalized not in PLAN_HIERARCHY:
            return ValidationResult(
                False,
                f"Invalid plan: {plan_id}",
                "INVALID_PLAN"
            )
        return ValidationResult(True)
    
    @staticmethod
    def validate_subscribe(state: SubscriptionState, target_plan: str) -> ValidationResult:
        """
        Validate new subscription
        
        Rules:
        1. Cannot subscribe to free (it's the default)
        2. Cannot subscribe if already has active paid subscription (use upgrade/downgrade instead)
        3. Can subscribe to paid plan if currently on free plan
        """
        # Validate target plan exists
        plan_check = SubscriptionValidator.validate_plan_exists(target_plan)
        if not plan_check.valid:
            return plan_check
        
        normalized_target = SubscriptionValidator.normalize_plan(target_plan)
        
        # Cannot subscribe to free
        if normalized_target == 'free':
            return ValidationResult(
                False,
                "Cannot subscribe to free plan (it's the default)",
                "INVALID_SUBSCRIPTION"
            )
        
        # If user already has a paid plan, they should upgrade/downgrade instead
        if state.current_plan in ['plus', 'pro'] and state.has_stripe_subscription:
            return ValidationResult(
                False,
                f"Already subscribed to {state.current_plan}. Use upgrade or downgrade instead.",
                "ALREADY_SUBSCRIBED"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_upgrade(state: SubscriptionState, target_plan: str) -> ValidationResult:
        """
        Validate upgrade
        
        Rules:
        1. Target plan must be higher tier than current plan
        2. Cannot upgrade if subscription is canceled
        3. Cannot upgrade if processing another change
        4. Cannot upgrade if refund is pending
        5. Valid upgrades: free→plus, free→pro, plus→pro
        """
        # Validate target plan exists
        plan_check = SubscriptionValidator.validate_plan_exists(target_plan)
        if not plan_check.valid:
            return plan_check
        
        normalized_target = SubscriptionValidator.normalize_plan(target_plan)
        current_level = SubscriptionValidator.get_plan_level(state.current_plan)
        target_level = SubscriptionValidator.get_plan_level(normalized_target)
        
        # Must be higher tier
        if target_level <= current_level:
            return ValidationResult(
                False,
                f"Cannot upgrade from {state.current_plan} to {normalized_target} (same or lower tier)",
                "INVALID_UPGRADE"
            )
        
        # Cannot upgrade canceled subscription
        if state.is_canceled:
            return ValidationResult(
                False,
                "Cannot upgrade a canceled subscription. Reactivate first.",
                "SUBSCRIPTION_CANCELED"
            )
        
        # Cannot upgrade if processing another change
        if state.is_processing:
            return ValidationResult(
                False,
                "Subscription change in progress. Please wait.",
                "PROCESSING_CHANGE"
            )
        
        # Cannot upgrade if refund is pending
        if state.has_pending_refund:
            return ValidationResult(
                False,
                "Cannot upgrade while refund request is pending",
                "REFUND_PENDING"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_downgrade(state: SubscriptionState, target_plan: str) -> ValidationResult:
        """
        Validate downgrade
        
        Rules:
        1. Target plan must be lower tier than current plan
        2. Cannot downgrade if already has pending downgrade
        3. Cannot downgrade if processing another change
        4. Cannot downgrade if subscription is canceled (no subscription to downgrade)
        5. Cannot downgrade if refund is pending
        6. Valid downgrades: pro→plus, pro→free, plus→free
        """
        # Validate target plan exists
        plan_check = SubscriptionValidator.validate_plan_exists(target_plan)
        if not plan_check.valid:
            return plan_check
        
        normalized_target = SubscriptionValidator.normalize_plan(target_plan)
        current_level = SubscriptionValidator.get_plan_level(state.current_plan)
        target_level = SubscriptionValidator.get_plan_level(normalized_target)
        
        # Must be lower tier
        if target_level >= current_level:
            return ValidationResult(
                False,
                f"Cannot downgrade from {state.current_plan} to {normalized_target} (same or higher tier)",
                "INVALID_DOWNGRADE"
            )
        
        # Cannot downgrade if already has pending downgrade
        if state.has_pending_change and state.pending_plan:
            pending_level = SubscriptionValidator.get_plan_level(state.pending_plan)
            if pending_level < current_level:
                return ValidationResult(
                    False,
                    f"Already has pending downgrade to {state.pending_plan}",
                    "PENDING_DOWNGRADE"
                )
        
        # Cannot downgrade if processing another change
        if state.is_processing:
            return ValidationResult(
                False,
                "Subscription change in progress. Please wait.",
                "PROCESSING_CHANGE"
            )
        
        # Cannot downgrade if subscription is canceled
        if state.is_canceled:
            return ValidationResult(
                False,
                "Subscription is already canceled",
                "SUBSCRIPTION_CANCELED"
            )
        
        # Cannot downgrade if refund is pending
        if state.has_pending_refund:
            return ValidationResult(
                False,
                "Cannot downgrade while refund request is pending",
                "REFUND_PENDING"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_cancel(state: SubscriptionState) -> ValidationResult:
        """
        Validate cancellation
        
        Rules:
        1. Must have active paid subscription
        2. Cannot cancel if already canceled
        3. Cannot cancel if processing another change
        4. Cannot cancel free plan (nothing to cancel)
        5. Cannot cancel if refund is pending (refund takes precedence)
        """
        # Cannot cancel free plan
        if state.current_plan == 'free':
            return ValidationResult(
                False,
                "Cannot cancel free plan (no subscription to cancel)",
                "NO_SUBSCRIPTION"
            )
        
        # Cannot cancel if already canceled
        if state.is_canceled:
            return ValidationResult(
                False,
                "Subscription is already canceled",
                "ALREADY_CANCELED"
            )
        
        # Cannot cancel if processing another change
        if state.is_processing:
            return ValidationResult(
                False,
                "Subscription change in progress. Please wait.",
                "PROCESSING_CHANGE"
            )
        
        # Must have Stripe subscription
        if not state.has_stripe_subscription:
            return ValidationResult(
                False,
                "No active subscription found",
                "NO_SUBSCRIPTION"
            )
        
        # Cannot cancel if refund is pending
        if state.has_pending_refund:
            return ValidationResult(
                False,
                "Cannot cancel while refund request is pending. Refund will cancel subscription if approved.",
                "REFUND_PENDING"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_reactivate(state: SubscriptionState) -> ValidationResult:
        """
        Validate reactivation (un-cancel)
        
        Rules:
        1. Must have canceled subscription (cancel_at_period_end = True)
        2. Must still be within billing period (period hasn't ended yet)
        3. Cannot reactivate if processing another change
        4. Cannot reactivate if refund is approved
        """
        # Must have canceled subscription
        if not state.is_canceled:
            return ValidationResult(
                False,
                "Subscription is not canceled (nothing to reactivate)",
                "NOT_CANCELED"
            )
        
        # Must still be within billing period
        if state.period_end and state.current_time >= state.period_end:
            return ValidationResult(
                False,
                "Billing period has ended. Cannot reactivate expired subscription.",
                "PERIOD_ENDED"
            )
        
        # Cannot reactivate if processing another change
        if state.is_processing:
            return ValidationResult(
                False,
                "Subscription change in progress. Please wait.",
                "PROCESSING_CHANGE"
            )
        
        # Must have Stripe subscription
        if not state.has_stripe_subscription:
            return ValidationResult(
                False,
                "No subscription found to reactivate",
                "NO_SUBSCRIPTION"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_refund(state: SubscriptionState, has_existing_refund: bool = False) -> ValidationResult:
        """
        Validate refund request
        
        Rules:
        1. Must have paid subscription
        2. Cannot request refund if already has pending or approved refund
        3. Cannot request refund on free plan
        4. Cannot refund if processing another change
        5. Subscription must have billing history (must have been charged)
        """
        # Cannot refund free plan
        if state.current_plan == 'free':
            return ValidationResult(
                False,
                "Cannot request refund for free plan",
                "NO_SUBSCRIPTION"
            )
        
        # Cannot request refund if already has one
        if has_existing_refund or state.has_pending_refund:
            return ValidationResult(
                False,
                "Already have a pending refund request",
                "REFUND_EXISTS"
            )
        
        # Cannot refund if processing another change
        if state.is_processing:
            return ValidationResult(
                False,
                "Subscription change in progress. Please wait.",
                "PROCESSING_CHANGE"
            )
        
        # Must have Stripe subscription
        if not state.has_stripe_subscription:
            return ValidationResult(
                False,
                "No subscription found to refund",
                "NO_SUBSCRIPTION"
            )
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_transition(current_state: SubscriptionState, action: str, target_plan: Optional[str] = None, **kwargs) -> ValidationResult:
        """
        Main validation entry point
        
        Args:
            current_state: Current subscription state
            action: Action to perform (subscribe, upgrade, downgrade, cancel, reactivate, refund)
            target_plan: Target plan for subscribe/upgrade/downgrade
            **kwargs: Additional context (e.g., has_existing_refund)
        
        Returns:
            ValidationResult indicating if transition is valid
        """
        action = action.lower()
        
        if action == 'subscribe':
            if not target_plan:
                return ValidationResult(False, "Target plan required for subscription", "MISSING_PLAN")
            return SubscriptionValidator.validate_subscribe(current_state, target_plan)
        
        elif action == 'upgrade':
            if not target_plan:
                return ValidationResult(False, "Target plan required for upgrade", "MISSING_PLAN")
            return SubscriptionValidator.validate_upgrade(current_state, target_plan)
        
        elif action == 'downgrade':
            if not target_plan:
                return ValidationResult(False, "Target plan required for downgrade", "MISSING_PLAN")
            return SubscriptionValidator.validate_downgrade(current_state, target_plan)
        
        elif action == 'cancel':
            return SubscriptionValidator.validate_cancel(current_state)
        
        elif action == 'reactivate':
            return SubscriptionValidator.validate_reactivate(current_state)
        
        elif action == 'refund':
            has_existing = kwargs.get('has_existing_refund', False)
            return SubscriptionValidator.validate_refund(current_state, has_existing)
        
        else:
            return ValidationResult(
                False,
                f"Unknown action: {action}",
                "INVALID_ACTION"
            )


def get_allowed_transitions(current_state: SubscriptionState) -> List[Dict]:
    """
    Get all valid transitions from current state
    
    Returns list of allowed actions with their targets
    """
    allowed = []
    validator = SubscriptionValidator()
    
    # Check subscribe (only if on free)
    if current_state.current_plan == 'free':
        for plan in ['starter', 'plus', 'pro', 'ultimate']:
            result = validator.validate_subscribe(current_state, plan)
            if result.valid:
                allowed.append({
                    'action': 'subscribe',
                    'target': plan,
                    'description': f'Subscribe to {plan.title()}'
                })
    
    # Check upgrades
    for plan in ['starter', 'plus', 'pro', 'ultimate']:
        result = validator.validate_upgrade(current_state, plan)
        if result.valid:
            allowed.append({
                'action': 'upgrade',
                'target': plan,
                'description': f'Upgrade to {plan.title()}'
            })
    
    # Check downgrades
    for plan in ['free', 'starter', 'plus', 'pro']:
        result = validator.validate_downgrade(current_state, plan)
        if result.valid:
            allowed.append({
                'action': 'downgrade',
                'target': plan,
                'description': f'Downgrade to {plan.title() if plan != "free" else "Starter"}'
            })
    
    # Check cancel
    result = validator.validate_cancel(current_state)
    if result.valid:
        allowed.append({
            'action': 'cancel',
            'target': None,
            'description': 'Cancel subscription'
        })
    
    # Check reactivate
    result = validator.validate_reactivate(current_state)
    if result.valid:
        allowed.append({
            'action': 'reactivate',
            'target': None,
            'description': 'Reactivate subscription'
        })
    
    # Check refund
    result = validator.validate_refund(current_state)
    if result.valid:
        allowed.append({
            'action': 'refund',
            'target': None,
            'description': 'Request refund'
        })
    
    return allowed

