// API Connection Test Page - verify frontend-backend connection
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';
import * as galleryService from '../services/galleryService';
import * as publicService from '../services/publicService';
import { CheckCircle, XCircle, Loader } from 'lucide-react';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message?: string;
  duration?: number;
}

export default function ApiTestPage() {
  const { user, isAuthenticated } = useAuth();
  const [results, setResults] = useState<TestResult[]>([]);
  const [testing, setTesting] = useState(false);

  const updateResult = (name: string, updates: Partial<TestResult>) => {
    setResults(prev => {
      const index = prev.findIndex(r => r.name === name);
      if (index >= 0) {
        const newResults = [...prev];
        newResults[index] = { ...newResults[index], ...updates };
        return newResults;
      }
      return [...prev, { name, status: 'pending', ...updates }];
    });
  };

  const runTest = async (name: string, testFn: () => Promise<unknown>) => {
    const startTime = Date.now();
    updateResult(name, { status: 'pending' });

    try {
      const response = await testFn() as { success: boolean; error?: string };
      const duration = Date.now() - startTime;
      
      if (response.success) {
        updateResult(name, {
          status: 'success',
          message: 'OK',
          duration,
        });
      } else {
        updateResult(name, {
          status: 'error',
          message: response.error || 'Failed',
          duration,
        });
      }
    } catch (error) {
      const duration = Date.now() - startTime;
      updateResult(name, {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
        duration,
      });
    }
  };

  const runAllTests = async () => {
    setTesting(true);
    setResults([]);

    // Test 1: Health check
    await runTest('Health Check', () => api.get('/health'));

    // Test 2: Auth status
    await runTest('Auth Status (/auth/me)', () => api.get('/auth/me'));

    // Test 3: City search (public)
    await runTest('City Search', () => publicService.searchCities('New'));

    // Test 4: Photographers list (public)
    await runTest('Photographers List', () => publicService.listPhotographers({ limit: 5 }));

    // Only test authenticated endpoints if logged in
    if (isAuthenticated) {
      // Test 5: List galleries
      await runTest('List Galleries', () => galleryService.listGalleries({ limit: 10 }));

      // Test 6: Dashboard stats
      await runTest('Dashboard Stats', () => api.get('/dashboard/stats'));

      // Test 7: Subscription info
      await runTest('Subscription Info', () => api.get('/billing/subscription'));

      // Test 8: Usage stats
      await runTest('Usage Stats', () => api.get('/billing/usage'));
    }

    setTesting(false);
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return <Loader className="w-5 h-5 text-gray-400 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />;
    }
  };

  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;
  const totalCount = results.length;

  return (
    <div className="min-h-screen bg-[#F5F5F7] px-6 py-12">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] mb-2">
            API Connection Test
          </h1>
          <p className="text-lg text-[#1D1D1F]/60">
            Test the connection between React frontend and backend
          </p>
        </div>

        {/* User Info */}
        <div className="glass-panel p-6 mb-6">
          <h2 className="text-lg font-medium text-[#1D1D1F] mb-3">User Status</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-[#1D1D1F]/60">Authenticated:</span>
              <span className={isAuthenticated ? 'text-green-600' : 'text-red-600'}>
                {isAuthenticated ? 'Yes' : 'No'}
              </span>
            </div>
            {user && (
              <>
                <div className="flex justify-between">
                  <span className="text-[#1D1D1F]/60">Name:</span>
                  <span className="text-[#1D1D1F]">{user.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#1D1D1F]/60">Email:</span>
                  <span className="text-[#1D1D1F]">{user.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#1D1D1F]/60">Role:</span>
                  <span className="text-[#1D1D1F]">{user.role}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Test Controls */}
        <div className="glass-panel p-6 mb-6">
          <button
            onClick={runAllTests}
            disabled={testing}
            className="w-full py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {testing ? 'Running Tests...' : 'Run All Tests'}
          </button>
        </div>

        {/* Test Results Summary */}
        {results.length > 0 && (
          <div className="glass-panel p-6 mb-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-medium text-[#1D1D1F]">{totalCount}</p>
                <p className="text-sm text-[#1D1D1F]/60">Total</p>
              </div>
              <div>
                <p className="text-2xl font-medium text-green-600">{successCount}</p>
                <p className="text-sm text-[#1D1D1F]/60">Passed</p>
              </div>
              <div>
                <p className="text-2xl font-medium text-red-600">{errorCount}</p>
                <p className="text-sm text-[#1D1D1F]/60">Failed</p>
              </div>
            </div>
          </div>
        )}

        {/* Test Results */}
        {results.length > 0 && (
          <div className="glass-panel divide-y divide-gray-200">
            {results.map((result) => (
              <div key={result.name} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    {getStatusIcon(result.status)}
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-[#1D1D1F] mb-1">
                        {result.name}
                      </h3>
                      {result.message && (
                        <p className={`text-xs ${
                          result.status === 'error' ? 'text-red-600' : 'text-[#1D1D1F]/60'
                        }`}>
                          {result.message}
                        </p>
                      )}
                    </div>
                  </div>
                  {result.duration && (
                    <span className="text-xs text-[#1D1D1F]/40">
                      {result.duration}ms
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Instructions */}
        {results.length === 0 && !testing && (
          <div className="glass-panel p-8 text-center">
            <p className="text-[#1D1D1F]/60 mb-4">
              Click "Run All Tests" to verify the API connection
            </p>
            <p className="text-sm text-[#1D1D1F]/40">
              {isAuthenticated 
                ? 'All endpoints will be tested'
                : 'Login to test authenticated endpoints'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

