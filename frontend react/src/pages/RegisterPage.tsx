// Register page with 2-step email verification
import { useState, FormEvent, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, User, Camera, Users, AlertCircle, Check, ArrowLeft } from 'lucide-react';
import { api } from '../utils/api';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuth();
  
  // 2-step verification state
  const [step, setStep] = useState<1 | 2>(1); // 1 = form, 2 = verify code
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'photographer',
  });
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationToken, setVerificationToken] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(user.role === 'client' ? '/client-dashboard' : '/dashboard');
  }
  }, [isAuthenticated, user, navigate]);

  // STEP 1: Request verification code
  const handleRequestVerification = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post<{ verification_token: string }>('/auth/request-verification', {
        email: formData.email,
      });

      if (response.success && response.data) {
        setVerificationToken(response.data.verification_token || '');
        setSuccess(`Verification code sent to ${formData.email}. Please check your inbox.`);
        setStep(2);
      } else {
        setError(response.error || 'Failed to send verification code');
      }
    } catch (err) {
      setError((err as Error).message || 'Failed to send verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // STEP 2: Verify code and complete registration
  const handleVerifyAndRegister = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter the 6-digit verification code');
      return;
    }

    setLoading(true);

    try {
      // Step 2a: Verify the code
      const verifyResponse = await api.post<{ verification_token: string }>('/auth/verify-email', {
        verification_token: verificationToken,
        code: verificationCode,
      });

      if (!verifyResponse.success) {
        setError(verifyResponse.error || 'Invalid verification code');
        setLoading(false);
        return;
      }

      // Get the new verification token from verify response
      const newToken = verifyResponse.data?.verification_token || verificationToken;

      // Step 2b: Complete registration
      const username = formData.name || formData.email.split('@')[0];
      const registerResponse = await api.post('/auth/register', {
        email: formData.email,
        username: username,
        password: formData.password,
        role: formData.role,
        verification_token: newToken,
      });

      if (!registerResponse.success) {
        setError(registerResponse.error || 'Registration failed');
        setLoading(false);
        return;
      }

      // Success! Show message and redirect
      setSuccess('Account created successfully! Redirecting...');

      // Auto-login after registration
      setTimeout(async () => {
        try {
          const loginResponse = await api.post('/auth/login', {
            email: formData.email,
            password: formData.password,
          });

          if (loginResponse.success) {
            // Check for plan parameter
            const plan = searchParams.get('plan');
            if (plan && plan !== 'free') {
              window.location.href = `/billing?plan=${plan}`;
            } else {
              const role = formData.role;
              window.location.href = role === 'client' ? '/client-dashboard' : '/dashboard';
            }
          } else {
            // If auto-login fails, redirect to login page
            navigate('/login');
          }
        } catch {
          // If auto-login fails, redirect to login page
          navigate('/login');
        }
      }, 1500);

    } catch (err) {
      setError((err as Error).message || 'Verification failed. Please try again.');
      setLoading(false);
    }
  };

  // Resend verification code
  const handleResendCode = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await api.post<{ verification_token: string }>('/auth/request-verification', {
        email: formData.email,
      });

      if (response.success && response.data) {
        setVerificationToken(response.data.verification_token || '');
        setSuccess('New verification code sent!');
    } else {
        setError(response.error || 'Failed to resend code');
      }
    } catch (err) {
      setError((err as Error).message || 'Failed to resend code');
    } finally {
      setLoading(false);
    }
  };

  // Go back to step 1
  const handleBackToForm = () => {
    setStep(1);
    setVerificationCode('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20">
      {/* Background Elements */}
      <div className="absolute top-20 right-10 w-72 h-72 bg-blue-100/30 rounded-full blur-[100px]" />
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-purple-100/20 rounded-full blur-[120px]" />

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
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className={`w-2 h-2 rounded-full ${step === 1 ? 'bg-[#0066CC]' : 'bg-gray-300'}`} />
            <div className={`w-2 h-2 rounded-full ${step === 2 ? 'bg-[#0066CC]' : 'bg-gray-300'}`} />
          </div>

          <h2 className="text-2xl font-medium text-[#1D1D1F] mb-2">
            {step === 1 ? 'Create account' : 'Verify your email'}
          </h2>
          <p className="text-sm text-[#1D1D1F]/60 mb-8">
            {step === 1 
              ? 'Start sharing beautiful galleries today'
              : `Enter the code we sent to ${formData.email}`
            }
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-100 rounded-2xl flex items-start gap-3">
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          {/* STEP 1: Registration Form */}
          {step === 1 && (
            <form onSubmit={handleRequestVerification} className="space-y-5">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                <input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                I am a
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, role: 'photographer' })}
                  className={`p-4 rounded-2xl border-2 transition-all ${
                    formData.role === 'photographer'
                      ? 'border-[#0066CC] bg-blue-50'
                      : 'border-gray-200 bg-white/50 hover:border-gray-300'
                  }`}
                >
                  <Camera className="w-6 h-6 mx-auto mb-2 text-[#0066CC]" />
                  <p className="text-sm font-medium text-[#1D1D1F]">Photographer</p>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, role: 'client' })}
                  className={`p-4 rounded-2xl border-2 transition-all ${
                    formData.role === 'client'
                      ? 'border-[#0066CC] bg-blue-50'
                      : 'border-gray-200 bg-white/50 hover:border-gray-300'
                  }`}
                >
                  <Users className="w-6 h-6 mx-auto mb-2 text-[#0066CC]" />
                  <p className="text-sm font-medium text-[#1D1D1F]">Client</p>
                </button>
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
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                    minLength={8}
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                <input
                  id="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  required
                  className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20"
            >
                {loading ? 'Sending code...' : 'Continue'}
              </button>
            </form>
          )}

          {/* STEP 2: Verification Code */}
          {step === 2 && (
            <form onSubmit={handleVerifyAndRegister} className="space-y-5">
              <div>
                <label htmlFor="code" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                  Verification Code
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
                  <input
                    id="code"
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    required
                    maxLength={6}
                    pattern="[0-9]{6}"
                    inputMode="numeric"
                    autoComplete="off"
                    autoFocus
                    className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all text-center tracking-widest text-2xl font-mono"
                    placeholder="000000"
                  />
                </div>
                <p className="mt-2 text-xs text-[#1D1D1F]/60 text-center">
                  Enter the 6-digit code sent to your email
                </p>
              </div>

              <div className="flex items-center justify-center gap-2">
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={loading}
                  className="text-sm text-[#0066CC] font-medium hover:text-[#0052A3] transition-colors disabled:opacity-50"
                >
                  Resend code
                </button>
                <span className="text-[#1D1D1F]/40">•</span>
                <button
                  type="button"
                  onClick={handleBackToForm}
                  disabled={loading}
                  className="text-sm text-[#0066CC] font-medium hover:text-[#0052A3] transition-colors disabled:opacity-50 flex items-center gap-1"
                >
                  <ArrowLeft className="w-3 h-3" />
                  Change email
                </button>
              </div>

              <button
                type="submit"
                disabled={loading || verificationCode.length !== 6}
                className="w-full py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20"
              >
                {loading ? 'Verifying...' : 'Verify & Create Account'}
            </button>
          </form>
          )}

          <div className="mt-8 text-center">
            <p className="text-sm text-[#1D1D1F]/60">
              Already have an account?{' '}
              <Link
                to={`/login${searchParams.toString() ? `?${searchParams.toString()}` : ''}`}
                className="text-[#0066CC] font-medium hover:text-[#0052A3] transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Trust Badge */}
        <div className="mt-8 text-center">
          <p className="text-xs text-[#1D1D1F]/40">
            By creating an account, you agree to our Terms and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
