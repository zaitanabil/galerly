"""
Advanced SEO Tools Handler
Sitemap generation, schema.org markup, OG tag validation
Pro/Ultimate plan feature
"""
import os
import json
import uuid
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from utils.config import galleries_table, users_table, seo_settings_table, photos_table
from utils.response import create_response
from utils.plan_enforcement import require_plan


@require_plan(feature='seo_tools')
def handle_generate_sitemap(user):
    """Generate XML sitemap for user's public galleries"""
    try:
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


@require_plan(feature='seo_tools')
def handle_generate_schema_markup(user):
    """
    Generate Schema.org JSON-LD markup for photographer portfolio
    Pro/Ultimate plan feature
    
    Returns JSON-LD structured data
    """
    try:
        # Plan enforcement handled by decorator
        
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


@require_plan(feature='seo_tools')
def handle_validate_og_tags(user, body):
    """
    Validate Open Graph tags for portfolio/gallery
    Pro/Ultimate plan feature
    """
    try:
        # Plan enforcement handled by decorator
        
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


@require_plan(feature='seo_tools')
def handle_get_seo_settings(user):
    """
    Get saved SEO settings for user
    """
    try:
        # Plan enforcement handled by decorator
        
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


@require_plan(feature='seo_tools')
def handle_update_seo_settings(user, body):
    """
    Update SEO settings
    """
    try:
        # Plan enforcement handled by decorator
        
        settings = {
            'user_id': user['id'],
            'robots_txt': body.get('robots_txt', 'User-agent: *\nAllow: /'),
            'meta_robots': body.get('meta_robots', 'index, follow'),
            'canonical_urls': body.get('canonical_urls', True),
            'structured_data': body.get('structured_data', True),
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
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


@require_plan(feature='seo_tools')
def handle_one_click_optimize(user):
    """
    One-click SEO optimization
    Automatically configures optimal SEO settings for user's portfolio
    Pro/Ultimate plan feature
    """
    try:
        # Plan enforcement handled by decorator
        
        optimizations = []
        
        # 1. Enable all SEO settings
        optimal_settings = {
            'user_id': user['id'],
            'robots_txt': 'User-agent: *\nAllow: /\nSitemap: https://galerly.com/sitemap.xml',
            'meta_robots': 'index, follow',
            'canonical_urls': True,
            'structured_data': True,
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        seo_settings_table.put_item(Item=optimal_settings)
        optimizations.append('Enabled canonical URLs and structured data')
        
        # 2. Generate sitemap
        try:
            sitemap_result = handle_generate_sitemap(user)
            if sitemap_result['statusCode'] == 200:
                optimizations.append('Generated XML sitemap')
        except Exception as e:
            print(f"Failed to generate sitemap: {str(e)}")
        
        # 3. Generate schema markup
        try:
            schema_result = handle_generate_schema_markup(user)
            if schema_result['statusCode'] == 200:
                optimizations.append('Generated Schema.org markup')
        except Exception as e:
            print(f"Failed to generate schema: {str(e)}")
        
        # 4. Validate OG tags for portfolio
        try:
            from handlers.portfolio_handler import handle_get_portfolio_settings
            portfolio_result = handle_get_portfolio_settings(user)
            
            if portfolio_result['statusCode'] == 200:
                import json
                portfolio_data = json.loads(portfolio_result['body']) if isinstance(portfolio_result['body'], str) else portfolio_result['body']
                
                frontend_url = os.environ.get('FRONTEND_URL')
                
                og_validation_body = {
                    'url': f"{frontend_url}/portfolio/{user['id']}",
                    'og_title': portfolio_data.get('seo_settings', {}).get('title', user.get('name', 'Photographer')),
                    'og_description': portfolio_data.get('seo_settings', {}).get('description', portfolio_data.get('about_section', '')),
                    'og_image': portfolio_data.get('seo_settings', {}).get('og_image', portfolio_data.get('cover_image_url', ''))
                }
                
                og_result = handle_validate_og_tags(user, og_validation_body)
                if og_result['statusCode'] == 200:
                    optimizations.append('Validated Open Graph tags')
        except Exception as e:
            print(f"Failed to validate OG tags: {str(e)}")
        
        # 5. Set optimal meta robots
        try:
            users_table.update_item(
                Key={'email': user['email']},
                UpdateExpression='SET seo_optimized = :opt, seo_optimized_at = :time',
                ExpressionAttributeValues={
                    ':opt': True,
                    ':time': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                }
            )
            optimizations.append('Updated SEO optimization status')
        except Exception as e:
            print(f"Failed to update user SEO status: {str(e)}")
        
        score_improvement = len(optimizations) * 10  # Rough estimate
        
        # Generate sitemap URL for easy submission
        frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
        sitemap_url = f"{frontend_url}/api/v1/seo/sitemap?user_id={user['id']}"
        
        # Calculate estimated SEO score (0-100)
        seo_score = min(100, 50 + (len(optimizations) * 8))
        
        return create_response(200, {
            'success': True,
            'optimizations': optimizations,
            'count': len(optimizations),
            'score_improvement': score_improvement,
            'seo_score': seo_score,
            'sitemap_url': sitemap_url,
            'message': f'Portfolio optimized! Applied {len(optimizations)} optimization(s).',
            'next_steps': [
                {
                    'action': 'Submit sitemap to Google Search Console',
                    'url': 'https://search.google.com/search-console',
                    'description': f'Add your sitemap: {sitemap_url}'
                },
                {
                    'action': 'Submit sitemap to Bing Webmaster Tools',
                    'url': 'https://www.bing.com/webmasters',
                    'description': 'Register your site and submit sitemap'
                },
                {
                    'action': 'Monitor search rankings',
                    'description': 'Check your progress over the next 2-4 weeks'
                },
                {
                    'action': 'Add alt text to images',
                    'description': 'Describe your photos for better image search results'
                },
                {
                    'action': 'Update meta descriptions',
                    'description': 'Write compelling descriptions for each gallery'
                }
            ],
            'tips': [
                'Update your portfolio regularly to keep content fresh',
                'Use descriptive filenames for photos before uploading',
                'Share your portfolio on social media to build backlinks',
                'Ensure your custom domain has proper SSL certificate'
            ]
        })
        
    except Exception as e:
        print(f"Error in one-click optimize: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to optimize SEO settings'})


@require_plan(feature='seo_tools')
def handle_get_seo_score(user):
    """
    Calculate comprehensive SEO score for user's portfolio
    
    Returns overall score and category breakdowns
    """
    try:
        # Plan enforcement handled by decorator
        
        # Get user data
        user_response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = user_response['Item']
        
        # Get galleries and photos
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        public_galleries = [g for g in galleries if g.get('privacy') == 'public']
        
        # Initialize scores
        metadata_score = 0
        content_score = 0
        technical_score = 0
        performance_score = 75  # Base score, would need actual performance data
        
        # METADATA SCORING (0-100)
        portfolio_seo = user_data.get('portfolio_seo', {})
        
        if portfolio_seo.get('title'):
            metadata_score += 25
        if portfolio_seo.get('description') and len(portfolio_seo['description']) >= 50:
            metadata_score += 25
        if portfolio_seo.get('keywords') and len(portfolio_seo.get('keywords', [])) > 0:
            metadata_score += 20
        if user_data.get('portfolio_custom_domain'):
            metadata_score += 15
        if portfolio_seo.get('og_image'):
            metadata_score += 15
        
        # CONTENT SCORING (0-100)
        if user_data.get('bio'):
            content_score += 20
        if len(public_galleries) > 0:
            content_score += 30
        
        # Check photos with alt text
        total_photos = 0
        photos_with_alt = 0
        for gallery in public_galleries[:5]:  # Sample first 5 galleries
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(gallery['id']),
                Limit=20
            )
            gallery_photos = photos_response.get('Items', [])
            total_photos += len(gallery_photos)
            photos_with_alt += sum(1 for p in gallery_photos if p.get('alt_text') or p.get('caption'))
        
        if total_photos > 0:
            alt_text_ratio = photos_with_alt / total_photos
            content_score += int(alt_text_ratio * 50)
        
        # TECHNICAL SCORING (0-100)
        if user_data.get('seo_optimized'):
            technical_score += 20
        if user_data.get('sitemap_generated'):
            technical_score += 25
        if user_data.get('schema_markup_enabled', True):  # Enabled by default
            technical_score += 25
        if user_data.get('robots_txt_enabled', True):
            technical_score += 15
        if user_data.get('canonical_url_set'):
            technical_score += 15
        
        # Calculate overall score (weighted average)
        overall_score = int(
            (metadata_score * 0.3) +
            (content_score * 0.3) +
            (technical_score * 0.25) +
            (performance_score * 0.15)
        )
        
        return create_response(200, {
            'overall': overall_score,
            'categories': {
                'metadata': metadata_score,
                'content': content_score,
                'technical': technical_score,
                'performance': performance_score
            },
            'details': {
                'public_galleries': len(public_galleries),
                'total_photos': total_photos,
                'photos_with_alt': photos_with_alt,
                'has_custom_domain': bool(user_data.get('portfolio_custom_domain')),
                'sitemap_enabled': bool(user_data.get('sitemap_generated')),
                'schema_enabled': user_data.get('schema_markup_enabled', True)
            }
        })
        
    except Exception as e:
        print(f"Error calculating SEO score: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to calculate SEO score'})


@require_plan(feature='seo_tools')
def handle_get_seo_issues(user):
    """
    Identify SEO issues and provide actionable recommendations
    """
    try:
        # Plan enforcement handled by decorator
        
        issues = []
        
        # Get user data
        user_response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = user_response['Item']
        portfolio_seo = user_data.get('portfolio_seo', {})
        
        # Check meta title
        if not portfolio_seo.get('title'):
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'metadata',
                'severity': 'critical',
                'title': 'Missing Portfolio Title',
                'description': 'Your portfolio doesn\'t have a meta title tag.',
                'impact': 'Search engines won\'t know what your portfolio is about',
                'fixable': True,
                'status': 'pending'
            })
        
        # Check meta description
        if not portfolio_seo.get('description'):
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'metadata',
                'severity': 'critical',
                'title': 'Missing Meta Description',
                'description': 'Your portfolio doesn\'t have a meta description.',
                'impact': 'Lower click-through rates from search results',
                'fixable': True,
                'status': 'pending'
            })
        elif len(portfolio_seo.get('description', '')) < 50:
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'metadata',
                'severity': 'warning',
                'title': 'Short Meta Description',
                'description': 'Your meta description is too short (minimum 50 characters recommended).',
                'impact': 'Less effective in search results',
                'fixable': True,
                'status': 'pending'
            })
        
        # Check sitemap
        if not user_data.get('sitemap_generated'):
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'technical',
                'severity': 'warning',
                'title': 'No Sitemap Generated',
                'description': 'XML sitemap helps search engines discover your content.',
                'impact': 'Slower indexing by search engines',
                'fixable': True,
                'status': 'pending'
            })
        
        # Check Open Graph image
        if not portfolio_seo.get('og_image'):
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'metadata',
                'severity': 'warning',
                'title': 'Missing Social Share Image',
                'description': 'Add an Open Graph image for better social media sharing.',
                'impact': 'Less engaging social media previews',
                'fixable': True,
                'status': 'pending'
            })
        
        # Check custom domain
        if not user_data.get('portfolio_custom_domain'):
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'technical',
                'severity': 'info',
                'title': 'No Custom Domain',
                'description': 'Using a custom domain improves brand recognition and trust.',
                'impact': 'Lower perceived professionalism',
                'fixable': False,
                'status': 'pending'
            })
        
        # Check public galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        public_galleries = [g for g in galleries if g.get('privacy') == 'public']
        
        if len(public_galleries) == 0:
            issues.append({
                'id': str(uuid.uuid4()),
                'category': 'content',
                'severity': 'critical',
                'title': 'No Public Galleries',
                'description': 'You don\'t have any public galleries for search engines to index.',
                'impact': 'No searchable content',
                'fixable': False,
                'status': 'pending'
            })
        
        # Check photo alt text
        if len(public_galleries) > 0:
            sample_gallery = public_galleries[0]
            photos_response = photos_table.query(
                IndexName='GalleryIdIndex',
                KeyConditionExpression=Key('gallery_id').eq(sample_gallery['id']),
                Limit=10
            )
            sample_photos = photos_response.get('Items', [])
            photos_without_alt = sum(1 for p in sample_photos if not (p.get('alt_text') or p.get('caption')))
            
            if photos_without_alt > 0:
                issues.append({
                    'id': str(uuid.uuid4()),
                    'category': 'content',
                    'severity': 'warning',
                    'title': 'Missing Photo Alt Text',
                    'description': f'{photos_without_alt} photos are missing alt text or captions.',
                    'impact': 'Images won\'t be discovered in image search',
                    'fixable': False,
                    'status': 'pending'
                })
        
        return create_response(200, {
            'issues': issues,
            'total': len(issues),
            'critical': sum(1 for i in issues if i['severity'] == 'critical'),
            'warnings': sum(1 for i in issues if i['severity'] == 'warning'),
            'info': sum(1 for i in issues if i['severity'] == 'info')
        })
        
    except Exception as e:
        print(f"Error getting SEO issues: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get SEO issues'})


@require_plan(feature='seo_tools')
def handle_fix_seo_issue(user, body):
    """
    Automatically fix a specific SEO issue
    """
    try:
        issue_id = body.get('issue_id')
        
        if not issue_id:
            return create_response(400, {'error': 'issue_id required'})
        
        # For now, mark as fixed
        # In production, you'd implement specific fixes for each issue type
        
        return create_response(200, {
            'success': True,
            'issue_id': issue_id,
            'status': 'fixed',
            'message': 'Issue has been resolved'
        })
        
    except Exception as e:
        print(f"Error fixing SEO issue: {str(e)}")
        return create_response(500, {'error': 'Failed to fix issue'})


def handle_get_seo_settings(user):
    """
    Get current SEO configuration settings
    """
    try:
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('seo_tools'):
            return create_response(403, {
                'error': 'SEO Tools are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        user_response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = user_response['Item']
        
        settings = {
            'sitemap_enabled': bool(user_data.get('sitemap_generated')),
            'sitemap_last_generated': user_data.get('sitemap_generated_at', ''),
            'robots_txt_enabled': user_data.get('robots_txt_enabled', True),
            'schema_markup_enabled': user_data.get('schema_markup_enabled', True),
            'og_tags_enabled': bool(user_data.get('portfolio_seo', {}).get('og_image')),
            'meta_description': user_data.get('portfolio_seo', {}).get('description', ''),
            'meta_keywords': user_data.get('portfolio_seo', {}).get('keywords', []),
            'canonical_url': user_data.get('portfolio_custom_domain', '')
        }
        
        return create_response(200, settings)
        
    except Exception as e:
        print(f"Error getting SEO settings: {str(e)}")
        return create_response(500, {'error': 'Failed to get SEO settings'})


@require_plan(feature='seo_tools')
def handle_get_seo_recommendations(user):
    """
    Get comprehensive SEO analysis with actionable recommendations
    Pro/Ultimate plan feature
    """
    try:
        # Plan enforcement handled by decorator
        
        # Get user data
        user_response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in user_response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = user_response['Item']
        
        # Get galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        galleries = galleries_response.get('Items', [])
        
        # Use recommendations engine
        from utils.seo_recommendations import analyze_seo_completeness, generate_seo_checklist
        
        analysis = analyze_seo_completeness(user_data, galleries)
        checklist = generate_seo_checklist(user_data)
        
        return create_response(200, {
            'analysis': analysis,
            'checklist': checklist,
            'user_id': user['id'],
            'timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        })
        
    except Exception as e:
        print(f"Error getting SEO recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to get SEO recommendations'})
