import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';

// Mock the API module
vi.mock('../../services/api', () => ({
  default: {
    getDashboardStats: vi.fn()
  }
}));

import adminAPI from '../../services/api';

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (adminAPI.getDashboardStats as any).mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    // Check for loading spinner
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeTruthy();
  });

  it('renders dashboard stats after loading', async () => {
    const mockStats = {
      total_users: 150,
      total_photographers: 45,
      total_clients: 105,
      total_galleries: 230,
      total_photos: 12500,
      active_subscriptions: 38,
      monthly_recurring_revenue: 1450,
      recent_activity_24h: 234
    };

    (adminAPI.getDashboardStats as any).mockResolvedValue(mockStats);
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // total users
    });
  });

  it('shows error state when API fails', async () => {
    (adminAPI.getDashboardStats as any).mockRejectedValue(new Error('API Error'));
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
    });
  });

  it('displays quick action links', async () => {
    (adminAPI.getDashboardStats as any).mockResolvedValue({
      total_users: 150,
      total_photographers: 45,
      total_clients: 105,
      total_galleries: 230,
      total_photos: 12500,
      active_subscriptions: 38,
      monthly_recurring_revenue: 1450,
      recent_activity_24h: 234
    });
    
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('View All Users')).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

