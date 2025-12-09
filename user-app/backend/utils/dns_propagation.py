"""
DNS Propagation Checker
Checks DNS propagation status across multiple DNS servers worldwide
"""
import dns.resolver
import socket
import time
from datetime import datetime


# Major DNS servers to check propagation
DNS_SERVERS = [
    {'name': 'Google Primary', 'ip': '8.8.8.8', 'location': 'Global'},
    {'name': 'Google Secondary', 'ip': '8.8.4.4', 'location': 'Global'},
    {'name': 'Cloudflare Primary', 'ip': '1.1.1.1', 'location': 'Global'},
    {'name': 'Cloudflare Secondary', 'ip': '1.0.0.1', 'location': 'Global'},
    {'name': 'OpenDNS Primary', 'ip': '208.67.222.222', 'location': 'Global'},
    {'name': 'OpenDNS Secondary', 'ip': '208.67.220.220', 'location': 'Global'},
    {'name': 'Quad9', 'ip': '9.9.9.9', 'location': 'Global'},
]


def check_dns_propagation(domain, expected_value=None, record_type='CNAME', timeout=5):
    """
    Check DNS propagation across multiple DNS servers
    
    Args:
        domain: Domain name to check
        expected_value: Expected DNS value (optional, for verification)
        record_type: DNS record type (CNAME, A, TXT, etc.)
        timeout: Timeout for each DNS query in seconds
    
    Returns:
        dict: {
            'success': bool,
            'propagated': bool,  # True if all servers return expected value
            'propagation_percentage': float,  # 0-100
            'servers_checked': int,
            'servers_propagated': int,
            'results': list of {
                'server': str,
                'location': str,
                'value': str,
                'matches': bool,
                'response_time': float,
                'error': str
            },
            'estimated_completion': str  # If not fully propagated
        }
    """
    try:
        results = []
        propagated_count = 0
        
        # Check each DNS server
        for server_info in DNS_SERVERS:
            server_result = _query_dns_server(
                domain=domain,
                dns_server=server_info['ip'],
                record_type=record_type,
                timeout=timeout
            )
            
            server_result['server'] = server_info['name']
            server_result['location'] = server_info['location']
            
            # Check if value matches expected
            if expected_value and server_result.get('value'):
                # Normalize values for comparison
                value_normalized = server_result['value'].lower().rstrip('.')
                expected_normalized = expected_value.lower().rstrip('.')
                
                matches = expected_normalized in value_normalized
                server_result['matches'] = matches
                
                if matches:
                    propagated_count += 1
            elif server_result.get('value'):
                # If no expected value, any non-error response counts
                server_result['matches'] = True
                propagated_count += 1
            else:
                server_result['matches'] = False
            
            results.append(server_result)
        
        total_servers = len(DNS_SERVERS)
        propagation_percentage = (propagated_count / total_servers) * 100
        fully_propagated = propagated_count == total_servers
        
        # Estimate completion time if not fully propagated
        estimated_completion = None
        if not fully_propagated:
            # DNS typically propagates within 1-48 hours
            # If 0% propagated: 24-48 hours
            # If 50% propagated: 2-6 hours
            # If 75% propagated: 1-2 hours
            if propagation_percentage == 0:
                estimated_completion = '24-48 hours'
            elif propagation_percentage < 50:
                estimated_completion = '6-24 hours'
            elif propagation_percentage < 75:
                estimated_completion = '2-6 hours'
            else:
                estimated_completion = '1-2 hours'
        
        return {
            'success': True,
            'propagated': fully_propagated,
            'propagation_percentage': round(propagation_percentage, 1),
            'servers_checked': total_servers,
            'servers_propagated': propagated_count,
            'results': results,
            'estimated_completion': estimated_completion,
            'checked_at': datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        print(f"Error checking DNS propagation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def _query_dns_server(domain, dns_server, record_type='CNAME', timeout=5):
    """
    Query a specific DNS server for a domain record
    
    Args:
        domain: Domain name to query
        dns_server: DNS server IP address
        record_type: DNS record type
        timeout: Query timeout in seconds
    
    Returns:
        dict: {
            'value': str,  # DNS record value
            'response_time': float,  # Query time in ms
            'error': str  # If query failed
        }
    """
    result = {
        'value': None,
        'response_time': None,
        'error': None
    }
    
    try:
        # Create custom resolver with specific DNS server
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        resolver.timeout = timeout
        resolver.lifetime = timeout
        
        # Time the query
        start_time = time.time()
        
        try:
            answers = resolver.resolve(domain, record_type)
            
            # Get response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            result['response_time'] = round(response_time, 2)
            
            # Get record values
            values = []
            for rdata in answers:
                if record_type == 'CNAME':
                    values.append(str(rdata.target))
                elif record_type == 'A':
                    values.append(str(rdata))
                elif record_type == 'TXT':
                    values.append(str(rdata))
                else:
                    values.append(str(rdata))
            
            result['value'] = ', '.join(values) if values else None
            
        except dns.resolver.NXDOMAIN:
            result['error'] = 'NXDOMAIN: Domain does not exist'
        except dns.resolver.NoAnswer:
            result['error'] = 'NoAnswer: No DNS records found'
        except dns.resolver.NoNameservers:
            result['error'] = 'NoNameservers: All nameservers failed'
        except dns.resolver.Timeout:
            result['error'] = 'Timeout: DNS query timed out'
        except Exception as e:
            result['error'] = f'Query error: {str(e)}'
    
    except Exception as e:
        result['error'] = f'Setup error: {str(e)}'
    
    return result


def check_cname_propagation(domain, expected_cname, min_propagation=80):
    """
    Simplified CNAME propagation check
    
    Args:
        domain: Domain to check
        expected_cname: Expected CNAME value
        min_propagation: Minimum propagation percentage to consider successful (default: 80%)
    
    Returns:
        dict: {
            'success': bool,
            'propagated': bool,
            'percentage': float,
            'ready': bool  # True if meets minimum propagation threshold
        }
    """
    result = check_dns_propagation(
        domain=domain,
        expected_value=expected_cname,
        record_type='CNAME'
    )
    
    if not result['success']:
        return result
    
    return {
        'success': True,
        'propagated': result['propagated'],
        'percentage': result['propagation_percentage'],
        'ready': result['propagation_percentage'] >= min_propagation,
        'servers_propagated': result['servers_propagated'],
        'servers_checked': result['servers_checked'],
        'estimated_completion': result.get('estimated_completion')
    }


def wait_for_propagation(domain, expected_value, record_type='CNAME', 
                         min_propagation=80, max_wait=3600, check_interval=60):
    """
    Wait for DNS propagation to reach minimum threshold
    
    Args:
        domain: Domain to check
        expected_value: Expected DNS value
        record_type: DNS record type
        min_propagation: Minimum propagation percentage (default: 80%)
        max_wait: Maximum wait time in seconds (default: 3600 = 1 hour)
        check_interval: Seconds between checks (default: 60)
    
    Returns:
        dict: {
            'success': bool,
            'propagated': bool,
            'percentage': float,
            'elapsed_time': float,  # Seconds waited
            'checks_performed': int
        }
    """
    start_time = time.time()
    checks = 0
    
    while True:
        checks += 1
        elapsed = time.time() - start_time
        
        # Check propagation
        result = check_dns_propagation(domain, expected_value, record_type)
        
        if not result['success']:
            return {
                'success': False,
                'error': result.get('error'),
                'elapsed_time': elapsed,
                'checks_performed': checks
            }
        
        percentage = result['propagation_percentage']
        
        # Check if threshold met
        if percentage >= min_propagation:
            return {
                'success': True,
                'propagated': True,
                'percentage': percentage,
                'elapsed_time': elapsed,
                'checks_performed': checks
            }
        
        # Check if max wait time exceeded
        if elapsed >= max_wait:
            return {
                'success': False,
                'propagated': False,
                'percentage': percentage,
                'elapsed_time': elapsed,
                'checks_performed': checks,
                'error': f'Propagation timeout: only {percentage}% after {max_wait}s'
            }
        
        # Wait before next check
        time.sleep(check_interval)


def verify_domain_ownership(domain, verification_token, verification_record='_galerly-verify'):
    """
    Verify domain ownership via TXT record
    
    Args:
        domain: Domain to verify
        verification_token: Token to look for in TXT record
        verification_record: Subdomain for verification (default: _galerly-verify)
    
    Returns:
        dict: {
            'success': bool,
            'verified': bool,
            'token_found': str,
            'error': str
        }
    """
    try:
        # Construct verification domain
        verify_domain = f"{verification_record}.{domain}"
        
        # Query TXT record
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        
        try:
            answers = resolver.resolve(verify_domain, 'TXT')
            
            for rdata in answers:
                txt_value = str(rdata).strip('"')
                
                if verification_token in txt_value:
                    return {
                        'success': True,
                        'verified': True,
                        'token_found': txt_value
                    }
            
            return {
                'success': True,
                'verified': False,
                'error': 'Verification token not found in TXT records'
            }
            
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return {
                'success': True,
                'verified': False,
                'error': f'No TXT record found at {verify_domain}'
            }
    
    except Exception as e:
        print(f"Error verifying domain ownership: {str(e)}")
        return {
            'success': False,
            'verified': False,
            'error': str(e)
        }
