// Client Dashboard page - View all galleries shared with the client
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';
import { Image, Calendar, User } from 'lucide-react';

interface ClientGallery {
  id: string;
  name: string;
  photographer_name: string;
  photo_count: number;
  created_at: string;
  cover_image?: string;
  photos?: { status: string }[];
}

export default function ClientDashboardPage() {
  const { user } = useAuth();
  const [galleries, setGalleries] = useState<ClientGallery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadClientGalleries();
  }, []);

  const loadClientGalleries = async () => {
    setLoading(true);
    
    const response = await api.get<{ galleries: ClientGallery[] }>('/client/galleries');
    if (response.success && response.data) {
      setGalleries(response.data.galleries || []);
    }

    setLoading(false);
  };

  const pendingPhotosCount = (gallery: ClientGallery) => 
    (gallery.photos || []).filter(p => p.status === 'pending').length;

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-serif font-medium text-[#1D1D1F]">
              Galerly
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-sm text-[#1D1D1F]/60">
                {user?.email}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] mb-2">
            Welcome, {user?.name || 'there'}
          </h1>
          <p className="text-lg text-[#1D1D1F]/60">
            Your shared galleries
          </p>
        </div>

        {/* Galleries Grid */}
        {loading ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#1D1D1F]/60">Loading galleries...</p>
          </div>
        ) : galleries.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Image className="w-8 h-8 text-[#0066CC]" />
            </div>
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">
              No galleries yet
            </h3>
            <p className="text-[#1D1D1F]/60">
              Galleries shared with you will appear here
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {galleries.map((gallery) => (
              <Link
                key={gallery.id}
                to={`/client-gallery/${gallery.id}`}
                className="glass-panel overflow-hidden group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 relative"
              >
                <div className="aspect-[4/3] bg-gray-100 overflow-hidden relative">
                  {gallery.cover_image ? (
                    <img
                      src={gallery.cover_image}
                      alt={gallery.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Image className="w-12 h-12 text-gray-300" />
                    </div>
                  )}
                  
                  {pendingPhotosCount(gallery) > 0 && (
                    <div className="absolute top-3 left-3 bg-amber-500 text-white text-xs font-bold px-2 py-1 rounded shadow-md">
                      {pendingPhotosCount(gallery)} pending
                    </div>
                  )}
                  
                  <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm text-white text-xs font-medium px-2 py-1 rounded">
                    {gallery.photo_count} photos
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="text-lg font-medium text-[#1D1D1F] mb-2 truncate">
                    {gallery.name}
                  </h3>
                  <div className="space-y-2 text-sm text-[#1D1D1F]/60">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      <span>{gallery.photographer_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Image className="w-4 h-4" />
                      <span>{gallery.photo_count} photos</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(gallery.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

