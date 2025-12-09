import { useState, useEffect } from 'react';
import { 
  Search, 
  CheckCircle2, 
  AlertCircle, 
  TrendingUp, 
  Globe, 
  FileText,
  Image as ImageIcon,
  Link as LinkIcon,
  Sparkles,
  Download,
  RefreshCw
} from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface SEOScore {
  overall: number;
  categories: {
    metadata: number;
    content: number;
    technical: number;
    performance: number;
  };
}

interface SEOIssue {
  id: string;
  category: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  impact: string;
  fixable: boolean;
  status: 'pending' | 'fixing' | 'fixed' | 'error';
}

interface SEOSettings {
  sitemap_enabled: boolean;
  sitemap_last_generated: string;
  robots_txt_enabled: boolean;
  schema_markup_enabled: boolean;
  og_tags_enabled: boolean;
  meta_description: string;
  meta_keywords: string[];
  canonical_url: string;
}

export default function SEODashboard() {
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [score, setScore] = useState<SEOScore | null>(null);
  const [issues, setIssues] = useState<SEOIssue[]>([]);
  const [settings, setSettings] = useState<SEOSettings | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'issues' | 'settings'>('overview');

  useEffect(() => {
    loadSEOData();
  }, []);

  const loadSEOData = async () => {
    setLoading(true);
    try {
      const [scoreRes, issuesRes, settingsRes] = await Promise.all([
        api.get('/seo/score'),
        api.get('/seo/issues'),
        api.get('/seo/settings')
      ]);

      if (scoreRes.success) setScore(scoreRes.data);
      if (issuesRes.success) setIssues(issuesRes.data.issues || []);
      if (settingsRes.success) setSettings(settingsRes.data);
    } catch (error) {
      console.error('Failed to load SEO data:', error);
      toast.error('Failed to load SEO dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizeAll = async () => {
    setOptimizing(true);
    const toastId = toast.loading('Optimizing your portfolio for search engines...');

    try {
      const response = await api.post('/seo/optimize-all', {});

      if (response.success) {
        toast.success(
          `Optimization complete! Fixed ${response.data.fixed_count} issues.`,
          { id: toastId }
        );
        
        // Reload data
        await loadSEOData();
      } else {
        toast.error(response.error || 'Optimization failed', { id: toastId });
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Optimization failed', { id: toastId });
    } finally {
      setOptimizing(false);
    }
  };

  const handleFixIssue = async (issueId: string) => {
    // Update issue status
    setIssues(prev => 
      prev.map(issue => 
        issue.id === issueId 
          ? { ...issue, status: 'fixing' as const }
          : issue
      )
    );

    try {
      const response = await api.post('/seo/fix-issue', { issue_id: issueId });

      if (response.success) {
        setIssues(prev =>
          prev.map(issue =>
            issue.id === issueId
              ? { ...issue, status: 'fixed' as const }
              : issue
          )
        );
        toast.success('Issue fixed successfully!');
        
        // Reload score
        const scoreRes = await api.get('/seo/score');
        if (scoreRes.success) setScore(scoreRes.data);
      } else {
        throw new Error(response.error);
      }
    } catch (error: any) {
      setIssues(prev =>
        prev.map(issue =>
          issue.id === issueId
            ? { ...issue, status: 'error' as const }
            : issue
        )
      );
      toast.error(error.response?.data?.error || 'Failed to fix issue');
    }
  };

  const handleGenerateSitemap = async () => {
    const toastId = toast.loading('Generating sitemap...');
    
    try {
      const response = await api.post('/seo/generate-sitemap', {});
      
      if (response.success) {
        toast.success('Sitemap generated successfully!', { id: toastId });
        await loadSEOData();
      } else {
        toast.error(response.error || 'Failed to generate sitemap', { id: toastId });
      }
    } catch (error) {
      toast.error('Failed to generate sitemap', { id: toastId });
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-600',
          badge: 'bg-red-100 text-red-700'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-600',
          badge: 'bg-yellow-100 text-yellow-700'
        };
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-600',
          badge: 'bg-blue-100 text-blue-700'
        };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50/30 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#1D1D1F] mb-2">
              SEO Dashboard
            </h1>
            <p className="text-[#1D1D1F]/60">
              Optimize your portfolio for search engines
            </p>
          </div>

          <button
            onClick={handleOptimizeAll}
            disabled={optimizing || (score?.overall || 0) >= 95}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white rounded-xl font-semibold hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Sparkles className="w-5 h-5" />
            {optimizing ? 'Optimizing...' : 'Optimize Portfolio'}
          </button>
        </div>

        {/* SEO Score Card */}
        {score && (
          <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 mb-8">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-[#1D1D1F] mb-6">
                  Overall SEO Score
                </h2>
                
                <div className="flex items-end gap-8">
                  {/* Overall Score */}
                  <div className="relative">
                    <div className={`w-32 h-32 rounded-full ${getScoreBgColor(score.overall)} flex items-center justify-center`}>
                      <div className="text-center">
                        <div className={`text-4xl font-bold ${getScoreColor(score.overall)}`}>
                          {score.overall}
                        </div>
                        <div className="text-xs text-[#1D1D1F]/60">out of 100</div>
                      </div>
                    </div>
                  </div>

                  {/* Category Scores */}
                  <div className="grid grid-cols-2 gap-6 flex-1">
                    {Object.entries(score.categories).map(([category, value]) => (
                      <div key={category} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="capitalize text-[#1D1D1F]/70">{category}</span>
                          <span className={`font-semibold ${getScoreColor(value)}`}>
                            {value}%
                          </span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${
                              value >= 80 ? 'bg-green-500' :
                              value >= 60 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={loadSEOData}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-5 h-5 text-[#1D1D1F]/60" />
              </button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {['overview', 'issues', 'settings'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === tab
                  ? 'bg-white text-[#0066CC] shadow-sm'
                  : 'text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-white/50'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Globe className="w-5 h-5 text-[#0066CC]" />
                </div>
                <h3 className="font-semibold text-[#1D1D1F]">Sitemap</h3>
              </div>
              <p className="text-sm text-[#1D1D1F]/60 mb-4">
                {settings?.sitemap_enabled 
                  ? `Last generated ${new Date(settings.sitemap_last_generated || '').toLocaleDateString()}`
                  : 'Not generated yet'}
              </p>
              <button
                onClick={handleGenerateSitemap}
                className="w-full py-2 bg-gray-100 text-[#1D1D1F] rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
              >
                Generate Sitemap
              </button>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <FileText className="w-5 h-5 text-green-600" />
                </div>
                <h3 className="font-semibold text-[#1D1D1F]">Schema Markup</h3>
              </div>
              <p className="text-sm text-[#1D1D1F]/60 mb-4">
                {settings?.schema_markup_enabled ? 'Enabled' : 'Disabled'}
              </p>
              <div className="flex items-center gap-2">
                <CheckCircle2 className={`w-4 h-4 ${settings?.schema_markup_enabled ? 'text-green-600' : 'text-gray-300'}`} />
                <span className="text-xs text-[#1D1D1F]/60">
                  {settings?.schema_markup_enabled ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="font-semibold text-[#1D1D1F]">Performance</h3>
              </div>
              <p className="text-sm text-[#1D1D1F]/60 mb-4">
                Page load optimization
              </p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500" style={{ width: `${score?.categories.performance || 0}%` }} />
                </div>
                <span className="text-xs font-semibold text-[#1D1D1F]">
                  {score?.categories.performance || 0}%
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'issues' && (
          <div className="space-y-4">
            {issues.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-gray-100">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-[#1D1D1F] mb-2">
                  No Issues Found!
                </h3>
                <p className="text-[#1D1D1F]/60">
                  Your portfolio is fully optimized for search engines.
                </p>
              </div>
            ) : (
              issues.map((issue) => {
                const styles = getSeverityStyles(issue.severity);
                
                return (
                  <div
                    key={issue.id}
                    className={`bg-white rounded-2xl p-6 shadow-sm border ${styles.border}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-start gap-3 mb-3">
                          <AlertCircle className={`w-5 h-5 mt-0.5 ${styles.icon}`} />
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-semibold text-[#1D1D1F]">
                                {issue.title}
                              </h3>
                              <span className={`text-xs px-2 py-1 rounded-full ${styles.badge} font-medium uppercase`}>
                                {issue.severity}
                              </span>
                            </div>
                            <p className="text-sm text-[#1D1D1F]/70 mb-2">
                              {issue.description}
                            </p>
                            <p className="text-xs text-[#1D1D1F]/50">
                              <strong>Impact:</strong> {issue.impact}
                            </p>
                          </div>
                        </div>
                      </div>

                      {issue.fixable && issue.status !== 'fixed' && (
                        <button
                          onClick={() => handleFixIssue(issue.id)}
                          disabled={issue.status === 'fixing'}
                          className="px-4 py-2 bg-[#0066CC] text-white rounded-lg hover:bg-[#0052A3] transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {issue.status === 'fixing' ? 'Fixing...' : 'Fix Now'}
                        </button>
                      )}
                      
                      {issue.status === 'fixed' && (
                        <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
                          <CheckCircle2 className="w-4 h-4" />
                          Fixed
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'settings' && settings && (
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold text-[#1D1D1F] mb-6">
              SEO Configuration
            </h2>
            
            <div className="space-y-6">
              {/* Sitemap */}
              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-[#1D1D1F] mb-1">XML Sitemap</h3>
                  <p className="text-sm text-[#1D1D1F]/60">
                    Automatically generate and submit sitemap to search engines
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  settings.sitemap_enabled 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {settings.sitemap_enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>

              {/* Schema Markup */}
              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-[#1D1D1F] mb-1">Schema.org Markup</h3>
                  <p className="text-sm text-[#1D1D1F]/60">
                    Rich snippets for better search results display
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  settings.schema_markup_enabled 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {settings.schema_markup_enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>

              {/* Open Graph */}
              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-[#1D1D1F] mb-1">Open Graph Tags</h3>
                  <p className="text-sm text-[#1D1D1F]/60">
                    Optimize how your portfolio appears on social media
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  settings.og_tags_enabled 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {settings.og_tags_enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>

              {/* Robots.txt */}
              <div className="flex items-center justify-between py-4">
                <div>
                  <h3 className="font-medium text-[#1D1D1F] mb-1">Robots.txt</h3>
                  <p className="text-sm text-[#1D1D1F]/60">
                    Control search engine crawler access
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  settings.robots_txt_enabled 
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {settings.robots_txt_enabled ? 'Enabled' : 'Disabled'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

