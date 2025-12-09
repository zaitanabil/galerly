import React, { useState } from 'react';
import { AlertTriangle, Clock, CheckCircle } from 'lucide-react';

interface AccountRestorationPromptProps {
  email: string;
  daysRemaining: number;
  deletionDate: string;
  onRestore: (email: string, password: string) => Promise<void>;
  onCancel: () => void;
}

/**
 * Modal shown when user tries to login to account pending deletion
 * Allows restoration within 30-day grace period
 */
export default function AccountRestorationPrompt({
  email,
  daysRemaining,
  deletionDate,
  onRestore,
  onCancel
}: AccountRestorationPromptProps) {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRestore = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!password) {
      setError('Password is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onRestore(email, password);
      // Success handled by parent component (redirect to dashboard)
    } catch (err: any) {
      setError(err.message || 'Failed to restore account. Please try again.');
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-orange-100 rounded-full">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
            <h2 className="text-xl font-semibold text-[#1D1D1F]">
              Account Scheduled for Deletion
            </h2>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-6">
            <div className="flex items-center gap-2 text-orange-600 mb-3">
              <Clock className="w-5 h-5" />
              <span className="font-medium">
                {daysRemaining} day{daysRemaining !== 1 ? 's' : ''} remaining
              </span>
            </div>
            
            <p className="text-[#1D1D1F]/70 mb-4">
              Your account was scheduled for deletion and will be permanently removed on{' '}
              <strong>{formatDate(deletionDate)}</strong>.
            </p>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg mb-4">
              <p className="text-sm text-blue-900">
                <strong>Good news!</strong> You can still restore your account. 
                All your data is safe and will be restored immediately.
              </p>
            </div>

            <form onSubmit={handleRestore}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Confirm your password to restore
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError('');
                  }}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 bg-white/50 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                  autoFocus
                />
                <p className="text-xs text-[#1D1D1F]/50 mt-1">
                  Logging in as: <strong>{email}</strong>
                </p>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onCancel}
                  disabled={loading}
                  className="flex-1 px-4 py-3 text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] border border-gray-300 rounded-xl transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !password}
                  className="flex-1 px-4 py-3 bg-[#0066CC] text-white text-sm font-medium rounded-xl hover:bg-[#0052A3] transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Restoring...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Restore Account
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <p className="text-xs text-[#1D1D1F]/50">
              <strong>What happens if you restore:</strong> Your account will be immediately reactivated 
              with all your galleries, photos, and settings intact. You'll be logged in automatically.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

