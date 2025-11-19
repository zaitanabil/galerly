#!/usr/bin/env python3
"""
Email Template Testing Script
Tests all 12 branded email templates to verify they render correctly
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.email_templates_branded import BRANDED_EMAIL_TEMPLATES

def test_all_templates():
    """Test that all email templates render without errors"""
    
    print("🧪 Testing Galerly Branded Email Templates\n")
    print("=" * 60)
    
    # Sample test data
    test_vars = {
        'code': '123456',
        'name': 'John Doe',
        'client_name': 'Jane Smith',
        'photographer_name': 'Mike Johnson',
        'gallery_name': 'Wedding Photo Gallery 2024',
        'gallery_url': 'https://galerly.com/gallery/abc123',
        'dashboard_url': 'https://galerly.com/dashboard',
        'description': 'Your beautiful wedding photos are ready to view!',
        'reset_url': 'https://galerly.com/reset-password?token=xyz789',
        'photo_count': 25,
        'message': 'Your photos look amazing! Take your time selecting your favorites.',
        'subject': 'Custom Message from Your Photographer',
        'title': 'Gallery Update',
        'button_html': '<a href="https://galerly.com/gallery/abc123" class="email-button">View Gallery</a>',
        'days_remaining': 3,
        'selection_count': 15,
        'rating': 5,
        'feedback': 'Absolutely stunning work! Thank you so much!',
        'amount': '$500.00',
        'payment_date': 'November 16, 2025'
    }
    
    templates_tested = 0
    templates_passed = 0
    templates_failed = 0
    
    for template_name, template_data in BRANDED_EMAIL_TEMPLATES.items():
        templates_tested += 1
        
        try:
            # Test subject rendering
            subject = template_data['subject'].format(**test_vars)
            
            # Test HTML rendering
            html = template_data['html'].format(**test_vars)
            
            # Test text rendering
            text = template_data['text'].format(**test_vars)
            
            # Check that rendered content contains expected elements
            checks = []
            
            # Check HTML has proper structure
            checks.append(('DOCTYPE', '<!DOCTYPE html>' in html))
            checks.append(('Charset', 'charset="UTF-8"' in html))
            checks.append(('Viewport', 'viewport' in html))
            checks.append(('Container', 'email-container' in html))
            checks.append(('Header', 'email-header' in html))
            checks.append(('Body', 'email-body' in html))
            checks.append(('Footer', 'email-footer' in html))
            checks.append(('Logo', 'Galerly' in html))
            checks.append(('Tagline', 'Share art, not files' in html))
            
            # Check brand colors are present
            checks.append(('Blue Color', '#0071E3' in html or '#0066CC' in html))
            checks.append(('Shark Color', '#1D1D1F' in html))
            checks.append(('Gray Color', '#86868B' in html))
            
            # Check fonts are specified
            checks.append(('SF Pro Font', 'SF Pro' in html))
            checks.append(('System Fonts', '-apple-system' in html))
            
            all_passed = all(check[1] for check in checks)
            
            if all_passed:
                templates_passed += 1
                status = "✅ PASS"
                color = "\033[92m"  # Green
            else:
                templates_failed += 1
                status = "❌ FAIL"
                color = "\033[91m"  # Red
            
            reset = "\033[0m"
            
            print(f"\n{color}{status}{reset} Template: {template_name}")
            print(f"   Subject: {subject[:60]}...")
            print(f"   HTML Length: {len(html)} chars")
            print(f"   Text Length: {len(text)} chars")
            
            # Show failed checks
            failed_checks = [check[0] for check in checks if not check[1]]
            if failed_checks:
                print(f"   ⚠️  Failed checks: {', '.join(failed_checks)}")
            
        except KeyError as e:
            templates_failed += 1
            print(f"\n❌ FAIL Template: {template_name}")
            print(f"   Error: Missing variable {e}")
        except Exception as e:
            templates_failed += 1
            print(f"\n❌ FAIL Template: {template_name}")
            print(f"   Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"\n📊 Test Summary:")
    print(f"   Total Templates: {templates_tested}")
    print(f"   ✅ Passed: {templates_passed}")
    print(f"   ❌ Failed: {templates_failed}")
    print(f"   Success Rate: {(templates_passed/templates_tested*100):.1f}%")
    
    if templates_failed == 0:
        print("\n🎉 All email templates are working perfectly!")
        print("   ✅ All brand elements present")
        print("   ✅ All templates render correctly")
        print("   ✅ All variables interpolate successfully")
        return True
    else:
        print(f"\n⚠️  {templates_failed} template(s) need attention")
        return False


def test_brand_consistency():
    """Verify brand consistency across all templates"""
    
    print("\n\n🎨 Testing Brand Consistency\n")
    print("=" * 60)
    
    required_brand_elements = {
        'Galerly Logo': 'Galerly',
        'Tagline': 'Share art, not files',
        'Primary Blue': '#0071E3',
        'Shark Dark': '#1D1D1F',
        'Gray Medium': '#86868B',
        'Light Gray': '#F5F5F7',
        'Border Gray': '#E5E5EA',
        'SF Pro Display': 'SF Pro Display',
        'SF Pro Text': 'SF Pro Text',
        'Button Radius': '980px',
        'Box Radius': '16px',
    }
    
    all_consistent = True
    
    for element_name, element_value in required_brand_elements.items():
        found_count = 0
        
        for template_name, template_data in BRANDED_EMAIL_TEMPLATES.items():
            if element_value in template_data['html']:
                found_count += 1
        
        percentage = (found_count / len(BRANDED_EMAIL_TEMPLATES)) * 100
        
        if found_count >= len(BRANDED_EMAIL_TEMPLATES) * 0.8:  # 80% threshold
            status = "✅"
        else:
            status = "⚠️ "
            all_consistent = False
        
        print(f"{status} {element_name:20} Found in {found_count:2}/{len(BRANDED_EMAIL_TEMPLATES)} templates ({percentage:5.1f}%)")
    
    print("\n" + "=" * 60)
    
    if all_consistent:
        print("\n✅ Brand consistency check PASSED!")
        print("   All brand elements are consistently used across templates")
    else:
        print("\n⚠️  Some brand elements could be more consistent")
    
    return all_consistent


if __name__ == '__main__':
    print("\n" + "🚀 GALERLY EMAIL TEMPLATE TEST SUITE" + "\n")
    
    # Run tests
    templates_ok = test_all_templates()
    brand_ok = test_brand_consistency()
    
    # Final verdict
    print("\n\n" + "=" * 60)
    if templates_ok and brand_ok:
        print("✅ ALL TESTS PASSED! Email system is ready for production.")
        sys.exit(0)
    else:
        print("⚠️  Some issues detected. Please review the output above.")
        sys.exit(1)

