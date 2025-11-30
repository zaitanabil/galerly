// Login page
import { useState, FormEvent, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserData } from '../utils/api';
import { Mail, Lock, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(user.role === 'client' ? '/client-dashboard' : '/dashboard');
  }
  }, [isAuthenticated, user, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);

    if (result.success) {
      // Check local data immediately after login success
      const userData = getUserData();
      const targetPath = userData?.role === 'client' ? '/client-dashboard' : '/dashboard';
      navigate(targetPath);
    } else {
      setError(result.error || 'Login failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20">
      {/* Background Elements */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100/30 rounded-full blur-[100px]" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-100/20 rounded-full blur-[120px]" />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <Link to="/" className="block text-center mb-8">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] tracking-tight">
            Galerly
          </h1>
          <p className="text-sm text-[#1D1D1F]/60 mt-2">Share art, not files.</p>
        </Link>

        {/* Form Card */}
        <div className="glass-panel p-8 md:p-10">
          <h2 className="text-2xl font-medium text-[#1D1D1F] mb-2">Welcome back</h2>
          <p className="text-sm text-[#1D1D1F]/60 mb-8">
            Sign in to your account to continue
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-gray-300 text-[#0066CC] focus:ring-[#0066CC]/20"
                />
                <span className="text-[#1D1D1F]/70">Remember me</span>
              </label>
              <Link
                to="/reset-password"
                className="text-[#0066CC] hover:text-[#0052A3] transition-colors"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-[#1D1D1F]/60">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-[#0066CC] font-medium hover:text-[#0052A3] transition-colors"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>

        {/* Trust Badge */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#1D1D1F]/40">
            Secured by AWS • SSL Encrypted • GDPR Ready
          </p>
        </div>
      </div>
    </div>
  );
}
