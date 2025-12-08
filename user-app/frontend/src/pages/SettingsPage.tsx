// Settings Page - Centralized settings hub
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  User, Bell, CreditCard, Shield, Globe, Palette, Mail,
  Settings as SettingsIcon, LogOut, ChevronRight, Camera,
  FileText, Calendar, Workflow
} from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/api';

interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: any;
  path: string;
  badge?: string;
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);

  const sections: SettingsSection[] = [
    {
      id: 'profile',
      title: 'Profile & Business',
      description: 'Manage your profile, business information, and branding',
      icon: User,
      path: '/profile'
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Control email and in-app notification preferences',
      icon: Bell,
      path: '/settings/notifications'
    },
    {
      id: 'billing',
      title: 'Billing & Subscription',
      description: 'Manage your plan, payment method, and billing history',
      icon: CreditCard,
      path: '/billing'
    },
    {
      id: 'portfolio',
      title: 'Portfolio Settings',
      description: 'Configure your public portfolio and custom domain',
      icon: Globe,
      path: '/portfolio-settings'
    },
    {
      id: 'branding',
      title: 'Branding & Watermarks',
      description: 'Upload logos, set colors, and configure watermarks',
      icon: Palette,
      path: '/profile',
      badge: 'Pro'
    },
    {
      id: 'email-templates',
      title: 'Email Templates',
      description: 'Customize email templates for galleries and clients',
      icon: Mail,
      path: '/email-templates'
    },
    {
      id: 'scheduler',
      title: 'Scheduler Settings',
      description: 'Configure availability, booking rules, and calendar sync',
      icon: Calendar,
      path: '/scheduler',
      badge: 'Ultimate'
    },
    {
      id: 'automation',
      title: 'Automation & Workflows',
      description: 'Manage automated follow-ups and client onboarding',
      icon: Workflow,
      path: '/onboarding/workflows',
      badge: 'Ultimate'
    },
    {
      id: 'contracts',
      title: 'Contracts & Templates',
      description: 'Manage contract templates and digital signatures',
      icon: FileText,
      path: '/contracts',
      badge: 'Pro'
    },
    {
      id: 'privacy',
      title: 'Privacy & Security',
      description: 'Password, two-factor authentication, and data privacy',
      icon: Shield,
      path: '/settings/privacy'
    }
  ];

  return (
    <div className="min-h-screen bg-[#F5F5F7]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-serif font-bold text-[#1D1D1F]">
              Galerly
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Dashboard</Link>
              <Link to="/galleries" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">Galleries</Link>
              <Link to="/crm" className="text-sm font-medium text-[#1D1D1F]/60 hover:text-[#1D1D1F] transition-colors">CRM</Link>
              <Link to="/settings" className="text-sm font-medium text-[#1D1D1F]">Settings</Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/settings" className="p-2 text-[#1D1D1F] bg-black/5 rounded-full">
              <SettingsIcon className="w-5 h-5" />
            </Link>
            <button onClick={logout} className="p-2 text-[#1D1D1F]/60 hover:text-red-600 hover:bg-red-50 rounded-full transition-all">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-serif font-medium text-[#1D1D1F] mb-3">
            Settings
          </h1>
          <p className="text-lg text-[#1D1D1F]/60">
            Manage your account, preferences, and business settings
          </p>
        </div>

        {/* Account Summary Card */}
        <div className="glass-panel p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-[#0066CC] to-purple-600 rounded-full flex items-center justify-center">
                <Camera className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-medium text-[#1D1D1F]">{user?.name}</h2>
                <p className="text-sm text-[#1D1D1F]/60">{user?.email}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-100 rounded-full">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span className="text-sm font-medium text-blue-700">
                  {user?.plan || 'Free'} Plan
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Sections Grid */}
        <div className="space-y-3">
          {sections.map((section) => (
            <Link
              key={section.id}
              to={section.path}
              className="glass-panel p-6 flex items-center gap-4 hover:shadow-lg transition-all duration-200 group"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                <section.icon className="w-6 h-6 text-[#0066CC]" />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium text-[#1D1D1F]">{section.title}</h3>
                  {section.badge && (
                    <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded">
                      {section.badge}
                    </span>
                  )}
                </div>
                <p className="text-sm text-[#1D1D1F]/60">{section.description}</p>
              </div>
              
              <ChevronRight className="w-5 h-5 text-[#1D1D1F]/40 group-hover:text-[#1D1D1F] group-hover:translate-x-1 transition-all" />
            </Link>
          ))}
        </div>

        {/* Danger Zone */}
        <div className="mt-12 glass-panel p-6 border-2 border-red-100">
          <h3 className="text-lg font-medium text-red-600 mb-4">Danger Zone</h3>
          <div className="space-y-3">
            <button className="w-full text-left px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-red-700 hover:bg-red-100 transition-colors">
              <div className="font-medium">Export All Data</div>
              <div className="text-sm text-red-600/80 mt-1">Download all your photos, galleries, and client data</div>
            </button>
            <button className="w-full text-left px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-red-700 hover:bg-red-100 transition-colors">
              <div className="font-medium">Delete Account</div>
              <div className="text-sm text-red-600/80 mt-1">Permanently delete your account and all data</div>
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
