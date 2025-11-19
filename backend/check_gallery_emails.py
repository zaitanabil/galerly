"""
Diagnostic script to check client_emails in galleries
Run this to see what emails are actually stored in your galleries
"""
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
galleries_table = dynamodb.Table('galerly-galleries')

def check_gallery_emails(user_id=None, gallery_id=None):
    """Check client_emails in galleries"""
    print("=" * 80)
    print("CHECKING GALLERY CLIENT EMAILS")
    print("=" * 80)
    
    try:
        if gallery_id and user_id:
            # Check specific gallery
            response = galleries_table.get_item(Key={'user_id': user_id, 'id': gallery_id})
            if 'Item' in response:
                galleries = [response['Item']]
            else:
                print(f"❌ Gallery not found: user_id={user_id}, gallery_id={gallery_id}")
                return
        elif user_id:
            # Check all galleries for specific user
            response = galleries_table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            galleries = response.get('Items', [])
        else:
            # Scan all galleries (use with caution)
            print("⚠️  WARNING: Scanning all galleries (this may take a while)")
            response = galleries_table.scan()
            galleries = response.get('Items', [])
        
        print(f"\n📊 Found {len(galleries)} gallery/galleries\n")
        
        for idx, gallery in enumerate(galleries, 1):
            print(f"\n{'─' * 80}")
            print(f"Gallery #{idx}")
            print(f"{'─' * 80}")
            print(f"  Gallery ID: {gallery.get('id')}")
            print(f"  Name: {gallery.get('name')}")
            print(f"  User ID: {gallery.get('user_id')}")
            print(f"  Client Name: {gallery.get('client_name')}")
            
            # Check client_emails field
            client_emails = gallery.get('client_emails', [])
            print(f"\n  📬 client_emails field:")
            print(f"     Type: {type(client_emails)}")
            print(f"     Length: {len(client_emails) if isinstance(client_emails, list) else 'N/A'}")
            print(f"     Raw value: {repr(client_emails)}")
            
            if isinstance(client_emails, list):
                if len(client_emails) == 0:
                    print(f"     ⚠️  EMPTY ARRAY - No client emails set!")
                else:
                    print(f"     Emails:")
                    for i, email in enumerate(client_emails, 1):
                        email_type = type(email).__name__
                        email_len = len(email) if isinstance(email, str) else 'N/A'
                        email_empty = email == '' if isinstance(email, str) else False
                        
                        print(f"       [{i}] '{email}'")
                        print(f"           Type: {email_type}")
                        print(f"           Length: {email_len}")
                        print(f"           Empty: {'✅ YES' if email_empty else '❌ NO'}")
                        
                        # Validate email format
                        if isinstance(email, str) and email:
                            import re
                            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                            is_valid = bool(re.match(email_pattern, email))
                            print(f"           Valid format: {'✅ YES' if is_valid else '❌ NO'}")
            else:
                print(f"     ❌ NOT AN ARRAY!")
            
            # Check for legacy client_email field
            if 'client_email' in gallery:
                print(f"\n  ⚠️  LEGACY 'client_email' field found: {gallery.get('client_email')}")
        
        print(f"\n{'=' * 80}")
        print("CHECK COMPLETE")
        print(f"{'=' * 80}\n")
        
    except Exception as e:
        print(f"\n❌ Error checking galleries: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 2:
        # python check_gallery_emails.py <user_id> <gallery_id>
        check_gallery_emails(user_id=sys.argv[1], gallery_id=sys.argv[2])
    elif len(sys.argv) > 1:
        # python check_gallery_emails.py <user_id>
        check_gallery_emails(user_id=sys.argv[1])
    else:
        print("Usage:")
        print("  python check_gallery_emails.py <user_id>                    # Check all galleries for user")
        print("  python check_gallery_emails.py <user_id> <gallery_id>       # Check specific gallery")
        print("\nExample:")
        print("  python check_gallery_emails.py abc123-user-id")
        print("  python check_gallery_emails.py abc123-user-id def456-gallery-id")

