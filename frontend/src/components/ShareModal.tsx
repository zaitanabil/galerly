import { useState, useEffect, useCallback } from 'react';
import { X, Copy, Check, Facebook, Twitter, Linkedin, Mail, Smartphone, Instagram } from 'lucide-react';
import { api } from '../utils/api';
import analyticsService from '../services/analyticsService';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  galleryId: string;
  photoId?: string; // Optional: if sharing a specific photo
  title?: string;
  shareUrl?: string; // Optional: pre-calculated share URL
}

interface ShareInfo {
  share_url: string;
  embed_code?: string;
  gallery_name?: string;
  direct_image_url?: string;
}

export default function ShareModal({
  isOpen,
  onClose,
  galleryId,
  photoId,
  title = 'Share',
  shareUrl: initialShareUrl
}: ShareModalProps) {
  const [loading, setLoading] = useState(false);
  const [shareInfo, setShareInfo] = useState<ShareInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'link' | 'social' | 'qr' | 'embed'>('link');
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedEmbed, setCopiedEmbed] = useState(false);
  const [error, setError] = useState('');
  const [notification, setNotification] = useState<{ message: string, type: 'success' | 'error' } | null>(null);

  const loadShareInfo = useCallback(async () => {
    // If we have an initial URL and no need for other info (like embed code for photos), use it
    if (initialShareUrl && !photoId) {
       setShareInfo({ share_url: initialShareUrl, gallery_name: title });
       return;
    }

    setLoading(true);
    try {
      const endpoint = photoId 
        ? `/share/photo/${photoId}` 
        : `/share/gallery/${galleryId}`;
      
      const response = await api.get<ShareInfo>(endpoint);
      
      if (response.success && response.data) {
        setShareInfo(response.data);
      } else {
        setError(response.error || 'Failed to load share information');
      }
    } catch {
      setError('An error occurred loading share information');
    } finally {
      setLoading(false);
    }
  }, [initialShareUrl, photoId, galleryId, title]);

  // Reset state when opening
  useEffect(() => {
    if (isOpen) {
      loadShareInfo();
      setActiveTab('link');
      setCopiedLink(false);
      setCopiedEmbed(false);
      setError('');
      setNotification(null);
    }
  }, [isOpen, loadShareInfo]);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleCopy = async (text: string, type: 'link' | 'embed') => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'link') {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2000);
        showNotification('Link copied to clipboard');
      } else {
        setCopiedEmbed(true);
        setTimeout(() => setCopiedEmbed(false), 2000);
        showNotification('Embed code copied');
      }
    } catch (err) {
      console.error('Failed to copy', err);
      showNotification('Failed to copy', 'error');
    }
  };

  const handleSocialShare = async (platform: string) => {
    if (!shareInfo) return;
    
    const url = shareInfo.share_url;
    const text = `Check out this ${photoId ? 'photo' : 'gallery'}: ${shareInfo.gallery_name || 'Gallery'}`;
    const encodedUrl = encodeURIComponent(url);
    const encodedText = encodeURIComponent(text);
    let shareLink = '';

    // Native Share API support
    if (platform === 'native') {
        if (typeof navigator.share === 'function') {
            try {
                await navigator.share({
                    title: shareInfo.gallery_name || 'Gallery',
                    text: text,
                    url: url
                });
                // Track share
                if (photoId) {
                    analyticsService.trackPhotoShare(photoId, 'native').catch(console.error);
                } else {
                    analyticsService.trackGalleryShare(galleryId, 'native').catch(console.error);
                }
                return;
            } catch (err) {
                if ((err as Error).name !== 'AbortError') {
                    console.error('Error sharing:', err);
                }
                return;
            }
        } else {
            showNotification('Native sharing not supported on this device', 'error');
            return;
        }
    }

    switch (platform) {
      case 'facebook':
        shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
        break;
      case 'twitter':
        shareLink = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`;
        break;
      case 'linkedin':
        shareLink = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`;
        break;
      case 'pinterest':
        shareLink = `https://pinterest.com/pin/create/button/?url=${encodedUrl}&description=${encodedText}`;
        break;
      case 'whatsapp':
        shareLink = `https://wa.me/?text=${encodedUrl} ${encodedText}`;
        break;
      case 'email':
        shareLink = `mailto:?subject=${encodedText}&body=${encodedUrl}`;
        break;
      case 'instagram':
        handleCopy(url, 'link');
        showNotification('Link copied! Open Instagram to share.', 'success');
        return;
    }

    if (shareLink) {
      // Track share
      if (photoId) {
        analyticsService.trackPhotoShare(photoId, platform).catch(console.error);
      } else {
        analyticsService.trackGalleryShare(galleryId, platform).catch(console.error);
      }

      if (platform === 'email') {
        window.location.href = shareLink;
      } else {
        window.open(shareLink, '_blank', 'width=600,height=400');
      }
    }
  };

  const generateQrCodeUrl = (text: string) => {
    return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(text)}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[20000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-md flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200 relative">
        
        {/* Notification Toast */}
        {notification && (
            <div className={`absolute top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full shadow-lg text-sm font-medium z-10 transition-all ${
                notification.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
                {notification.message}
            </div>
        )}

        {/* Header */}
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-serif font-medium text-[#1D1D1F]">
            Share {photoId ? 'Photo' : 'Gallery'}
          </h2>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-[#1D1D1F]/60" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="w-8 h-8 border-2 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-6 text-red-500">
              <p>{error}</p>
              <button 
                onClick={loadShareInfo}
                className="mt-4 px-4 py-2 bg-[#0066CC] text-white rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          ) : shareInfo ? (
            <>
              {/* Tabs */}
              <div className="flex gap-2 mb-6 border-b border-gray-100">
                <button
                  onClick={() => setActiveTab('link')}
                  className={`pb-2 px-1 text-sm font-medium transition-colors relative ${
                    activeTab === 'link' ? 'text-[#0066CC]' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Link
                  {activeTab === 'link' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0066CC]" />}
                </button>
                <button
                  onClick={() => setActiveTab('social')}
                  className={`pb-2 px-1 text-sm font-medium transition-colors relative ${
                    activeTab === 'social' ? 'text-[#0066CC]' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Social
                  {activeTab === 'social' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0066CC]" />}
                </button>
                <button
                  onClick={() => setActiveTab('qr')}
                  className={`pb-2 px-1 text-sm font-medium transition-colors relative ${
                    activeTab === 'qr' ? 'text-[#0066CC]' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  QR Code
                  {activeTab === 'qr' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0066CC]" />}
                </button>
                {!photoId && (
                  <button
                    onClick={() => setActiveTab('embed')}
                    className={`pb-2 px-1 text-sm font-medium transition-colors relative ${
                      activeTab === 'embed' ? 'text-[#0066CC]' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Embed
                    {activeTab === 'embed' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#0066CC]" />}
                  </button>
                )}
              </div>

              {/* Tab Content */}
              <div className="min-h-[200px]">
                {/* Link Tab */}
                {activeTab === 'link' && (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-500">Copy the link below to share:</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        readOnly
                        value={shareInfo.share_url}
                        className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] focus:outline-none"
                        onClick={(e) => e.currentTarget.select()}
                      />
                      <button
                        onClick={() => handleCopy(shareInfo.share_url, 'link')}
                        className={`px-4 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
                          copiedLink 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-[#0066CC] text-white hover:bg-[#0052A3]'
                        }`}
                      >
                        {copiedLink ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        {copiedLink ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Social Tab */}
                {activeTab === 'social' && (
                  <div className="grid grid-cols-4 gap-4">
                    {typeof navigator.share === 'function' && (
                        <button onClick={() => handleSocialShare('native')} className="flex flex-col items-center gap-2 group">
                            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-[#1D1D1F] group-hover:scale-110 transition-transform">
                                <Smartphone className="w-6 h-6" />
                            </div>
                            <span className="text-xs text-gray-600">Share</span>
                        </button>
                    )}
                    <button onClick={() => handleSocialShare('facebook')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-[#1877F2] rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Facebook className="w-6 h-6" />
                      </div>
                      <span className="text-xs text-gray-600">Facebook</span>
                    </button>
                    <button onClick={() => handleSocialShare('twitter')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-black rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Twitter className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600">X</span>
                    </button>
                    <button onClick={() => handleSocialShare('instagram')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-gradient-to-tr from-[#fdf497] via-[#fd5949] to-[#285AEB] rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Instagram className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600">Instagram</span>
                    </button>
                    <button onClick={() => handleSocialShare('linkedin')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-[#0077B5] rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Linkedin className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600">LinkedIn</span>
                    </button>
                    <button onClick={() => handleSocialShare('whatsapp')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-[#25D366] rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Smartphone className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600">WhatsApp</span>
                    </button>
                    <button onClick={() => handleSocialShare('email')} className="flex flex-col items-center gap-2 group">
                      <div className="w-12 h-12 bg-gray-600 rounded-full flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                        <Mail className="w-5 h-5" />
                      </div>
                      <span className="text-xs text-gray-600">Email</span>
                    </button>
                  </div>
                )}

                {/* QR Tab */}
                {activeTab === 'qr' && (
                  <div className="flex flex-col items-center space-y-4">
                    <div className="p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
                      <img 
                        src={generateQrCodeUrl(shareInfo.share_url)} 
                        alt="QR Code" 
                        className="w-48 h-48"
                      />
                    </div>
                    <p className="text-sm text-gray-500 text-center">
                      Scan to view on mobile
                    </p>
                  </div>
                )}

                {/* Embed Tab */}
                {activeTab === 'embed' && !photoId && (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-500">Copy embed code to add to your website:</p>
                    <div className="relative">
                      <textarea
                        readOnly
                        value={shareInfo.embed_code || `<iframe src="${shareInfo.share_url}" width="100%" height="600" frameborder="0"></iframe>`}
                        className="w-full h-32 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-[#1D1D1F] font-mono focus:outline-none resize-none"
                        onClick={(e) => e.currentTarget.select()}
                      />
                      <button
                        onClick={() => handleCopy(shareInfo.embed_code || `<iframe src="${shareInfo.share_url}" width="100%" height="600" frameborder="0"></iframe>`, 'embed')}
                        className={`absolute top-2 right-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                          copiedEmbed 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {copiedEmbed ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                        {copiedEmbed ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
