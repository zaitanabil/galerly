// Protected route component
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireRole?: string;
}

export default function ProtectedRoute({ children, requireRole }: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F7]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[#1D1D1F]/60">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireRole && user?.role !== requireRole) {
    if (user?.role === 'client') {
      // Smart redirect: If trying to access a photographer gallery link, redirect to client view
      if (location.pathname.startsWith('/gallery/')) {
        const galleryId = location.pathname.split('/')[2];
        if (galleryId) {
          return <Navigate to={`/client-gallery/${galleryId}`} replace />;
        }
      }
      return <Navigate to="/client-dashboard" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

