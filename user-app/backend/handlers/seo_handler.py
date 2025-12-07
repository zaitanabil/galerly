"""
Advanced SEO Tools Handler
Sitemap generation, schema.org markup, OG tag validation
Pro/Ultimate plan feature
"""
import os
import json
from datetime import datetime
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table, seo_settings_table
from utils.response import create_response


def handle_generate_sitemap(user):
    """
    Generate XML sitemap for photographer's portfolio
    Pro/Ultimate plan feature
    
    Returns XML sitemap content
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True,
                'required_feature': 'seo_tools'
            })
        
        # Get user's public galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        
        galleries = [g for g in galleries_response.get('Items', []) if g.get('privacy') == 'public']
        
        # Base URL
        frontend_url = os.environ.get('FRONTEND_URL')
        username = user.get('username', user['id'])
        
        # Build sitemap XML
        sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        # Portfolio homepage
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{frontend_url}/portfolio/{user["id"]}</loc>\n'
        sitemap_xml += f'    <changefreq>weekly</changefreq>\n'
        sitemap_xml += f'    <priority>1.0</priority>\n'
        sitemap_xml += '  </url>\n'
        
        # Each public gallery
        for gallery in galleries:
            sitemap_xml += '  <url>\n'
            sitemap_xml += f'    <loc>{frontend_url}/gallery/{gallery["id"]}</loc>\n'
            sitemap_xml += f'    <lastmod>{gallery.get("updated_at", gallery.get("created_at", ""))}</lastmod>\n'
            sitemap_xml += f'    <changefreq>weekly</changefreq>\n'
            sitemap_xml += f'    <priority>0.8</priority>\n'
            sitemap_xml += '  </url>\n'
        
        sitemap_xml += '</urlset>'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/xml',
                'Access-Control-Allow-Origin': '*'
            },
            'body': sitemap_xml
        }
        
    except Exception as e:
        print(f"Error generating sitemap: {str(e)}")
        return create_response(500, {'error': 'Failed to generate sitemap'})


def handle_generate_schema_markup(user):
    """
    Generate Schema.org JSON-LD markup for photographer portfolio
    Pro/Ultimate plan feature
    
    Returns JSON-LD structured data
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Get portfolio settings
        from handlers.portfolio_handler import handle_get_portfolio_settings
        portfolio_response = handle_get_portfolio_settings(user)
        
        if portfolio_response['statusCode'] != 200:
            portfolio_data = {}
        else:
            portfolio_data = json.loads(portfolio_response['body']) if isinstance(portfolio_response['body'], str) else portfolio_response['body']
        
        frontend_url = os.environ.get('FRONTEND_URL')
        
        # Build Schema.org markup for Professional Service / Photographer
        schema = {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "name": user.get('name', 'Photographer'),
            "description": user.get('bio', 'Professional photography services'),
            "url": f"{frontend_url}/portfolio/{user['id']}",
            "telephone": user.get('phone', ''),
            "email": user.get('email', ''),
            "address": {
                "@type": "PostalAddress",
                "addressLocality": user.get('city', '')
            },
            "priceRange": "$$",
            "image": portfolio_data.get('cover_image_url', ''),
            "logo": portfolio_data.get('logo_url', '')
        }
        
        # Add social links
        social_links = portfolio_data.get('social_links', {})
        same_as = []
        if social_links.get('instagram'):
            same_as.append(social_links['instagram'])
        if social_links.get('facebook'):
            same_as.append(social_links['facebook'])
        if social_links.get('website'):
            same_as.append(social_links['website'])
        
        if same_as:
            schema['sameAs'] = same_as
        
        # Add specialties as services offered
        if user.get('specialties'):
            schema['hasOfferCatalog'] = {
                "@type": "OfferCatalog",
                "name": "Photography Services",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "itemOffered": {
                            "@type": "Service",
                            "name": specialty
                        }
                    }
                    for specialty in user.get('specialties', [])
                ]
            }
        
        # Clean up None values
        schema = {k: v for k, v in schema.items() if v}
        
        return create_response(200, {
            'schema': schema,
            'script_tag': f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
        })
        
    except Exception as e:
        print(f"Error generating schema markup: {str(e)}")
        return create_response(500, {'error': 'Failed to generate schema markup'})


