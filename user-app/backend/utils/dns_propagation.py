"""
DNS Propagation Checker
Checks DNS propagation status across multiple nameservers worldwide
"""
import dns.resolver
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed


# Global DNS servers to check propagation
GLOBAL_DNS_SERVERS = [
    '8.8.8.8',        # Google Primary
    '8.8.4.4',        # Google Secondary
    '1.1.1.1',        # Cloudflare Primary
    '1.0.0.1',        # Cloudflare Secondary
    '208.67.222.222', # OpenDNS Primary
    '208.67.220.220', # OpenDNS Secondary
    '9.9.9.9',        # Quad9
    '149.112.112.112',# Quad9 Secondary
]


def check_dns_record(domain, record_type='A', nameserver='8.8.8.8', timeout=5):
    """
    Check a specific DNS record from a specific nameserver
    
    Args:
        domain: Domain to check
        record_type: DNS record type (A, AAAA, CNAME, TXT, MX, etc.)
        nameserver: Nameserver IP to query
        timeout: Query timeout in seconds
    
    Returns:
        dict: {
            'success': bool,
            'records': list,
            'nameserver': str,
            'error': str (if failed)
        }
    """
    try:
        # Create resolver with specific nameserver
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [nameserver]
        resolver.timeout = timeout
        resolver.lifetime = timeout
        
        # Query DNS
        answers = resolver.resolve(domain, record_type)
        
        records = []
        for rdata in answers:
            if record_type == 'CNAME':
                records.append(str(rdata.target).rstrip('.'))
            elif record_type == 'A' or record_type == 'AAAA':
                records.append(str(rdata))
            elif record_type == 'TXT':
                records.append(str(rdata))
            elif record_type == 'MX':
                records.append(f"{rdata.preference} {str(rdata.exchange).rstrip('.')}")
            else:
                records.append(str(rdata))
        
        return {
            'success': True,
            'records': records,
            'nameserver': nameserver,
            'record_type': record_type
        }
        
    except dns.resolver.NXDOMAIN:
        return {
            'success': False,
            'error': 'Domain does not exist',
            'nameserver': nameserver
        }
    except dns.resolver.NoAnswer:
        return {
            'success': False,
            'error': f'No {record_type} record found',
            'nameserver': nameserver
        }
    except dns.resolver.Timeout:
        return {
            'success': False,
            'error': 'DNS query timeout',
            'nameserver': nameserver
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'nameserver': nameserver
        }


def check_dns_propagation(domain, record_type='A', expected_value=None, nameservers=None):
    """
    Check DNS propagation across multiple global nameservers
    
    Args:
        domain: Domain to check
        record_type: DNS record type
        expected_value: Optional expected value to match against
        nameservers: Optional list of nameserver IPs (uses global list if not provided)
    
    Returns:
        dict: {
            'propagated': bool,  # True if all servers have the record
            'percentage': float,  # Percentage of servers with the record
            'servers_propagated': int,
            'servers_checked': int,
            'results': list,  # Individual server results
            'ready': bool  # True if >= 80% propagated
        }
    """
    if nameservers is None:
        nameservers = GLOBAL_DNS_SERVERS
    
    results = []
    propagated_count = 0
    
    # Check all nameservers in parallel
    with ThreadPoolExecutor(max_workers=len(nameservers)) as executor:
        future_to_ns = {
            executor.submit(check_dns_record, domain, record_type, ns): ns
            for ns in nameservers
        }
        
        for future in as_completed(future_to_ns):
            ns = future_to_ns[future]
            try:
                result = future.result()
                results.append(result)
                
                # Check if propagated
                if result['success']:
                    # If expected value provided, check for match
                    if expected_value:
                        if any(expected_value in record for record in result['records']):
                            propagated_count += 1
                    else:
                        # Just check if record exists
                        propagated_count += 1
                        
            except Exception as e:
                print(f"Error checking {ns}: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'nameserver': ns
                })
    
    total_servers = len(nameservers)
    percentage = (propagated_count / total_servers * 100) if total_servers > 0 else 0
    
    return {
        'propagated': propagated_count == total_servers,
        'percentage': round(percentage, 1),
        'servers_propagated': propagated_count,
        'servers_checked': total_servers,
        'ready': percentage >= 80.0,  # Consider ready if 80%+ propagated
        'results': results,
        'domain': domain,
        'record_type': record_type
    }


