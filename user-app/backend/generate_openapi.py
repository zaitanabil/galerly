"""
OpenAPI / Swagger Documentation Generator for Galerly API
Generates comprehensive API documentation from endpoint handlers
"""
import os
import json
from typing import Dict, List, Any


def generate_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for Galerly API
    
    Returns:
        dict: Complete OpenAPI specification
    """
    
    # Get API base URL from environment
    api_base_url = os.environ.get('API_BASE_URL', 'https://api.galerly.com')
    frontend_url = os.environ.get('FRONTEND_URL', 'https://galerly.com')
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Galerly API",
            "version": "3.0.0",
            "description": "Professional photography gallery management platform API. Share art, not files.",
            "contact": {
                "name": "Galerly Support",
                "email": "support@galerly.com",
                "url": frontend_url
            },
            "license": {
                "name": "Proprietary",
                "url": f"{frontend_url}/legal/terms"
            }
        },
        "servers": [
            {
                "url": api_base_url,
                "description": "Production API"
            },
            {
                "url": "http://localhost:5001",
                "description": "Local Development"
            }
        ],
        "tags": [
            {"name": "Authentication", "description": "User authentication and authorization"},
            {"name": "Galleries", "description": "Gallery management operations"},
            {"name": "Photos", "description": "Photo upload and management"},
            {"name": "Videos", "description": "Video upload and streaming"},
            {"name": "Analytics", "description": "Usage and engagement analytics"},
            {"name": "Billing", "description": "Subscription and payment management"},
            {"name": "Portfolio", "description": "Public portfolio customization"},
            {"name": "Custom Domain", "description": "Custom domain setup and management"},
            {"name": "Watermarking", "description": "Watermark configuration and application"},
            {"name": "Invoices", "description": "Client invoicing"},
            {"name": "Contracts", "description": "Contract management and eSignatures"},
            {"name": "Scheduler", "description": "Appointment scheduling"},
            {"name": "Email", "description": "Email templates and automation"},
            {"name": "SEO", "description": "SEO optimization tools"},
            {"name": "RAW Vault", "description": "RAW photo archival"},
        ],
        "paths": {},
        "components": {
            "securitySchemes": {
                "cookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session",
                    "description": "Session cookie authentication"
                },
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token authentication"
                }
            },
            "schemas": {},
            "responses": {}
        },
        "security": []
    }
    
    # Add common schemas
    spec["components"]["schemas"].update(_get_common_schemas())
    
    # Add endpoint paths
    spec["paths"].update(_get_auth_paths())
    spec["paths"].update(_get_gallery_paths())
    spec["paths"].update(_get_photo_paths())
    spec["paths"].update(_get_billing_paths())
    spec["paths"].update(_get_portfolio_paths())
    spec["paths"].update(_get_custom_domain_paths())
    spec["paths"].update(_get_watermark_paths())
    
    return spec


def _get_common_schemas() -> Dict[str, Any]:
    """Common reusable schemas"""
    return {
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Error message"}
            }
        },
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "email": {"type": "string", "format": "email"},
                "username": {"type": "string"},
                "plan": {"type": "string", "enum": ["free", "starter", "plus", "pro", "ultimate"]},
                "created_at": {"type": "string", "format": "date-time"}
            }
        },
        "Gallery": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "user_id": {"type": "string", "format": "uuid"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "cover_photo_url": {"type": "string", "format": "uri"},
                "share_token": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "photo_count": {"type": "integer"}
            }
        },
        "Photo": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "gallery_id": {"type": "string", "format": "uuid"},
                "filename": {"type": "string"},
                "url": {"type": "string", "format": "uri"},
                "thumbnail_url": {"type": "string", "format": "uri"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        }
    }


def _get_auth_paths() -> Dict[str, Any]:
    """Authentication endpoint paths"""
    return {
        "/v1/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register new user",
                "operationId": "register",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "password", "username"],
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string", "minLength": 8},
                                    "username": {"type": "string", "minLength": 3}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Registration successful",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "400": {"description": "Invalid input"},
                    "409": {"description": "Email already exists"}
                }
            }
        },
        "/v1/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Login user",
                "operationId": "login",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "password"],
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        },
                        "headers": {
                            "Set-Cookie": {
                                "schema": {"type": "string"},
                                "description": "Session cookie"
                            }
                        }
                    },
                    "401": {"description": "Invalid credentials"}
                }
            }
        },
        "/v1/auth/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get current user",
                "operationId": "getCurrentUser",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {
                        "description": "User details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "401": {"description": "Not authenticated"}
                }
            }
        }
    }


def _get_gallery_paths() -> Dict[str, Any]:
    """Gallery management paths"""
    return {
        "/v1/galleries": {
            "get": {
                "tags": ["Galleries"],
                "summary": "List user galleries",
                "operationId": "listGalleries",
                "security": [{"cookieAuth": []}],
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20, "maximum": 100}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Gallery list",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "galleries": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Gallery"}
                                        },
                                        "total": {"type": "integer"},
                                        "page": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Galleries"],
                "summary": "Create new gallery",
                "operationId": "createGallery",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "client_emails": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "email"}
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Gallery created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Gallery"}
                            }
                        }
                    }
                }
            }
        }
    }


def _get_photo_paths() -> Dict[str, Any]:
    """Photo management paths"""
    return {
        "/v1/galleries/{galleryId}/photos": {
            "post": {
                "tags": ["Photos"],
                "summary": "Upload photo to gallery",
                "operationId": "uploadPhoto",
                "security": [{"cookieAuth": []}],
                "parameters": [
                    {
                        "name": "galleryId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["filename", "data"],
                                "properties": {
                                    "filename": {"type": "string"},
                                    "data": {"type": "string", "format": "base64"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Photo uploaded",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Photo"}
                            }
                        }
                    }
                }
            }
        }
    }


def _get_billing_paths() -> Dict[str, Any]:
    """Billing paths"""
    return {
        "/v1/billing/checkout": {
            "post": {
                "tags": ["Billing"],
                "summary": "Create checkout session",
                "operationId": "createCheckoutSession",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["plan", "interval"],
                                "properties": {
                                    "plan": {
                                        "type": "string",
                                        "enum": ["starter", "plus", "pro", "ultimate"]
                                    },
                                    "interval": {
                                        "type": "string",
                                        "enum": ["monthly", "annual"]
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Checkout session created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "checkout_url": {"type": "string", "format": "uri"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def _get_portfolio_paths() -> Dict[str, Any]:
    """Portfolio paths"""
    return {
        "/v1/portfolio/settings": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Get portfolio settings",
                "operationId": "getPortfolioSettings",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {
                        "description": "Portfolio settings"
                    }
                }
            },
            "put": {
                "tags": ["Portfolio"],
                "summary": "Update portfolio settings",
                "operationId": "updatePortfolioSettings",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "theme": {"type": "string"},
                                    "primary_color": {"type": "string"},
                                    "about_section": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Settings updated"}
                }
            }
        }
    }


def _get_custom_domain_paths() -> Dict[str, Any]:
    """Custom domain paths"""
    return {
        "/v1/portfolio/custom-domain/setup": {
            "post": {
                "tags": ["Custom Domain"],
                "summary": "Setup custom domain with SSL",
                "description": "Automatically creates CloudFront distribution and ACM certificate",
                "operationId": "setupCustomDomain",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["domain"],
                                "properties": {
                                    "domain": {
                                        "type": "string",
                                        "example": "gallery.yourstudio.com"
                                    },
                                    "auto_provision": {
                                        "type": "boolean",
                                        "default": True
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Domain setup initiated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "certificate_arn": {"type": "string"},
                                        "distribution_id": {"type": "string"},
                                        "validation_records": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "value": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/v1/portfolio/custom-domain/status": {
            "get": {
                "tags": ["Custom Domain"],
                "summary": "Check custom domain status",
                "operationId": "checkCustomDomainStatus",
                "security": [{"cookieAuth": []}],
                "parameters": [
                    {
                        "name": "domain",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Domain status"
                    }
                }
            }
        }
    }


def _get_watermark_paths() -> Dict[str, Any]:
    """Watermark paths"""
    return {
        "/v1/profile/watermark-logo": {
            "post": {
                "tags": ["Watermarking"],
                "summary": "Upload watermark logo",
                "operationId": "uploadWatermarkLogo",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["file_data", "filename"],
                                "properties": {
                                    "file_data": {
                                        "type": "string",
                                        "format": "base64"
                                    },
                                    "filename": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Logo uploaded",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "s3_key": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/v1/profile/watermark-settings": {
            "get": {
                "tags": ["Watermarking"],
                "summary": "Get watermark settings",
                "operationId": "getWatermarkSettings",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {"description": "Watermark settings"}
                }
            },
            "put": {
                "tags": ["Watermarking"],
                "summary": "Update watermark settings",
                "operationId": "updateWatermarkSettings",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "watermark_enabled": {"type": "boolean"},
                                    "watermark_position": {
                                        "type": "string",
                                        "enum": ["top-left", "top-right", "bottom-left", "bottom-right", "center"]
                                    },
                                    "watermark_opacity": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1
                                    },
                                    "watermark_size_percent": {
                                        "type": "integer",
                                        "minimum": 5,
                                        "maximum": 50
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Settings updated"}
                }
            }
        },
        "/v1/profile/watermark-batch-apply": {
            "post": {
                "tags": ["Watermarking"],
                "summary": "Apply watermark to existing photos",
                "operationId": "batchApplyWatermark",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["gallery_id"],
                                "properties": {
                                    "gallery_id": {"type": "string", "format": "uuid"},
                                    "photo_ids": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "uuid"}
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch processing completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "processed": {"type": "integer"},
                                        "failed": {"type": "integer"},
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def save_openapi_spec(output_path: str = "openapi.json"):
    """
    Generate and save OpenAPI specification to file
    
    Args:
        output_path: Path to output file
    """
    spec = generate_openapi_spec()
    
    with open(output_path, 'w') as f:
        json.dump(spec, f, indent=2)
    
    print(f"OpenAPI specification saved to {output_path}")
    return spec


if __name__ == '__main__':
    # Generate and save when run directly
    save_openapi_spec()

