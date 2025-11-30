// Photographers Directory page - Redesigned as a stunning landing page
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Instagram, Globe, Camera, Search, TrendingUp, Users, Award, ArrowRight } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { api } from '../utils/api';

interface Photographer {
  id: string;
  name: string;
  business_name?: string;
  city?: string;
  country?: string;
  website?: string;
  instagram?: string;
  bio?: string;
  cover_photo_url?: string;
  specialties?: string[];
  gallery_count?: number;
  photo_count?: number;
}

import CityAutocomplete from '../components/CityAutocomplete';

export default function PhotographersPage() {
  const [photographers, setPhotographers] = useState<Photographer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'wedding' | 'portrait' | 'event' | 'commercial'>('all');

  const loadPhotographers = useCallback(async () => {
    setLoading(true);
    
    // Build query params
    const params = new URLSearchParams();
    if (searchTerm) {
      // Backend supports filtering by city via 'city' param. 
      // For general search, we might need client-side filtering if backend doesn't support 'q'.
      // But let's assume 'city' is the primary search intent for now as per backend.
      // If the user types a city name, we send it.
      params.append('city', searchTerm);
    }
    
    if (selectedFilter !== 'all') {
      params.append('specialty', selectedFilter);
    }

    const response = await api.get<{ photographers: Photographer[] }>(`/photographers?${params.toString()}`);
    
    if (response.success && response.data) {
      setPhotographers(response.data.photographers || []);
    }
    
    setLoading(false);
  }, [searchTerm, selectedFilter]);

  useEffect(() => {
    loadPhotographers();
  }, [loadPhotographers]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadPhotographers();
    }, 500);
    return () => clearTimeout(timer);
  }, [loadPhotographers]);

  // Client-side filtering as a fallback for name/bio search if backend only filters by city/specialty
  const filteredPhotographers = photographers.filter(() => {
    if (!searchTerm) return true;
    // We rely on backend filtering mostly now
    return true; 
  });

  const categories = [
    { id: 'all', label: 'All Photographers', icon: Camera },
    { id: 'wedding', label: 'Wedding', icon: Award },
    { id: 'portrait', label: 'Portrait', icon: Users },
    { id: 'event', label: 'Event', icon: TrendingUp },
    { id: 'commercial', label: 'Commercial', icon: Globe },
  ];

  const stats = [
    { value: photographers.length > 0 ? `${photographers.length}+` : '---', label: 'Photographers' },
    { value: '50+', label: 'Cities' },
    { value: '10K+', label: 'Photos Shared' },
    { value: '98%', label: 'Satisfaction' },
  ];

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        {/* Hero Section */}
        <div className="max-w-7xl mx-auto mb-20">
          <div className="glass-panel p-12 md:p-16 lg:p-20 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#1D1D1F]/60 mb-6">
              DISCOVER
            </p>
            <div className="flex items-center justify-center gap-3 mb-8 text-sm text-[#1D1D1F]/60">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#0066CC]" />
              <p>Talented photographers • Every city • Every style</p>
            </div>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-light text-[#1D1D1F] mb-8 leading-tight">
              Find Professional<br />Photographers Near You
            </h1>
            <p className="text-lg md:text-xl text-[#1D1D1F]/70 max-w-3xl mx-auto mb-12 leading-relaxed">
              Search local photographers by city and specialty. Discover wedding photographers, portrait photographers, event photographers, and commercial photographers. Browse portfolios, view their work, and connect with professionals who match your style.
            </p>

            {/* Enhanced Search Bar */}
            <div className="max-w-3xl mx-auto mb-12">
              <div className="relative">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40 z-10" />
                <CityAutocomplete
                  value={searchTerm}
                  onChange={setSearchTerm}
                  placeholder="Search by city (e.g. New York)..."
                  className="w-full"
                />
              </div>
            </div>

            {/* Category Filters */}
            <div className="flex flex-wrap justify-center gap-3 mb-12">
              {categories.map((category) => {
                const Icon = category.icon;
                return (
                  <button
                    key={category.id}
                    onClick={() => setSelectedFilter(category.id as typeof selectedFilter)}
                    className={`
                      flex items-center gap-2 px-6 py-3 rounded-full transition-all duration-300
                      ${selectedFilter === category.id
                        ? 'bg-[#0066CC] text-white shadow-lg scale-105'
                        : 'bg-white/60 text-[#1D1D1F]/70 hover:bg-white/80'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{category.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 pt-8 border-t border-[#1D1D1F]/10">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-light text-[#1D1D1F] mb-2">
                    {stat.value}
                  </div>
                  <div className="text-sm text-[#1D1D1F]/60">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="max-w-7xl mx-auto">
          {/* Results Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-light text-[#1D1D1F] mb-2">
                {searchTerm ? 'Search Results' : 'All Photographers'}
              </h2>
              <p className="text-sm text-[#1D1D1F]/60">
                {filteredPhotographers.length} photographer{filteredPhotographers.length !== 1 ? 's' : ''} found
              </p>
            </div>
          </div>

          {loading ? (
            <div className="glass-panel p-20 text-center">
              <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-6" />
              <p className="text-lg text-[#1D1D1F]/60">Loading photographers...</p>
              <p className="text-sm text-[#1D1D1F]/40 mt-2">Discovering talent near you</p>
            </div>
          ) : filteredPhotographers.length === 0 ? (
            <div className="glass-panel p-16 text-center">
              <Camera className="w-20 h-20 text-[#1D1D1F]/20 mx-auto mb-6" />
              <h3 className="text-2xl font-light text-[#1D1D1F] mb-3">
                No photographers found
              </h3>
              <p className="text-[#1D1D1F]/60 mb-8 max-w-md mx-auto">
                {searchTerm 
                  ? 'Try adjusting your search terms or browse all photographers'
                  : 'Be the first photographer to join our community'
                }
              </p>
              {!searchTerm && (
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-[#0066CC] text-white hover:bg-[#0055AA] transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <span>Join as Photographer</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>
              )}
            </div>
          ) : (
            <>
              {/* Photographers Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
                {filteredPhotographers.map((photographer) => (
                  <Link
                    key={photographer.id}
                    to={`/portfolio/${photographer.id}`}
                    className="glass-panel overflow-hidden group hover:shadow-2xl transition-all duration-500 hover:-translate-y-2"
                  >
                    {/* Cover Photo */}
                    <div className="aspect-[4/3] bg-gradient-to-br from-[#0066CC]/5 to-[#0066CC]/10 overflow-hidden relative">
                      {photographer.cover_photo_url ? (
                        <img
                          src={photographer.cover_photo_url}
                          alt={photographer.name}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Camera className="w-16 h-16 text-[#1D1D1F]/20" />
                        </div>
                      )}
                      {/* Overlay on Hover */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-end p-6">
                        <span className="text-white font-medium flex items-center gap-2">
                          View Portfolio
                          <ArrowRight className="w-4 h-4" />
                        </span>
                      </div>
                    </div>

                    {/* Info */}
                    <div className="p-6">
                      <h3 className="text-xl font-medium text-[#1D1D1F] mb-2 group-hover:text-[#0066CC] transition-colors">
                        {photographer.business_name || photographer.name}
                      </h3>
                      
                      {photographer.city && photographer.country && (
                        <div className="flex items-center gap-2 text-sm text-[#1D1D1F]/60 mb-2">
                          <MapPin className="w-4 h-4" />
                          <span>
                            {photographer.city}, {photographer.country}
                          </span>
                        </div>
                      )}
                      
                      {photographer.specialties && photographer.specialties.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-4">
                          {photographer.specialties.slice(0, 3).map((spec, i) => (
                            <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                              {spec}
                            </span>
                          ))}
                        </div>
                      )}
                      
                      {photographer.bio && (
                        <p className="text-sm text-[#1D1D1F]/70 line-clamp-2 mb-4 leading-relaxed">
                          {photographer.bio}
                        </p>
                      )}

                      <div className="flex gap-4 mb-4 text-sm text-[#1D1D1F]/60">
                        <div>
                            <span className="font-semibold text-[#1D1D1F]">{photographer.gallery_count || 0}</span> galleries
                        </div>
                        <div>
                            <span className="font-semibold text-[#1D1D1F]">{photographer.photo_count || 0}</span> photos
                        </div>
                      </div>
                      
                      {/* Social Links */}
                      {(photographer.website || photographer.instagram) && (
                        <div className="flex items-center gap-2 pt-4 border-t border-[#1D1D1F]/10">
                          {photographer.website && (
                            <a
                              href={photographer.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="p-2.5 hover:bg-[#1D1D1F]/5 rounded-full transition-all duration-300 group/icon"
                              title="Visit website"
                            >
                              <Globe className="w-4 h-4 text-[#1D1D1F]/60 group-hover/icon:text-[#0066CC] transition-colors" />
                            </a>
                          )}
                          {photographer.instagram && (
                            <a
                              href={`https://instagram.com/${photographer.instagram.replace('@', '')}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="p-2.5 hover:bg-[#1D1D1F]/5 rounded-full transition-all duration-300 group/icon"
                              title="View Instagram"
                            >
                              <Instagram className="w-4 h-4 text-[#1D1D1F]/60 group-hover/icon:text-[#0066CC] transition-colors" />
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </Link>
                ))}
              </div>

              {/* CTA Section for Photographers */}
              <div className="glass-panel p-12 md:p-16 text-center">
                <div className="max-w-3xl mx-auto">
                  <Camera className="w-16 h-16 text-[#0066CC] mx-auto mb-6" />
                  <h2 className="text-3xl md:text-4xl font-light text-[#1D1D1F] mb-4">
                    Are you a photographer?
                  </h2>
                  <p className="text-lg text-[#1D1D1F]/70 mb-8 leading-relaxed">
                    Join our community of professional photographers. Showcase your work, connect with clients, and grow your business with Galerly.
                  </p>
                  <div className="flex flex-wrap justify-center gap-4">
                    <Link
                      to="/register"
                      className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-[#0066CC] text-white hover:bg-[#0055AA] transition-all duration-300 shadow-lg hover:shadow-xl"
                    >
                      <span className="font-medium">Join as Photographer</span>
                      <ArrowRight className="w-5 h-5" />
                    </Link>
                    <Link
                      to="/pricing"
                      className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-white/60 text-[#1D1D1F] hover:bg-white/80 transition-all duration-300"
                    >
                      <span className="font-medium">View Pricing</span>
                    </Link>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
