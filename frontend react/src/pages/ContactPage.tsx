// Contact page
import { useState, FormEvent } from 'react';
import { Mail, MessageCircle, Send, Check, AlertCircle } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    issueType: 'other',
    message: '',
  });
  const [status, setStatus] = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus({ type: '', text: '' });
    setLoading(true);

    try {
      const response = await api.post('/contact/submit', formData);

      if (response.success) {
        setStatus({ type: 'success', text: 'Message sent! We will get back to you soon.' });
        setFormData({ name: '', email: '', issueType: 'other', message: '' });
      } else {
        setStatus({ type: 'error', text: response.error || 'Failed to send message' });
      }
    } catch {
      setStatus({ type: 'error', text: 'Failed to send message. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-serif font-medium text-[#1D1D1F] mb-6">
              Get in Touch
            </h1>
            <p className="text-xl text-[#1D1D1F]/70 max-w-2xl mx-auto">
              Have questions? We're here to help. Send us a message and we'll respond as soon as possible.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Contact Info */}
            <div className="space-y-6">
              <div className="glass-panel p-6">
                <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
                  <Mail className="w-6 h-6 text-[#0066CC]" />
                </div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                  Email Us
                </h3>
                <p className="text-[#1D1D1F]/60 mb-4">
                  Our team responds within 24 hours
                </p>
                <a
                  href="mailto:support@galerly.com"
                  className="text-[#0066CC] hover:text-[#0052A3] transition-colors"
                >
                  support@galerly.com
                </a>
              </div>

              <div className="glass-panel p-6">
                <div className="w-12 h-12 bg-purple-50 rounded-2xl flex items-center justify-center mb-4">
                  <MessageCircle className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                  Live Chat
                </h3>
                <p className="text-[#1D1D1F]/60 mb-4">
                  Chat with our support team
                </p>
                <button className="text-[#0066CC] hover:text-[#0052A3] transition-colors">
                  Start Chat
                </button>
              </div>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2 glass-panel p-8">
              <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-6">
                Send us a Message
              </h2>

              {status.text && (
                <div
                  className={`mb-6 p-4 rounded-2xl flex items-start gap-3 ${
                    status.type === 'success'
                      ? 'bg-green-50 border border-green-100'
                      : 'bg-red-50 border border-red-100'
                  }`}
                >
                  {status.type === 'success' ? (
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  )}
                  <p
                    className={`text-sm ${
                      status.type === 'success' ? 'text-green-800' : 'text-red-800'
                    }`}
                  >
                    {status.text}
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                      Name
                    </label>
                    <input
                      id="name"
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                      Email
                    </label>
                    <input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                      placeholder="you@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="issueType" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Topic
                  </label>
                  <select
                    id="issueType"
                    value={formData.issueType}
                    onChange={(e) => setFormData({ ...formData, issueType: e.target.value })}
                    required
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
                  >
                    <option value="account">Account Support</option>
                    <option value="gallery">Gallery Issues</option>
                    <option value="upload">Upload Problems</option>
                    <option value="sharing">Sharing & Access</option>
                    <option value="billing">Billing & Subscription</option>
                    <option value="technical">Technical Bug</option>
                    <option value="other">Other Inquiry</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-[#1D1D1F] mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    required
                    rows={6}
                    className="w-full px-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all resize-none"
                    placeholder="Tell us more about your question or feedback..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>Sending...</>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Send Message
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

