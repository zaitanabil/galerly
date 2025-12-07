import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ArrowLeft, Mail, Calendar, CreditCard, Activity as ActivityIcon, UserX, UserCheck, Trash2, AlertTriangle } from 'lucide-react';
import adminAPI from '../services/api';

export default function UserDetails() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [userData, setUserData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [suspendReason, setSuspendReason] = useState('');
  
  useEffect(() => {
    if (userId) {
      loadUserDetails();
    }
  }, [userId]);
  
  const loadUserDetails = async () => {
    try {
      const data = await adminAPI.getUserDetails(userId!);
      setUserData(data);
    } catch (error) {
      console.error('Error loading user details:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSuspend = async () => {
    if (!suspendReason.trim()) {
      alert('Please provide a reason for suspension');
      return;
    }
    
    setActionLoading(true);
    try {
      await adminAPI.suspendUser(userId!, suspendReason);
      setShowSuspendModal(false);
      setSuspendReason('');
      await loadUserDetails();
      alert('User suspended successfully');
    } catch (error: any) {
      alert('Error suspending user: ' + error.message);
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleUnsuspend = async () => {
    setActionLoading(true);
    try {
      await adminAPI.unsuspendUser(userId!);
      await loadUserDetails();
      alert('User unsuspended successfully');
    } catch (error: any) {
      alert('Error unsuspending user: ' + error.message);
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await adminAPI.deleteUser(userId!);
      alert('User deleted successfully');
      navigate('/users');
    } catch (error: any) {
      alert('Error deleting user: ' + error.message);
      setActionLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (!userData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">User not found</p>
      </div>
    );
  }
  
  const { user, galleries, subscription, billing_history, recent_activity } = userData;
  
  const isSuspended = user.account_status === 'suspended';
  
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <a href="/users" className="inline-flex items-center gap-2 text-gray-600 hover:text-dark mb-4">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Users</span>
        </a>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-dark">{user.name}</h1>
            <p className="text-gray-600 mt-1">{user.email}</p>
            {isSuspended && (
              <span className="inline-flex items-center gap-1 px-3 py-1 mt-2 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                <UserX className="w-4 h-4" />
                Account Suspended
              </span>
            )}
          </div>
          
          {/* Admin Actions */}
          <div className="flex items-center gap-2">
            {isSuspended ? (
              <button
                onClick={handleUnsuspend}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <UserCheck className="w-4 h-4" />
                Unsuspend
              </button>
            ) : (
              <button
                onClick={() => setShowSuspendModal(true)}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50"
              >
                <UserX className="w-4 h-4" />
                Suspend
              </button>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={actionLoading}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        </div>
      </div>
      
      {/* Suspend Modal */}
      {showSuspendModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-dark mb-4">Suspend User</h3>
            <p className="text-gray-600 mb-4">
              This will prevent the user from accessing their account. Provide a reason:
            </p>
            <textarea
              value={suspendReason}
              onChange={(e) => setSuspendReason(e.target.value)}
              placeholder="Reason for suspension..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary mb-4"
              rows={3}
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowSuspendModal(false);
                  setSuspendReason('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSuspend}
                disabled={actionLoading || !suspendReason.trim()}
                className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50"
              >
                Suspend
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-600" />
              <h3 className="text-xl font-bold text-dark">Delete User</h3>
            </div>
            <p className="text-gray-600 mb-4">
              This action cannot be undone. This will permanently delete the user account, 
              all galleries, photos, and related data.
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-800 font-medium">
                User: {user.email}
              </p>
              <p className="text-sm text-red-600 mt-1">
                {galleries.length} galleries and all associated photos will be deleted
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={actionLoading}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {actionLoading ? 'Deleting...' : 'Delete Forever'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* User Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Mail className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-dark">Profile</h3>
          </div>
          <dl className="space-y-2">
            <div>
              <dt className="text-sm text-gray-600">Role</dt>
              <dd className="font-medium">{user.role}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Plan</dt>
              <dd className="font-medium">{user.plan}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">City</dt>
              <dd className="font-medium">{user.city || 'Not set'}</dd>
            </div>
          </dl>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-dark">Dates</h3>
          </div>
          <dl className="space-y-2">
            <div>
              <dt className="text-sm text-gray-600">Joined</dt>
              <dd className="font-medium">{new Date(user.created_at).toLocaleDateString()}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Last Login</dt>
              <dd className="font-medium">{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</dd>
            </div>
          </dl>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <CreditCard className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-dark">Subscription</h3>
          </div>
          {subscription ? (
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-600">Status</dt>
                <dd className="font-medium">{subscription.status}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Plan</dt>
                <dd className="font-medium">{subscription.plan}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-gray-500">No active subscription</p>
          )}
        </div>
      </div>
      
      {/* Galleries */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h3 className="font-semibold text-dark mb-4">Galleries ({galleries.length})</h3>
        {galleries.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {galleries.map((gallery: any) => (
              <div key={gallery.id} className="border border-gray-200 rounded-lg p-4">
                <p className="font-medium text-dark">{gallery.name}</p>
                <p className="text-sm text-gray-600 mt-1">{gallery.photo_count || 0} photos</p>
                <p className="text-xs text-gray-500 mt-2">
                  Created {new Date(gallery.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No galleries yet</p>
        )}
      </div>
      
      {/* Recent Activity */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <ActivityIcon className="w-5 h-5 text-gray-400" />
          <h3 className="font-semibold text-dark">Recent Activity</h3>
        </div>
        {recent_activity && recent_activity.length > 0 ? (
          <div className="space-y-3">
            {recent_activity.slice(0, 10).map((activity: any, index: number) => (
              <div key={index} className="flex items-start gap-3 pb-3 border-b border-gray-100 last:border-0">
                <div className="w-2 h-2 rounded-full bg-primary mt-2" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-dark">{activity.action}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No recent activity</p>
        )}
      </div>
    </div>
  );
}

