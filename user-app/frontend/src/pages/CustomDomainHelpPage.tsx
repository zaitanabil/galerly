// Custom Domain Setup Help Page
import { useState } from 'react';
import { ChevronDown, Globe, Shield, Zap, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';

interface HelpSection {
  title: string;
  content: string;
  category: string;
}

const helpSections: HelpSection[] = [
  {
    category: 'Getting Started',
    title: 'What is a Custom Domain?',
    content: 'A custom domain lets you use your own domain name (like portfolio.yourname.com) instead of the default Galerly subdomain. This provides a more professional appearance and strengthens your brand identity.',
  },
  {
    category: 'Getting Started',
    title: 'Which plans include Custom Domain?',
    content: 'Custom domain is available on Plus, Pro, and Ultimate plans. Free and Starter plans use the default galerly.com subdomain.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 1: Choose Your Domain',
    content: 'You can use either a subdomain (portfolio.yourname.com) or an apex domain (yourname.com). Subdomains are recommended as they are easier to configure and more flexible.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 2: Auto-Provision SSL Certificate',
    content: 'Click the "Auto-Setup" button in your Portfolio Settings. This will automatically request an SSL certificate from AWS Certificate Manager and create a CloudFront distribution for your portfolio.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 3: Add DNS Records',
    content: 'After auto-provisioning, you will see DNS records that need to be added to your domain registrar. There are two types: (1) SSL Validation CNAME - required to validate your certificate, and (2) Domain CNAME - points your domain to CloudFront.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 4: Configure DNS at Your Registrar',
    content: 'Log into your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.) and add the CNAME records shown in your Galerly dashboard. Copy the exact values including the trailing dot if shown.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 5: Wait for DNS Propagation',
    content: 'DNS changes can take 5 minutes to 48 hours to propagate globally. The Galerly dashboard will show you real-time propagation status across multiple DNS servers worldwide.',
  },
  {
    category: 'DNS Setup',
    title: 'Step 6: Verify SSL Certificate',
    content: 'Once DNS propagation is complete, click "Check SSL" to verify your certificate. AWS will automatically validate the certificate once it detects the DNS records.',
  },
  {
    category: 'Troubleshooting',
    title: 'SSL Certificate Pending',
    content: 'If your SSL certificate stays in "Pending Validation" status: (1) Double-check the DNS records are correct, (2) Wait 30-60 minutes for DNS propagation, (3) Click "Check SSL" to manually trigger validation, (4) Contact support if it remains pending after 24 hours.',
  },
  {
    category: 'Troubleshooting',
    title: 'DNS Propagation Slow',
    content: 'DNS propagation typically takes 5-30 minutes but can take up to 48 hours. Factors affecting speed: (1) Your DNS provider\'s TTL settings, (2) Geographic location, (3) DNS caching by ISPs. You can check propagation at whatsmydns.net.',
  },
  {
    category: 'Troubleshooting',
    title: 'Domain Not Working',
    content: 'If your domain is not loading: (1) Verify DNS records are correct with no typos, (2) Ensure SSL certificate shows "Issued" status, (3) Clear your browser cache and try incognito mode, (4) Check if your domain registrar requires additional verification.',
  },
  {
    category: 'Troubleshooting',
    title: 'Certificate Validation Failed',
    content: 'Common causes: (1) DNS records not added correctly, (2) Domain ownership cannot be verified, (3) Domain is already in use elsewhere. Solution: Remove all old CNAME records, add only the new ones from Galerly, and wait 1 hour before retrying.',
  },
  {
    category: 'Advanced',
    title: 'Using Apex Domains',
    content: 'Apex domains (yourname.com) require ALIAS or ANAME records, not CNAME. Some registrars (Cloudflare, Route53) support this. Others require subdomain setup (www.yourname.com). Check your registrar documentation.',
  },
  {
    category: 'Advanced',
    title: 'CloudFront Distribution Details',
    content: 'Galerly creates a CloudFront distribution for your custom domain. This provides: (1) Global CDN for fast loading, (2) DDoS protection, (3) HTTPS encryption, (4) Cache optimization. You can see the distribution ID in the status panel.',
  },
  {
    category: 'Advanced',
    title: 'SSL Certificate Management',
    content: 'SSL certificates are automatically managed by AWS Certificate Manager: (1) Certificates auto-renew before expiration, (2) Galerly monitors certificate health, (3) No manual renewal required, (4) Certificates are free of charge.',
  },
  {
    category: 'Advanced',
    title: 'Changing or Removing Custom Domain',
    content: 'To change your domain: (1) Remove DNS records from old domain, (2) Set up new domain following the normal process. To remove: Delete the custom domain in settings, DNS records will become inactive within 48 hours.',
  },
  {
    category: 'Domain Registrars',
    title: 'GoDaddy Setup',
    content: 'In GoDaddy: DNS Management > Add Record > Type: CNAME > Host: subdomain name (e.g., "portfolio") > Points to: CloudFront URL > TTL: 600 seconds. Click Save.',
  },
  {
    category: 'Domain Registrars',
    title: 'Namecheap Setup',
    content: 'In Namecheap: Advanced DNS > Add New Record > Type: CNAME > Host: subdomain > Target: CloudFront URL > TTL: Automatic. Save changes.',
  },
  {
    category: 'Domain Registrars',
    title: 'Cloudflare Setup',
    content: 'In Cloudflare: DNS > Add Record > Type: CNAME > Name: subdomain > Target: CloudFront URL > Proxy status: DNS only (gray cloud) > Save. Important: Disable Cloudflare proxy for custom domains.',
  },
  {
    category: 'Domain Registrars',
    title: 'Google Domains Setup',
    content: 'In Google Domains: DNS > Custom Resource Records > Name: subdomain > Type: CNAME > TTL: 600 > Data: CloudFront URL > Add.',
  },
  {
    category: 'Security',
    title: 'HTTPS and SSL',
    content: 'All custom domains use HTTPS encryption. SSL certificates are issued by AWS Certificate Manager and are trusted by all major browsers. Certificates include: SHA-256 encryption, RSA 2048-bit keys, and automatic renewal.',
  },
  {
    category: 'Security',
    title: 'Domain Verification',
    content: 'DNS validation proves you own the domain. AWS Certificate Manager uses DNS-based validation (not email) for security. This prevents unauthorized certificate issuance.',
  },
];

export default function CustomDomainHelpPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', ...Array.from(new Set(helpSections.map((section) => section.category)))];
  const filteredSections = selectedCategory === 'All' 
    ? helpSections 
    : helpSections.filter((section) => section.category === selectedCategory);

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-3 mb-6 px-6 py-3 bg-blue-50 border border-blue-200 rounded-full">
              <Globe className="w-5 h-5 text-[#0066CC]" />
              <span className="text-sm font-medium text-[#0066CC]">Custom Domain Setup</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-serif font-medium text-[#1D1D1F] mb-6">
              Custom Domain Guide
            </h1>
            <p className="text-xl text-[#1D1D1F]/70 max-w-2xl mx-auto">
              Complete guide to setting up and managing your custom domain
            </p>
          </div>

          {/* Quick Start Steps */}
          <div className="glass-panel p-8 mb-12">
            <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-6 flex items-center gap-3">
              <Zap className="w-6 h-6 text-[#0066CC]" />
              Quick Start
            </h2>
            <div className="space-y-4">
              {[
                { step: 1, text: 'Go to Portfolio Settings > Custom Domain' },
                { step: 2, text: 'Enter your domain name (e.g., portfolio.yourname.com)' },
                { step: 3, text: 'Click "Auto-Setup" to provision SSL certificate' },
                { step: 4, text: 'Copy the DNS records shown in the dashboard' },
                { step: 5, text: 'Add DNS records to your domain registrar' },
                { step: 6, text: 'Wait for DNS propagation (5-60 minutes)' },
                { step: 7, text: 'Click "Check SSL" to verify certificate' },
                { step: 8, text: 'Your custom domain is live!' },
              ].map(({ step, text }) => (
                <div key={step} className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-[#0066CC] text-white rounded-full flex items-center justify-center font-medium text-sm">
                    {step}
                  </div>
                  <p className="text-[#1D1D1F]/80 pt-1">{text}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="glass-panel p-6">
              <Shield className="w-8 h-8 text-[#0066CC] mb-4" />
              <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                Free SSL Certificate
              </h3>
              <p className="text-sm text-[#1D1D1F]/70">
                Automatic HTTPS encryption with AWS Certificate Manager
              </p>
            </div>
            <div className="glass-panel p-6">
              <Zap className="w-8 h-8 text-[#0066CC] mb-4" />
              <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                Global CDN
              </h3>
              <p className="text-sm text-[#1D1D1F]/70">
                Fast loading worldwide with CloudFront distribution
              </p>
            </div>
            <div className="glass-panel p-6">
              <CheckCircle2 className="w-8 h-8 text-[#0066CC] mb-4" />
              <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
                Auto-Renewal
              </h3>
              <p className="text-sm text-[#1D1D1F]/70">
                SSL certificates renew automatically before expiration
              </p>
            </div>
          </div>

          {/* Category Filter */}
          <div className="flex flex-wrap gap-3 justify-center mb-12">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-6 py-2.5 rounded-full font-medium transition-all ${
                  selectedCategory === category
                    ? 'bg-[#0066CC] text-white shadow-lg shadow-blue-500/20'
                    : 'bg-white/50 border border-gray-200 text-[#1D1D1F] hover:bg-white'
                }`}
              >
                {category}
              </button>
            ))}
          </div>

          {/* Help Sections */}
          <div className="space-y-4 mb-12">
            {filteredSections.map((section, index) => (
              <div key={index} className="glass-panel overflow-hidden">
                <button
                  onClick={() => setOpenIndex(openIndex === index ? null : index)}
                  className="w-full px-8 py-6 flex items-center justify-between text-left hover:bg-white/50 transition-colors"
                >
                  <span className="text-lg font-medium text-[#1D1D1F]">{section.title}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-[#1D1D1F]/50 transition-transform ${
                      openIndex === index ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {openIndex === index && (
                  <div className="px-8 pb-6 text-[#1D1D1F]/70 leading-relaxed whitespace-pre-line">
                    {section.content}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Additional Resources */}
          <div className="glass-panel p-8 mb-12">
            <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-6">
              Additional Resources
            </h2>
            <div className="space-y-4">
              <a
                href="https://www.whatsmydns.net"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 bg-white/50 rounded-xl hover:bg-white transition-colors group"
              >
                <div>
                  <p className="font-medium text-[#1D1D1F]">Check DNS Propagation</p>
                  <p className="text-sm text-[#1D1D1F]/70">Verify your DNS records are propagating globally</p>
                </div>
                <ExternalLink className="w-5 h-5 text-[#0066CC] group-hover:translate-x-1 transition-transform" />
              </a>
              <a
                href="https://docs.aws.amazon.com/acm/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 bg-white/50 rounded-xl hover:bg-white transition-colors group"
              >
                <div>
                  <p className="font-medium text-[#1D1D1F]">AWS Certificate Manager Docs</p>
                  <p className="text-sm text-[#1D1D1F]/70">Learn more about SSL certificate management</p>
                </div>
                <ExternalLink className="w-5 h-5 text-[#0066CC] group-hover:translate-x-1 transition-transform" />
              </a>
              <a
                href="https://docs.aws.amazon.com/cloudfront/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 bg-white/50 rounded-xl hover:bg-white transition-colors group"
              >
                <div>
                  <p className="font-medium text-[#1D1D1F]">CloudFront CDN Documentation</p>
                  <p className="text-sm text-[#1D1D1F]/70">Understand how content delivery works</p>
                </div>
                <ExternalLink className="w-5 h-5 text-[#0066CC] group-hover:translate-x-1 transition-transform" />
              </a>
            </div>
          </div>

          {/* Support CTA */}
          <div className="glass-panel p-8 text-center">
            <AlertCircle className="w-12 h-12 text-[#0066CC] mx-auto mb-4" />
            <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-3">
              Still Need Help?
            </h2>
            <p className="text-[#1D1D1F]/70 mb-6 max-w-lg mx-auto">
              Our support team is here to help you get your custom domain set up correctly.
            </p>
            <a
              href="/contact"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#0066CC] text-white rounded-2xl font-medium hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              Contact Support
            </a>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
