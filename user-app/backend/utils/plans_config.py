"""
Shared plan configuration - imported by billing and subscription handlers
Extracted to prevent circular dependencies
"""
import os

# Plan configurations - ALIGNED WITH PRICING PAGE
PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'stripe_price_id': None,
        'max_galleries': 3,  # TOTAL galleries (not per month)
        'galleries_per_month': -1,  # Keep for backward compat but unused
        'storage_gb': 2,
        'feature_ids': ['storage_2gb', 'video_30min_hd', 'analytics_basic', 'branding_on'],
        'features': [
            '2 GB Smart Storage',
            '3 Active Galleries',
            'Unlimited Photo Uploads',
            '30 min Video (HD)',
            'Basic Portfolio',
            'Priority Support',
            'Galerly Branding'
        ]
    },
    'starter': {
        'name': 'Starter',
        'price': 10,
        'price_annual': 96,  # Save $24/year
        'stripe_price_id': os.environ.get('STRIPE_PRICE_STARTER_MONTHLY'),
        'stripe_price_id_monthly': os.environ.get('STRIPE_PRICE_STARTER_MONTHLY'),
        'stripe_price_id_annual': os.environ.get('STRIPE_PRICE_STARTER_ANNUAL'),
        'max_galleries': -1,  # Unlimited
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 25,
        'feature_ids': ['storage_25gb', 'video_60min_hd', 'unlimited_galleries', 'no_branding', 'client_proofing', 'edit_requests', 'analytics_basic'],
        'features': [
            '25 GB Smart Storage',
            'Unlimited Galleries',
            'Unlimited Photo Uploads',
            '1 Hour Video (HD)',
            'Remove Galerly Branding',
            'Client Favorites & Proofing',
            'Basic Analytics'
        ]
    },
    'plus': {
        'name': 'Plus',
        'price': 24,
        'price_annual': 228,  # Save $60/year
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PLUS_MONTHLY'),
        'stripe_price_id_monthly': os.environ.get('STRIPE_PRICE_PLUS_MONTHLY'),
        'stripe_price_id_annual': os.environ.get('STRIPE_PRICE_PLUS_ANNUAL'),
        'max_galleries': -1,  # Unlimited
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 100,
        'feature_ids': ['storage_100gb', 'video_4hr_4k', 'unlimited_galleries', 'custom_domain', 'no_branding', 'analytics_advanced', 'watermarking', 'client_proofing', 'edit_requests'],
        'features': [
            '100 GB Smart Storage',
            'Unlimited Galleries',
            'Unlimited Photo Uploads',
            '4 Hours Video (4K)',
            'Custom Domain',
            'Automated Watermarking',
            'Client Favorites & Proofing',
            'Advanced Analytics'
        ]
    },
    'pro': {
        'name': 'Pro',
        'price': 49,
        'price_annual': 468,  # Save $120/year
        'stripe_price_id': os.environ.get('STRIPE_PRICE_PRO_MONTHLY'),
        'stripe_price_id_monthly': os.environ.get('STRIPE_PRICE_PRO_MONTHLY'),
        'stripe_price_id_annual': os.environ.get('STRIPE_PRICE_PRO_ANNUAL'),
        'max_galleries': -1,  # Unlimited
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 500,
        'feature_ids': ['storage_500gb', 'video_10hr_4k', 'unlimited_galleries', 'custom_domain', 'no_branding', 'analytics_pro', 'raw_support', 'email_templates', 'smart_invoicing', 'seo_tools', 'client_proofing', 'watermarking', 'lightroom_workflow', 'edit_requests'],
        'features': [
            '500 GB Smart Storage',
            'Unlimited Galleries',
            'Unlimited Photo Uploads',
            '10 Hours Video (4K)',
            'RAW Photo Support',
            'Client Invoicing',
            'Email Automation',
            'Scheduler',
            'eSignatures',
            'SEO Optimization Tools',
            'Pro Analytics'
        ]
    },
    'ultimate': {
        'name': 'Ultimate',
        'price': 99,
        'price_annual': 948,  # Save $240/year
        'stripe_price_id': os.environ.get('STRIPE_PRICE_ULTIMATE_MONTHLY'),
        'stripe_price_id_monthly': os.environ.get('STRIPE_PRICE_ULTIMATE_MONTHLY'),
        'stripe_price_id_annual': os.environ.get('STRIPE_PRICE_ULTIMATE_ANNUAL'),
        'max_galleries': -1,  # Unlimited
        'galleries_per_month': -1,  # Unlimited
        'storage_gb': 2000,  # 2 TB
        'feature_ids': ['storage_2tb', 'video_10hr_4k', 'unlimited_galleries', 'custom_domain', 'no_branding', 'analytics_pro', 'raw_support', 'email_templates', 'smart_invoicing', 'scheduler', 'e_signatures', 'seo_tools', 'client_proofing', 'watermarking', 'lightroom_workflow', 'raw_vault', 'edit_requests'],
        'features': [
            '2 TB Smart Storage',
            'Unlimited Galleries',
            'Unlimited Photo Uploads',
            '10 Hours Video (4K)',
            'RAW Vault Archival',
            'All Pro Features'
        ]
    }
}
