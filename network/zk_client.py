"""
ZKTeco device connection wrapper.
"""

from __future__ import annotations

from zk import ZK


def connect_device(ip: str, port: int = 4370, comm_key: int = 0):
    """
    Connect to a ZK device.

    Args:
        ip: Device IP.
        port: Device port.
        comm_key: Device communication key.

    Returns:
        Connected ZK session object.
    """
    zk = ZK(
        ip,
        port=int(port),
        timeout=10,
        password=int(comm_key),
        force_udp=False,
        ommit_ping=True,
    )

    conn = zk.connect()
    conn.disable_device()
    return conn