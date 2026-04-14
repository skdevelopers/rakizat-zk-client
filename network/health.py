"""
Network health checks.
"""

from __future__ import annotations

import socket


def tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Check whether a TCP service is reachable.

    Args:
        host: IP or hostname.
        port: TCP port.
        timeout: Timeout in seconds.

    Returns:
        True if reachable, otherwise False.
    """
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False