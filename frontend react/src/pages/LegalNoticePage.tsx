// Legal Notice page with improved design
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function LegalNoticePage() {
  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Hero Section */}
          <div className="mb-16">
            <div className="glass-panel p-12 md:p-16">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#1D1D1F]/60 mb-6">
                LEGAL
              </p>
              <div className="flex items-center gap-3 mb-10 text-sm text-[#1D1D1F]/60">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#0066CC]" />
                <p>Terms & Conditions • GDPR Compliant • AWS Infrastructure</p>
              </div>
              <h1 className="text-5xl md:text-7xl font-light text-[#1D1D1F] mb-8 leading-tight">
                Terms and conditions.
              </h1>
              <div className="text-lg md:text-xl text-[#1D1D1F]/70 space-y-4 max-w-3xl">
                <p>Legal notice governing the use of Galerly photography platform.</p>
                <p className="text-base md:text-lg opacity-85">
                  Last updated December 2025. Questions? Email{' '}
                  <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                    support@galerly.com
                  </a>
                </p>
              </div>
              <div className="flex flex-wrap gap-4 mt-10">
                <Link
                  to="/privacy"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#0066CC] text-white hover:bg-[#0055AA] transition-all duration-300"
                >
                  <span>Privacy Policy</span>
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
              LEGAL NOTICE
            </h2>
            <p className="text-sm text-[#1D1D1F]/60 mb-6">
              Terms and conditions governing the use of Galerly photography platform
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'Acceptance of Terms',
                'Description of Services',
                'Account Registration',
                'Intellectual Property',
                'Acceptable Use',
                'Subscription & Payments',
                'Account Cancellation',
                'Data Responsibility',
                'Limitation of Liability',
                'Third-Party Services',
                'Governing Law',
                'Modifications & Contact'
              ].map((section, index) => (
                <a
                  key={index}
                  href={`#section-${index + 1}`}
                  className="text-sm text-[#1D1D1F]/70 hover:text-[#0066CC] transition-colors duration-200 flex items-center gap-2"
                >
                  <span className="text-xs text-[#1D1D1F]/40">
                    {index + 1 < 10 ? `0${index + 1}` : index + 1}
                  </span>
                  <span>{section}</span>
                </a>
              ))}
            </div>
          </div>

          {/* Content Sections */}
          <div className="space-y-8">
            {/* Acceptance of Terms */}
            <div id="section-1" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">01</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Acceptance of Terms
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    By accessing and using Galerly, you accept and agree to be bound by these Terms of Service and our Privacy Policy. If you do not agree to these terms, please do not use our service.
                  </p>
                  <p>
                    We reserve the right to update these Terms at any time. Your continued use of Galerly after changes constitutes acceptance of the modified terms. We recommend reviewing this page periodically.
                  </p>
                </div>
              </div>
            </div>

            {/* Description of Services */}
            <div id="section-2" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">02</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Description of Services
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    Galerly provides cloud-based tools for photographers to create, manage, and share professional photo galleries with clients.
                  </p>
                  <p>
                    Services include photo storage, gallery creation, client sharing, download management, branding customization, and analytics tools.
                  </p>
                </div>
              </div>
            </div>

            {/* Account Registration */}
            <div id="section-3" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">03</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Account Registration
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    To use Galerly, you must create an account by providing accurate and complete information. You are responsible for maintaining the confidentiality of your account credentials.
                  </p>
                  <p>
                    You may not share your account with others. Notify us immediately if you suspect unauthorized access to your account.
                  </p>
                </div>
              </div>
            </div>

            {/* Intellectual Property & Content License */}
            <div id="section-4" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">04</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Intellectual Property & Content License
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Your Content:</strong> You retain all ownership rights to photographs and content you upload to Galerly. By uploading content, you grant us a limited license to store, display, and process your content solely to provide our services.
                  </p>
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Our Platform:</strong> All content on this website, including software, design, logos, and text, is owned by Galerly and protected by copyright laws. You may not copy, modify, or distribute any part of our platform without written permission.
                  </p>
                  <p>
                    <strong className="text-[#1D1D1F]">Copyright Infringement:</strong> If you believe content on Galerly infringes your copyright, contact{' '}
                    <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                      support@galerly.com
                    </a>{' '}
                    with detailed information about the alleged infringement.
                  </p>
                </div>
              </div>
            </div>

            {/* Acceptable Use */}
            <div id="section-5" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">05</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Acceptable Use
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    You agree to use Galerly only for lawful purposes. You may not upload content that is illegal, offensive, defamatory, violates intellectual property rights, or infringes on others' privacy.
                  </p>
                  <p className="mb-4">
                    Prohibited activities include: attempting to breach security, accessing other users' accounts without permission, distributing malware, spamming, or using automated tools to scrape content.
                  </p>
                  <p>
                    We reserve the right to remove content or terminate accounts that violate these terms.
                  </p>
                </div>
              </div>
            </div>

            {/* Subscription Plans & Payments */}
            <div id="section-6" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">06</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Subscription Plans & Payments
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    Galerly offers Starter (free), Professional, and Business subscription plans. Paid subscriptions require payment in advance and automatically renew unless canceled.
                  </p>
                  <p className="mb-4">
                    All payments are processed securely through Stripe. You are responsible for applicable taxes, including Swiss VAT where applicable.
                  </p>
                  <p>
                    <strong className="text-[#1D1D1F]">Refund Policy:</strong> Refunds are available within 14 days of initial purchase for paid plans, provided you have not used the upgraded features. Once you upload content or use paid features, the service is considered consumed and refunds are not applicable. Swiss consumer protection laws apply.
                  </p>
                </div>
              </div>
            </div>

            {/* Account Cancellation & Data Deletion */}
            <div id="section-7" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">07</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Account Cancellation & Data Deletion
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    You may cancel your subscription at any time through your account dashboard. After cancellation, your galleries and data remain accessible for 30 days for export purposes, then permanently deleted.
                  </p>
                  <p className="mb-4">
                    <strong className="text-[#1D1D1F]">Instant Deletion:</strong> When you manually delete content (photos, galleries, or your account), it is immediately and permanently removed from our database. We do not retain deleted content.
                  </p>
                  <p>
                    We may suspend or terminate accounts that violate these Terms or Swiss law.
                  </p>
                </div>
              </div>
            </div>

            {/* Data Responsibility */}
            <div id="section-8" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">08</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Data Responsibility
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    You are responsible for backing up your content. While we implement industry-standard security measures, we cannot guarantee absolute protection against data loss.
                  </p>
                  <p>
                    We are not liable for any loss or corruption of your data. See our{' '}
                    <Link to="/privacy" className="text-[#0066CC] hover:underline">
                      Privacy Policy
                    </Link>{' '}
                    for details on how we handle your information.
                  </p>
                </div>
              </div>
            </div>

            {/* Limitation of Liability */}
            <div id="section-9" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">09</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Limitation of Liability
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    GALERLY IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND. WE DO NOT GUARANTEE UNINTERRUPTED, ERROR-FREE, OR SECURE SERVICE.
                  </p>
                  <p className="mb-4">
                    TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE ARE NOT LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF DATA, REVENUE, OR PROFITS.
                  </p>
                  <p>
                    Our total liability is limited to the amount you paid for the service in the past 12 months.
                  </p>
                </div>
              </div>
            </div>

            {/* Third-Party Services */}
            <div id="section-10" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">10</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Third-Party Services
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    Galerly integrates with third-party services (payment processors, hosting providers). We are not responsible for the actions or policies of these third parties.
                  </p>
                  <p>
                    Links to external websites do not imply endorsement. You access third-party sites at your own risk.
                  </p>
                </div>
              </div>
            </div>

            {/* Governing Law & Jurisdiction */}
            <div id="section-11" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">11</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Governing Law & Jurisdiction
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    These Terms are governed by and construed in accordance with Swiss law. Any disputes arising from these Terms or your use of Galerly shall be subject to the exclusive jurisdiction of the courts of Switzerland.
                  </p>
                  <p>
                    Swiss consumer protection laws apply to all users. EU/EEA users retain their consumer rights under applicable EU regulations.
                  </p>
                </div>
              </div>
            </div>

            {/* Modifications & Contact */}
            <div id="section-12" className="glass-panel p-8 md:p-10 scroll-mt-32">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-sm font-mono text-[#0066CC] bg-[#0066CC]/10 px-3 py-1 rounded-full">12</span>
                <h3 className="text-2xl md:text-3xl font-light text-[#1D1D1F]">
                  Modifications & Contact
                </h3>
              </div>
              <div className="space-y-6 text-[#1D1D1F]/70 leading-relaxed">
                <div className="pl-0 md:pl-16">
                  <p className="mb-4">
                    We may modify these Terms at any time. Material changes will be communicated via email. Continued use after changes constitutes acceptance.
                  </p>
                  <div className="space-y-2 mb-6">
                    <p className="font-semibold text-[#1D1D1F]">Questions?</p>
                    <p>
                      Contact us at{' '}
                      <a href="mailto:support@galerly.com" className="text-[#0066CC] hover:underline">
                        support@galerly.com
                      </a>
                    </p>
                  </div>
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
