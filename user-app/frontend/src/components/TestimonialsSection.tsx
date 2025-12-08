// Testimonials Section Component - For public portfolio display
import { useState, useEffect } from 'react';
import { Star, Quote } from 'lucide-react';
import { api } from '../utils/api';

interface Testimonial {
  id: string;
  client_name: string;
  client_initial: string;
  service_type: string;
  rating: number;
  title: string;
  content: string;
  event_date: string;
  created_at: string;
  would_recommend: boolean;
  photo_url?: string;
}

interface TestimonialsProps {
  photographerId: string;
  limit?: number;
  showSubmitForm?: boolean;
}

export default function TestimonialsSection({ photographerId, limit = 6, showSubmitForm = false }: TestimonialsProps) {
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [stats, setStats] = useState({ total: 0, average_rating: 0 });
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    client_name: '',
    client_email: '',
    service_type: '',
    rating: 5,
    title: '',
    content: '',
    event_date: '',
    would_recommend: true
  });
  const [submitStatus, setSubmitStatus] = useState<{ type: string; message: string } | null>(null);

  useEffect(() => {
    loadTestimonials();
  }, [photographerId]);

  const loadTestimonials = async () => {
    try {
      const response = await api.get(`/public/photographers/${photographerId}/testimonials`);
      if (response.success && response.data) {
        setTestimonials(response.data.testimonials.slice(0, limit));
        setStats(response.data.stats || { total: 0, average_rating: 0 });
      }
    } catch (error) {
      console.error('Error loading testimonials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitStatus(null);

    try {
      const response = await api.post(`/public/photographers/${photographerId}/testimonials`, formData);
      if (response.success) {
        setSubmitStatus({ type: 'success', message: 'Thank you for your feedback! Your testimonial is pending approval.' });
        setFormData({
          client_name: '',
          client_email: '',
          service_type: '',
          rating: 5,
          title: '',
          content: '',
          event_date: '',
          would_recommend: true
        });
        setShowForm(false);
      } else {
        setSubmitStatus({ type: 'error', message: response.error || 'Failed to submit testimonial' });
      }
    } catch (error) {
      setSubmitStatus({ type: 'error', message: 'Failed to submit testimonial. Please try again.' });
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`w-4 h-4 ${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
          />
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="py-8 text-center">
        <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    );
  }

  if (testimonials.length === 0 && !showSubmitForm) {
    return null; // Don't show empty section
  }

  return (
    <div className="py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-serif font-medium text-[#1D1D1F] mb-4">
          Client Testimonials
        </h2>
        {stats.total > 0 && (
          <div className="flex items-center justify-center gap-4 text-[#1D1D1F]/60">
            <div className="flex items-center gap-2">
              {renderStars(Math.round(stats.average_rating))}
              <span className="font-medium">{stats.average_rating.toFixed(1)}</span>
            </div>
            <span>•</span>
            <span>{stats.total} {stats.total === 1 ? 'review' : 'reviews'}</span>
          </div>
        )}
      </div>

      {/* Testimonials Grid */}
      {testimonials.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {testimonials.map((testimonial) => (
            <div key={testimonial.id} className="glass-panel p-6 relative">
              <Quote className="absolute top-4 right-4 w-8 h-8 text-[#0066CC]/10" />
              
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-[#0066CC] to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-lg">{testimonial.client_initial}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-[#1D1D1F] truncate">{testimonial.client_name}</h3>
                  {renderStars(testimonial.rating)}
                </div>
              </div>

              {testimonial.title && (
                <h4 className="font-medium text-[#1D1D1F] mb-2">{testimonial.title}</h4>
              )}

              <p className="text-[#1D1D1F]/70 text-sm leading-relaxed mb-4 line-clamp-4">
                {testimonial.content}
              </p>

              <div className="flex items-center justify-between text-xs text-[#1D1D1F]/40">
                <span className="capitalize">{testimonial.service_type}</span>
                <span>{new Date(testimonial.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Submit Testimonial Button/Form */}
      {showSubmitForm && (
        <>
          {!showForm ? (
            <div className="text-center">
              <button
                onClick={() => setShowForm(true)}
                className="px-8 py-3 bg-[#0066CC] text-white rounded-full hover:bg-[#0052A3] transition-all hover:scale-105"
              >
                Leave a Review
              </button>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto glass-panel p-8">
              <h3 className="text-2xl font-medium text-[#1D1D1F] mb-6">Share Your Experience</h3>

              {submitStatus && (
                <div className={`mb-6 p-4 rounded-xl ${submitStatus.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                  {submitStatus.message}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Your Name *</label>
                    <input
                      type="text"
                      required
                      value={formData.client_name}
                      onChange={(e) => setFormData({ ...formData, client_name: e.target.value })}
                      className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Email *</label>
                    <input
                      type="email"
                      required
                      value={formData.client_email}
                      onChange={(e) => setFormData({ ...formData, client_email: e.target.value })}
                      className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Service Type</label>
                    <select
                      value={formData.service_type}
                      onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                      className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                    >
                      <option value="">Select service</option>
                      <option value="wedding">Wedding</option>
                      <option value="portrait">Portrait</option>
                      <option value="event">Event</option>
                      <option value="commercial">Commercial</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Rating *</label>
                    <div className="flex gap-2 pt-2">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setFormData({ ...formData, rating: star })}
                          className="focus:outline-none"
                        >
                          <Star
                            className={`w-8 h-8 transition-all ${star <= formData.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 hover:text-yellow-200'}`}
                          />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Review Title</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                    placeholder="e.g., Amazing experience!"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#1D1D1F] mb-2">Your Review *</label>
                  <textarea
                    required
                    rows={5}
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 resize-none"
                    placeholder="Share your experience..."
                    minLength={20}
                  />
                </div>

                <div className="flex gap-4">
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-all"
                  >
                    Submit Review
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-6 py-3 border border-gray-200 text-[#1D1D1F] rounded-xl hover:bg-gray-50 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}
        </>
      )}
    </div>
  );
}
