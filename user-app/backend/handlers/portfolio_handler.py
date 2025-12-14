"""
Portfolio customization handlers
"""
import os
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from utils.config import users_table, galleries_table, dynamodb
from utils.response import create_response
from handlers.subscription_handler import get_user_features

# Import custom domain utilities
try:
    from utils.cloudfront_manager import (
        create_distribution,
        get_distribution_status,
        update_distribution,
        delete_distribution,
        create_invalidation,
        wait_for_deployment
    )
    CLOUDFRONT_AVAILABLE = True
except ImportError:
    CLOUDFRONT_AVAILABLE = False
    print("Warning: CloudFront manager not available")

try:
    from utils.acm_manager import (
        request_certificate,
        describe_certificate,
        wait_for_validation,
        get_certificate_validation_records
    )
    ACM_AVAILABLE = True
except ImportError:
    ACM_AVAILABLE = False
    print("Warning: ACM manager not available")

try:
    from utils.dns_checker import (
        check_propagation,
        verify_dns_configuration,
        check_domain_availability
    )
    DNS_CHECKER_AVAILABLE = True
except ImportError:
    DNS_CHECKER_AVAILABLE = False
    print("Warning: DNS checker not available")

# Custom domain configurations table
custom_domains_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_CUSTOM_DOMAINS', 'galerly-custom-domains-local'))