def check_cname_propagation(domain, expected_cname):
    """
    Check CNAME record propagation
    
    Args:
        domain: Domain to check
        expected_cname: Expected CNAME target (e.g., 'cdn.galerly.com')
    
    Returns:
        dict: Same format as check_dns_propagation
    """
    return check_dns_propagation(
        domain=domain,
        record_type='CNAME',
        expected_value=expected_cname
    )


def check_a_record_propagation(domain, expected_ip=None):
    """
    Check A record propagation
    
    Args:
        domain: Domain to check
        expected_ip: Optional expected IP address
    
    Returns:
        dict: Same format as check_dns_propagation
    """
    return check_dns_propagation(
        domain=domain,
        record_type='A',
        expected_value=expected_ip
    )


def check_txt_record(domain, expected_text=None):
    """
    Check TXT record (useful for domain verification)
    
    Args:
        domain: Domain to check
        expected_text: Optional expected TXT record content
    
    Returns:
        dict: Same format as check_dns_propagation
    """
    return check_dns_propagation(
        domain=domain,
        record_type='TXT',
        expected_value=expected_text
    )


def get_nameservers(domain):
    """
    Get authoritative nameservers for a domain
    
    Args:
        domain: Domain to check
    
    Returns:
        dict: {
            'success': bool,
            'nameservers': list,
            'error': str (if failed)
        }
    """
    try:
        # Get root domain (remove subdomain)
        parts = domain.split('.')
        if len(parts) > 2:
            root_domain = '.'.join(parts[-2:])
        else:
            root_domain = domain
        
        answers = dns.resolver.resolve(root_domain, 'NS')
        
        nameservers = []
        for rdata in answers:
            ns = str(rdata.target).rstrip('.')
            nameservers.append(ns)
        
        return {
            'success': True,
            'nameservers': nameservers,
            'domain': root_domain
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def validate_domain_format(domain):
    """
    Validate domain name format
    
    Args:
        domain: Domain to validate
    
    Returns:
        dict: {
            'valid': bool,
            'error': str (if invalid)
        }
    """
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
    
    # Check length
    if len(domain) > 253:
        return {
            'valid': False,
            'error': 'Domain name too long (max 253 characters)'
        }
    
    if len(domain) == 0:
        return {
            'valid': False,
            'error': 'Domain name is empty'
        }
    
    # Check for at least one dot
    if '.' not in domain:
        return {
            'valid': False,
            'error': 'Invalid domain format (must have TLD)'
        }
    
    # Check each label
    labels = domain.split('.')
    for label in labels:
        if len(label) == 0:
            return {
                'valid': False,
                'error': 'Empty label in domain'
            }
        
        if len(label) > 63:
            return {
                'valid': False,
                'error': f'Label too long: {label} (max 63 characters)'
            }
        
        # Check for invalid characters
        if not all(c.isalnum() or c == '-' for c in label):
            return {
                'valid': False,
                'error': f'Invalid characters in label: {label}'
            }
        
        # Cannot start or end with hyphen
        if label.startswith('-') or label.endswith('-'):
            return {
                'valid': False,
                'error': f'Label cannot start or end with hyphen: {label}'
            }
    
    return {
        'valid': True
    }


def resolve_domain_to_ip(domain):
    """
    Resolve domain to IP address
    
    Args:
        domain: Domain to resolve
    
    Returns:
        dict: {
            'success': bool,
            'ip_addresses': list,
            'error': str (if failed)
        }
    """
    try:
        ip_addresses = []
        
        # Try IPv4
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for rdata in answers:
                ip_addresses.append(str(rdata))
        except:
            pass
        
        # Try IPv6
        try:
            answers = dns.resolver.resolve(domain, 'AAAA')
            for rdata in answers:
                ip_addresses.append(str(rdata))
        except:
            pass
        
        if not ip_addresses:
            return {
                'success': False,
                'error': 'No IP addresses found'
            }
        
        return {
            'success': True,
            'ip_addresses': ip_addresses
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
