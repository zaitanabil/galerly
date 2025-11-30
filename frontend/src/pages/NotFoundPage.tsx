// 404 Not Found page
import { Link } from 'react-router-dom';
import { Home, Search } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function NotFoundPage() {
  const { user } = useAuth();
  const dashboardLink = user?.role === 'client' ? '/client-dashboard' : '/dashboard';

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      {/* Background Elements */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100/30 rounded-full blur-[100px]" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-100/20 rounded-full blur-[120px]" />

      <div className="relative z-10 text-center max-w-2xl mx-auto">
        {/* 404 Number */}
        <div className="mb-8">
          <h1 className="text-[200px] leading-none font-serif font-medium text-[#1D1D1F]/10 select-none">
            404
          </h1>
        </div>

        {/* Content */}
        <div className="glass-panel p-12 -mt-32">
          <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Search className="w-8 h-8 text-[#0066CC]" />
          </div>
          
          <h2 className="text-3xl font-serif font-medium text-[#1D1D1F] mb-4">
            Page not found
          </h2>
          
          <p className="text-lg text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
            The page you're looking for doesn't exist or has been moved.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-105 shadow-lg shadow-blue-500/20"
            >
              <Home className="w-5 h-5" />
              Back to Home
            </Link>
            
            <Link
              to={dashboardLink}
              className="inline-flex items-center gap-2 px-8 py-4 bg-white/50 border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-white transition-all"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>

        {/* Help Text */}
        <p className="mt-8 text-sm text-[#1D1D1F]/40">
          If you believe this is an error, please contact support
        </p>
      </div>
    </div>
  );
}

