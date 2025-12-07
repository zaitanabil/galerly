import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { adminAPI } from '../api';

// Mock fetch
global.fetch = vi.fn();

describe('Admin API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDashboardStats', () => {
    it('fetches dashboard statistics', async () => {
      const mockStats = {
        total_users: 150,
        total_photographers: 45,
        total_galleries: 230,
        active_subscriptions: 38,
        monthly_recurring_revenue: 1450
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      });

      const result = await adminAPI.getDashboardStats();
      
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5002/api/dashboard/stats');
      expect(result).toEqual(mockStats);
    });

    it('throws error on failed request', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error'
      });

      await expect(adminAPI.getDashboardStats()).rejects.toThrow('API Error: Internal Server Error');
    });
  });

  describe('getUsers', () => {
    it('fetches users without parameters', async () => {
      const mockUsers = {
        users: [{ id: '1', email: 'test@example.com', name: 'Test User' }],
        count: 1
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers
      });

      const result = await adminAPI.getUsers();
      
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5002/api/users');
      expect(result).toEqual(mockUsers);
    });

    it('fetches users with filters', async () => {
      const mockUsers = { users: [], count: 0 };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers
      });

      await adminAPI.getUsers({ role: 'photographer', plan: 'plus' });
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5002/api/users?role=photographer&plan=plus'
      );
    });
  });

  describe('getUserDetails', () => {
    it('fetches user details by ID', async () => {
      const userId = 'user-123';
      const mockUserDetails = {
        user: { id: userId, email: 'test@example.com' },
        galleries: [],
        subscription: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUserDetails
      });

      const result = await adminAPI.getUserDetails(userId);
      
      expect(global.fetch).toHaveBeenCalledWith(`http://localhost:5002/api/users/${userId}`);
      expect(result).toEqual(mockUserDetails);
    });
  });

  describe('getActivity', () => {
    it('fetches activity with default parameters', async () => {
      const mockActivity = {
        activities: [{ action: 'login', timestamp: '2025-12-05T10:00:00Z' }],
        count: 1
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockActivity
      });

      const result = await adminAPI.getActivity();
      
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5002/api/activity');
      expect(result).toEqual(mockActivity);
    });

    it('fetches activity with custom parameters', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ activities: [], count: 0 })
      });

      await adminAPI.getActivity({ hours: 48, limit: 50 });
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5002/api/activity?hours=48&limit=50'
      );
    });
  });

  describe('getRevenueStats', () => {
    it('fetches revenue statistics', async () => {
      const mockRevenue = {
        total_revenue: 5000,
        monthly_revenue: { '2025-12': 1500 },
        revenue_by_plan: { plus: 1200, pro: 3800 }
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRevenue
      });

      const result = await adminAPI.getRevenueStats();
      
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5002/api/revenue');
      expect(result).toEqual(mockRevenue);
    });
  });

  describe('getSubscriptions', () => {
    it('fetches all subscriptions', async () => {
      const mockSubs = {
        subscriptions: [{ plan: 'plus', status: 'active' }],
        count: 1,
        by_plan: { plus: 1 }
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSubs
      });

      const result = await adminAPI.getSubscriptions();
      
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:5002/api/subscriptions');
      expect(result).toEqual(mockSubs);
    });

    it('fetches subscriptions with status filter', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscriptions: [], count: 0, by_plan: {} })
      });

      await adminAPI.getSubscriptions('canceled');
      
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:5002/api/subscriptions?status=canceled'
      );
    });
  });
});

