import { useState, useEffect } from 'react';
import { 
  TrendingUp, Search, FileText, Globe, CheckCircle, AlertCircle, 
  Zap, Download, RefreshCw, ExternalLink, Target, BarChart3
} from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface SEOScore {
  overall: number;
  categories: {
    technical: number;
    content: number;
    metadata: number;
    performance: number;
  };
}

interface SEOIssue {
  type: 'error' | 'warning' | 'info';
  category: string;
  title: string;
  description: string;
  actionable: boolean;
  fix?: string;
}

interface SEORecommendation {
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  effort: 'easy' | 'moderate' | 'complex';
  implemented: boolean;
}

export default function SEODashboard() {
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [score, setScore] = useState<SEOScore>({
    overall: 0,
    categories: {
      technical: 0,
      content: 0,
      metadata: 0,
      performance: 0
    }
  });
  const [issues, setIssues] = useState<SEOIssue[]>([]);
  const [recommendations, setRecommendations] = useState<SEORecommendation[]>([]);
  const [portfolioSettings, setPortfolioSettings] = useState<any>(null);
  const [sitemapUrl, setSitemapUrl] = useState<string>('');

  useEffect(() => {
    loadSEOData();
  }, []);

  const loadSEOData = async () => {
    try {
      setLoading(true);
      
      // Load portfolio settings
      const settingsResponse = await api.get('/portfolio/settings');
      if (settingsResponse.success) {
        setPortfolioSettings(settingsResponse.data);
      }

      // Load SEO settings
      const seoResponse = await api.get('/seo/settings');
      if (seoResponse.success) {
        // Calculate SEO score based on current settings
        calculateSEOScore(settingsResponse.data, seoResponse.data);
      }

      // Load schema markup
      const schemaResponse = await api.get('/seo/schema-markup');
      if (schemaResponse.success) {
        // Schema is available
      }

    } catch (error: any) {
      if (error.response?.status !== 403) {
        console.error('Failed to load SEO data:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const calculateSEOScore = (portfolio: any, seoSettings: any) => {
    let technicalScore = 0;
    let contentScore = 0;
    let metadataScore = 0;
    let performanceScore = 100;

    const issuesList: SEOIssue[] = [];
    const recommendationsList: SEORecommendation[] = [];

    // Technical checks
    if (seoSettings?.canonical_urls) {
      technicalScore += 25;
    } else {
      issuesList.push({
        type: 'warning',
        category: 'Technical',
        title: 'Canonical URLs not enabled',
        description: 'Enable canonical URLs to avoid duplicate content issues',
        actionable: true,
        fix: 'Enable canonical URLs in SEO settings'
      });
    }

    if (seoSettings?.structured_data) {
      technicalScore += 25;
    } else {
      issuesList.push({
        type: 'warning',
        category: 'Technical',
        title: 'Structured data not enabled',
        description: 'Schema.org markup helps search engines understand your content',
        actionable: true,
        fix: 'Enable structured data in SEO settings'
      });
    }

    if (seoSettings?.robots_txt) {
      technicalScore += 25;
    }

    if (portfolio?.custom_domain) {
      technicalScore += 25;
      recommendationsList.push({
        title: 'Custom domain configured',
        description: 'Using a custom domain improves credibility and SEO',
        impact: 'high',
        effort: 'easy',
        implemented: true
      });
    } else {
      issuesList.push({
        type: 'info',
        category: 'Technical',
        title: 'Custom domain not configured',
        description: 'A custom domain improves your professional appearance and SEO rankings',
        actionable: true,
        fix: 'Set up a custom domain in Portfolio Settings'
      });
      recommendationsList.push({
        title: 'Set up custom domain',
        description: 'Use your own domain for better branding and SEO',
        impact: 'high',
        effort: 'moderate',
        implemented: false
      });
    }

    // Content checks
    if (portfolio?.about_section && portfolio.about_section.length > 100) {
      contentScore += 33;
    } else {
      issuesList.push({
        type: 'warning',
        category: 'Content',
        title: 'About section is too short',
        description: 'Add at least 100 characters to your about section for better SEO',
        actionable: true,
        fix: 'Update your about section with detailed information'
      });
    }

    if (portfolio?.featured_galleries && portfolio.featured_galleries.length > 0) {
      contentScore += 33;
    } else {
      recommendationsList.push({
        title: 'Feature your best galleries',
        description: 'Select galleries to showcase on your portfolio homepage',
        impact: 'medium',
        effort: 'easy',
        implemented: false
      });
    }

    if (portfolio?.social_links?.instagram || portfolio?.social_links?.website) {
      contentScore += 34;
    } else {
      issuesList.push({
        type: 'info',
        category: 'Content',
        title: 'Social links missing',
        description: 'Add social media links to improve credibility',
        actionable: true,
        fix: 'Add social media links in Portfolio Settings'
      });
    }

    // Metadata checks
    const seoMeta = portfolio?.seo_settings || {};
    if (seoMeta.title && seoMeta.title.length >= 30 && seoMeta.title.length <= 60) {
      metadataScore += 33;
    } else {
      issuesList.push({
        type: 'error',
        category: 'Metadata',
        title: 'SEO title missing or incorrect length',
        description: 'SEO title should be 30-60 characters for optimal search display',
        actionable: true,
        fix: 'Set a descriptive SEO title in Portfolio Settings'
      });
    }

    if (seoMeta.description && seoMeta.description.length >= 120 && seoMeta.description.length <= 160) {
      metadataScore += 33;
    } else {
      issuesList.push({
        type: 'error',
        category: 'Metadata',
        title: 'Meta description missing or incorrect length',
        description: 'Meta description should be 120-160 characters',
        actionable: true,
        fix: 'Add a compelling meta description'
      });
    }

    if (seoMeta.og_image) {
      metadataScore += 34;
      recommendationsList.push({
        title: 'Open Graph image set',
        description: 'Your portfolio will look great when shared on social media',
        impact: 'medium',
        effort: 'easy',
        implemented: true
      });
    } else {
      issuesList.push({
        type: 'warning',
        category: 'Metadata',
        title: 'Open Graph image missing',
        description: 'Add an OG image to control how your portfolio appears when shared',
        actionable: true,
        fix: 'Upload an Open Graph image (1200x630px recommended)'
      });
    }

    // Additional recommendations
    if (!recommendationsList.find(r => r.title === 'Custom domain configured')) {
      recommendationsList.push({
        title: 'Generate XML sitemap',
        description: 'Submit your sitemap to Google Search Console for better indexing',
        impact: 'high',
        effort: 'easy',
        implemented: false
      });
    }

    recommendationsList.push({
      title: 'Optimize image alt text',
      description: 'Add descriptive alt text to all your gallery images',
      impact: 'medium',
      effort: 'moderate',
      implemented: false
    });

    recommendationsList.push({
      title: 'Create blog content',
      description: 'Regular blog posts about your work can significantly improve SEO',
      impact: 'high',
      effort: 'complex',
      implemented: false
    });

    const overallScore = Math.round(
      (technicalScore + contentScore + metadataScore + performanceScore) / 4
    );

    setScore({
      overall: overallScore,
      categories: {
        technical: technicalScore,
        content: contentScore,
        metadata: metadataScore,
        performance: performanceScore
      }
    });

    setIssues(issuesList);
    setRecommendations(recommendationsList);
  };

  const handleOneClickOptimize = async () => {
    setOptimizing(true);
    const toastId = toast.loading('Optimizing your portfolio for SEO...');

    try {
      const response = await api.post('/seo/optimize', {});
      
      if (response.success && response.data) {
        const { optimizations, count, score_improvement, next_steps } = response.data;
        
        toast.success(
          `Portfolio optimized! Completed ${count} optimization(s).`,
          { id: toastId, duration: 5000 }
        );

        // Show next steps
        if (next_steps && next_steps.length > 0) {
          setTimeout(() => {
            toast(
              <div>
                <p className="font-semibold mb-2">Next Steps:</p>
                <ul className="text-sm space-y-1">
                  {next_steps.map((step: string, idx: number) => (
                    <li key={idx}>• {step}</li>
                  ))}
                </ul>
              </div>,
              { duration: 8000, icon: '💡' }
            );
          }, 1000);
        }
        
        // Reload data to show improvements
        await loadSEOData();
      } else {
        toast.error(response.error || 'Failed to optimize portfolio', { id: toastId });
      }

    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to optimize portfolio';
      toast.error(errorMsg, { id: toastId });
    } finally {
      setOptimizing(false);
    }
  };

  const handleDownloadSitemap = async () => {
    try {
      const response = await api.get('/seo/sitemap');
      if (response.success) {
        // Create blob and download
        const blob = new Blob([response.data], { type: 'application/xml' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sitemap.xml';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        toast.success('Sitemap downloaded successfully');
      }
    } catch (error) {
      toast.error('Failed to download sitemap');
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-amber-50';
    return 'bg-red-50';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Needs Work';
    return 'Poor';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* SEO Score Overview */}
      <div className="bg-gradient-to-br from-blue-50 to-white border border-gray-200 rounded-3xl p-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-[#1D1D1F] mb-2">
              SEO Performance
            </h2>
            <p className="text-[#1D1D1F]/60">
              Your portfolio's search engine optimization score
            </p>
          </div>
          
          <button
            onClick={handleOneClickOptimize}
            disabled={optimizing}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white rounded-2xl font-semibold hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {optimizing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                One-Click Optimize
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Overall Score */}
          <div className="lg:col-span-2">
            <div className={`${getScoreBgColor(score.overall)} border border-gray-200 rounded-2xl p-6`}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-[#1D1D1F]/60">Overall Score</span>
                <Target className="w-5 h-5 text-[#0066CC]" />
              </div>
              <div className="flex items-baseline gap-3 mb-2">
                <span className={`text-6xl font-bold ${getScoreColor(score.overall)}`}>
                  {score.overall}
                </span>
                <span className="text-2xl text-[#1D1D1F]/40">/100</span>
              </div>
              <p className={`text-sm font-semibold ${getScoreColor(score.overall)}`}>
                {getScoreLabel(score.overall)}
              </p>
            </div>
          </div>

          {/* Category Scores */}
          <div className="lg:col-span-3 grid grid-cols-2 gap-4">
            {Object.entries(score.categories).map(([category, value]) => (
              <div key={category} className="bg-white border border-gray-200 rounded-2xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-[#1D1D1F]/60 capitalize">
                    {category}
                  </span>
                  <span className={`text-lg font-bold ${getScoreColor(value)}`}>
                    {value}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Issues & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Issues */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-red-50 rounded-xl">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[#1D1D1F]">
                Issues Found
              </h3>
              <p className="text-sm text-[#1D1D1F]/60">
                {issues.length} item{issues.length !== 1 ? 's' : ''} need attention
              </p>
            </div>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {issues.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                <p className="text-sm text-[#1D1D1F]/60">
                  No issues found! Your SEO is looking great.
                </p>
              </div>
            ) : (
              issues.map((issue, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-xl">
                  <div className="flex items-start gap-3">
                    {issue.type === 'error' && <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
                    {issue.type === 'warning' && <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />}
                    {issue.type === 'info' && <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-[#1D1D1F]/40 uppercase">
                          {issue.category}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-[#1D1D1F] mb-1">
                        {issue.title}
                      </h4>
                      <p className="text-xs text-[#1D1D1F]/60 mb-2">
                        {issue.description}
                      </p>
                      {issue.fix && (
                        <div className="text-xs text-[#0066CC] font-medium">
                          Fix: {issue.fix}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-50 rounded-xl">
              <TrendingUp className="w-5 h-5 text-[#0066CC]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[#1D1D1F]">
                Recommendations
              </h3>
              <p className="text-sm text-[#1D1D1F]/60">
                {recommendations.filter(r => !r.implemented).length} suggestions to improve SEO
              </p>
            </div>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recommendations.map((rec, index) => (
              <div key={index} className={`p-4 rounded-xl ${rec.implemented ? 'bg-green-50' : 'bg-gray-50'}`}>
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-sm font-semibold text-[#1D1D1F]">
                    {rec.title}
                  </h4>
                  {rec.implemented && (
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                  )}
                </div>
                <p className="text-xs text-[#1D1D1F]/60 mb-3">
                  {rec.description}
                </p>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    rec.impact === 'high' ? 'bg-red-100 text-red-700' :
                    rec.impact === 'medium' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {rec.impact} impact
                  </span>
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700 font-medium">
                    {rec.effort} effort
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white border border-gray-200 rounded-3xl p-6">
        <h3 className="text-lg font-semibold text-[#1D1D1F] mb-4">
          Quick Actions
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={handleDownloadSitemap}
            className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors text-left"
          >
            <Download className="w-5 h-5 text-[#0066CC]" />
            <div>
              <div className="text-sm font-semibold text-[#1D1D1F]">
                Download Sitemap
              </div>
              <div className="text-xs text-[#1D1D1F]/60">
                Submit to search engines
              </div>
            </div>
          </button>

          <button
            onClick={() => loadSEOData()}
            className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors text-left"
          >
            <RefreshCw className="w-5 h-5 text-[#0066CC]" />
            <div>
              <div className="text-sm font-semibold text-[#1D1D1F]">
                Refresh Score
              </div>
              <div className="text-xs text-[#1D1D1F]/60">
                Recalculate SEO metrics
              </div>
            </div>
          </button>

          <a
            href="https://search.google.com/search-console"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors text-left"
          >
            <ExternalLink className="w-5 h-5 text-[#0066CC]" />
            <div>
              <div className="text-sm font-semibold text-[#1D1D1F]">
                Google Search Console
              </div>
              <div className="text-xs text-[#1D1D1F]/60">
                Monitor search performance
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
