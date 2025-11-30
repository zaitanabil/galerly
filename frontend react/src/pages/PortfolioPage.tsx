// Portfolio page - Individual photographer portfolio
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MapPin, Instagram, Globe, Mail, ArrowLeft } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';
import { cdnBaseUrl } from '../config/env';

interface Photographer {
  name: string;
  business_name?: string;
  city?: string;
  country?: string;
  website?: string;
  instagram?: string;
  bio?: string;
  email: string;
}

interface PortfolioPhoto {
  photo_id: string;
  thumbnail_url: string;
  gallery_name: string;
}

interface PortfolioGallery {
  name: string;
  photos?: {
    id: string;
    url: string;
    thumbnail_url?: string;
  }[];
}

export default function PortfolioPage() {
  const { userId } = useParams<{ userId: string }>();
  const [photographer, setPhotographer] = useState<Photographer | null>(null);
  const [photos, setPhotos] = useState<PortfolioPhoto[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPortfolio = useCallback(async () => {
    if (!userId) return;
    
    setLoading(true);

    try {
      // Use portfolio endpoint to get full customization and SEO settings
      const response = await api.get<{ 
        photographer: Photographer;
        portfolio: {
          seo_settings?: {
            title?: string;
            description?: string;
            keywords?: string;
          };
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          [key: string]: any;
        };
        galleries: PortfolioGallery[];
      }>(`/portfolio/${userId}`);

      if (response.success && response.data) {
        setPhotographer(response.data.photographer);
        
        // Apply SEO Settings
        const seo = response.data.portfolio?.seo_settings;
        if (seo) {
          if (seo.title) document.title = seo.title;
          if (seo.description) {
            let metaDesc = document.querySelector('meta[name="description"]');
            if (!metaDesc) {
              metaDesc = document.createElement('meta');
              metaDesc.setAttribute('name', 'description');
              document.head.appendChild(metaDesc);
            }
            metaDesc.setAttribute('content', seo.description);
          }
        } else if (response.data.photographer) {
           // Fallback SEO
           document.title = `${response.data.photographer.name} | Portfolio`;
        }
        
        // Extract photos from public galleries
        const allPhotos: PortfolioPhoto[] = [];
        if (response.data.galleries && Array.isArray(response.data.galleries)) {
          response.data.galleries.forEach((gallery) => {
            if (gallery.photos && Array.isArray(gallery.photos)) {
              gallery.photos.forEach((photo) => {
                allPhotos.push({
                  photo_id: photo.id,
                  thumbnail_url: photo.thumbnail_url || photo.url,
                  gallery_name: gallery.name
                });
              });
            }
          });
        }
        setPhotos(allPhotos);
      }
    } catch (error) {
      console.error("Error loading portfolio:", error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (userId) {
      loadPortfolio();
    }
  }, [userId, loadPortfolio]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-[#1D1D1F]/60">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (!photographer) {
    return (
      <div className="min-h-screen bg-[#F5F5F7]">
        <Header />
        <div className="flex items-center justify-center min-h-[70vh]">
          <div className="text-center">
            <p className="text-lg text-[#1D1D1F]/60 mb-4">Portfolio not found</p>
            <Link to="/photographers" className="text-[#0066CC] hover:text-[#0052A3]">
              Back to Photographers
            </Link>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Back Button */}
          <Link
            to="/photographers"
            className="inline-flex items-center gap-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Photographers
          </Link>

          {/* Photographer Info */}
          <div className="glass-panel p-8 md:p-12 mb-12">
            <div className="max-w-3xl">
              <h1 className="text-4xl md:text-5xl font-serif font-medium text-[#1D1D1F] mb-4">
                {photographer.business_name || photographer.name}
              </h1>
              
              {photographer.city && photographer.country && (
                <div className="flex items-center gap-2 text-lg text-[#1D1D1F]/60 mb-6">
                  <MapPin className="w-5 h-5" />
                  <span>
                    {photographer.city}, {photographer.country}
                  </span>
                </div>
              )}

              {photographer.bio && (
                <p className="text-lg text-[#1D1D1F]/70 leading-relaxed mb-8">
                  {photographer.bio}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-4">
                <a
                  href={`mailto:${photographer.email}`}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-105 shadow-lg shadow-blue-500/20"
                >
                  <Mail className="w-5 h-5" />
                  Get in Touch
                </a>
                
                {photographer.website && (
                  <a
                    href={photographer.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-white/50 border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-white transition-all"
                  >
                    <Globe className="w-5 h-5" />
                    Website
                  </a>
                )}
                
                {photographer.instagram && (
                  <a
                    href={`https://instagram.com/${photographer.instagram.replace('@', '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-white/50 border border-gray-200 text-[#1D1D1F] rounded-full font-medium hover:bg-white transition-all"
                  >
                    <Instagram className="w-5 h-5" />
                    Instagram
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Portfolio Grid */}
          <div>
            <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-6">
              Portfolio
            </h2>
            
            {photos.length === 0 ? (
              <div className="glass-panel p-12 text-center">
                <p className="text-[#1D1D1F]/60">No portfolio photos yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {photos.map((photo) => (
                  <div
                    key={photo.photo_id}
                    className="aspect-square bg-gray-100 rounded-2xl overflow-hidden group cursor-pointer"
                  >
                    <img
                      src={`${cdnBaseUrl}${photo.thumbnail_url}`}
                      alt={photo.gallery_name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

