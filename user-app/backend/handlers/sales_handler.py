"""
Photo Sales Handler
Stripe Payment Intents integration for selling individual photos and packages
"""
import uuid
import stripe
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, users_table, photos_table, galleries_table
from utils.response import create_response
from utils.email import send_email
import os

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Initialize DynamoDB tables
sales_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_SALES'))
packages_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_PACKAGES'))
downloads_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_DOWNLOADS'))


def handle_list_packages(photographer_id, is_public=True):
    """
    List photo packages for a photographer
    
    GET /api/v1/public/photographers/{photographer_id}/packages
    GET /api/v1/packages (authenticated photographer)
    """
    try:
        response = packages_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(photographer_id)
        )
        
        packages = response.get('Items', [])
        
        # Filter by active status if public view
        if is_public:
            packages = [p for p in packages if p.get('active') == True]
        
        # Sort by display_order
        packages.sort(key=lambda x: x.get('display_order', 999))
        
        return create_response(200, {'packages': packages})
        
    except Exception as e:
        print(f"Error listing packages: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve packages'})


def handle_create_package(user, body):
    """
    Create a new photo package
    
    POST /api/v1/packages
    Body: {
        "name": "Wedding Premium Collection",
        "description": "50 high-resolution edited photos",
        "price": 500,
        "photo_count": 50,
        "includes_raw": false,
        "includes_prints": false,
        "gallery_id": "optional-gallery-id",
        "photo_ids": ["photo1", "photo2"],
        "active": true
    }
    """
    try:
        # Validate required fields
        name = body.get('name', '').strip()
        price = body.get('price', 0)
        
        if not name:
            return create_response(400, {'error': 'Package name is required'})
        if price <= 0:
            return create_response(400, {'error': 'Package price must be greater than 0'})
        
        # Create package
        package_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        package = {
            'id': package_id,
            'photographer_id': user['id'],
            'name': name,
            'description': body.get('description', ''),
            'price': Decimal(str(price)),
            'currency': body.get('currency', 'USD'),
            'photo_count': body.get('photo_count', 0),
            'includes_raw': body.get('includes_raw', False),
            'includes_prints': body.get('includes_prints', False),
            'gallery_id': body.get('gallery_id', ''),
            'photo_ids': body.get('photo_ids', []),
            'active': body.get('active', True),
            'display_order': body.get('display_order', 999),
            'created_at': timestamp,
            'updated_at': timestamp,
            'sales_count': 0
        }
        
        packages_table.put_item(Item=package)
        
        print(f"Package created: {package_id} by {user['id']}")
        
        return create_response(201, package)
        
    except Exception as e:
        print(f"Error creating package: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create package'})


def handle_create_payment_intent(body):
    """
    Create Stripe Payment Intent for photo/package purchase
    
    POST /api/v1/sales/create-payment-intent
    Body: {
        "type": "package" | "photos",
        "package_id": "optional",
        "photo_ids": ["optional"],
        "photographer_id": "required",
        "customer_email": "required",
        "customer_name": "required"
    }
    """
    try:
        purchase_type = body.get('type')
        photographer_id = body.get('photographer_id')
        customer_email = body.get('customer_email', '').strip().lower()
        customer_name = body.get('customer_name', '').strip()
        
        if not purchase_type or purchase_type not in ['package', 'photos']:
            return create_response(400, {'error': 'Invalid purchase type'})
        
        if not photographer_id:
            return create_response(400, {'error': 'Photographer ID is required'})
        
        if not customer_email or not customer_name:
            return create_response(400, {'error': 'Customer email and name are required'})
        
        # Get photographer info
        photographer_response = users_table.get_item(Key={'id': photographer_id})
        if 'Item' not in photographer_response:
            return create_response(404, {'error': 'Photographer not found'})
        
        photographer = photographer_response['Item']
        
        # Calculate amount based on purchase type
        amount = 0
        items = []
        
        if purchase_type == 'package':
            package_id = body.get('package_id')
            if not package_id:
                return create_response(400, {'error': 'Package ID is required'})
            
            # Get package details
            package_response = packages_table.get_item(Key={'id': package_id})
            if 'Item' not in package_response:
                return create_response(404, {'error': 'Package not found'})
            
            package = package_response['Item']
            
            if package['photographer_id'] != photographer_id:
                return create_response(403, {'error': 'Package does not belong to this photographer'})
            
            amount = int(float(package['price']) * 100)  # Convert to cents
            items.append({
                'id': package_id,
                'type': 'package',
                'name': package['name'],
                'price': float(package['price'])
            })
        
        elif purchase_type == 'photos':
            photo_ids = body.get('photo_ids', [])
            if not photo_ids:
                return create_response(400, {'error': 'Photo IDs are required'})
            
            # Get photo details and calculate price
            price_per_photo = float(body.get('price_per_photo', 10))  # Default $10 per photo
            amount = int(len(photo_ids) * price_per_photo * 100)  # Convert to cents
            
            items = [{
                'id': photo_id,
                'type': 'photo',
                'name': f'Photo {idx + 1}',
                'price': price_per_photo
            } for idx, photo_id in enumerate(photo_ids)]
        
        # Create sale record
        sale_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        sale = {
            'id': sale_id,
            'photographer_id': photographer_id,
            'customer_email': customer_email,
            'customer_name': customer_name,
            'purchase_type': purchase_type,
            'items': items,
            'amount': Decimal(str(amount / 100)),
            'currency': 'USD',
            'status': 'pending',
            'payment_intent_id': '',
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Create Stripe Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'sale_id': sale_id,
                'photographer_id': photographer_id,
                'photographer_email': photographer.get('email'),
                'customer_email': customer_email,
                'customer_name': customer_name,
                'purchase_type': purchase_type
            },
            receipt_email=customer_email,
            description=f"{purchase_type.capitalize()} purchase from {photographer.get('name', 'photographer')}"
        )
        
        # Update sale with payment intent ID
        sale['payment_intent_id'] = payment_intent.id
        sale['client_secret'] = payment_intent.client_secret
        
        sales_table.put_item(Item=sale)
        
        print(f"Payment Intent created: {payment_intent.id} for sale {sale_id}")
        
        return create_response(200, {
            'client_secret': payment_intent.client_secret,
            'sale_id': sale_id,
            'amount': amount / 100
        })
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        return create_response(500, {'error': f'Payment processing error: {str(e)}'})
    except Exception as e:
        print(f"Error creating payment intent: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create payment'})


def handle_confirm_sale(sale_id, payment_intent_id):
    """
    Confirm sale after successful payment (called by webhook or frontend)
    
    POST /api/v1/sales/{sale_id}/confirm
    """
    try:
        # Get sale
        sale_response = sales_table.get_item(Key={'id': sale_id})
        if 'Item' not in sale_response:
            return create_response(404, {'error': 'Sale not found'})
        
        sale = sale_response['Item']
        
        # Verify payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != 'succeeded':
            return create_response(400, {'error': 'Payment not completed'})
        
        # Update sale status
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        sales_table.update_item(
            Key={'id': sale_id},
            UpdateExpression='SET #status = :status, payment_confirmed_at = :timestamp, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':timestamp': timestamp,
                ':updated_at': timestamp
            }
        )
        
        # Create download links for purchased items
        download_links = []
        for item in sale.get('items', []):
            download_id = str(uuid.uuid4())
            
            download = {
                'id': download_id,
                'sale_id': sale_id,
                'photographer_id': sale['photographer_id'],
                'customer_email': sale['customer_email'],
                'item_id': item['id'],
                'item_type': item['type'],
                'status': 'available',
                'download_count': 0,
                'max_downloads': 10,  # Allow 10 downloads
                'expires_at': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat() + 'Z',
                'created_at': timestamp
            }
            
            downloads_table.put_item(Item=download)
            download_links.append({
                'download_id': download_id,
                'item_name': item['name']
            })
        
        # Send confirmation email to customer
        try:
            send_email(
                to_addresses=[sale['customer_email']],
                subject=f"Your Purchase is Ready - {sale['photographer_id']}",
                body_html=f"""
                <h2>Purchase Confirmed!</h2>
                <p>Hi {sale['customer_name']},</p>
                <p>Your payment of ${sale['amount']} has been processed successfully.</p>
                <p>You can download your photos here: <a href="{os.environ.get('FRONTEND_URL')}/downloads/{sale_id}">Download Your Photos</a></p>
                <p>Downloads are available for 30 days.</p>
                <p>Thank you for your purchase!</p>
                """,
                body_text=f"Hi {sale['customer_name']}, Your purchase is ready! Download link: {os.environ.get('FRONTEND_URL')}/downloads/{sale_id}"
            )
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")
        
        # Notify photographer
        try:
            photographer_response = users_table.get_item(Key={'id': sale['photographer_id']})
            if 'Item' in photographer_response:
                photographer = photographer_response['Item']
                send_email(
                    to_addresses=[photographer.get('email')],
                    subject=f"New Sale: ${sale['amount']}",
                    body_html=f"<p>You have a new sale from {sale['customer_name']} ({sale['customer_email']}) for ${sale['amount']}.</p>",
                    body_text=f"New sale from {sale['customer_name']} for ${sale['amount']}"
                )
        except Exception as e:
            print(f"Failed to notify photographer: {str(e)}")
        
        return create_response(200, {
            'message': 'Sale confirmed',
            'download_links': download_links
        })
        
    except Exception as e:
        print(f"Error confirming sale: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to confirm sale'})


def handle_get_download(download_id, customer_email):
    """
    Get download link for purchased item
    
    GET /api/v1/downloads/{download_id}?email={customer_email}
    """
    try:
        # Get download record
        download_response = downloads_table.get_item(Key={'id': download_id})
        if 'Item' not in download_response:
            return create_response(404, {'error': 'Download not found'})
        
        download = download_response['Item']
        
        # Verify customer email
        if download['customer_email'].lower() != customer_email.lower():
            return create_response(403, {'error': 'Access denied'})
        
        # Check if expired
        if datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z' > download['expires_at']:
            return create_response(410, {'error': 'Download link has expired'})
        
        # Check download limit
        if download['download_count'] >= download['max_downloads']:
            return create_response(429, {'error': 'Download limit exceeded'})
        
        # Generate presigned URL based on item type
        from utils.secure_url_generator import SecureURLGenerator
        url_generator = SecureURLGenerator()
        
        if download['item_type'] == 'photo':
            # Get photo S3 key
            photo_response = photos_table.get_item(Key={'id': download['item_id']})
            if 'Item' not in photo_response:
                return create_response(404, {'error': 'Photo not found'})
            
            photo = photo_response['Item']
            download_url = url_generator.generate_download_url(
                s3_key=photo.get('s3_key'),
                filename=f"photo_{download['item_id']}.jpg",
                expiry_minutes=60
            )
        
        elif download['item_type'] == 'package':
            # For packages, we'd generate a ZIP or multiple URLs
            # Simplified: return package info
            package_response = packages_table.get_item(Key={'id': download['item_id']})
            if 'Item' not in package_response:
                return create_response(404, {'error': 'Package not found'})
            
            package = package_response['Item']
            # Generate URLs for all photos in package
            download_url = f"Package download - {len(package.get('photo_ids', []))} photos"
        
        # Increment download count
        downloads_table.update_item(
            Key={'id': download_id},
            UpdateExpression='SET download_count = download_count + :inc, last_downloaded_at = :timestamp',
            ExpressionAttributeValues={
                ':inc': 1,
                ':timestamp': datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
            }
        )
        
        return create_response(200, {
            'download_url': download_url,
            'download_count': download['download_count'] + 1,
            'max_downloads': download['max_downloads'],
            'expires_at': download['expires_at']
        })
        
    except Exception as e:
        print(f"Error getting download: {str(e)}")
        return create_response(500, {'error': 'Failed to generate download link'})


def handle_list_sales(user, query_params=None):
    """List sales for photographer with revenue stats"""
    try:
        # Check plan permission
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        if not features.get('client_invoicing'):  # Sales bundled with invoicing
            return create_response(403, {
                'error': 'Photo sales features are available on Pro and Ultimate plans.',
                'upgrade_required': True
            })
        
        # Query sales
        response = sales_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(user['id']),
            ScanIndexForward=False
        )
        
        sales = response.get('Items', [])
        
        # Calculate revenue stats
        total_revenue = sum(float(s.get('amount', 0)) for s in sales if s.get('status') == 'completed')
        pending_revenue = sum(float(s.get('amount', 0)) for s in sales if s.get('status') == 'pending')
        
        return create_response(200, {
            'sales': sales,
            'stats': {
                'total_sales': len(sales),
                'completed_sales': len([s for s in sales if s.get('status') == 'completed']),
                'total_revenue': round(total_revenue, 2),
                'pending_revenue': round(pending_revenue, 2)
            }
        })
        
    except Exception as e:
        print(f"Error listing sales: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve sales'})
