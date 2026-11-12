import ipaddress
import socket
import urllib.parse
from typing import Tuple
import httpx

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
}

def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) vulnerabilities.
    Restricts to http/https, blocks loopback, link-local (cloud metadata 169.254.x.x),
    private IP ranges (RFC 1918), and reserved/multicast addresses.
    """
    if not url or not isinstance(url, str):
        return False, "URL string is empty or invalid"

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"

    # Scheme validation: ONLY http and https
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL contains no valid hostname"

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Access to blocked host '{hostname}' is denied"

    # Resolve hostname to IP addresses via DNS
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        return False, f"DNS resolution failed for host '{hostname}': {str(e)}"
    except Exception as e:
        return False, f"Error resolving host '{hostname}': {str(e)}"

    if not addr_info:
        return False, f"No IP addresses resolved for host '{hostname}'"

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid resolved IP address: {ip_str}"

        # Block loopback (127.0.0.0/8, ::1)
        if ip.is_loopback:
            return False, f"Access to loopback address ({ip_str}) is blocked"

        # Block private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
        if ip.is_private:
            return False, f"Access to private internal network ({ip_str}) is blocked"

        # Block link-local and cloud metadata (169.254.0.0/16, fe80::/10)
        if ip.is_link_local:
            return False, f"Access to link-local/cloud metadata address ({ip_str}) is blocked"

        # Block multicast, reserved, and unspecified
        if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False, f"Access to reserved IP address ({ip_str}) is blocked"

    return True, ""

async def safe_url_head_or_get(url: str, timeout: float = 5.0, max_redirects: int = 3) -> Tuple[bool, int, str]:
    """
    Safely checks URL reachability with hop-by-hop SSRF validation across redirects.
    Returns: (is_reachable, status_code, error_message)
    """
    current_url = url

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for hop in range(max_redirects + 1):
            is_safe, reason = is_safe_url(current_url)
            if not is_safe:
                return False, 0, f"SSRF Guard: {reason}"

            try:
                response = await client.head(current_url)
                
                # If server redirects (301, 302, 303, 307, 308), re-evaluate next hop
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        return False, response.status_code, "Redirect response missing Location header"
                    current_url = urllib.parse.urljoin(current_url, location)
                    continue

                # If HEAD is disallowed (405), fallback to GET
                if response.status_code == 405:
                    response = await client.get(current_url)

                if response.status_code >= 400:
                    return False, response.status_code, f"URL returned HTTP error status {response.status_code}"

                return True, response.status_code, ""

            except httpx.TimeoutException:
                return False, 0, f"Connection to {current_url} timed out after {timeout}s"
            except httpx.RequestError as e:
                return False, 0, f"HTTP request failed: {str(e)}"

        return False, 0, f"Exceeded maximum redirect limit of {max_redirects} hops"
