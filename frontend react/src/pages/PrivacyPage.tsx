// Privacy Policy page with improved design
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Hero Section */}
          <div className="mb-16">
            <div className="glass-panel p-12 md:p-16">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#1D1D1F]/60 mb-6">
                PRIVACY
              </p>
              <div className="flex items-center gap-3 mb-10 text-sm text-[#1D1D1F]/60">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#0066CC]" />
                <p>Data Protection • GDPR Compliant</p>
              </div>
              <h1 className="text-5xl md:text-7xl font-light text-[#1D1D1F] mb-8 leading-tight">
                Your data, protected.
              </h1>
              <div className="text-lg md:text-xl text-[#1D1D1F]/70 space-y-4 max-w-3xl">
                <p>How we collect, use, and protect your personal information on Galerly.</p>
                <p className="text-base md:text-lg opacity-85">
                  Last updated December 2025. GDPR compliant. Questions? Email{' '}
                  <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                    support@galerly.com
                  </a>
                </p>
              </div>
              <div className="flex flex-wrap gap-4 mt-10">
                <Link
                  to="/legal"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#0066CC] text-white hover:bg-[#0055AA] transition-all duration-300"
                >
                  <span>Legal Notice</span>
                  <svg width="17" height="14" viewBox="0 0 17 14" fill="none" className="w-4 h-4">
                    <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M1 7L16 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </Link>
                <Link
                  to="/contact"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#1D1D1F]/5 text-[#1D1D1F] hover:bg-[#1D1D1F]/10 transition-all duration-300"
                >
                  <span>Contact Us</span>
                  <svg width="17" height="14" viewBox="0 0 17 14" fill="none" className="w-4 h-4">
                    <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M1 7L16 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>

          {/* Table of Contents */}
          <div className="glass-panel p-8 mb-12">
            <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-[#1D1D1F]/60 mb-6">
              PRIVACY POLICY
            </h2>
            <p className="text-sm text-[#1D1D1F]/60 mb-6">
              How we collect, use, and protect your personal information on Galerly
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'Information We Collect',
                'How We Use Your Information',
                'Data Sharing & Third Parties',
                'Data Security',
                'Your Privacy Rights',
                'Cookies & Local Storage',
                'Data Retention',
                'International Data Transfers',
                'Children\'s Privacy',
                'Policy Updates & Contact'
              ].map((section, index) => (
                <a
                  key={index}
                  href={`#section-${index + 1}`}
                  className="text-sm text-[#1D1D1F]/70 hover:text-[#0066CC] transition-colors duration-200 flex items-center gap-2"
                >
                  <span className="text-xs text-[#1D1D1F]/40">0{index + 1}</span>
                  <span>{section}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Content Sections */}
          <div className="space-y-8">
            {/* Information We Collect */}
            <div id="section-1" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">01</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Information We Collect
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Account Information:</strong> When you register, we collect your email address and password. You may optionally provide profile information such as name, phone number, bio, location, website, and social media links.
                  </p>
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Content You Upload:</strong> Photographs, gallery titles, descriptions, client information (names, emails), and file metadata.
                  </p>
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Payment Information:</strong> Payment details are processed by Stripe. We do not store credit card numbers. We retain subscription status and transaction records.
                  </p>
                  <p>
                    <strong className="text-[#1D1D1F]">Usage Information:</strong> We collect data about how you interact with Galerly, including pages visited, features used, and session information to improve our service.
                  </p>
                </div>
              </div>
            </div>

            {/* How We Use Your Information */}
            <div id="section-2" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">02</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  How We Use Your Information
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">We use your information to:</p>
                  <ul className="space-y-2 mb-4">
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Provide and maintain gallery hosting services</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Process payments and manage subscriptions</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Send account notifications, password resets, and gallery updates</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Improve platform usability and identify technical issues</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Analyze usage patterns to improve features</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <span>Prevent fraud and ensure security</span>
                    </li>
                  </ul>
                  <p>
                    We send automated emails for account activities. You can manage notification preferences in your account settings.
                  </p>
                </div>
              </div>
            </div>

            {/* Data Sharing & Third Parties */}
            <div id="section-3" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">03</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Data Sharing & Third Parties
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">We do NOT sell your data.</strong> We share information only with:
                  </p>
                  <ul className="space-y-3 mb-4">
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <div>
                        <strong className="text-[#1D1D1F]">Service Providers:</strong> Cloud hosting, email delivery, payment processing (Stripe), and analytics services that help us operate Galerly.
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <div>
                        <strong className="text-[#1D1D1F]">Legal Requirements:</strong> When required by law, court order, or to protect our rights.
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-[#0066CC] mt-1.5">•</span>
                      <div>
                        <strong className="text-[#1D1D1F]">Your Clients:</strong> Galleries you create are accessible to clients via links you generate or via email invitations. You control privacy settings for each gallery.
                      </div>
                    </li>
                  </ul>
                  <p>
                    Third-party service providers are contractually obligated to protect your data and use it only for services they provide to us.
                  </p>
                </div>
              </div>
            </div>

            {/* Data Security */}
            <div id="section-4" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">04</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Data Security
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    We implement industry-standard security measures to protect your data, including encrypted storage, secure transmission (HTTPS), and password hashing.
                  </p>
                  <p className="mb-4">
                    Authentication tokens expire after 7 days. We regularly review security practices to protect against unauthorized access.
                  </p>
                  <p>
                    While we take reasonable precautions, no system is completely secure. You accept the inherent risks of transmitting data online.
                  </p>
                </div>
              </div>
            </div>

            {/* Your Privacy Rights */}
            <div id="section-5" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">05</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Your Privacy Rights
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <div className="space-y-4">
                    <p>
                      <strong className="text-[#1D1D1F]">Access:</strong> Download your data from your dashboard.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Correction:</strong> Update your profile information anytime.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Deletion:</strong> Delete your account or content anytime. When you manually delete content (photos, galleries, or your account), it is immediately and permanently removed from our database. We do not retain deleted content.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Portability:</strong> Export your data in standard formats.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Objection:</strong> Opt out of optional analytics and marketing cookies.
                    </p>
                    <p>
                      Contact{' '}
                      <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                        support@galerly.com
                      </a>{' '}
                      for privacy-related requests. Swiss data protection laws and EU GDPR apply.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Cookies & Local Storage */}
            <div id="section-6" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">06</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Cookies & Local Storage
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">We use cookies and browser storage to improve your experience:</p>
                  <div className="space-y-4">
                    <p>
                      <strong className="text-[#1D1D1F]">Necessary:</strong> Authentication and session management. Required for the service to function.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Analytics:</strong> Optional. Aggregate statistics about platform usage.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Marketing:</strong> Optional. Third-party advertising if you consent.
                    </p>
                    <p>
                      Manage cookie preferences via the popup or browser settings. Disabling necessary cookies may limit functionality.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Data Retention */}
            <div id="section-7" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">07</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Data Retention
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <div className="space-y-4">
                    <p>
                      <strong className="text-[#1D1D1F]">Active Account Data:</strong> Retained while your account is active.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Canceled Subscriptions:</strong> After cancellation, data remains accessible for 30 days for export, then permanently deleted.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Manual Deletions:</strong> Content you manually delete (photos, galleries, account) is immediately and permanently removed. No retention period applies.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Usage Analytics:</strong> Aggregated, anonymized data retained to improve service quality.
                    </p>
                    <p>
                      <strong className="text-[#1D1D1F]">Payment Records:</strong> Retained for 10 years as required by Swiss tax and accounting regulations.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* International Data Transfers */}
            <div id="section-8" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">08</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  International Data Transfers
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    Galerly is a Swiss company. Your data is stored on secure cloud servers that may be located outside Switzerland.
                  </p>
                  <p>
                    For EU/EEA users, we ensure adequate safeguards through Standard Contractual Clauses and compliance with Swiss-EU data adequacy decisions. Your data is protected under Swiss Federal Act on Data Protection (FADP) and EU GDPR where applicable.
                  </p>
                </div>
              </div>
            </div>

            {/* Children's Privacy */}
            <div id="section-9" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">09</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Children's Privacy
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    Galerly is not intended for users under 16. We do not knowingly collect information from children.
                  </p>
                  <p>
                    If we discover an account belongs to a child, we will delete it immediately. Parents or guardians should contact us if they believe their child has created an account.
                  </p>
                </div>
              </div>
            </div>

            {/* Policy Updates & Contact */}
            <div id="section-10" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">10</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Policy Updates & Contact
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    We may update this Privacy Policy to reflect changes in our practices or legal requirements. Material changes will be notified via email and posted here.
                  </p>
                  <p className="mb-4">
                    Your continued use after updates constitutes acceptance. We recommend reviewing this page periodically.
                  </p>
                  <div className="space-y-2 mb-6">
                    <p className="font-semibold text-[#1D1D1F]">Privacy Questions?</p>
                    <p>
                      Email:{' '}
                      <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                        support@galerly.com
                      </a>
                    </p>
                    <p>For Swiss FADP or EU GDPR requests, data access, or deletion inquiries.</p>
                  </div>
                  <p className="mb-6">
                    <strong className="text-[#1D1D1F]">Jurisdiction:</strong> Swiss law governs this Privacy Policy. Disputes subject to Swiss courts jurisdiction.
                  </p>
                  <p className="pt-6 border-t border-[#1D1D1F]/10 text-[#1D1D1F]/60 text-sm">
                    Last updated: December 2025
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
