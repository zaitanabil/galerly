import { useState, useEffect } from 'react';
import { Globe, CheckCircle, AlertCircle, Copy, ExternalLink, RefreshCw, Info } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface CustomDomainConfigProps {
  initialDomain?: string;
  onUpdate?: (domain: string) => void;
}

interface DomainStatus {
  configured: boolean;
  verified: boolean;
  cname_record?: string;
  last_verified?: string;
  dns_records?: {
    type: string;
    name: string;
    value: string;
    status: 'verified' | 'pending' | 'error';
  }[];
}

export default function CustomDomainConfig({ initialDomain = '', onUpdate }: CustomDomainConfigProps) {
  const [domain, setDomain] = useState(initialDomain);
  const [domainStatus, setDomainStatus] = useState<DomainStatus>({
    configured: false,
    verified: false
  });
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);

  useEffect(() => {
    if (initialDomain) {
      setDomain(initialDomain);
      checkDomainStatus(initialDomain);
    }
  }, [initialDomain]);

  const checkDomainStatus = async (checkDomain: string) => {
    if (!checkDomain) return;
    
    try {
      const response = await api.get(`/portfolio/domain-status?domain=${encodeURIComponent(checkDomain)}`);
      if (response.success && response.data) {
        setDomainStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to check domain status:', error);
    }
  };

  const handleVerify = async () => {
    if (!domain) {
      toast.error('Please enter a domain name');
      return;
    }

    // Validate domain format
    const domainRegex = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$/i;
    if (!domainRegex.test(domain)) {
      toast.error('Please enter a valid domain name (e.g., gallery.yourstudio.com)');
      return;
    }

    setVerifying(true);
    try {
      const response = await api.post('/portfolio/verify-domain', { domain });
      
      if (response.success) {
        toast.success('Domain verified successfully!');
        setDomainStatus({
          configured: true,
          verified: true,
          last_verified: new Date().toISOString()
        });
        if (onUpdate) {
          onUpdate(domain);
        }
      } else {
        toast.error(response.error || 'Domain verification failed');
        setDomainStatus({
          configured: true,
          verified: false
        });
      }
      
      // Refresh status after verification attempt
      await checkDomainStatus(domain);
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || 'Failed to verify domain';
      toast.error(errorMsg);
      setDomainStatus({
        configured: true,
        verified: false
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await api.put('/portfolio/settings', { custom_domain: domain });
      if (response.success) {
        toast.success('Domain configuration saved');
        if (onUpdate) {
          onUpdate(domain);
        }
        if (domain) {
          setShowInstructions(true);
        }
      } else {
        toast.error(response.error || 'Failed to save domain');
      }
    } catch (error) {
      toast.error('Failed to save domain configuration');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const getDNSRecords = () => {
    const subdomain = domain.split('.')[0];
    const rootDomain = domain.split('.').slice(1).join('.');
    
    return [
      {
        type: 'CNAME',
        name: subdomain,
        value: 'cdn.galerly.com',
        description: 'Points your subdomain to Galerly'
      },
      {
        type: 'TXT',
        name: `_galerly-verify.${subdomain}`,
        value: `galerly-domain-verification=${Math.random().toString(36).substring(2, 15)}`,
        description: 'Verifies domain ownership (optional)'
      }
    ];
  };

  return (
    <div className="space-y-6">
      {/* Domain Input */}
      <div>
        <label className="block text-sm font-medium text-[#1D1D1F] mb-2">
          Custom Domain
        </label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#1D1D1F]/40" />
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value.toLowerCase())}
              className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all"
              placeholder="gallery.yourstudio.com"
            />
            {domainStatus.verified && (
              <CheckCircle className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-green-600" />
            )}
          </div>
          <button
            type="button"
            onClick={handleSave}
            disabled={loading || !domain || domain === initialDomain}
            className="px-6 py-3.5 bg-white border border-gray-200 rounded-2xl font-medium text-[#1D1D1F] hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={handleVerify}
            disabled={verifying || !domain}
            className="px-6 py-3.5 bg-[#0066CC] text-white rounded-2xl font-medium hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {verifying ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Verify
              </>
            )}
          </button>
        </div>

        {/* Status Indicator */}
        {domain && (
          <div className="mt-3 flex items-start gap-2">
            {domainStatus.verified ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-green-700 font-medium">Domain verified and active</p>
                  {domainStatus.last_verified && (
                    <p className="text-xs text-green-600/70 mt-0.5">
                      Last verified: {new Date(domainStatus.last_verified).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </>
            ) : domainStatus.configured ? (
              <>
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-amber-700 font-medium">DNS configuration pending</p>
                  <p className="text-xs text-amber-600/70 mt-0.5">
                    Configure your DNS records and click Verify
                  </p>
                </div>
              </>
            ) : (
              <>
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-700">
                  Save to see DNS configuration instructions
                </p>
              </>
            )}
          </div>
        )}
      </div>

      {/* DNS Configuration Instructions */}
      {domain && (domainStatus.configured || showInstructions) && (
        <div className="border border-blue-100 bg-blue-50/30 rounded-2xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Globe className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#1D1D1F]">
                  DNS Configuration Required
                </h3>
                <p className="text-xs text-[#1D1D1F]/70 mt-1">
                  Add these DNS records to your domain provider to complete setup
                </p>
              </div>
            </div>
          </div>

          {/* DNS Records Table */}
          <div className="space-y-4">
            {getDNSRecords().map((record, index) => (
              <div key={index} className="bg-white rounded-xl p-4 border border-gray-200">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-[#0066CC] bg-blue-50 px-2 py-0.5 rounded">
                        {record.type}
                      </span>
                      <span className="text-sm font-medium text-[#1D1D1F]">
                        {record.name}
                      </span>
                    </div>
                    <p className="text-xs text-[#1D1D1F]/60">
                      {record.description}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div>
                    <label className="text-xs font-medium text-[#1D1D1F]/60 block mb-1">
                      Name/Host
                    </label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono text-[#1D1D1F]">
                        {record.name}
                      </code>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(record.name)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Copy to clipboard"
                      >
                        <Copy className="w-4 h-4 text-[#1D1D1F]/60" />
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs font-medium text-[#1D1D1F]/60 block mb-1">
                      Value/Points to
                    </label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs font-mono text-[#1D1D1F]">
                        {record.value}
                      </code>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(record.value)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Copy to clipboard"
                      >
                        <Copy className="w-4 h-4 text-[#1D1D1F]/60" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Provider-Specific Instructions */}
          <div className="mt-6 pt-6 border-t border-blue-100">
            <h4 className="text-xs font-semibold text-[#1D1D1F] mb-3 uppercase tracking-wider">
              Common DNS Providers
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {[
                { name: 'Cloudflare', url: 'https://dash.cloudflare.com' },
                { name: 'GoDaddy', url: 'https://dcc.godaddy.com/manage/dns' },
                { name: 'Namecheap', url: 'https://ap.www.namecheap.com' },
                { name: 'Google Domains', url: 'https://domains.google.com' }
              ].map((provider) => (
                <a
                  key={provider.name}
                  href={provider.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between px-4 py-2.5 bg-white border border-gray-200 rounded-lg hover:border-[#0066CC] hover:bg-blue-50/50 transition-all group"
                >
                  <span className="text-sm font-medium text-[#1D1D1F]">
                    {provider.name}
                  </span>
                  <ExternalLink className="w-4 h-4 text-[#1D1D1F]/40 group-hover:text-[#0066CC]" />
                </a>
              ))}
            </div>
          </div>

          {/* Important Notes */}
          <div className="mt-6 p-4 bg-amber-50 border border-amber-100 rounded-lg">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-800 space-y-1">
                <p className="font-semibold">Important Notes:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>DNS changes can take 24-48 hours to propagate globally</li>
                  <li>Most providers show changes within 1-2 hours</li>
                  <li>Make sure to use your subdomain (e.g., gallery.yourdomain.com)</li>
                  <li>Do not use the root domain (yourdomain.com) - it won't work</li>
                  <li>Click "Verify" button once DNS is configured to activate your domain</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Help Link */}
      <div className="text-center">
        <a
          href="https://help.galerly.com/custom-domain"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-[#0066CC] hover:underline"
        >
          Need help setting up your custom domain?
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
}
