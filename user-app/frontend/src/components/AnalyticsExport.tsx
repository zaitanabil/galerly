// Analytics Export Component
import { useState } from 'react';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface AnalyticsExportProps {
  onClose?: () => void;
}

export default function AnalyticsExport({ onClose }: AnalyticsExportProps) {
  const [exportType, setExportType] = useState<'summary' | 'galleries' | 'photos' | 'clients' | 'revenue'>('summary');
  const [format, setFormat] = useState<'csv' | 'pdf'>('csv');
  const [dateRange, setDateRange] = useState('30');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - parseInt(dateRange) * 24 * 60 * 60 * 1000).toISOString();

      if (format === 'csv') {
        // Download CSV directly
        const params = new URLSearchParams({
          type: exportType,
          start_date: startDate,
          end_date: endDate
        });
        
        const response = await fetch(`/api/v1/analytics/export/csv?${params.toString()}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_${exportType}_${startDate.slice(0, 10)}_to_${endDate.slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('CSV exported successfully');
      } else {
        // Generate PDF
        const response = await api.post('/analytics/export/pdf', {
          type: exportType,
          start_date: startDate,
          end_date: endDate
        });
        
        if (response.success && response.data.pdf_url) {
          window.open(response.data.pdf_url, '_blank');
          toast.success('PDF generated successfully');
        }
      }
      
      if (onClose) onClose();
    } catch (error) {
      toast.error('Failed to export analytics');
      console.error('Export error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 max-w-md w-full">
        <h2 className="text-xl font-medium text-[#1D1D1F] dark:text-white mb-4">
          Export Analytics
        </h2>

        {/* Export Type */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-[#1D1D1F] dark:text-white mb-2">
            Data to Export
          </label>
          <select
            value={exportType}
            onChange={(e) => setExportType(e.target.value as any)}
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
          >
            <option value="summary">Summary Statistics</option>
            <option value="galleries">Galleries</option>
            <option value="photos">Photos</option>
            <option value="clients">Clients</option>
            <option value="revenue">Revenue</option>
          </select>
        </div>

        {/* Date Range */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-[#1D1D1F] dark:text-white mb-2">
            Date Range
          </label>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>

        {/* Format */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-[#1D1D1F] dark:text-white mb-2">
            Format
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setFormat('csv')}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 transition-all ${
                format === 'csv'
                  ? 'border-[#0066CC] bg-blue-50 dark:bg-blue-900/20 text-[#0066CC]'
                  : 'border-gray-200 dark:border-gray-700 text-[#1D1D1F] dark:text-white'
              }`}
            >
              <FileSpreadsheet className="w-5 h-5" />
              <span>CSV</span>
            </button>
            <button
              onClick={() => setFormat('pdf')}
              className={`flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 transition-all ${
                format === 'pdf'
                  ? 'border-[#0066CC] bg-blue-50 dark:bg-blue-900/20 text-[#0066CC]'
                  : 'border-gray-200 dark:border-gray-700 text-[#1D1D1F] dark:text-white'
              }`}
            >
              <FileText className="w-5 h-5" />
              <span>PDF</span>
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {onClose && (
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-700 text-[#1D1D1F] dark:text-white rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={loading}
            className="flex-1 px-4 py-2.5 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>Exporting...</>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Export
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
