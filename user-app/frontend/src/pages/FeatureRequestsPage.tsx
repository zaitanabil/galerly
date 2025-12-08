// Feature Request Voting Component
import { useState, useEffect } from 'react';
import { ThumbsUp, Plus, Check, Filter, TrendingUp, Clock, MessageSquare } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  status: 'pending' | 'planned' | 'in_progress' | 'completed' | 'declined';
  votes: number;
  voters: string[];
  submitter_name: string;
  created_at: string;
  comments_count: number;
}

export default function FeatureRequestsPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<FeatureRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('votes');
  const [showSubmitForm, setShowSubmitForm] = useState(false);

  useEffect(() => {
    loadRequests();
  }, [filter, sort]);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        status: filter,
        sort: sort
      });
      const response = await api.get(`/feature-requests?${params.toString()}`);
      if (response.success) {
        setRequests(response.data.feature_requests);
      }
    } catch (error) {
      console.error('Failed to load feature requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (requestId: string) => {
    try {
      const request = requests.find(r => r.id === requestId);
      if (!request) return;

      const hasVoted = request.voters.includes(user?.user_id || '');

      if (hasVoted) {
        await api.delete(`/feature-requests/${requestId}/vote`);
        toast.success('Vote removed');
      } else {
        await api.post(`/feature-requests/${requestId}/vote`);
        toast.success('Vote recorded!');
      }

      loadRequests();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to vote');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-700';
      case 'planned': return 'bg-blue-100 text-blue-700';
      case 'in_progress': return 'bg-purple-100 text-purple-700';
      case 'completed': return 'bg-green-100 text-green-700';
      case 'declined': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] py-8 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] mb-3">
            Feature Requests
          </h1>
          <p className="text-lg text-[#1D1D1F]/60">
            Vote on features you'd like to see in Galerly
          </p>
        </div>

        {/* Actions Bar */}
        <div className="glass-panel p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Filter */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
            >
              <option value="all">All Requests</option>
              <option value="pending">Pending</option>
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>

            {/* Sort */}
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
            >
              <option value="votes">Most Voted</option>
              <option value="recent">Most Recent</option>
              <option value="oldest">Oldest First</option>
            </select>
          </div>

          <button
            onClick={() => setShowSubmitForm(true)}
            className="px-4 py-2 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Submit Request
          </button>
        </div>

        {/* Requests List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-sm text-[#1D1D1F]/60">Loading requests...</p>
          </div>
        ) : requests.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <p className="text-[#1D1D1F]/60">No feature requests found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {requests.map((request) => {
              const hasVoted = request.voters.includes(user?.user_id || '');
              
              return (
                <div
                  key={request.id}
                  className="glass-panel p-6 flex items-start gap-4 hover:shadow-lg transition-all"
                >
                  {/* Vote Button */}
                  <button
                    onClick={() => handleVote(request.id)}
                    className={`flex flex-col items-center gap-1 px-4 py-3 rounded-xl transition-all ${
                      hasVoted
                        ? 'bg-[#0066CC] text-white'
                        : 'bg-gray-100 text-[#1D1D1F] hover:bg-gray-200'
                    }`}
                  >
                    <ThumbsUp className={`w-5 h-5 ${hasVoted ? 'fill-current' : ''}`} />
                    <span className="text-lg font-bold">{request.votes}</span>
                  </button>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <h3 className="text-lg font-medium text-[#1D1D1F]">
                        {request.title}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium flex-shrink-0 ${getStatusColor(request.status)}`}>
                        {request.status.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <p className="text-sm text-[#1D1D1F]/60 mb-3">
                      {request.description}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-[#1D1D1F]/40">
                      <span>By {request.submitter_name}</span>
                      <span>•</span>
                      <span>{new Date(request.created_at).toLocaleDateString()}</span>
                      {request.comments_count > 0 && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="w-3 h-3" />
                            {request.comments_count} comments
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Submit Form Modal */}
        {showSubmitForm && (
          <SubmitFeatureRequestModal
            onClose={() => setShowSubmitForm(false)}
            onSubmit={() => {
              setShowSubmitForm(false);
              loadRequests();
            }}
          />
        )}
      </div>
    </div>
  );
}

// Submit Feature Request Modal
function SubmitFeatureRequestModal({ onClose, onSubmit }: { onClose: () => void; onSubmit: () => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (title.length < 10) {
      toast.error('Title must be at least 10 characters');
      return;
    }
    
    if (description.length < 20) {
      toast.error('Description must be at least 20 characters');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/feature-requests', {
        title,
        description,
        category
      });
      
      toast.success('Feature request submitted!');
      onSubmit();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6">
        <h2 className="text-2xl font-medium text-[#1D1D1F] mb-4">
          Submit Feature Request
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What feature would you like?"
              className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
              required
              minLength={10}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
            >
              <option value="general">General</option>
              <option value="ui">User Interface</option>
              <option value="integration">Integration</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
              Description *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the feature in detail..."
              rows={5}
              className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 resize-none"
              required
              minLength={20}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-3 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
