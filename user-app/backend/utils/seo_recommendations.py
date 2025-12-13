"""
Enhanced SEO Recommendations Engine
Provides actionable, prioritized SEO recommendations based on portfolio analysis
"""
from typing import Dict, List, Any
from datetime import datetime, timezone


def analyze_seo_completeness(user_data: Dict[str, Any], galleries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze SEO completeness and generate prioritized recommendations
    
    Args:
        user_data: User profile data
        galleries: List of user's galleries
    
    Returns:
        Dict with analysis and recommendations
    """
    
    issues = []
    recommendations = []
    quick_wins = []
    score = 50  # Base score
    
    # Portfolio SEO settings
    portfolio_seo = user_data.get('portfolio_seo', {})
    
    # Check meta title
    if not portfolio_seo.get('title'):
        issues.append({
            'severity': 'high',
            'category': 'Metadata',
            'issue': 'Missing meta title',
            'description': 'Your portfolio needs a title for search engines',
            'impact': 'High impact on search rankings',
            'fix': 'Add a descriptive title in Portfolio Settings → SEO'
        })
        score -= 15
    else:
        score += 10
        title_len = len(portfolio_seo.get('title', ''))
        if title_len < 30 or title_len > 60:
            recommendations.append({
                'priority': 'medium',
                'category': 'Metadata',
                'recommendation': 'Optimize meta title length',
                'description': f'Current length: {title_len} characters. Ideal: 30-60 characters',
                'action': 'Edit your meta title to be between 30-60 characters'
            })
    
    # Check meta description
    if not portfolio_seo.get('description'):
        issues.append({
            'severity': 'high',
            'category': 'Metadata',
            'issue': 'Missing meta description',
            'description': 'Meta descriptions improve click-through rates',
            'impact': 'Medium impact on search rankings',
            'fix': 'Add a compelling description in Portfolio Settings → SEO'
        })
        score -= 15
    else:
        score += 10
        desc_len = len(portfolio_seo.get('description', ''))
        if desc_len < 120 or desc_len > 160:
            recommendations.append({
                'priority': 'medium',
                'category': 'Metadata',
                'recommendation': 'Optimize meta description length',
                'description': f'Current length: {desc_len} characters. Ideal: 120-160 characters',
                'action': 'Edit your meta description to be between 120-160 characters'
            })
        else:
            score += 5
    
    # Check OG image
    if not portfolio_seo.get('og_image'):
        issues.append({
            'severity': 'medium',
            'category': 'Social',
            'issue': 'Missing Open Graph image',
            'description': 'Social media posts will not show a preview image',
            'impact': 'Low impact on search, high impact on social sharing',
            'fix': 'Upload a cover image in Portfolio Settings'
        })
        score -= 5
    else:
        score += 10
    
    # Check custom domain
    if not user_data.get('portfolio_custom_domain'):
        recommendations.append({
            'priority': 'high',
            'category': 'Technical',
            'recommendation': 'Setup custom domain',
            'description': 'Custom domains improve brand recognition and SEO',
            'action': 'Configure a custom domain in Portfolio Settings',
            'plan_required': 'Plus'
        })
    else:
        score += 15
        quick_wins.append('Custom domain configured ✓')
    
    # Check public galleries
    public_galleries = [g for g in galleries if g.get('privacy') == 'public']
    if len(public_galleries) == 0:
        issues.append({
            'severity': 'critical',
            'category': 'Content',
            'issue': 'No public galleries',
            'description': 'Search engines cannot index private galleries',
            'impact': 'Critical - portfolio not visible to search engines',
            'fix': 'Make at least one gallery public in Gallery Settings'
        })
        score -= 30
    else:
        score += 20
        quick_wins.append(f'{len(public_galleries)} public galleries')
        
        # Check gallery descriptions
        galleries_without_desc = [g for g in public_galleries if not g.get('description')]
        if len(galleries_without_desc) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'Content',
                'recommendation': 'Add descriptions to galleries',
                'description': f'{len(galleries_without_desc)} galleries missing descriptions',
                'action': 'Add keyword-rich descriptions to your galleries'
            })
    
    # Check bio/about section
    if not user_data.get('bio') or len(user_data.get('bio', '')) < 100:
        recommendations.append({
            'priority': 'medium',
            'category': 'Content',
            'recommendation': 'Complete your bio',
            'description': 'A detailed bio helps search engines understand your services',
            'action': 'Write a comprehensive bio (200+ words recommended)'
        })
    else:
        score += 10
        quick_wins.append('Complete bio')
    
    # Check structured data
    seo_settings = user_data.get('seo_settings', {})
    if not seo_settings.get('structured_data'):
        recommendations.append({
            'priority': 'high',
            'category': 'Technical',
            'recommendation': 'Enable structured data',
            'description': 'Schema.org markup helps search engines understand your content',
            'action': 'Click "One-Click Optimize" to enable automatically'
        })
    else:
        score += 10
        quick_wins.append('Structured data enabled ✓')
    
    # Check sitemap
    if not user_data.get('seo_optimized'):
        recommendations.append({
            'priority': 'high',
            'category': 'Technical',
            'recommendation': 'Generate and submit sitemap',
            'description': 'Sitemaps help search engines discover all your pages',
            'action': 'Click "One-Click Optimize" then submit to Google Search Console'
        })
    else:
        score += 10
        quick_wins.append('Sitemap generated ✓')
    
    # Location optimization
    if not user_data.get('city'):
        recommendations.append({
            'priority': 'medium',
            'category': 'Local SEO',
            'recommendation': 'Add your location',
            'description': 'Location helps with local search results',
            'action': 'Add your city in Profile Settings'
        })
    else:
        score += 5
        quick_wins.append('Location specified')
    
    # Calculate overall health
    total_issues = len(issues)
    critical_issues = len([i for i in issues if i['severity'] == 'critical'])
    high_issues = len([i for i in issues if i['severity'] == 'high'])
    
    # Ensure score is between 0-100
    score = max(0, min(100, score))
    
    # Determine health status
    if score >= 80:
        health = 'excellent'
        health_color = 'green'
    elif score >= 60:
        health = 'good'
        health_color = 'blue'
    elif score >= 40:
        health = 'fair'
        health_color = 'yellow'
    else:
        health = 'poor'
        health_color = 'red'
    
    return {
        'score': score,
        'health': health,
        'health_color': health_color,
        'issues': sorted(issues, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['severity']]),
        'recommendations': sorted(recommendations, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']]),
        'quick_wins': quick_wins,
        'stats': {
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'high_priority_issues': high_issues,
            'completed_optimizations': len(quick_wins)
        },
        'next_action': issues[0] if issues else recommendations[0] if recommendations else None
    }


def generate_seo_checklist(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate comprehensive SEO checklist
    
    Returns:
        List of checklist items with completion status
    """
    
    portfolio_seo = user_data.get('portfolio_seo', {})
    
    checklist = [
        {
            'item': 'Meta title configured',
            'completed': bool(portfolio_seo.get('title')),
            'category': 'Basics',
            'importance': 'critical'
        },
        {
            'item': 'Meta description configured',
            'completed': bool(portfolio_seo.get('description')),
            'category': 'Basics',
            'importance': 'critical'
        },
        {
            'item': 'Open Graph image set',
            'completed': bool(portfolio_seo.get('og_image')),
            'category': 'Basics',
            'importance': 'high'
        },
        {
            'item': 'Custom domain configured',
            'completed': bool(user_data.get('portfolio_custom_domain')),
            'category': 'Technical',
            'importance': 'high'
        },
        {
            'item': 'Structured data enabled',
            'completed': bool(user_data.get('seo_settings', {}).get('structured_data')),
            'category': 'Technical',
            'importance': 'high'
        },
        {
            'item': 'Sitemap generated',
            'completed': bool(user_data.get('seo_optimized')),
            'category': 'Technical',
            'importance': 'high'
        },
        {
            'item': 'Bio/about section complete',
            'completed': len(user_data.get('bio', '')) >= 100,
            'category': 'Content',
            'importance': 'medium'
        },
        {
            'item': 'Location specified',
            'completed': bool(user_data.get('city')),
            'category': 'Local SEO',
            'importance': 'medium'
        },
        {
            'item': 'Social links added',
            'completed': bool(user_data.get('portfolio_social_links', {}).get('instagram')),
            'category': 'Social',
            'importance': 'low'
        },
        {
            'item': 'SSL certificate active',
            'completed': bool(user_data.get('custom_domain_certificate_arn')),
            'category': 'Security',
            'importance': 'high'
        }
    ]
    
    # Calculate completion percentage
    completed_count = len([item for item in checklist if item['completed']])
    total_count = len(checklist)
    completion_percentage = int((completed_count / total_count) * 100)
    
    return {
        'checklist': checklist,
        'completion_percentage': completion_percentage,
        'completed_count': completed_count,
        'total_count': total_count
    }

