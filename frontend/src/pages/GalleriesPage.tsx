// Galleries List Page
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGalleries, usePhotos } from '../hooks/useApi';
import { 
  Plus, Image as ImageIcon, Users, Search, 
  Settings, LogOut, ChevronRight, LayoutGrid, List as ListIcon, Download, Eye
} from 'lucide-react';
import { getImageUrl } from '../config/env';
import ProgressiveImage from '../components/ProgressiveImage';

interface Gallery {
  id: string;
  name: string;
  client_name?: string;
  status: string;
  cover_photo?: string;
  cover_photo_url?: string;
  thumbnail_url?: string;
  photo_count?: number;
  view_count?: number;
  download_count?: number;
  created_at: string;
  updated_at: string;
}

export default function GalleriesPage() {
  const { logout } = useAuth();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchType, setSearchType] = useState<'gallery' | 'photo'>('gallery');
  const [searchTerm, setSearchTerm] = useState('');
  // Debounce search term could be good, but for now simple
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  const { data: galleriesData, loading: galleriesLoading } = useGalleries();
  const { data: photosData, loading: photosLoading } = usePhotos(
    searchType === 'photo' ? { q: searchTerm } : { q: '' }
  );

  const galleries = galleriesData?.galleries || [];
  const photos = photosData?.photos || [];
  const loading = galleriesLoading || (searchType === 'photo' && photosLoading);

  // Filter galleries
  const filteredGalleries = galleries.filter(gallery => {
    if (searchType === 'photo') return false; // Don't filter galleries in photo mode
    const matchesSearch = (gallery.name || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (gallery.client_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || 
                          (statusFilter === 'active' && (gallery.status === 'active' || gallery.status === 'published')) ||
                          gallery.status === statusFilter;
                          
    return matchesSearch && matchesStatus;
  });

  if (loading && !searchTerm && searchType === 'gallery') {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-[#1D1D1F]/60 text-sm font-medium animate-pulse">Loading Galleries...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Dashboard</Link>
              <Link to="/galleries" className="text-sm font-medium text-[#1D1D1F]">Galleries</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Analytics</Link>
              <Link to="/billing" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Billing</Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full transition-all">
              <Settings className="w-5 h-5" />
            </Link>
            <button onClick={logout} className="p-2 text-[#1D1D1F]/60 hover:text-red-600 hover:bg-red-50 rounded-full transition-all">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <h1 className="text-3xl font-medium text-[#1D1D1F] tracking-tight mb-2">
              Your Galleries
            </h1>
            <p className="text-[#1D1D1F]/60">
              Manage your client collections ({filteredGalleries.length} total)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link 
              to="/new-gallery" 
              className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black hover:shadow-lg transition-all"
            >
              <Plus className="w-4 h-4" />
              New Gallery
            </Link>
          </div>
        </div>

        {/* Toolbar */}
        <div className="bg-white p-4 rounded-2xl border border-gray-200/60 shadow-sm mb-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto flex-1">
             {/* Search Type Toggle */}
             <div className="flex bg-[#F5F5F7] p-1 rounded-xl shrink-0">
                <button
                    onClick={() => setSearchType('gallery')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        searchType === 'gallery' ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-[#1D1D1F]/60'
                    }`}
                >
                    Galleries
                </button>
                <button
                    onClick={() => setSearchType('photo')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        searchType === 'photo' ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-[#1D1D1F]/60'
                    }`}
                >
                    Photos
                </button>
             </div>

             {/* Search Input */}
             <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#1D1D1F]/40" />
            <input 
              type="text" 
                placeholder={searchType === 'gallery' ? "Search galleries..." : "Search photos by tag, filename..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[#F5F5F7] border-none rounded-xl text-sm focus:ring-2 focus:ring-[#0066CC]/20 focus:bg-white transition-all"
            />
            </div>
          </div>
          
          <div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto">
            {searchType === 'gallery' && (
                <>
            <div className="flex items-center gap-1 bg-[#F5F5F7] p-1 rounded-lg">
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-[#1D1D1F]/40 hover:text-[#1D1D1F]'}`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? 'bg-white shadow-sm text-[#1D1D1F]' : 'text-[#1D1D1F]/40 hover:text-[#1D1D1F]'}`}
              >
                <ListIcon className="w-4 h-4" />
              </button>
            </div>
            
            <div className="h-6 w-px bg-gray-200 mx-1"></div>
            
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-[#F5F5F7] border-none rounded-xl text-sm text-[#1D1D1F] focus:ring-2 focus:ring-[#0066CC]/20 cursor-pointer"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </select>
                </>
            )}
          </div>
        </div>

        {/* Content */}
        {searchType === 'photo' ? (
            // Photo Grid
            photos.length === 0 ? (
                <div className="bg-white rounded-[32px] border border-gray-200 border-dashed p-16 text-center">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <ImageIcon className="w-8 h-8 text-gray-300" />
                    </div>
                    <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">
                    {searchTerm ? 'No photos found' : 'Search for photos'}
                    </h3>
                    <p className="text-[#1D1D1F]/60 text-sm mb-0 max-w-sm mx-auto">
                    Enter keywords to search across all your galleries.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {photos.map((photo) => (
                        <Link 
                            key={photo.id} 
                            to={`/gallery/${photo.gallery_id}`}
                            className="aspect-square bg-gray-100 rounded-xl overflow-hidden group relative block"
                        >
                            <ProgressiveImage
                                src={getImageUrl(photo.thumbnail_url || photo.url)}
                                placeholderSrc=""
                                alt={photo.filename}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                            <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-[10px] text-white bg-black/50 backdrop-blur-sm px-2 py-1 rounded-full truncate block">
                                    {photo.filename}
                                </span>
                            </div>
                        </Link>
                    ))}
                </div>
            )
        ) : (
            // Gallery Grid/List
            filteredGalleries.length === 0 ? (
          <div className="bg-white rounded-[32px] border border-gray-200 border-dashed p-16 text-center">
            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <ImageIcon className="w-8 h-8 text-gray-300" />
            </div>
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">
              {searchTerm ? 'No galleries found' : 'No galleries yet'}
            </h3>
            <p className="text-[#1D1D1F]/60 text-sm mb-8 max-w-sm mx-auto">
              {searchTerm ? 'Try adjusting your search terms.' : 'Create your first gallery to start sharing your work with clients.'}
            </p>
            {!searchTerm && (
              <Link to="/new-gallery" className="inline-flex items-center gap-2 px-6 py-3 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black transition-all">
                <Plus className="w-4 h-4" /> Create Gallery
              </Link>
            )}
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredGalleries.map((gallery: Gallery) => {
              const coverImage = gallery.cover_photo || gallery.cover_photo_url || gallery.thumbnail_url;
              return (
                <Link 
                  key={gallery.id} 
                  to={`/gallery/${gallery.id}`}
                  className="group bg-white rounded-[24px] p-3 border border-gray-200/60 shadow-[0_2px_8px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300"
                >
                  <div className="flex flex-col h-full">
                    <div className="aspect-[3/2] rounded-2xl bg-gray-100 overflow-hidden relative shadow-inner mb-4">
                      {coverImage ? (
                        <img src={getImageUrl(coverImage)} alt={gallery.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-300 bg-gray-50">
                          <ImageIcon className="w-8 h-8 opacity-50" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors" />
                      
                      <div className="absolute top-3 right-3">
                        <span className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full backdrop-blur-md border shadow-sm ${
                          gallery.status === 'published' || gallery.status === 'active' 
                            ? 'bg-white/90 text-green-700 border-white/20' 
                            : 'bg-white/90 text-gray-600 border-white/20'
                        }`}>
                          {gallery.status || 'Active'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="px-1 flex flex-col flex-grow">
                      <h3 className="text-lg font-medium text-[#1D1D1F] truncate mb-1 group-hover:text-[#0066CC] transition-colors">
                        {gallery.name || 'Untitled Gallery'}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-[#1D1D1F]/50 mb-4">
                        <span className="flex items-center gap-1.5 truncate"><Users className="w-3 h-3" /> {gallery.client_name || 'No Client'}</span>
                        <span className="text-gray-300">•</span>
                        <span className="flex-shrink-0">{gallery.photo_count || 0} photos</span>
                      </div>
                      
                      <div className="mt-auto pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-[#1D1D1F]/40">
                        <span>Updated {new Date(gallery.updated_at || gallery.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="bg-white rounded-[24px] border border-gray-200/60 shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-[#F5F5F7] border-b border-gray-200">
                <tr>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">Gallery</th>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">Client</th>
                  <th className="text-left py-4 px-6 text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">Status</th>
                  <th className="text-right py-4 px-6 text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">Stats</th>
                  <th className="text-right py-4 px-6 text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">Created</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredGalleries.map((gallery: Gallery) => {
                   const coverImage = gallery.cover_photo || gallery.cover_photo_url || gallery.thumbnail_url;
                   return (
                    <tr key={gallery.id} className="group hover:bg-[#F5F5F7]/50 transition-colors">
                      <td className="py-4 px-6">
                        <Link to={`/gallery/${gallery.id}`} className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                            {coverImage ? (
                              <img src={getImageUrl(coverImage)} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-300">
                                <ImageIcon className="w-4 h-4" />
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-[#1D1D1F] group-hover:text-[#0066CC] transition-colors">{gallery.name || 'Untitled'}</p>
                            <p className="text-xs text-[#1D1D1F]/50">{gallery.photo_count || 0} photos</p>
                          </div>
                        </Link>
                      </td>
                      <td className="py-4 px-6 text-sm text-[#1D1D1F]/70">{gallery.client_name || '-'}</td>
                      <td className="py-4 px-6">
                        <span className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border ${
                          gallery.status === 'published' || gallery.status === 'active' 
                            ? 'bg-green-50 text-green-700 border-green-100' 
                            : 'bg-yellow-50 text-yellow-700 border-yellow-100'
                        }`}>
                          {gallery.status || 'Active'}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right text-sm text-[#1D1D1F]/70">
                        <div className="flex items-center justify-end gap-3 text-xs">
                          <span className="flex items-center gap-1" title="Views"><Eye className="w-3 h-3 text-[#1D1D1F]/30" /> {gallery.view_count || 0}</span>
                          <span className="flex items-center gap-1" title="Downloads"><Download className="w-3 h-3 text-[#1D1D1F]/30" /> {gallery.download_count || 0}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-right text-sm text-[#1D1D1F]/70">
                        {new Date(gallery.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <Link to={`/gallery/${gallery.id}`} className="p-2 hover:bg-gray-100 rounded-full inline-block text-[#1D1D1F]/40 hover:text-[#0066CC]">
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                   );
                })}
              </tbody>
            </table>
          </div>
        ))}
      </main>
    </div>
  );
}

