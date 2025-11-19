"""
Script to remove all legacy client_email references from code
"""

# Files to update and their patterns
UPDATES = {
    'backend/handlers/gallery_handler.py': [
        # Line 91: Remove client_email from search filter
        ('client_filter in g.get(\'client_email\', \'\').lower() or\n                       ', ''),
        # Lines 181-182: Remove client_email assignment
        ('        \'client_emails\': client_emails,  # NEW: Array of client emails\n        \'client_email\': client_emails[0] if client_emails else \'\',  # Legacy support\n', '        \'client_emails\': client_emails,\n'),
        # Lines 300-315: Remove client_email update logic
        ('        # Handle both single client_email and client_emails array\n        if \'client_emails\' in body or \'clientEmails\' in body:\n            client_emails = body.get(\'client_emails\') or body.get(\'clientEmails\', [])\n            # Normalize and validate emails\n            client_emails = [email.strip().lower() for email in client_emails if email.strip()]\n            for email in client_emails:\n                if len(email) > 255:\n                    return create_response(400, {\'error\': f\'Client email "{email}" must be less than 255 characters\'})\n            gallery[\'client_emails\'] = client_emails\n            gallery[\'client_email\'] = client_emails[0] if client_emails else \'\'  # Legacy support\n        elif \'client_email\' in body or \'clientEmail\' in body:\n            # Legacy single email support\n            client_email = (body.get(\'client_email\') or body.get(\'clientEmail\', \'\')).strip().lower()\n            if client_email and len(client_email) > 255:\n                return create_response(400, {\'error\': \'Client email must be less than 255 characters\'})\n            gallery[\'client_emails\'] = [client_email] if client_email else []\n            gallery[\'client_email\'] = client_email\n',
         '        # Handle client_emails array\n        if \'client_emails\' in body or \'clientEmails\' in body:\n            client_emails = body.get(\'client_emails\') or body.get(\'clientEmails\', [])\n            # Normalize and validate emails\n            client_emails = [email.strip().lower() for email in client_emails if email.strip()]\n            for email in client_emails:\n                if len(email) > 255:\n                    return create_response(400, {\'error\': f\'Client email "{email}" must be less than 255 characters\'})\n            gallery[\'client_emails\'] = client_emails\n'),
        # Lines 390-391: Remove client_email from duplicate
        ('            \'client_emails\': original_gallery.get(\'client_emails\', []),\n            \'client_email\': original_gallery.get(\'client_email\', \'\'),\n', '            \'client_emails\': original_gallery.get(\'client_emails\', []),\n'),
    ]
}

print("This is a reference file showing which lines need to be updated.")
print("Use search_replace tool to apply these changes.")

