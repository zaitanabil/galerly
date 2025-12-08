// Global Search Component - Search across galleries, photos, clients, leads
import { useState, useEffect, useRef } from 'react';
import { Search, X, Image, Users, Mail, Calendar, Filter } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';

interface SearchResult {
  id: string;
  type: 'gallery' | 'photo' | 'client' | 'lead';
  title: string;
  subtitle: string;
  metadata?: string;
  url: string;
  thumbnail?: string;
}

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function GlobalSearch({ isOpen, onClose }: GlobalSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    galleries: true,
    photos: true,
    clients: true,
    leads: true
  });
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (query.length >= 2) {
      performSearch();
    } else {
      setResults([]);
    }
  }, [query, filters]);

  const performSearch = async () => {
    setLoading(true);
    try {
      // Search multiple endpoints
      const searchPromises = [];

      if (filters.galleries) {
        searchPromises.push(
          api.get(`/galleries/search?q=${encodeURIComponent(query)}`).catch(() => ({ data: { galleries: [] } }))
        );
      }

      if (filters.clients) {
        searchPromises.push(
          api.get(`/crm/leads?search=${encodeURIComponent(query)}`).catch(() => ({ data: { leads: [] } }))
        );
      }

      const responses = await Promise.all(searchPromises);
      
      // Combine and format results
      const combinedResults: SearchResult[] = [];

      // Process galleries
      if (responses[0]?.data?.galleries) {
        responses[0].data.galleries.slice(0, 5).forEach((gallery: any) => {
          combinedResults.push({
            id: gallery.id,
            type: 'gallery',
            title: gallery.name,
            subtitle: gallery.client_email || 'No client',
            metadata: new Date(gallery.created_at).toLocaleDateString(),
            url: `/gallery/${gallery.id}`,
            thumbnail: gallery.cover_photo_url
          });
        });
      }

      // Process leads/clients
      if (responses[1]?.data?.leads) {
        responses[1].data.leads.slice(0, 5).forEach((lead: any) => {
          combinedResults.push({
            id: lead.id,
            type: 'lead',
            title: lead.name,
            subtitle: lead.email,
            metadata: `${lead.quality} - ${lead.status}`,
            url: `/crm#lead-${lead.id}`
          });
        });
      }

      setResults(combinedResults);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'gallery': return Image;
      case 'photo': return Image;
      case 'client': return Users;
      case 'lead': return Mail;
      default: return Calendar;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-20 px-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[70vh] flex flex-col">
        {/* Search Input */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-[#1D1D1F]/40 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search galleries, clients, leads..."
              className="flex-1 text-lg bg-transparent outline-none text-[#1D1D1F] placeholder-[#1D1D1F]/40"
            />
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
            >
              <X className="w-5 h-5 text-[#1D1D1F]/60" />
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 mt-3">
            <Filter className="w-4 h-4 text-[#1D1D1F]/40" />
            {Object.entries(filters).map(([key, value]) => (
              <button
                key={key}
                onClick={() => setFilters({ ...filters, [key]: !value })}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  value
                    ? 'bg-[#0066CC] text-white'
                    : 'bg-gray-100 text-[#1D1D1F]/60'
                }`}
              >
                {key.charAt(0).toUpperCase() + key.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-2">
          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-[#1D1D1F]/60">Searching...</p>
            </div>
          ) : query.length < 2 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-[#1D1D1F]/20 mx-auto mb-3" />
              <p className="text-sm text-[#1D1D1F]/60">Type at least 2 characters to search</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-[#1D1D1F]/60">No results found</p>
            </div>
          ) : (
            <div className="space-y-1">
              {results.map((result) => {
                const Icon = getIcon(result.type);
                return (
                  <Link
                    key={result.id}
                    to={result.url}
                    onClick={onClose}
                    className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    {result.thumbnail ? (
                      <img
                        src={result.thumbnail}
                        alt={result.title}
                        className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-[#0066CC]" />
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h4 className="font-medium text-[#1D1D1F] truncate">{result.title}</h4>
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                          {result.type}
                        </span>
                      </div>
                      <p className="text-sm text-[#1D1D1F]/60 truncate">{result.subtitle}</p>
                      {result.metadata && (
                        <p className="text-xs text-[#1D1D1F]/40 mt-0.5">{result.metadata}</p>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-100 text-center">
          <p className="text-xs text-[#1D1D1F]/40">
            Press <kbd className="px-2 py-1 bg-gray-100 rounded text-[#1D1D1F]/60">ESC</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );
}

// Global Search Trigger Button - For header/dashboard
export function GlobalSearchTrigger({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-4 py-2 bg-white/50 border border-gray-200 rounded-full hover:bg-white hover:border-gray-300 transition-all"
    >
      <Search className="w-4 h-4 text-[#1D1D1F]/60" />
      <span className="text-sm text-[#1D1D1F]/60">Search...</span>
      <kbd className="ml-2 px-2 py-0.5 bg-gray-100 text-xs text-[#1D1D1F]/60 rounded">
        ⌘K
      </kbd>
    </button>
  );
}

// Keyboard shortcut hook (Cmd+K / Ctrl+K)
export function useGlobalSearchShortcut(onOpen: () => void) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpen();
      }
      if (e.key === 'Escape') {
        onOpen(); // Toggle off
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onOpen]);
}
