// Billing service - handles subscription and payment operations
import { api } from '../utils/api';

export interface SubscriptionDetails {
  id: string;
  user_id: string;
  stripe_subscription_id?: string;
  stripe_customer_id?: string;
  plan: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  subscription: SubscriptionDetails | null;
  plan: string;
  status: string;
  plan_details?: Record<string, unknown>;
  pending_plan?: string;
  pending_plan_change_at?: string;
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  invoice_pdf?: string;
  created_at: string;
}

export interface UsageStats {
  galleries_count: number;
  photos_count: number;
  storage_used: number;
  tier_limits: {
    max_galleries: number;
    max_photos_per_gallery: number;
    max_storage_gb: number;
  };
}

// Create Stripe checkout session
export async function createCheckoutSession(planId: string) {
  // Backend expects 'plan' in the body (e.g., 'plus', 'pro')
  return api.post<{ sessionId: string; url: string }>('/billing/checkout', {
    plan: planId,
  });
}

// Get current subscription
export async function getSubscription() {
  return api.get<Subscription>('/billing/subscription');
}

// Cancel subscription
export async function cancelSubscription() {
  return api.post('/billing/subscription/cancel');
}

// Change plan
export async function changePlan(newPlan: string, priceId: string) {
  return api.post('/billing/subscription/change-plan', {
    plan: newPlan,
    price_id: priceId,
  });
}

// Check downgrade limits
export async function checkDowngradeLimits(targetPlan: string) {
  return api.get<{ can_downgrade: boolean; issues: string[] }>(
    `/billing/subscription/check-downgrade?target_plan=${targetPlan}`
  );
}

// Downgrade subscription
export async function downgradeSubscription(targetPlan: string) {
  return api.post('/billing/subscription/downgrade', {
    target_plan: targetPlan,
  });
}

// Get billing history
export async function getBillingHistory(params?: { page?: number; limit?: number }) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  
  const queryString = queryParams.toString();
  const endpoint = queryString ? `/billing/history?${queryString}` : '/billing/history';
  
  return api.get<{ invoices: Invoice[]; total: number }>(endpoint);
}

// Get invoice PDF
export async function getInvoicePdf(invoiceId: string) {
  return api.get<{ pdf_url: string }>(`/billing/invoice/${invoiceId}/pdf`);
}

// Get usage stats
export async function getUsage() {
  return api.get<UsageStats>('/subscription/usage');
}

// Refund operations
export async function checkRefundEligibility() {
  return api.get<{ eligible: boolean; reason?: string }>('/billing/refund/check');
}

export async function requestRefund(reason: string) {
  return api.post('/billing/refund/request', { reason });
}

export async function getRefundStatus() {
  return api.get('/billing/refund/status');
}

export default {
  createCheckoutSession,
  getSubscription,
  cancelSubscription,
  changePlan,
  checkDowngradeLimits,
  downgradeSubscription,
  getBillingHistory,
  getInvoicePdf,
  getUsage,
  checkRefundEligibility,
  requestRefund,
  getRefundStatus,
};
