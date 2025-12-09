"""
Script to archive duplicate Stripe prices created by the buggy invoice handler.
Run this once to clean up your Stripe account.

Usage:
    From user-app/backend directory:
    python3 scripts/cleanup_stripe_prices.py
    
    Or from project root:
    python3 user-app/backend/scripts/cleanup_stripe_prices.py
"""
import os
import sys
import stripe
from pathlib import Path
from dotenv import load_dotenv

# Find and load .env.development or .env.production from project root
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
project_root = backend_dir.parent.parent

# Try to load .env files from project root
env_dev = project_root / '.env.development'
env_prod = project_root / '.env.production'

if env_dev.exists():
    load_dotenv(env_dev)
    print(f"Loaded environment from: {env_dev}")
elif env_prod.exists():
    load_dotenv(env_prod)
    print(f"Loaded environment from: {env_prod}")
else:
    print(f"Warning: No .env file found in {project_root}")
    print("Looking for .env.development or .env.production")

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

if not stripe.api_key:
    print("Error: STRIPE_SECRET_KEY not found in environment variables")
    exit(1)

print("Fetching all prices from Stripe...")
prices = stripe.Price.list(limit=100)

wedding_prices = []
for price in prices.auto_paging_iter():
    # Find prices with "Wedding Photography" in the product name
    if price.product:
        try:
            product = stripe.Product.retrieve(price.product)
            if product.name == "Wedding Photography" or "Service" in product.name:
                wedding_prices.append({
                    'price_id': price.id,
                    'product_id': product.id,
                    'product_name': product.name,
                    'amount': price.unit_amount / 100 if price.unit_amount else 0,
                    'active': price.active
                })
        except Exception as e:
            print(f"Error retrieving product for price {price.id}: {e}")

print(f"\nFound {len(wedding_prices)} prices to archive:")
for p in wedding_prices[:10]:  # Show first 10
    print(f"  - {p['price_id']}: {p['product_name']} (${p['amount']})")
if len(wedding_prices) > 10:
    print(f"  ... and {len(wedding_prices) - 10} more")

if len(wedding_prices) == 0:
    print("\nNo prices to archive. Your Stripe account is clean!")
    exit(0)

# Archive automatically (non-interactive mode for scripts)
print(f"\nArchiving {len(wedding_prices)} prices...")
print("Note: Prices cannot be deleted because they were used.")
print("Setting them to inactive will hide them from your dashboard.\n")
archived_count = 0
for p in wedding_prices:
    try:
        # Archive the price (can't delete if used)
        stripe.Price.modify(p['price_id'], active=False)
        archived_count += 1
        print(f"  ✓ Archived {p['price_id']}")
    except Exception as e:
        print(f"  ✗ Failed to archive {p['price_id']}: {e}")

print(f"\n✅ Archived {archived_count} out of {len(wedding_prices)} prices")
print("\nThese prices are now hidden from your Stripe dashboard.")
print("They can't be deleted because they were used in payment links,")
print("but they won't appear in your active product catalog anymore.")
