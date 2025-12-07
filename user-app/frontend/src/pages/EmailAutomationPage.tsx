import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, Clock, CheckCircle, XCircle, Calendar, AlertCircle, Trash2 } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { useBrandedModal } from '../components/BrandedModal';

interface ScheduledEmail {
  id: string;
  gallery_id: string;
  email_type: string;
  recipient_email: string;
  scheduled_time: string;
  status: 'scheduled' | 'sent' | 'failed' | 'cancelled';
  created_at: string;
  sent_at?: string;
  attempts?: number;
  error?: string;
}

export default function EmailAutomationPage() {
  const { user } = useAuth();
  const { showConfirm, ModalComponent } = useBrandedModal();
  const [scheduledEmails, setScheduledEmails] = useState<ScheduledEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Check if user has access to email automation
  const hasAccess = user?.plan === 'pro' || user?.plan === 'ultimate';

  useEffect(() => {
    if (hasAccess) {
      loadScheduledEmails();
    } else {
      setLoading(false);
    }
  }, [hasAccess]);

  const loadScheduledEmails = async () => {
    try {
      const response = await api.get('/email-automation/scheduled');
      if (response.success && response.data) {
        setScheduledEmails(response.data.scheduled_emails || []);
      }
    } catch (error) {
      console.error('Failed to load scheduled emails:', error);
      toast.error('Failed to load scheduled emails');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEmail = async (emailId: string) => {
    const confirmed = await showConfirm(
      'Cancel Scheduled Email',
      'Are you sure you want to cancel this scheduled email?',
      'Cancel Email',
      'Keep Scheduled',
      'danger'
    );

    if (!confirmed) return;

    try {
      const response = await api.delete(`/email-automation/scheduled/${emailId}`);
      if (response.success) {
        toast.success('Email cancelled successfully');
        loadScheduledEmails();
      } else {
        toast.error(response.error || 'Failed to cancel email');
      }
    } catch (error) {
      console.error('Error cancelling email:', error);
      toast.error('Failed to cancel email');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'sent':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'cancelled':
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
      default:
        return <Mail className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      scheduled: 'bg-blue-50 text-blue-700 border-blue-100',
      sent: 'bg-green-50 text-green-700 border-green-100',
      failed: 'bg-red-50 text-red-700 border-red-100',
      cancelled: 'bg-gray-50 text-gray-700 border-gray-100'
    };

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles] || styles.cancelled}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getEmailTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'expiration_reminder': 'Expiration Reminder',
      'selection_reminder': 'Selection Reminder',
      'download_reminder': 'Download Reminder',
      'custom': 'Custom Message'
    };
    return labels[type] || type;
  };

  const filteredEmails = filterStatus === 'all'
    ? scheduledEmails
    : scheduledEmails.filter(email => email.status === filterStatus);

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
                  Email Automation
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
              <Mail className="w-8 h-8 text-[#0066CC]" />
            </div>
            <h2 className="text-2xl font-medium text-[#1D1D1F] mb-4">
              Email Automation
            </h2>
            <p className="text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
              Automated email scheduling and reminders are available on Pro and Ultimate plans.
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
                Email Automation
              </h1>
            </div>
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Info Banner */}
        <div className="glass-panel p-6 mb-8 border border-blue-100 bg-blue-50/30">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
              <Mail className="w-6 h-6 text-[#0066CC]" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                Automated Email System
              </h3>
              <p className="text-sm text-[#1D1D1F]/70 mb-4">
                Emails are automatically sent to clients based on gallery settings and deadlines.
                Set up automation when creating or editing galleries.
              </p>
              <div className="flex gap-4">
                <Link
                  to="/email-templates"
                  className="text-sm font-medium text-[#0066CC] hover:underline"
                >
                  Customize Email Templates →
                </Link>
                <Link
                  to="/galleries"
                  className="text-sm font-medium text-[#0066CC] hover:underline"
                >
                  Manage Galleries →
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'scheduled', 'sent', 'failed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                filterStatus === status
                  ? 'bg-[#0066CC] text-white shadow-lg shadow-blue-500/20'
                  : 'bg-white text-[#1D1D1F] hover:bg-gray-50'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
              {status !== 'all' && (
                <span className="ml-2 opacity-70">
                  ({scheduledEmails.filter(e => e.status === status).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Scheduled Emails List */}
        {loading ? (
          <div className="glass-panel p-12 text-center">
            <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#1D1D1F]/60">Loading scheduled emails...</p>
          </div>
        ) : filteredEmails.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
              No {filterStatus !== 'all' && filterStatus} emails found
            </h3>
            <p className="text-sm text-[#1D1D1F]/60">
              Automated emails will appear here when you set up gallery automation.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredEmails.map((email) => (
              <div key={email.id} className="glass-panel p-6 hover:shadow-lg transition-all">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-1">
                    {getStatusIcon(email.status)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-base font-medium text-[#1D1D1F] mb-1">
                          {getEmailTypeLabel(email.email_type)}
                        </h3>
                        <p className="text-sm text-[#1D1D1F]/60">
                          To: {email.recipient_email}
                        </p>
                      </div>
                      {getStatusBadge(email.status)}
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                      <div>
                        <span className="text-[#1D1D1F]/50 text-xs">Scheduled For</span>
                        <p className="text-[#1D1D1F] font-medium">
                          {new Date(email.scheduled_time).toLocaleString()}
                        </p>
                      </div>
                      {email.sent_at && (
                        <div>
                          <span className="text-[#1D1D1F]/50 text-xs">Sent At</span>
                          <p className="text-[#1D1D1F] font-medium">
                            {new Date(email.sent_at).toLocaleString()}
                          </p>
                        </div>
                      )}
                      {email.attempts && email.attempts > 0 && (
                        <div>
                          <span className="text-[#1D1D1F]/50 text-xs">Attempts</span>
                          <p className="text-[#1D1D1F] font-medium">
                            {email.attempts}
                          </p>
                        </div>
                      )}
                    </div>

                    {email.error && (
                      <div className="p-3 bg-red-50 border border-red-100 rounded-xl mb-4">
                        <p className="text-xs text-red-700">
                          <span className="font-semibold">Error:</span> {email.error}
                        </p>
                      </div>
                    )}

                    {email.status === 'scheduled' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleCancelEmail(email.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-xl text-sm font-medium hover:bg-red-100 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <ModalComponent />
    </div>
  );
}
