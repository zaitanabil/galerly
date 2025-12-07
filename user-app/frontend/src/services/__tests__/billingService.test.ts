/**
 * Tests for billingService
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as billingService from '../billingService';
import { api } from '../../utils/api';

// Mock API
vi.mock('../../utils/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

describe('billingService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getSubscription', () => {
    it('fetches subscription successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          plan: 'plus',
          status: 'active',
          subscription: {
            id: 'sub_123',
            user_id: 'user_123',
            status: 'active',
            plan: 'plus',
            current_period_end: '2025-01-01T00:00:00Z',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          }
        }
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await billingService.getSubscription();

      expect(api.get).toHaveBeenCalledWith('/billing/subscription');
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors', async () => {
      vi.mocked(api.get).mockResolvedValue({
        success: false,
        error: 'Failed to fetch subscription'
      });

      const result = await billingService.getSubscription();

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('getUsage', () => {
    it('fetches usage data successfully', async () => {
      const mockUsage = {
        success: true,
        data: {
          plan: {
            plan: 'plus',
            plan_name: 'Plus',
            galleries_per_month: -1,
            storage_gb: 100
          },
          storage_limit: {
            used_gb: 50,
            limit_gb: 100,
            remaining_gb: 50,
            usage_percent: 50
          },
          gallery_limit: {
            used: 10,
            limit: -1,
            remaining: -1,
            allowed: true
          },
          video_limit: {
            used_minutes: 30,
            limit_minutes: 60,
            remaining_minutes: 30,
            usage_percent: 50,
            allowed: true,
            quality: 'hd',
            video_count: 5
          }
        }
      };

      vi.mocked(api.get).mockResolvedValue(mockUsage);

      const result = await billingService.getUsage();

      expect(api.get).toHaveBeenCalledWith('/subscription/usage');
      expect(result.data).toHaveProperty('storage_limit');
      expect(result.data).toHaveProperty('gallery_limit');
      expect(result.data).toHaveProperty('video_limit');
      expect(result.data.video_limit!.quality).toBe('hd');
    });

    it('includes video_limit in response', async () => {
      const mockResponse = {
        success: true,
        data: {
          plan: { plan: 'starter', plan_name: 'Starter', galleries_per_month: -1, storage_gb: 25 },
          storage_limit: { used_gb: 10, limit_gb: 25, remaining_gb: 15, usage_percent: 40 },
          gallery_limit: { used: 5, limit: -1, remaining: -1, allowed: true },
          video_limit: {
            used_minutes: 15,
            limit_minutes: 30,
            remaining_minutes: 15,
            usage_percent: 50,
            allowed: true,
            quality: 'hd',
            video_count: 3
          }
        }
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await billingService.getUsage();

      expect(result.data.video_limit).toBeDefined();
      expect(result.data.video_limit!.used_minutes).toBe(15);
      expect(result.data.video_limit!.limit_minutes).toBe(30);
      expect(result.data.video_limit!.quality).toBe('hd');
      expect(result.data.video_limit!.video_count).toBe(3);
    });
  });

  describe('getBillingHistory', () => {
    it('fetches billing history successfully', async () => {
      const mockHistory = {
        success: true,
        data: {
          invoices: [
            {
              id: 'inv_123',
              amount: 2900,
              currency: 'usd',
              status: 'paid',
              created_at: '2024-01-01T00:00:00Z'
            }
          ],
          total: 1
        }
      };

      vi.mocked(api.get).mockResolvedValue(mockHistory);

      const result = await billingService.getBillingHistory();

      expect(api.get).toHaveBeenCalledWith('/billing/history');
      expect(result.data.invoices).toHaveLength(1);
      expect(result.data.invoices[0].status).toBe('paid');
    });

    it('handles empty history', async () => {
      vi.mocked(api.get).mockResolvedValue({
        success: true,
        data: { invoices: [], total: 0 }
      });

      const result = await billingService.getBillingHistory();

      expect(result.data.invoices).toEqual([]);
    });
  });

  describe('cancelSubscription', () => {
    it('cancels subscription successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          message: 'Subscription canceled',
          cancel_at_period_end: true
        }
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await billingService.cancelSubscription();

      expect(api.post).toHaveBeenCalledWith('/billing/subscription/cancel');
      expect(result.success).toBe(true);
    });

    it('handles cancellation errors', async () => {
      vi.mocked(api.post).mockResolvedValue({
        success: false,
        error: 'Cannot cancel subscription'
      });

      const result = await billingService.cancelSubscription();

      expect(result.success).toBe(false);
    });
  });

  describe('createCheckoutSession', () => {
    it('creates checkout session successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          sessionId: 'cs_test_123',
          url: 'https://checkout.stripe.com/pay/cs_test_123'
        }
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await billingService.createCheckoutSession('plus', 'annual');

      expect(api.post).toHaveBeenCalledWith('/billing/checkout', {
        plan: 'plus',
        interval: 'annual'
      });
      expect(result.data.url).toBeDefined();
    });

    it('handles invalid plan', async () => {
      vi.mocked(api.post).mockResolvedValue({
        success: false,
        error: 'Invalid plan'
      });

      const result = await billingService.createCheckoutSession('invalid_plan', 'monthly');

      expect(result.success).toBe(false);
    });
  });

  describe('checkRefundEligibility', () => {
    it('checks refund eligibility', async () => {
      const mockResponse = {
        success: true,
        data: {
          eligible: true
        }
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await billingService.checkRefundEligibility();

      expect(api.get).toHaveBeenCalledWith('/billing/refund/check');
      expect(result.data.eligible).toBe(true);
    });
  });

  describe('TypeScript interfaces', () => {
    it('UsageStats interface includes video_limit', () => {
      const usage: billingService.UsageStats = {
        plan: {
          plan: 'plus',
          plan_name: 'Plus',
          galleries_per_month: -1,
          storage_gb: 100
        },
        storage_limit: {
          used_gb: 50,
          limit_gb: 100,
          remaining_gb: 50,
          usage_percent: 50
        },
        gallery_limit: {
          used: 10,
          limit: -1,
          remaining: -1,
          allowed: true
        },
        video_limit: {
          used_minutes: 30,
          limit_minutes: 60,
          remaining_minutes: 30,
          usage_percent: 50,
          allowed: true,
          quality: 'hd',
          video_count: 5
        }
      };

      expect(usage.video_limit?.quality).toBe('hd');
      expect(usage.video_limit?.video_count).toBe(5);
    });

    it('Invoice interface structure is correct', () => {
      const invoice: billingService.Invoice = {
        id: 'inv_123',
        amount: 2900,
        currency: 'usd',
        status: 'paid',
        created_at: '2024-01-01T00:00:00Z'
      };

      expect(invoice.amount).toBe(2900);
      expect(invoice.status).toBe('paid');
    });
  });
});
