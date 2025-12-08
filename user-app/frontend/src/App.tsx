import { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { useVisitorTracking } from './hooks/useVisitorTracking';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

import MouseFollower from './components/MouseFollower';
import GrainOverlay from './components/GrainOverlay';
import GridBackground from './components/GridBackground';

// Lazy Load Pages
const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const NewGalleryPage = lazy(() => import('./pages/NewGalleryPage'));
const GalleryPage = lazy(() => import('./pages/GalleryPage'));
const ProfileSettingsPage = lazy(() => import('./pages/ProfileSettingsPage'));
const BillingPage = lazy(() => import('./pages/BillingPage'));
const EmailTemplatesPage = lazy(() => import('./pages/EmailTemplatesPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const GalleriesPage = lazy(() => import('./pages/GalleriesPage'));
const ContactPage = lazy(() => import('./pages/ContactPage'));
const FAQPage = lazy(() => import('./pages/FAQPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const LegalNoticePage = lazy(() => import('./pages/LegalNoticePage'));
const PricingPage = lazy(() => import('./pages/PricingPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const PhotographersPage = lazy(() => import('./pages/PhotographersPage'));
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'));
const ClientDashboardPage = lazy(() => import('./pages/ClientDashboardPage'));
const ClientGalleryPage = lazy(() => import('./pages/ClientGalleryPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
const ApiTestPage = lazy(() => import('./pages/ApiTestPage'));
const InvoicesPage = lazy(() => import('./pages/InvoicesPage'));
const SchedulerPage = lazy(() => import('./pages/SchedulerPage'));
const ContractsPage = lazy(() => import('./pages/ContractsPage'));
const SignContractPage = lazy(() => import('./pages/SignContractPage'));
const PublicBookingPage = lazy(() => import('./pages/PublicBookingPage'));
const RAWVaultPage = lazy(() => import('./pages/RAWVaultPage'));
const EmailAutomationPage = lazy(() => import('./pages/EmailAutomationPage'));
const CRMPage = lazy(() => import('./pages/CRMPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const NotificationPreferencesPage = lazy(() => import('./pages/NotificationPreferencesPage'));

// Loading Fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-[#F5F5F7]">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-sm text-[#1D1D1F]/60">Loading...</p>
    </div>
  </div>
);

// Tracking component to use inside Router
function VisitorTracker() {
  useVisitorTracking();
  return null;
}

// Components
import CookieConsent from './components/CookieConsent';

function App() {
  return (
    <ErrorBoundary>
    <AuthProvider>
      <Router>
        <VisitorTracker />
        <CookieConsent />
        <div className="min-h-screen bg-transparent text-[#1D1D1F] selection:bg-[#0066CC] selection:text-white">
          {/* Global Interactive Elements */}
          <MouseFollower />
          <GrainOverlay />
          <GridBackground />
          
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HomePage />} />
            <Route path="/start" element={<Navigate to="/register" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/faq" element={<FAQPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/legal" element={<LegalNoticePage />} />
            <Route path="/photographers" element={<PhotographersPage />} />
            <Route path="/portfolio/:userId" element={<PortfolioPage />} />
              
              {/* API Test Route (dev only) */}
              <Route path="/api-test" element={<ApiTestPage />} />
            
            {/* Public Signing Route */}
            <Route path="/sign-contract/:contractId" element={<SignContractPage />} />
            
            {/* Public Booking Route */}
            <Route path="/book/:userId" element={<PublicBookingPage />} />
            
            {/* Client Routes */}
            <Route
              path="/client-dashboard"
              element={
                <ProtectedRoute requireRole="client">
                  <ClientDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="/client-gallery/:galleryId" element={<ClientGalleryPage />} />
            <Route path="/client-gallery" element={<ClientGalleryPage />} /> {/* Token-based access via query param */}
            
            {/* Photographer Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute requireRole="photographer">
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/new-gallery"
              element={
                <ProtectedRoute requireRole="photographer">
                  <NewGalleryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/gallery/:galleryId"
              element={
                <ProtectedRoute requireRole="photographer">
                  <GalleryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/galleries"
              element={
                <ProtectedRoute requireRole="photographer">
                  <GalleriesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfileSettingsPage />
                </ProtectedRoute>
              }
            />
            {/* Redirect /settings to /profile */}
            <Route path="/settings" element={<Navigate to="/profile" replace />} />
            <Route
              path="/billing"
              element={
                <ProtectedRoute requireRole="photographer">
                  <BillingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/email-templates"
              element={
                <ProtectedRoute requireRole="photographer">
                  <EmailTemplatesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute requireRole="photographer">
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/invoices"
              element={
                <ProtectedRoute requireRole="photographer">
                  <InvoicesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/scheduler"
              element={
                <ProtectedRoute requireRole="photographer">
                  <SchedulerPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contracts"
              element={
                <ProtectedRoute requireRole="photographer">
                  <ContractsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/raw-vault"
              element={
                <ProtectedRoute requireRole="photographer">
                  <RAWVaultPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/email-automation"
              element={
                <ProtectedRoute requireRole="photographer">
                  <EmailAutomationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/crm"
              element={
                <ProtectedRoute requireRole="photographer">
                  <CRMPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings/notifications"
              element={
                <ProtectedRoute>
                  <NotificationPreferencesPage />
                </ProtectedRoute>
              }
            />
            
              {/* 404 */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </div>
      </Router>
    </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
