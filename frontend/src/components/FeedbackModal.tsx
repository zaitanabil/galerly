import { useState, useEffect } from 'react';
import { X, Star, PenTool } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import * as clientService from '../services/clientService';
import * as photoService from '../services/photoService';
import { Comment } from '../services/photoService';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  galleryId: string;
  photoId?: string; // Optional: if provided, this is a photo comment/edit request
  annotation?: string; // Optional: SVG path or JSON data
  initialComment?: string;
  onCommentAdded?: (comment: Comment) => void; // Callback to update UI
}

export default function FeedbackModal({ isOpen, onClose, galleryId, photoId, annotation, initialComment, onCommentAdded }: FeedbackModalProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    clientName: '',
    clientEmail: '',
    overallRating: 5,
    photoQualityRating: 0,
    deliveryTimeRating: 0,
    communicationRating: 0,
    valueRating: 0,
    wouldRecommend: false,
    comments: '',
  });

  // Load guest info from local storage or auth user on mount
  useEffect(() => {
    if (isOpen) {
      if (user) {
        setFormData(prev => ({
          ...prev,
          clientName: user.name || user.username || '',
          clientEmail: user.email || ''
        }));
      } else {
        const storedName = localStorage.getItem('guest_name');
        const storedEmail = localStorage.getItem('guest_email');
        if (storedName || storedEmail) {
            setFormData(prev => ({
                ...prev,
                clientName: storedName || prev.clientName,
                clientEmail: storedEmail || prev.clientEmail
            }));
        }
      }
    }
  }, [isOpen, user]);

  // Pre-fill comments if provided
  useEffect(() => {
      // Set initial comment if available
      if (initialComment) {
          setFormData(prev => ({ ...prev, comments: initialComment + (prev.comments ? '\n' + prev.comments : '') }));
      }
  }, [initialComment, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Save guest info
    if (formData.clientName) localStorage.setItem('guest_name', formData.clientName);
    if (formData.clientEmail) localStorage.setItem('guest_email', formData.clientEmail);

    try {
      if (photoId) {
          // SUBMIT PHOTO COMMENT / EDIT REQUEST
          const response = await photoService.addComment(
              photoId,
              formData.comments,
              undefined, // parentId
              formData.clientName,
              formData.clientEmail,
              annotation
          );
          
          if (response.success && response.data) {
                   setSuccess(true);
              if (onCommentAdded) onCommentAdded(response.data);
                   setTimeout(() => {
                       onClose();
                       setSuccess(false);
                       setFormData(prev => ({ ...prev, comments: '' }));
                   }, 1500);
               } else {
              setError(response.error || 'Failed to submit request');
          }

      } else {
          // SUBMIT GENERAL GALLERY FEEDBACK
      const response = await clientService.submitFeedback(galleryId, {
        client_name: formData.clientName,
        client_email: formData.clientEmail,
        rating: formData.overallRating, // Mapping overall to rating
        comment: formData.comments,
      });

      if (response.success) {
        setSuccess(true);
        setTimeout(() => {
          onClose();
          setSuccess(false);
          setFormData({
            clientName: '',
            clientEmail: '',
            overallRating: 5,
            photoQualityRating: 0,
            deliveryTimeRating: 0,
            communicationRating: 0,
            valueRating: 0,
            wouldRecommend: false,
            comments: '',
          });
        }, 2000);
      } else {
        setError(response.error || 'Failed to submit feedback');
      }
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating: number, setRating: (r: number) => void, label: string) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-[#1D1D1F] mb-1">{label}</label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => setRating(star)}
            className="p-1 transition-transform hover:scale-110 focus:outline-none"
          >
            <Star
              className={`w-6 h-6 ${
                star <= rating ? 'fill-amber-400 text-amber-400' : 'fill-gray-100 text-gray-300'
              }`}
            />
          </button>
        ))}
      </div>
    </div>
  );

  const isEditRequest = !!photoId;

  return (
    <div className="fixed inset-0 z-[20000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in duration-300 overflow-hidden">
        
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white">
          <h2 className="text-xl font-serif font-medium text-[#1D1D1F]">
              {isEditRequest ? 'Request Edit / Modification' : 'Share Your Feedback'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6">
          {success ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
                {isEditRequest ? <PenTool className="w-8 h-8" /> : <Star className="w-8 h-8 fill-current" />}
              </div>
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">{isEditRequest ? 'Request Sent' : 'Thank You!'}</h3>
              <p className="text-[#1D1D1F]/60">
                  {isEditRequest ? 'Your edit request has been added to the photo comments.' : 'Your feedback has been submitted successfully.'}
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                  {error}
                </div>
              )}

              {!user && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-1">Your Name</label>
                  <input
                    type="text"
                    required
                    value={formData.clientName}
                    onChange={(e) => setFormData({ ...formData, clientName: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                    placeholder="Jane Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-1">Email</label>
                  <input
                    type="email"
                    required
                    value={formData.clientEmail}
                    onChange={(e) => setFormData({ ...formData, clientEmail: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                    placeholder="jane@example.com"
                  />
                </div>
              </div>
              )}

              {!isEditRequest && (
              <div className="bg-gray-50 p-4 rounded-xl space-y-4 border border-gray-100">
                {renderStars(formData.overallRating, (r) => setFormData({ ...formData, overallRating: r }), 'Overall Experience')}
                </div>
              )}

              {annotation && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
                      <PenTool className="w-5 h-5 text-yellow-600" />
                      <span className="text-sm text-yellow-800 font-medium">Edit zone marked on photo</span>
              </div>
              )}

              <div>
                <label className="block text-sm font-medium text-[#1D1D1F] mb-1">
                   {isEditRequest ? 'Describe the modification needed' : 'Comments'}
                </label>
                <textarea
                  rows={4}
                  required={isEditRequest}
                  value={formData.comments}
                  onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC]"
                  placeholder={isEditRequest ? "E.g. Please remove the object in the selected area, crop this part, etc." : "Share your thoughts..."}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 shadow-lg shadow-blue-500/20"
              >
                {loading ? 'Submitting...' : (isEditRequest ? 'Send Request' : 'Submit Feedback')}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

