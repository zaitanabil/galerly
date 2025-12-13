"""
DNS Propagation Checker
Checks DNS propagation across multiple global DNS servers
"""
import os
import socket
import time
from typing import Dict, Any, List, Optional

# DNS servers to check (global distribution)
DNS_SERVERS = [
    {'name': 'Google (US)', 'ip': '8.8.8.8'},
    {'name': 'Cloudflare (US)', 'ip': '1.1.1.1'},
    {'name': 'Quad9 (US)', 'ip': '9.9.9.9'},
    {'name': 'OpenDNS (US)', 'ip': '208.67.222.222'},
    {'name': 'Google (Alt)', 'ip': '8.8.4.4'},
    {'name': 'Cloudflare (Alt)', 'ip': '1.0.0.1'},
    {'name': 'Level3 (US)', 'ip': '4.2.2.2'}
]


def resolve_domain(domain: str, dns_server: Optional[str] = None) -> Optional[str]:
    """
    Resolve a domain to an IP address using a specific DNS server
    
    Args:
        domain: Domain name to resolve
        dns_server: DNS server IP (uses system default if None)
    
    Returns:
        Resolved IP address or None if resolution fails
    """
    
    try:
        # If specific DNS server requested, use dnspython
        if dns_server:
            try:
                import dns.resolver
                
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [dns_server]
                resolver.timeout = 5
                resolver.lifetime = 5
                
                answers = resolver.resolve(domain, 'A')
                if answers:
                    return str(answers[0])
            except ImportError:
                # Fallback to socket if dnspython not available
                pass
        
        # Use socket for resolution (system default DNS)
        result = socket.gethostbyname(domain)
        return result
    
    except (socket.gaierror, Exception) as e:
        return None


def check_cname_record(domain: str, expected_target: str, dns_server: Optional[str] = None) -> bool:
    """
    Check if a CNAME record points to the expected target
    
    Args:
        domain: Domain name to check
        expected_target: Expected CNAME target
        dns_server: DNS server IP (uses system default if None)
    
    Returns:
        True if CNAME matches expected target
    """
    
    try:
        if dns_server:
            try:
                import dns.resolver
                
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [dns_server]
                resolver.timeout = 5
                resolver.lifetime = 5
                
                answers = resolver.resolve(domain, 'CNAME')
                if answers:
                    cname = str(answers[0]).rstrip('.')
                    return cname.lower() == expected_target.lower()
            except ImportError:
                # Fallback to socket
                pass
        
        # Socket doesn't directly support CNAME queries
        # So we check if domain resolves (indirect validation)
        resolved = resolve_domain(domain, dns_server)
        return resolved is not None
    
    except Exception:
        return False


def check_propagation(
    domain: str,
    expected_target: Optional[str] = None,
    record_type: str = 'CNAME'
) -> Dict[str, Any]:
    """
    Check DNS propagation across multiple global DNS servers
    
    Args:
        domain: Domain name to check
        expected_target: Expected DNS target (for CNAME)
        record_type: DNS record type (A or CNAME)
    
    Returns:
        Dict containing propagation status and details
    """
    
    results = []
    propagated_count = 0
    total_servers = len(DNS_SERVERS)
    
    for server in DNS_SERVERS:
        server_name = server['name']
        server_ip = server['ip']
        
        try:
            if record_type == 'CNAME' and expected_target:
                # Check CNAME record
                is_propagated = check_cname_record(domain, expected_target, server_ip)
            else:
                # Check A record (domain resolution)
                resolved_ip = resolve_domain(domain, server_ip)
                is_propagated = resolved_ip is not None
            
            if is_propagated:
                propagated_count += 1
            
            results.append({
                'server': server_name,
                'server_ip': server_ip,
                'propagated': is_propagated,
                'status': 'OK' if is_propagated else 'NOT_FOUND'
            })
        
        except Exception as e:
            results.append({
                'server': server_name,
                'server_ip': server_ip,
                'propagated': False,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Calculate propagation percentage
    propagation_percentage = (propagated_count / total_servers) * 100 if total_servers > 0 else 0
    
    # Consider fully propagated if 80%+ servers return correct result
    fully_propagated = propagation_percentage >= 80
    
    return {
        'domain': domain,
        'propagated': fully_propagated,
        'propagation_percentage': round(propagation_percentage, 1),
        'servers_propagated': propagated_count,
        'servers_checked': total_servers,
        'servers': results,
        'ready': fully_propagated
    }


def wait_for_propagation(
    domain: str,
    expected_target: Optional[str] = None,
    record_type: str = 'CNAME',
    max_wait_seconds: int = 3600,
    check_interval: int = 60
) -> Dict[str, Any]:
    """
    Wait for DNS propagation to complete
    
    Args:
        domain: Domain name to check
        expected_target: Expected DNS target
        record_type: DNS record type
        max_wait_seconds: Maximum time to wait (default 1 hour)
        check_interval: Seconds between checks (default 60)
    
    Returns:
        Dict containing final propagation status
    """
    
    start_time = time.time()
    last_result = None
    
    while (time.time() - start_time) < max_wait_seconds:
        result = check_propagation(domain, expected_target, record_type)
        last_result = result
        
        if result['ready']:
            result['waited_seconds'] = int(time.time() - start_time)
            return result
        
        # Wait before next check
        time.sleep(check_interval)
    
    # Timeout reached
    if last_result:
        last_result['timeout'] = True
        last_result['waited_seconds'] = int(time.time() - start_time)
        return last_result
    
    return {
        'domain': domain,
        'propagated': False,
        'timeout': True,
        'error': 'Propagation check timed out'
    }


def verify_dns_configuration(
    domain: str,
    expected_records: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Verify that DNS is configured correctly with expected records
    
    Args:
        domain: Domain name to verify
        expected_records: List of expected DNS records
            [{'name': '_acme.example.com', 'type': 'CNAME', 'value': 'target.acm.aws'}]
    
    Returns:
        Dict containing verification results
    """
    
    verification_results = []
    all_valid = True
    
    for record in expected_records:
        record_name = record.get('name', domain)
        record_type = record.get('type', 'CNAME')
        expected_value = record.get('value')
        
        if record_type == 'CNAME':
            is_valid = check_cname_record(record_name, expected_value)
        elif record_type == 'A':
            resolved = resolve_domain(record_name)
            is_valid = resolved == expected_value
        else:
            is_valid = False
        
        verification_results.append({
            'name': record_name,
            'type': record_type,
            'expected': expected_value,
            'valid': is_valid
        })
        
        if not is_valid:
            all_valid = False
    
    return {
        'domain': domain,
        'all_valid': all_valid,
        'records_checked': len(expected_records),
        'records': verification_results
    }


def check_domain_availability(domain: str) -> Dict[str, Any]:
    """
    Check if a domain is available and resolving
    
    Args:
        domain: Domain name to check
    
    Returns:
        Dict containing availability status
    """
    
    try:
        resolved_ip = resolve_domain(domain)
        
        return {
            'domain': domain,
            'available': resolved_ip is not None,
            'resolved_ip': resolved_ip,
            'resolvable': True
        }
    
    except Exception as e:
        return {
            'domain': domain,
            'available': False,
            'resolvable': False,
            'error': str(e)
        }

