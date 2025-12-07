"""
Secure URL Generator - Step 6
Generates signed CloudFront URLs for secure, time-limited access
Prevents unauthorized sharing while maintaining direct CDN access
"""
import os
import json
from datetime import datetime, timedelta
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import boto3


class SecureURLGenerator:
    """
    Generates secure, signed URLs for CloudFront distribution
    Enables fast direct access while preventing unauthorized sharing
    """
    
    def __init__(self):
        self.cdn_domain = os.environ.get('CDN_DOMAIN')
        self.cloudfront_key_pair_id = os.environ.get('CLOUDFRONT_KEY_PAIR_ID')
        self.cloudfront_private_key_path = os.environ.get('CLOUDFRONT_PRIVATE_KEY_PATH')
        
        # Load private key if available
        self.private_key = None
        if self.cloudfront_private_key_path and os.path.exists(self.cloudfront_private_key_path):
            with open(self.cloudfront_private_key_path, 'rb') as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
    
    
    def generate_signed_url(self, s3_key, expiry_minutes=60, download_filename=None):
        """
        Generate signed CloudFront URL for secure access
        
        Args:
            s3_key: S3 object key
            expiry_minutes: URL expiry time in minutes (default 60)
            download_filename: Optional filename for Content-Disposition header
        
        Returns:
            Signed URL string or regular CloudFront URL if signing not configured
        """
        # Base CloudFront URL
        url = f"https://{self.cdn_domain}/{s3_key}"
        
        # If signing is not configured, return regular URL
        if not self.private_key or not self.cloudfront_key_pair_id:
            print(" CloudFront signing not configured, returning unsigned URL")
            return url
        
        try:
            # Calculate expiry timestamp
            expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            # Create CloudFront signer
            def rsa_signer(message):
                return self.private_key.sign(
                    message,
                    padding.PKCS1v15(),
                    hashes.SHA1()
                )
            
            cloudfront_signer = CloudFrontSigner(
                self.cloudfront_key_pair_id,
                rsa_signer
            )
            
            # Generate signed URL
            signed_url = cloudfront_signer.generate_presigned_url(
                url,
                date_less_than=expiry_time
            )
            
            # Add download filename if specified
            if download_filename:
                separator = '&' if '?' in signed_url else '?'
                signed_url = f"{signed_url}{separator}response-content-disposition=attachment;filename={download_filename}"
            
            print(f"Generated signed URL for {s3_key}, expires in {expiry_minutes} minutes")
            return signed_url
            
        except Exception as e:
            print(f"Failed to generate signed URL: {str(e)}")
            return url  # Fallback to unsigned URL
    
    
    def generate_download_url(self, s3_key, filename, expiry_minutes=15):
        """
        Generate secure download URL with proper headers
        Short expiry for downloads (15 minutes default)
        
        Args:
            s3_key: S3 object key
            filename: Original filename for download
            expiry_minutes: URL expiry time (default 15 minutes for downloads)
        
        Returns:
            Signed download URL
        """
        return self.generate_signed_url(
            s3_key,
            expiry_minutes=expiry_minutes,
            download_filename=filename
        )
    
    
    def generate_presigned_s3_url(self, s3_key, expiry_seconds=3600):
        """
        Generate presigned S3 URL as fallback
        Used when CloudFront signing is not available
        
        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time in seconds
        
        Returns:
            Presigned S3 URL
        """
        try:
            s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION'))
            bucket = os.environ.get('S3_PHOTOS_BUCKET')
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiry_seconds
            )
            
            print(f"Generated presigned S3 URL for {s3_key}")
            return url
            
        except Exception as e:
            print(f"Failed to generate presigned S3 URL: {str(e)}")
            return None
    
    
    def generate_batch_urls(self, s3_keys, expiry_minutes=60):
        """
        Generate signed URLs for multiple files efficiently
        Used for bulk downloads or gallery views
        
        Args:
            s3_keys: List of S3 object keys
            expiry_minutes: URL expiry time
        
        Returns:
            Dictionary mapping s3_key to signed URL
        """
        urls = {}
        
        for s3_key in s3_keys:
            urls[s3_key] = self.generate_signed_url(s3_key, expiry_minutes)
        
        return urls


# Global instance
_secure_url_generator = None

def get_secure_url_generator():
    """Get or create global SecureURLGenerator instance"""
    global _secure_url_generator
    if _secure_url_generator is None:
        _secure_url_generator = SecureURLGenerator()
    return _secure_url_generator


def generate_secure_download_url(s3_key, filename, expiry_minutes=15):
    """
    Convenience function to generate secure download URL
    
    Args:
        s3_key: S3 object key
        filename: Original filename
        expiry_minutes: URL expiry time (default 15 minutes)
    
    Returns:
        Signed download URL
    """
    generator = get_secure_url_generator()
    return generator.generate_download_url(s3_key, filename, expiry_minutes)


def generate_secure_view_url(s3_key, expiry_minutes=60):
    """
    Convenience function to generate secure view URL
    Longer expiry for viewing (60 minutes default)
    
    Args:
        s3_key: S3 object key
        expiry_minutes: URL expiry time (default 60 minutes)
    
    Returns:
        Signed URL
    """
    generator = get_secure_url_generator()
    return generator.generate_signed_url(s3_key, expiry_minutes)

