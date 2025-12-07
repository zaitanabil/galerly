import { useEffect, useState } from 'react';
import { Image, Trash2, Search, User, Calendar } from 'lucide-react';
import adminAPI from '../services/api';

export default function Galleries() {
  const [galleries, setGalleries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deleteModal, setDeleteModal] = useState<any>(null);
  
  useEffect(() => {
    loadGalleries();
  }, []);
  
  const loadGalleries = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getAllGalleries(search);
      setGalleries(data.galleries);
    } catch (error) {
      console.error('Error loading galleries:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearch = () => {
    loadGalleries();
  };
  
  const handleDelete = async (gallery: any) => {
    try {
      await adminAPI.deleteGallery(gallery.id);
      setDeleteModal(null);
      loadGalleries();
    } catch (error) {
      console.error('Error deleting gallery:', error);
      alert('Failed to delete gallery');
    }
  };
  
  return (
    <div>
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-dark">Galleries</h1>
        <p className="text-sm sm:text-base text-gray-600 mt-1">View and manage all galleries across the platform</p>
      </div>
      
      {/* Search */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search galleries by name, client, or photographer..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Total Galleries</p>
          <p className="text-2xl font-bold text-dark mt-1">{galleries.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Total Photos</p>
          <p className="text-2xl font-bold text-dark mt-1">
            {galleries.reduce((sum, g) => sum + (g.photo_count || 0), 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-600">Avg Photos/Gallery</p>
          <p className="text-2xl font-bold text-dark mt-1">
            {galleries.length > 0 ? Math.round(galleries.reduce((sum, g) => sum + (g.photo_count || 0), 0) / galleries.length) : 0}
          </p>
        </div>
      </div>
      
      {/* Gallery List */}
      {loading ? (
        <div className="flex items-center justify-center h-64 bg-white rounded-xl border border-gray-200">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : galleries.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Image className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No galleries found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {galleries.map((gallery) => (
            <div key={gallery.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
              {/* Cover Image */}
              {gallery.cover_photo_url || gallery.thumbnail_url ? (
                <div className="aspect-video bg-gray-100 overflow-hidden">
                  <img 
                    src={gallery.cover_photo_url || gallery.thumbnail_url} 
                    alt={gallery.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="aspect-video bg-gray-100 flex items-center justify-center">
                  <Image className="w-12 h-12 text-gray-300" />
                </div>
              )}
              
              {/* Info */}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-dark mb-2 truncate">{gallery.name}</h3>
                
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="w-4 h-4" />
                    <span className="truncate">{gallery.user?.name || gallery.user?.email || 'Unknown'}</span>
                  </div>
                  
                  {gallery.client_name && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <User className="w-4 h-4" />
                      <span className="truncate">Client: {gallery.client_name}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(gallery.created_at).toLocaleDateString()}</span>
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Image className="w-4 h-4" />
                    <span>{gallery.photo_count || 0} photos</span>
                  </div>
                </div>
                
                {/* Actions */}
                <button
                  onClick={() => setDeleteModal(gallery)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Gallery
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {deleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-dark mb-4">Delete Gallery?</h3>
            <p className="text-gray-600 mb-2">
              Are you sure you want to delete <strong>{deleteModal.name}</strong>?
            </p>
            <p className="text-sm text-gray-500 mb-6">
              This will permanently delete {deleteModal.photo_count || 0} photos and cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteModal(null)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteModal)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