def handle_get_portfolio_settings(user):
    """Get portfolio customization settings for current user"""
    try:
        # Get user data which contains portfolio settings
        response = users_table.get_item(Key={'email': user['email']})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        
        # Extract portfolio settings (defaults if not set)
        portfolio_settings = {
            'theme': user_data.get('portfolio_theme', 'default'),
            'primary_color': user_data.get('portfolio_primary_color', '#0066CC'),
            'secondary_color': user_data.get('portfolio_secondary_color', '#FFD700'),
            'logo_url': user_data.get('portfolio_logo_url', ''),
            'cover_image_url': user_data.get('portfolio_cover_image_url', ''),
            'about_section': user_data.get('portfolio_about', ''),
            'show_contact_form': user_data.get('portfolio_show_contact_form', True),
            'social_links': user_data.get('portfolio_social_links', {
                'instagram': '',
                'website': '',
                'facebook': '',
                'twitter': ''
            }),
            'featured_galleries': user_data.get('portfolio_featured_galleries', []),
            'portfolio_sections': user_data.get('portfolio_sections', []),
            'custom_domain': user_data.get('portfolio_custom_domain', ''),
            'seo_settings': user_data.get('portfolio_seo', {
                'title': '',
                'description': '',
                'keywords': '',
                'og_image': ''
            })
        }
        
        return create_response(200, portfolio_settings)
    except Exception as e:
        print(f"Error getting portfolio settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load portfolio settings'})

def handle_update_portfolio_settings(user, body):
    """Update portfolio customization settings"""
    try:
        # Check plan permission for portfolio customization
        # Portfolio customization is available on all paid plans (Starter+)
        # No branding removal requires Starter+, custom domain requires Plus+
        features, plan_id, _ = get_user_features(user)
        
        # Basic portfolio editing is allowed for all users
        # Advanced features checked individually below
        
        # Build update expression
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        # Theme
        if 'theme' in body:
            update_expressions.append('portfolio_theme = :theme')
            expression_values[':theme'] = body['theme']
        
        # Colors
        if 'primary_color' in body:
            update_expressions.append('portfolio_primary_color = :primary_color')
            expression_values[':primary_color'] = body['primary_color']
        
        if 'secondary_color' in body:
            update_expressions.append('portfolio_secondary_color = :secondary_color')
            expression_values[':secondary_color'] = body['secondary_color']
        
        # Logo and cover image
        if 'logo_url' in body:
            update_expressions.append('portfolio_logo_url = :logo_url')
            expression_values[':logo_url'] = body['logo_url']
        
        if 'cover_image_url' in body:
            update_expressions.append('portfolio_cover_image_url = :cover_image_url')
            expression_values[':cover_image_url'] = body['cover_image_url']
        
        # About section
        if 'about_section' in body:
            update_expressions.append('portfolio_about = :about_section')
            expression_values[':about_section'] = body['about_section']
        
        # Contact form
        if 'show_contact_form' in body:
            update_expressions.append('portfolio_show_contact_form = :show_contact_form')
            expression_values[':show_contact_form'] = body['show_contact_form']
        
        # Social links
        if 'social_links' in body:
            update_expressions.append('portfolio_social_links = :social_links')
            expression_values[':social_links'] = body['social_links']
        
        # Featured galleries
        if 'featured_galleries' in body:
            update_expressions.append('portfolio_featured_galleries = :featured_galleries')
            expression_values[':featured_galleries'] = body['featured_galleries']
        
        # Portfolio sections
        if 'portfolio_sections' in body:
            update_expressions.append('portfolio_sections = :portfolio_sections')
            expression_values[':portfolio_sections'] = body['portfolio_sections']
        
        # Custom domain
        if 'custom_domain' in body:
            update_expressions.append('portfolio_custom_domain = :custom_domain')
            expression_values[':custom_domain'] = body['custom_domain']
            
        # SEO
        if 'seo_settings' in body:
            update_expressions.append('portfolio_seo = :seo')
            expression_values[':seo'] = body['seo_settings']
        
        # Always update updated_at
        from datetime import datetime
        update_expressions.append('updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        if not update_expressions:
            return create_response(400, {'error': 'No fields to update'})
        
        # Update user record
        update_expression = 'SET ' + ', '.join(update_expressions)
        
        update_params = {
            'Key': {'email': user['email']},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values
        }
        
        # Only add ExpressionAttributeNames if we have any
        if expression_names:
            update_params['ExpressionAttributeNames'] = expression_names
        
        users_table.update_item(**update_params)
        
        # Return updated settings
        return handle_get_portfolio_settings(user)
    except Exception as e:
        print(f"Error updating portfolio settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to update portfolio settings'})

def handle_get_public_portfolio(photographer_id):
    """Get public portfolio view with customization applied"""
    try:
        # Get photographer data
        response = users_table.scan(
            FilterExpression='id = :id AND #role = :role',
            ExpressionAttributeValues={':id': photographer_id, ':role': 'photographer'},
            ExpressionAttributeNames={'#role': 'role'}
        )
        
        users = response.get('Items', [])
        if not users:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = users[0]
        
        # Get portfolio settings
        portfolio_settings = {
            'theme': photographer.get('portfolio_theme', 'default'),
            'primary_color': photographer.get('portfolio_primary_color', '#0066CC'),
            'secondary_color': photographer.get('portfolio_secondary_color', '#FFD700'),
            'logo_url': photographer.get('portfolio_logo_url', ''),
            'cover_image_url': photographer.get('portfolio_cover_image_url', ''),
            'about_section': photographer.get('portfolio_about', photographer.get('bio', '')),
            'show_contact_form': photographer.get('portfolio_show_contact_form', True),
            'social_links': photographer.get('portfolio_social_links', {
                'instagram': '',
                'website': '',
                'facebook': '',
                'twitter': ''
            }),
            'featured_galleries': photographer.get('portfolio_featured_galleries', []),
            'portfolio_sections': photographer.get('portfolio_sections', []),
            'seo_settings': photographer.get('portfolio_seo', {
                'title': '',
                'description': '',
                'keywords': '',
                'og_image': ''
            })
        }
        
        # Get photographer's galleries
        galleries_response = galleries_table.query(
            KeyConditionExpression=Key('user_id').eq(photographer_id)
        )
        all_galleries = galleries_response.get('Items', [])
        
        # Filter to only PUBLIC galleries
        public_galleries = [g for g in all_galleries if g.get('privacy', 'private') == 'public']
        
        # Sort galleries: featured first, then by date
        featured_ids = portfolio_settings.get('featured_galleries', [])
        featured_galleries = [g for g in public_galleries if g['id'] in featured_ids]
        other_galleries = [g for g in public_galleries if g['id'] not in featured_ids]
        
        # Sort featured by featured order, others by date
        featured_galleries.sort(key=lambda x: featured_ids.index(x['id']) if x['id'] in featured_ids else 999)
        other_galleries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        sorted_galleries = featured_galleries + other_galleries
        
        # Remove sensitive info
        for gallery in sorted_galleries:
            gallery.pop('client_name', None)
            gallery.pop('client_email', None)
            gallery.pop('password', None)
        
        return create_response(200, {
            'photographer': {
                'id': photographer['id'],
                'name': photographer.get('name'),
                'username': photographer.get('username'),
                'city': photographer.get('city'),
                'bio': photographer.get('bio'),
                'specialties': photographer.get('specialties', [])
            },
            'portfolio': portfolio_settings,
            'galleries': sorted_galleries,
            'gallery_count': len(sorted_galleries),
            'photo_count': sum(int(g.get('photo_count', 0)) for g in sorted_galleries)
        })
    except Exception as e:
        print(f"Error getting public portfolio: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to load portfolio'})

def handle_check_domain_status(user, domain):
    """
    Check current status of custom domain configuration
    Returns verification status and DNS configuration info
    """
    try:
        # Check plan permission
        features, _, _ = get_user_features(user)
        if not features.get('custom_domain', False):
            return create_response(403, {
                'error': 'Custom domain is available on Plus, Pro, and Ultimate plans.',
                'upgrade_required': True
            })
        
        if not domain:
            return create_response(400, {'error': 'Domain parameter required'})
        
        # Check if domain is configured
        response = users_table.get_item(Key={'email': user['email']})
        if 'Item' not in response:
            return create_response(404, {'error': 'User not found'})
        
        user_data = response['Item']
        configured_domain = user_data.get('portfolio_custom_domain', '')
        
        # Verify CNAME record
        verified = False
        cname_value = None
        try:
            answers = dns.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                cname_value = str(rdata.target).rstrip('.')
                if 'galerly.com' in cname_value or 'cloudfront.net' in cname_value:
                    verified = True
                    break
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, Exception) as e:
            print(f"DNS lookup failed for {domain}: {str(e)}")
            verified = False
        
        return create_response(200, {
            'configured': configured_domain == domain,
            'verified': verified,
            'cname_record': cname_value,
            'last_verified': user_data.get('domain_last_verified'),
            'target_cname': 'cdn.galerly.com'
        })
        
    except Exception as e:
        print(f"Error checking domain status: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to check domain status'})


def handle_verify_domain(user, body):
    """
    Verify custom domain ownership via DNS CNAME check
    Requires 'custom_domain' feature (Plus plan and above)
    """
    try:
        # 1. Check Plan Limits
        features, _, _ = get_user_features(user)
        if not features.get('custom_domain', False):
            return create_response(403, {
                'error': 'Custom domains are available on Plus, Pro, and Ultimate plans. Please upgrade to use this feature.',
                'upgrade_required': True
            })

        domain = body.get('domain', '').strip().lower()
        if not domain or '.' not in domain:
             return create_response(400, {'error': 'Invalid domain format. Example: photos.yourdomain.com'})
             
        # Remove protocol if present
        domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
        
        # 2. Check for Domain Collision
        # Scan users table to see if domain is already taken
        # (Note: In high scale, this should be a GSI or separate Domains table)
        scan_response = users_table.scan(
            FilterExpression='portfolio_custom_domain = :d',
            ExpressionAttributeValues={':d': domain}
        )
        
        existing_users = scan_response.get('Items', [])
        if existing_users:
            # If taken by SOMEONE ELSE
            if existing_users[0]['id'] != user['id']:
                return create_response(409, {'error': 'This domain is already connected to another account.'})
        
        # 3. Verify DNS CNAME
        cname_target = os.environ.get('CNAME_TARGET')
        # Expected target format with trailing dot
        EXPECTED_TARGETS = [f'{cname_target}.', f'domains.{cname_target}.']
        verified = False
        
        try:
            answers = dns.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                cname_target = str(rdata.target).lower()
                # Check if target matches any of our expected endpoints
                # DNS python returns trailing dot
                if any(t in cname_target for t in EXPECTED_TARGETS):
                    verified = True
                    break
        except dns.resolver.NoAnswer:
            cname_target = os.environ.get('CNAME_TARGET')
            return create_response(400, {'error': f'No CNAME record found. Please add a CNAME record pointing to {cname_target}'})
        except dns.resolver.NXDOMAIN:
            return create_response(400, {'error': 'Domain does not exist. Please check the spelling.'})
        except Exception as e:
            print(f"DNS Error: {str(e)}")
            # In LocalStack/Dev, we might want to bypass strict DNS check or mock it
            # For now, we fail safe
            return create_response(400, {'error': f'DNS verification failed: {str(e)}'})

        if not verified:
            expected_cname = os.environ.get('CNAME_TARGET')
            return create_response(400, {
                'error': f'CNAME verification failed. Your domain points to {cname_target if "cname_target" in locals() else "unknown"}, but should point to {expected_cname}'
            })
        
        # 4. Save if verified
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET portfolio_custom_domain = :d, updated_at = :now',
            ExpressionAttributeValues={
                ':d': domain,
                ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        return create_response(200, {
            'verified': True, 
            'domain': domain, 
            'message': 'Domain verified and connected successfully. HTTPS certificates will be provisioned shortly.'
        })
    except Exception as e:
        print(f"Error verifying domain: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to verify domain'})


@require_plan(feature='custom_domain')
@require_role('photographer')
def handle_setup_custom_domain(user, body):
    """
    Complete custom domain setup with CloudFront and ACM integration
    This creates a CloudFront distribution and requests SSL certificate
    
    Request body:
    {
        "domain": "gallery.yourstudio.com",
        "auto_provision": true  # Auto-create CloudFront and ACM resources
    }
    
    Returns:
        dict: {
            'success': bool,
            'domain': str,
            'certificate_arn': str,
            'distribution_id': str,
            'validation_records': list,  # DNS records needed for SSL validation
            'status': str,
            'next_steps': list
        }
    """
    try:
        # Plan enforcement handled by decorators
        
        domain = body.get('domain', '').strip().lower()
        auto_provision = body.get('auto_provision', True)
        
        if not domain:
            return create_response(400, {'error': 'Domain is required'})
        
        # Remove protocol if present
        domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
        
        # Check if domain already configured by another user
        scan_response = users_table.scan(
            FilterExpression='portfolio_custom_domain = :d',
            ExpressionAttributeValues={':d': domain}
        )
        
        existing_users = scan_response.get('Items', [])
        if existing_users and existing_users[0]['id'] != user['id']:
            return create_response(409, {
                'error': 'This domain is already connected to another account.'
            })
        
        # Check if domain configuration already exists
        try:
            existing_config = custom_domains_table.get_item(
                Key={'user_id': user['id'], 'domain': domain}
            )
            
            if 'Item' in existing_config:
                config = existing_config['Item']
                
                # Return existing configuration
                return create_response(200, {
                    'success': True,
                    'domain': domain,
                    'certificate_arn': config.get('certificate_arn'),
                    'distribution_id': config.get('distribution_id'),
                    'distribution_domain': config.get('distribution_domain'),
                    'status': config.get('status', 'pending'),
                    'validation_records': config.get('validation_records', []),
                    'existing': True,
                    'message': 'Domain configuration already exists'
                })
        except:
            pass  # Table might not exist in local env
        
        if not auto_provision:
            return create_response(200, {
                'success': True,
                'domain': domain,
                'message': 'Domain saved. Enable auto_provision to create CloudFront and SSL certificate.',
                'next_steps': [
                    'Set auto_provision=true to automatically create resources',
                    'Or manually configure CloudFront and ACM'
                ]
            })
        
        # Check if utilities are available
        if not ACM_AVAILABLE or not CLOUDFRONT_AVAILABLE:
            return create_response(500, {
                'error': 'Custom domain automation not available. Please check server configuration.'
            })
        
        # Step 1: Request ACM certificate
        print(f"Requesting SSL certificate for {domain}...")
        try:
            cert_result = request_certificate(domain, validation_method='DNS')
            certificate_arn = cert_result['certificate_arn']
            validation_records = cert_result['validation_records']
            
            print(f"✓ SSL certificate requested: {certificate_arn}")
        except Exception as e:
            return create_response(500, {
                'error': f'Failed to request SSL certificate: {str(e)}'
            })
        
        # Step 2: Create CloudFront distribution with certificate placeholder
        print(f"Creating CloudFront distribution for {domain}...")
        try:
            # Note: Certificate will be added after validation
            dist_result = create_distribution(
                domain=domain,
                certificate_arn=certificate_arn,
                user_id=user['id'],
                comment=f"Galerly portfolio for {user.get('username', user['id'])}"
            )
            
            distribution_id = dist_result['distribution_id']
            distribution_domain = dist_result['domain_name']
            
            print(f"✓ CloudFront distribution created: {distribution_id}")
        except Exception as e:
            # If distribution fails, try to clean up certificate
            print(f"Warning: Distribution creation failed, certificate remains: {certificate_arn}")
            return create_response(500, {
                'error': f'Failed to create CloudFront distribution: {str(e)}',
                'certificate_arn': certificate_arn,
                'note': 'SSL certificate was created but distribution failed. Contact support.'
            })
        
        # Step 3: Save configuration to database
        domain_config = {
            'user_id': user['id'],
            'domain': domain,
            'certificate_arn': certificate_arn,
            'distribution_id': distribution_id,
            'distribution_domain': distribution_domain,
            'status': 'pending_validation',
            'validation_records': validation_records,
            'created_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z',
            'updated_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        }
        
        try:
            custom_domains_table.put_item(Item=domain_config)
        except Exception as table_error:
            print(f"Warning: Could not save to custom_domains table: {str(table_error)}")
        
        # Step 4: Update user record
        users_table.update_item(
            Key={'email': user['email']},
            UpdateExpression='SET portfolio_custom_domain = :d, custom_domain_distribution_id = :dist_id, custom_domain_certificate_arn = :cert_arn, updated_at = :now',
            ExpressionAttributeValues={
                ':d': domain,
                ':dist_id': distribution_id,
                ':cert_arn': certificate_arn,
                ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        # Prepare next steps for user
        next_steps = [
            f'Add DNS validation records to verify SSL certificate',
            f'Add CNAME record pointing {domain} to {distribution_domain}',
            'Wait for DNS propagation (1-48 hours)',
            'SSL certificate will auto-validate once DNS records are added',
            'CloudFront distribution will be updated with certificate once validated'
        ]
        
        return create_response(200, {
            'success': True,
            'domain': domain,
            'certificate_arn': certificate_arn,
            'distribution_id': distribution_id,
            'distribution_domain': distribution_domain,
            'status': 'pending_validation',
            'validation_records': validation_records,
            'next_steps': next_steps,
            'message': 'Custom domain setup initiated. Complete DNS configuration to activate.'
        })
        
    except Exception as e:
        print(f"Error setting up custom domain: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to setup custom domain'})


@require_plan(feature='custom_domain')
def handle_check_custom_domain_status(user, domain):
    """
    Check complete status of custom domain including CloudFront, ACM, and DNS
    
    Returns:
        dict: {
            'domain': str,
            'overall_status': str,  # pending, active, error
            'dns_propagation': dict,
            'certificate_status': dict,
            'distribution_status': dict,
            'ready': bool
        }
    """
    try:
        # Plan enforcement handled by decorator
        
        if not domain:
            return create_response(400, {'error': 'Domain parameter required'})
        
        # Get domain configuration
        try:
            config_response = custom_domains_table.get_item(
                Key={'user_id': user['id'], 'domain': domain}
            )
            
            if 'Item' not in config_response:
                return create_response(404, {
                    'error': 'Domain configuration not found. Please setup the domain first.'
                })
            
            config = config_response['Item']
        except:
            # Fallback to user record if table doesn't exist
            user_response = users_table.get_item(Key={'email': user['email']})
            if 'Item' not in user_response:
                return create_response(404, {'error': 'User not found'})
            
            user_data = user_response['Item']
            config = {
                'certificate_arn': user_data.get('custom_domain_certificate_arn'),
                'distribution_id': user_data.get('custom_domain_distribution_id')
            }
        
        certificate_arn = config.get('certificate_arn')
        distribution_id = config.get('distribution_id')
        distribution_domain = config.get('distribution_domain')
        
        # Check if utilities are available
        if not ACM_AVAILABLE or not CLOUDFRONT_AVAILABLE or not DNS_CHECKER_AVAILABLE:
            return create_response(500, {
                'error': 'Custom domain status checking not available'
            })
        
        # Check certificate status
        cert_status = None
        if certificate_arn:
            try:
                cert_details = describe_certificate(certificate_arn)
                if not cert_details.get('error'):
                    cert_status = {
                        'arn': certificate_arn,
                        'status': cert_details['status'],
                        'issued': cert_details['issued'],
                        'validation_records': cert_details.get('validation_records', [])
                    }
            except Exception as e:
                print(f"Error checking certificate: {str(e)}")
                cert_status = {'error': str(e)}
        
        # Check CloudFront distribution status
        dist_status = None
        if distribution_id:
            try:
                dist_details = get_distribution_status(distribution_id)
                if not dist_details.get('error'):
                    dist_status = {
                        'id': distribution_id,
                        'domain': dist_details['domain_name'],
                        'status': dist_details['status'],
                        'deployed': dist_details['deployed'],
                        'enabled': dist_details.get('enabled', True)
                    }
            except Exception as e:
                print(f"Error checking distribution: {str(e)}")
                dist_status = {'error': str(e)}
        
        # Check DNS propagation
        dns_status = None
        if distribution_domain:
            try:
                dns_result = check_propagation(
                    domain=domain,
                    expected_target=distribution_domain,
                    record_type='CNAME'
                )
                dns_status = {
                    'propagated': dns_result['propagated'],
                    'percentage': dns_result['propagation_percentage'],
                    'ready': dns_result['ready'],
                    'servers_propagated': dns_result['servers_propagated'],
                    'servers_checked': dns_result['servers_checked']
                }
            except Exception as e:
                print(f"Error checking DNS: {str(e)}")
                dns_status = {'error': str(e), 'propagated': False, 'ready': False}
        
        # Determine overall status
        cert_ready = cert_status and cert_status['issued']
        dist_ready = dist_status and dist_status['deployed']
        dns_ready = dns_status['ready']
        
        if cert_ready and dist_ready and dns_ready:
            overall_status = 'active'
            ready = True
        elif cert_status or dist_status:
            overall_status = 'pending'
            ready = False
        else:
            overall_status = 'not_configured'
            ready = False
        
        return create_response(200, {
            'domain': domain,
            'overall_status': overall_status,
            'ready': ready,
            'certificate': cert_status,
            'distribution': dist_status,
            'dns_propagation': dns_status,
            'checked_at': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        })
        
    except Exception as e:
        print(f"Error checking custom domain status: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to check domain status'})


@require_plan(feature='custom_domain')
@require_role('photographer')
def handle_refresh_custom_domain_certificate(user, domain):
    """
    Check if certificate is validated and update CloudFront distribution
    This should be called periodically or triggered by user after adding DNS records
    """
    try:
        # Get domain configuration
        try:
            config_response = custom_domains_table.get_item(
                Key={'user_id': user['id'], 'domain': domain}
            )
            
            if 'Item' not in config_response:
                return create_response(404, {'error': 'Domain configuration not found'})
            
            config = config_response['Item']
        except:
            return create_response(404, {'error': 'Domain configuration not found'})
        
        certificate_arn = config.get('certificate_arn')
        distribution_id = config.get('distribution_id')
        
        if not certificate_arn or not distribution_id:
            return create_response(400, {'error': 'Incomplete domain configuration'})
        
        # Check certificate status
        cert_result = get_certificate_status(certificate_arn)
        
        if not cert_result['success']:
            return create_response(500, {
                'error': f'Failed to check certificate: {cert_result.get("error")}'
            })
        
        cert_status = cert_result['status']
        
        if cert_status == 'ISSUED':
            # Certificate is validated! Update CloudFront distribution
            print(f"Certificate validated for {domain}, updating CloudFront...")
            
            update_result = update_distribution_certificate(distribution_id, certificate_arn)
            
            if not update_result['success']:
                return create_response(500, {
                    'error': f'Failed to update distribution: {update_result.get("error")}'
                })
            
            # Update config status
            try:
                custom_domains_table.update_item(
                    Key={'user_id': user['id'], 'domain': domain},
                    UpdateExpression='SET #status = :active, certificate_validated_at = :now, updated_at = :now',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':active': 'active',
                        ':now': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                    }
                )
            except:
                pass
            
            print(f"✓ Custom domain {domain} is now active with SSL!")
            
            return create_response(200, {
                'success': True,
                'domain': domain,
                'status': 'active',
                'certificate_status': cert_status,
                'message': 'Domain is now active with SSL certificate!'
            })
        
        elif cert_status in ['PENDING_VALIDATION']:
            return create_response(200, {
                'success': True,
                'domain': domain,
                'status': 'pending_validation',
                'certificate_status': cert_status,
                'validation_records': cert_result.get('validation_records', []),
                'message': 'Certificate is still pending validation. Add DNS validation records and try again.'
            })
        
        else:
            return create_response(400, {
                'error': f'Certificate has unexpected status: {cert_status}'
            })
        
    except Exception as e:
        print(f"Error refreshing certificate: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to refresh certificate status'})
