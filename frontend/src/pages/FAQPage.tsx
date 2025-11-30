// FAQ page
import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';

interface FAQ {
  question: string;
  answer: string;
  category: string;
}

const faqs: FAQ[] = [
  {
    category: 'Getting Started',
    question: 'How do I create my first gallery?',
    answer: 'After signing up, click "New Gallery" from your dashboard. Add a name, client email, and upload your photos. Your client will receive an email with access to view and interact with the gallery.',
  },
  {
    category: 'Getting Started',
    question: 'What file formats are supported?',
    answer: 'We support JPG, PNG, HEIC, and RAW formats. Files are automatically converted and optimized for web viewing while preserving original quality for downloads.',
  },
  {
    category: 'Pricing',
    question: 'Can I try Galerly for free?',
    answer: 'Yes! We offer a 14-day free trial with full access to all features. No credit card required.',
  },
  {
    category: 'Pricing',
    question: 'Can I cancel my subscription anytime?',
    answer: 'Absolutely. You can cancel your subscription at any time from the billing page. Your access continues until the end of your billing period.',
  },
  {
    category: 'Features',
    question: 'How long do galleries stay active?',
    answer: 'Gallery expiration is customizable. You can set galleries to expire after 7, 14, 30, 60, 90, or 180 days, or keep them active for up to a year.',
  },
  {
    category: 'Features',
    question: 'Can clients download photos?',
    answer: 'Yes, you can enable or disable downloads on a per-gallery basis. Clients can download individual photos or entire galleries in high resolution.',
  },
  {
    category: 'Technical',
    question: 'Where are my photos stored?',
    answer: 'All photos are securely stored on AWS S3 with automatic backups. We use enterprise-grade encryption and follow industry best practices for data security.',
  },
  {
    category: 'Technical',
    question: 'What happens to my photos after my subscription ends?',
    answer: 'You have 30 days to download your photos before they are permanently deleted. We will send you reminders before any deletion occurs.',
  },
];

export default function FAQPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', ...Array.from(new Set(faqs.map((faq) => faq.category)))];
  const filteredFaqs = selectedCategory === 'All' 
    ? faqs 
    : faqs.filter((faq) => faq.category === selectedCategory);

  return (
    <div className="min-h-screen bg-transparent">
      <Header />
      
      <main className="relative z-10 min-h-screen pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-serif font-medium text-[#1D1D1F] mb-6">
              Frequently Asked Questions
            </h1>
            <p className="text-xl text-[#1D1D1F]/70 max-w-2xl mx-auto">
              Find answers to common questions about Galerly
            </p>
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

          {/* FAQ List */}
          <div className="space-y-4">
            {filteredFaqs.map((faq, index) => (
              <div key={index} className="glass-panel overflow-hidden">
                <button
                  onClick={() => setOpenIndex(openIndex === index ? null : index)}
                  className="w-full p-6 flex items-center justify-between text-left hover:bg-white/50 transition-colors"
                >
                  <div className="flex-1 pr-6">
                    <span className="text-xs font-medium text-[#0066CC] uppercase tracking-wider mb-2 block">
                      {faq.category}
                    </span>
                    <h3 className="text-lg font-medium text-[#1D1D1F]">
                      {faq.question}
                    </h3>
                  </div>
                  <ChevronDown
                    className={`w-5 h-5 text-[#1D1D1F]/60 flex-shrink-0 transition-transform ${
                      openIndex === index ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {openIndex === index && (
                  <div className="px-6 pb-6">
                    <p className="text-[#1D1D1F]/70 leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Contact CTA */}
          <div className="mt-16 glass-panel p-8 text-center">
            <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-4">
              Still have questions?
            </h2>
            <p className="text-[#1D1D1F]/70 mb-6">
              Our support team is here to help
            </p>
            <a
              href="/contact"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-105 shadow-lg shadow-blue-500/20"
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