def handle_validate_og_tags(user, body):
    """
    Validate Open Graph tags for portfolio/gallery
    Pro/Ultimate plan feature
    
    Request body:
    {
        "url": "https://galerly.com/portfolio/user-id",
        "og_title": "...",
        "og_description": "...",
        "og_image": "..."
    }
    
    Returns validation results and recommendations
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        url = body.get('url', '')
        og_title = body.get('og_title', '')
        og_description = body.get('og_description', '')
        og_image = body.get('og_image', '')
        
        issues = []
        warnings = []
        recommendations = []
        
        # Validate OG Title
        if not og_title:
            issues.append('OG Title is missing')
        elif len(og_title) < 10:
            warnings.append('OG Title is too short (min 10 characters recommended)')
        elif len(og_title) > 60:
            warnings.append('OG Title is too long (max 60 characters recommended)')
        else:
            recommendations.append('OG Title length is good')
        
        # Validate OG Description
        if not og_description:
            issues.append('OG Description is missing')
        elif len(og_description) < 50:
            warnings.append('OG Description is too short (min 50 characters recommended)')
        elif len(og_description) > 200:
            warnings.append('OG Description is too long (max 200 characters recommended)')
        else:
            recommendations.append('OG Description length is good')
        
        # Validate OG Image
        if not og_image:
            issues.append('OG Image is missing')
        else:
            if not (og_image.startswith('http://') or og_image.startswith('https://')):
                issues.append('OG Image must be a full URL (including https://)')
            else:
                recommendations.append('OG Image URL is valid')
            
            # Check image format
            if not any(og_image.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                warnings.append('OG Image should be JPG, PNG, or WebP')
            
            # Image dimensions recommendation
            recommendations.append('Recommended OG Image size: 1200x630px (1.91:1 ratio)')
        
        # Validate URL
        if not url:
            warnings.append('URL is missing')
        elif not (url.startswith('http://') or url.startswith('https://')):
            issues.append('URL must include protocol (https://)')
        
        # SEO Score calculation
        score = 100
        score -= len(issues) * 20
        score -= len(warnings) * 10
        score = max(0, score)
        
        # Additional recommendations
        if score == 100:
            recommendations.append('All OG tags are properly configured!')
        elif score >= 80:
            recommendations.append('Good! Fix warnings for perfect score')
        elif score >= 60:
            recommendations.append('Needs improvement - fix issues and warnings')
        else:
            recommendations.append('Critical issues detected - fix immediately')
        
        return create_response(200, {
            'score': score,
            'status': 'excellent' if score >= 90 else 'good' if score >= 70 else 'needs_improvement',
            'issues': issues,
            'warnings': warnings,
            'recommendations': recommendations,
            'og_tags': {
                'og:title': og_title,
                'og:description': og_description,
                'og:image': og_image,
                'og:url': url,
                'og:type': 'website'
            }
        })
        
    except Exception as e:
        print(f"Error validating OG tags: {str(e)}")
        return create_response(500, {'error': 'Failed to validate OG tags'})


def handle_get_seo_settings(user):
    """
    Get saved SEO settings for user
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        response = seo_settings_table.get_item(Key={'user_id': user['id']})
        
        if 'Item' not in response:
            # Return defaults
            return create_response(200, {
                'robots_txt': 'User-agent: *\nAllow: /',
                'meta_robots': 'index, follow',
                'canonical_urls': True,
                'structured_data': True
            })
        
        return create_response(200, response['Item'])
        
    except Exception as e:
        print(f"Error getting SEO settings: {str(e)}")
        return create_response(500, {'error': 'Failed to get SEO settings'})


def handle_update_seo_settings(user, body):
    """
    Update SEO settings
    """
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        settings = {
            'user_id': user['id'],
            'robots_txt': body.get('robots_txt', 'User-agent: *\nAllow: /'),
            'meta_robots': body.get('meta_robots', 'index, follow'),
            'canonical_urls': body.get('canonical_urls', True),
            'structured_data': body.get('structured_data', True),
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        seo_settings_table.put_item(Item=settings)
        
        return create_response(200, settings)
        
    except Exception as e:
        print(f"Error updating SEO settings: {str(e)}")
        return create_response(500, {'error': 'Failed to update SEO settings'})


def handle_get_robots_txt(user):
    """
    Get robots.txt content
    """
    try:
        response = seo_settings_table.get_item(Key={'user_id': user['id']})
        
        robots_txt = response.get('Item', {}).get('robots_txt', 'User-agent: *\nAllow: /')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': '*'
            },
            'body': robots_txt
        }
        
    except Exception as e:
        print(f"Error getting robots.txt: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': 'User-agent: *\nAllow: /'
        }
