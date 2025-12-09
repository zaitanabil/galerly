import { Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp } from 'lucide-react';
import SEODashboard from '../components/SEODashboard';
import { useAuth } from '../contexts/AuthContext';

export default function SEOPage() {
  const { user } = useAuth();
  
  // Check if user has access to SEO tools
  const hasAccess = user?.plan === 'pro' || user?.plan === 'ultimate';

  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-[#F5F5F7]">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link to="/dashboard" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                  <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
                </Link>
                <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                  SEO Tools
                </h1>
              </div>
              <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
                Galerly
              </Link>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-6 py-12">
          <div className="glass-panel p-12 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <TrendingUp className="w-8 h-8 text-[#0066CC]" />
            </div>
            <h2 className="text-2xl font-medium text-[#1D1D1F] mb-4">
              SEO Tools
            </h2>
            <p className="text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
              Advanced SEO optimization tools are available on Pro and Ultimate plans.
            </p>
            <Link
              to="/billing"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all shadow-lg shadow-blue-500/20"
            >
              Upgrade to Pro
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/dashboard" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                <ArrowLeft className="w-5 h-5 text-[#1D1D1F]" />
              </Link>
              <h1 className="text-xl font-serif font-medium text-[#1D1D1F]">
                SEO Tools
              </h1>
            </div>
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <SEODashboard />
      </main>
    </div>
  );
}
