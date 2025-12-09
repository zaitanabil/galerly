"""
Client Onboarding Automation
Automated workflows for new client onboarding
"""
import uuid
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key, Attr
from utils.config import dynamodb, users_table
from utils.response import create_response
from utils.email import send_email
import os

# Initialize DynamoDB tables
onboarding_workflows_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_ONBOARDING_WORKFLOWS'))
leads_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_LEADS'))


def handle_create_onboarding_workflow(user, body):
    """
    Create automated onboarding workflow template
    
    POST /api/v1/onboarding/workflows
    Body: {
        "name": "Wedding Photography Onboarding",
        "trigger": "lead_converted" | "contract_signed" | "payment_received",
        "steps": [
            {
                "order": 1,
                "delay_hours": 0,
                "type": "email",
                "template": "welcome",
                "subject": "Welcome! Here's what to expect",
                "content": "..."
            },
            {
                "order": 2,
                "delay_hours": 24,
                "type": "email",
                "template": "questionnaire",
                "content": "..."
            }
        ]
    }
    """
    try:
        # Validate required fields
        name = body.get('name', '').strip()
        trigger = body.get('trigger', '')
        steps = body.get('steps', [])
        
        if not name:
            return create_response(400, {'error': 'Workflow name is required'})
        
        if trigger not in ['lead_converted', 'contract_signed', 'payment_received', 'appointment_confirmed']:
            return create_response(400, {'error': 'Invalid trigger type'})
        
        if not steps:
            return create_response(400, {'error': 'At least one step is required'})
        
        # Create workflow
        workflow_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        workflow = {
            'id': workflow_id,
            'photographer_id': user['id'],
            'name': name,
            'trigger': trigger,
            'steps': steps,
            'active': body.get('active', True),
            'created_at': timestamp,
            'updated_at': timestamp,
            'execution_count': 0
        }
        
        onboarding_workflows_table.put_item(Item=workflow)
        
        print(f"Onboarding workflow created: {workflow_id} by {user['id']}")
        
        return create_response(201, workflow)
        
    except Exception as e:
        print(f"Error creating onboarding workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_response(500, {'error': 'Failed to create workflow'})


def handle_trigger_onboarding(photographer_id, trigger_type, client_data):
    """
    Trigger onboarding workflow for a client
    
    Internal function called when trigger event occurs
    
    Args:
        photographer_id: ID of photographer
        trigger_type: Type of trigger (lead_converted, contract_signed, etc.)
        client_data: {
            'client_email': 'email',
            'client_name': 'name',
            'lead_id': 'optional',
            'contract_id': 'optional'
        }
    """
    try:
        # Find active workflows for this photographer with matching trigger
        response = onboarding_workflows_table.scan(
            FilterExpression=Attr('photographer_id').eq(photographer_id) & 
                           Attr('trigger').eq(trigger_type) & 
                           Attr('active').eq(True)
        )
        
        workflows = response.get('Items', [])
        
        if not workflows:
            print(f"No active onboarding workflows found for photographer {photographer_id} with trigger {trigger_type}")
            return
        
        # Get photographer details
        photographer_response = users_table.get_item(Key={'id': photographer_id})
        if 'Item' not in photographer_response:
            print(f"Photographer {photographer_id} not found")
            return
        
        photographer = photographer_response['Item']
        
        # Execute each workflow
        for workflow in workflows:
            try:
                execution_id = str(uuid.uuid4())
                timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
                
                # Create execution record
                execution = {
                    'id': execution_id,
                    'workflow_id': workflow['id'],
                    'photographer_id': photographer_id,
                    'client_email': client_data['client_email'],
                    'client_name': client_data.get('client_name', ''),
                    'trigger_type': trigger_type,
                    'steps': workflow['steps'],
                    'current_step': 0,
                    'status': 'active',
                    'created_at': timestamp,
                    'updated_at': timestamp
                }
                
                # Store execution (you'd need an executions table)
                # For now, we'll just execute the workflow immediately
                
                # Execute first step immediately if delay is 0
                for step in workflow['steps']:
                    if step.get('delay_hours', 0) == 0:
                        send_onboarding_email(
                            photographer=photographer,
                            client_email=client_data['client_email'],
                            client_name=client_data.get('client_name', ''),
                            step=step
                        )
                
                # Increment execution count
                onboarding_workflows_table.update_item(
                    Key={'id': workflow['id']},
                    UpdateExpression='SET execution_count = execution_count + :inc',
                    ExpressionAttributeValues={':inc': 1}
                )
                
                print(f"Onboarding workflow {workflow['id']} triggered for {client_data['client_email']}")
                
            except Exception as workflow_error:
                print(f"Error executing workflow {workflow.get('id')}: {str(workflow_error)}")
                continue
        
    except Exception as e:
        print(f"Error triggering onboarding: {str(e)}")
        import traceback
        traceback.print_exc()


def send_onboarding_email(photographer, client_email, client_name, step):
    """Send onboarding email step"""
    try:
        subject = step.get('subject', 'Welcome!')
        content = step.get('content', '')
        
        # Replace variables in content
        content = content.replace('{client_name}', client_name)
        content = content.replace('{photographer_name}', photographer.get('name', ''))
        content = content.replace('{business_name}', photographer.get('business_name', photographer.get('name', '')))
        
        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            {content}
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 14px;">
                {photographer.get('name', 'Your photographer')}<br>
                {photographer.get('email', '')}
            </p>
        </div>
        """
        
        send_email(
            to_addresses=[client_email],
            subject=subject,
            body_html=body_html,
            body_text=content
        )
        
        print(f"Onboarding email sent to {client_email}: {subject}")
        
    except Exception as e:
        print(f"Error sending onboarding email: {str(e)}")


def handle_list_workflows(user):
    """List onboarding workflows for photographer"""
    try:
        response = onboarding_workflows_table.query(
            IndexName='PhotographerIdIndex',
            KeyConditionExpression=Key('photographer_id').eq(user['id'])
        )
        
        workflows = response.get('Items', [])
        
        return create_response(200, {'workflows': workflows})
        
    except Exception as e:
        print(f"Error listing workflows: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve workflows'})


def handle_update_workflow(user, workflow_id, body):
    """Update onboarding workflow"""
    try:
        # Get workflow
        response = onboarding_workflows_table.get_item(Key={'id': workflow_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Workflow not found'})
        
        workflow = response['Item']
        
        # Verify ownership
        if workflow['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Build update expression
        update_fields = []
        expr_values = {}
        
        updateable = ['name', 'trigger', 'steps', 'active']
        
        for field in updateable:
            if field in body:
                update_fields.append(f'{field} = :{field}')
                expr_values[f':{field}'] = body[field]
        
        if not update_fields:
            return create_response(400, {'error': 'No valid fields to update'})
        
        # Always update timestamp
        update_fields.append('updated_at = :updated_at')
        expr_values[':updated_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        
        # Execute update
        update_expression = 'SET ' + ', '.join(update_fields)
        
        result = onboarding_workflows_table.update_item(
            Key={'id': workflow_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )
        
        return create_response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating workflow: {str(e)}")
        return create_response(500, {'error': 'Failed to update workflow'})


def handle_delete_workflow(user, workflow_id):
    """Delete onboarding workflow"""
    try:
        # Get workflow to verify ownership
        response = onboarding_workflows_table.get_item(Key={'id': workflow_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Workflow not found'})
        
        workflow = response['Item']
        
        # Verify ownership
        if workflow['photographer_id'] != user['id']:
            return create_response(403, {'error': 'Access denied'})
        
        # Delete workflow
        onboarding_workflows_table.delete_item(Key={'id': workflow_id})
        
        return create_response(200, {'message': 'Workflow deleted'})
        
    except Exception as e:
        print(f"Error deleting workflow: {str(e)}")
        return create_response(500, {'error': 'Failed to delete workflow'})
