"""
Contract and eSignature handlers
"""
import uuid
import base64
import os
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from utils.config import contracts_table, s3_client, S3_BUCKET
from utils.response import create_response
from utils.email import send_email

def handle_list_contracts(user, query_params=None):
    """List contracts"""
    try:
        response = contracts_table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('user_id').eq(user['id'])
        )
        contracts = response.get('Items', [])
        contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return create_response(200, {'contracts': contracts})
    except Exception as e:
        print(f"Error listing contracts: {str(e)}")
        return create_response(500, {'error': 'Failed to list contracts'})

def handle_create_contract(user, body):
    """Create draft contract - Photographer only"""
    try:
        # Check user role - photographers only
        if user.get('role') != 'photographer':
            return create_response(403, {
                'error': 'Only photographers can create contracts',
                'required_role': 'photographer'
            })
        
        # Check Plan Limits
        from handlers.subscription_handler import get_user_features
        features, _, _ = get_user_features(user)
        
        # Check for e_signatures feature
        if not features.get('e_signatures'):
             return create_response(403, {
                 'error': 'Contracts and eSignatures are available on the Ultimate plan.',
                 'upgrade_required': True
             })

        if 'client_email' not in body or 'content' not in body:
            return create_response(400, {'error': 'Missing required fields'})
            
        contract_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        contract = {
            'id': contract_id,
            'user_id': user['id'],
            'client_name': body.get('client_name', ''),
            'client_email': body['client_email'],
            'title': body.get('title', 'Photography Contract'),
            'content': body['content'],
            'status': 'draft',
            'created_at': current_time,
            'updated_at': current_time
        }
        
        contracts_table.put_item(Item=contract)
        return create_response(201, contract)
    except Exception as e:
        print(f"Error creating contract: {str(e)}")
        return create_response(500, {'error': 'Failed to create contract'})

def handle_get_contract(contract_id, user=None):
    """Get contract details (Auth user OR public if signed/sent)"""
    try:
        response = contracts_table.get_item(Key={'id': contract_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
            
        contract = response['Item']
        
        # Access control
        if user:
            if contract['user_id'] != user['id']:
                return create_response(403, {'error': 'Access denied'})
        else:
            # Public access (signing view) - only allow if sent or signed
            if contract['status'] == 'draft':
                return create_response(403, {'error': 'Contract is not ready'})
                
        return create_response(200, contract)
    except Exception as e:
        print(f"Error getting contract: {str(e)}")
        return create_response(500, {'error': 'Failed to get contract'})

def handle_update_contract(contract_id, user, body):
    """Update draft contract"""
    try:
        response = contracts_table.get_item(Key={'id': contract_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
            
        contract = response['Item']
        if contract['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        if contract['status'] != 'draft':
            return create_response(400, {'error': 'Cannot edit sent or signed contracts'})
            
        fields = ['client_name', 'client_email', 'title', 'content']
        for f in fields:
            if f in body:
                contract[f] = body[f]
                
        contract['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        contracts_table.put_item(Item=contract)
        
        return create_response(200, contract)
    except Exception as e:
        print(f"Error updating contract: {str(e)}")
        return create_response(500, {'error': 'Failed to update contract'})

def handle_delete_contract(contract_id, user):
    """Delete contract"""
    try:
        response = contracts_table.get_item(Key={'id': contract_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
            
        if response['Item']['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        contracts_table.delete_item(Key={'id': contract_id})
        return create_response(200, {'message': 'Contract deleted'})
    except Exception as e:
        print(f"Error deleting contract: {str(e)}")
        return create_response(500, {'error': 'Failed to delete contract'})

def handle_send_contract(contract_id, user):
    """Send contract to client"""
    try:
        response = contracts_table.get_item(Key={'id': contract_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
            
        contract = response['Item']
        if contract['user_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
            
        contract['status'] = 'sent'
        contract['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        contracts_table.put_item(Item=contract)
        
        # Send email
        frontend_url = os.environ.get('FRONTEND_URL')
        sign_link = f"{frontend_url}/sign-contract/{contract_id}"
        
        send_email(
            to_addresses=[contract['client_email']],
            subject=f"Please Sign: {contract['title']}",
            body_html=f"<p>Hi {contract.get('client_name','')},</p><p>Please review and sign your contract here: <a href='{sign_link}'>{sign_link}</a></p>",
            body_text=f"Please sign your contract: {sign_link}"
        )
        
        return create_response(200, {'message': 'Contract sent', 'contract': contract})
    except Exception as e:
        print(f"Error sending contract: {str(e)}")
        return create_response(500, {'error': 'Failed to send contract'})

def handle_sign_contract(contract_id, body, ip_address):
    """Sign contract (Public endpoint)"""
    try:
        response = contracts_table.get_item(Key={'id': contract_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Contract not found'})
            
        contract = response['Item']
        
        if contract['status'] == 'signed':
            return create_response(400, {'error': 'Already signed'})
            
        signature_data = body.get('signature_data') # Base64 image
        if not signature_data:
            return create_response(400, {'error': 'Signature required'})
            
        # Upload signature to S3
        try:
            # Remove header if present (data:image/png;base64,...)
            if 'base64,' in signature_data:
                signature_data = signature_data.split('base64,')[1]
                
            image_data = base64.b64decode(signature_data)
            key = f"contracts/{contract_id}/signature.png"
            
            # Note: ACLs might be disabled, so we rely on bucket policies or presigned URLs usually.
            # Here we try public-read, if fails we catch it.
            extra_args = {'ContentType': 'image/png'}
            # extra_args['ACL'] = 'public-read' # Skipping ACL to avoid BlockPublicAccess errors, assuming app handles access via presigned or proxy if needed.
            
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=image_data,
                **extra_args
            )
            
            # If we can't make it public, we generate a presigned URL on fetch.
            # But for simplicity in this variable:
            signature_path = key
            
        except Exception as s3_err:
            print(f"S3 Upload Error: {s3_err}")
            return create_response(500, {'error': 'Failed to save signature'})
            
        contract['status'] = 'signed'
        contract['signature_key'] = signature_path # Store Key instead of URL to be safe
        contract['signed_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        contract['signed_ip'] = ip_address
        contract['updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        contracts_table.put_item(Item=contract)
        
        return create_response(200, {'message': 'Contract signed successfully', 'contract': contract})
    except Exception as e:
        print(f"Error signing contract: {str(e)}")
        return create_response(500, {'error': 'Failed to sign contract'})

