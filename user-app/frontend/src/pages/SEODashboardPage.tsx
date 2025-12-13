import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, TrendingUp, FileText, Globe, Settings, AlertCircle, CheckCircle, XCircle, Zap, ExternalLink } from 'lucide-react';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

interface SEOSettings {
  meta_title?: string;
  meta_description?: string;
  og_image_url?: string;
  sitemap_enabled: boolean;
  robots_txt_enabled: boolean;
  schema_markup_enabled: boolean;
  last_optimized_at?: string;
}

interface SEOScore {
  overall_score: number;
  meta_score: number;
  performance_score: number;
  content_score: number;
  technical_score: number;
}

interface SEOIssue {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: string;
  title: string;
  description: string;
  fix_action?: string;
}

export default function SEODashboardPage() {
  const [settings, setSettings] = useState<SEOSettings>({
    sitemap_enabled: true,
    robots_txt_enabled: true,
    schema_markup_enabled: true
  });
  const [score, setScore] = useState<SEOScore | null>(null);
  const [issues, setIssues] = useState<SEOIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);

  useEffect(() => {
    loadSEOData();
  }, []);

  const loadSEOData = async () => {
    try {
      const [settingsRes, scoreRes, issuesRes] = await Promise.all([
        api.get('/seo/settings'),
        api.get('/seo/score'),
        api.get('/seo/issues')
      ]);

      if (settingsRes.success && settingsRes.data) {
        setSettings(settingsRes.data);
      }

      if (scoreRes.success && scoreRes.data) {
        setScore(scoreRes.data);
      }

      if (issuesRes.success && issuesRes.data) {
        setIssues(issuesRes.data.issues || []);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('SEO Tools is a Pro/Ultimate feature');
      } else {
        toast.error('Failed to load SEO data');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOneClickOptimize = async () => {
    setOptimizing(true);
    try {
      const response = await api.post('/seo/one-click-optimize');
      if (response.success) {
        toast.success('SEO optimization complete!');
        loadSEOData();
      } else {
        toast.error('Optimization failed');
      }
    } catch (error) {
      toast.error('Failed to optimize SEO');
    } finally {
      setOptimizing(false);
    }
  };

  const handleFixIssue = async (issueId: string) => {
    try {
      const response = await api.post(`/seo/issues/${issueId}/fix`);
      if (response.success) {
        toast.success('Issue fixed!');
        loadSEOData();
      } else {
        toast.error('Failed to fix issue');
      }
    } catch (error) {
      toast.error('Failed to fix issue');
    }
  };

  const handleUpdateSettings = async (updates: Partial<SEOSettings>) => {
    try {
      const response = await api.put('/seo/settings', { ...settings, ...updates });
      if (response.success) {
        setSettings({ ...settings, ...updates });
        toast.success('Settings updated');
      } else {
        toast.error('Failed to update settings');
      }
    } catch (error) {
      toast.error('Failed to update settings');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const getSeverityBadge = (severity: string) => {
    const badges = {
      critical: { color: 'bg-red-100 text-red-800 border-red-200', icon: XCircle },
      warning: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertCircle },
      info: { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: AlertCircle }
    };
    
    const badge = badges[severity as keyof typeof badges] || badges.info;
    const Icon = badge.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
        <Icon className="w-3.5 h-3.5" />
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F5F7] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-[#1D1D1F]/60">Loading SEO data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Dashboard</Link>
              <Link to="/seo" className="text-sm font-medium text-[#1D1D1F]">SEO</Link>
              <Link to="/analytics" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F]">Analytics</Link>
            </nav>
          </div>
          <Link to="/settings" className="p-2 text-[#1D1D1F]/60 hover:text-[#1D1D1F] hover:bg-black/5 rounded-full">
            <Settings className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-medium text-[#1D1D1F]">SEO Dashboard</h1>
              <span className="px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">Pro</span>
            </div>
            <p className="text-[#1D1D1F]/60">Search engine optimization tools and insights for your portfolio</p>
          </div>
          <button
            onClick={handleOneClickOptimize}
            disabled={optimizing}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#1D1D1F] text-white rounded-full text-sm font-medium hover:bg-black disabled:opacity-50"
          >
            <Zap className="w-4 h-4" />
            {optimizing ? 'Optimizing...' : 'One-Click Optimize'}
          </button>
        </div>

        {/* SEO Score Overview */}
        {score && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-8">
            {/* Overall Score */}
            <div className="lg:col-span-2 bg-white rounded-3xl border border-gray-200 p-6">
              <div className="text-center">
                <div className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider mb-4">Overall SEO Score</div>
                <div className={`text-6xl font-bold ${getScoreColor(score.overall_score)} mb-2`}>
                  {score.overall_score}
                </div>
                <div className="text-sm text-[#1D1D1F]/60">out of 100</div>
                <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${score.overall_score >= 80 ? 'bg-green-500' : score.overall_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${score.overall_score}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Detailed Scores */}
            <div className="lg:col-span-3 grid grid-cols-2 gap-4">
              {[
                { label: 'Meta Tags', value: score.meta_score, icon: FileText },
                { label: 'Performance', value: score.performance_score, icon: TrendingUp },
                { label: 'Content', value: score.content_score, icon: FileText },
                { label: 'Technical', value: score.technical_score, icon: Settings }
              ].map((item, i) => (
                <div key={i} className="bg-white rounded-2xl border border-gray-200 p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase tracking-wider">{item.label}</span>
                    <div className={`p-2 rounded-xl ${getScoreBg(item.value)}`}>
                      <item.icon className={`w-4 h-4 ${getScoreColor(item.value)}`} />
                    </div>
                  </div>
                  <div className={`text-3xl font-medium ${getScoreColor(item.value)}`}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Settings */}
        <div className="bg-white rounded-3xl border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-medium text-[#1D1D1F] mb-6">Quick Settings</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { key: 'sitemap_enabled', label: 'XML Sitemap', description: 'Auto-generate sitemap for search engines' },
              { key: 'robots_txt_enabled', label: 'Robots.txt', description: 'Configure search engine crawlers' },
              { key: 'schema_markup_enabled', label: 'Schema Markup', description: 'Structured data for rich results' }
            ].map((setting) => (
              <div key={setting.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl">
                <div className="flex-1">
                  <div className="text-sm font-medium text-[#1D1D1F] mb-1">{setting.label}</div>
                  <div className="text-xs text-[#1D1D1F]/60">{setting.description}</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={settings[setting.key as keyof SEOSettings] as boolean}
                    onChange={(e) => handleUpdateSettings({ [setting.key]: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* SEO Issues */}
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden mb-8">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-xl font-medium text-[#1D1D1F]">SEO Issues & Recommendations</h2>
          </div>

          {issues.length === 0 ? (
            <div className="p-12 text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">No issues found!</h3>
              <p className="text-[#1D1D1F]/60">Your portfolio is well-optimized for search engines.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {issues.map((issue) => (
                <div key={issue.id} className="p-6 hover:bg-gray-50 transition-colors group">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-[#1D1D1F]">{issue.title}</h3>
                        {getSeverityBadge(issue.severity)}
                      </div>
                      <p className="text-sm text-[#1D1D1F]/70 mb-2">{issue.description}</p>
                      <div className="text-xs text-[#1D1D1F]/40">
                        Category: {issue.category}
                      </div>
                    </div>
                    {issue.fix_action && (
                      <button
                        onClick={() => handleFixIssue(issue.id)}
                        className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        Fix Now
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Resources */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">Google Search Console</h3>
                <p className="text-sm text-[#1D1D1F]/70 mb-4">
                  Monitor your portfolio's performance in Google search results.
                </p>
                <a
                  href="https://search.google.com/search-console"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  Open Console <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-teal-50 border border-green-200 rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-green-100 rounded-xl">
                <Globe className="w-6 h-6 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">View Public Portfolio</h3>
                <p className="text-sm text-[#1D1D1F]/70 mb-4">
                  See how your portfolio appears to search engines and visitors.
                </p>
                <Link
                  to="/portfolio"
                  className="inline-flex items-center gap-2 text-sm font-medium text-green-600 hover:text-green-700"
                >
                  View Portfolio <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
