#!/usr/bin/env python3
"""
Quick RTT probe to cloud region endpoints (TCP connect time to 443).
This measures client→region RTT from your machine to approximate network conditions.

Note: This is NOT region↔region latency, but it can help calibrate or sanity-check
your override values.
"""
import socket
import time

REGION_HOSTS = {
    # AWS EC2 endpoints (representative)
    'us-east-1': 'ec2.us-east-1.amazonaws.com',
    'us-west-2': 'ec2.us-west-2.amazonaws.com',
    'eu-west-1': 'ec2.eu-west-1.amazonaws.com',
    'eu-central-1': 'ec2.eu-central-1.amazonaws.com',
    'ap-south-1': 'ec2.ap-south-1.amazonaws.com',
    'ap-northeast-1': 'ec2.ap-northeast-1.amazonaws.com',
}


def tcp_connect_ms(host: str, port: int = 443, timeout: float = 1.5, attempts: int = 3) -> float:
    times = []
    for _ in range(attempts):
        start = time.time()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
            elapsed = (time.time() - start) * 1000.0
            times.append(elapsed)
        except Exception:
            times.append(timeout * 1000.0)
        time.sleep(0.05)
    times.sort()
    # median
    return round(times[len(times)//2], 1)


def main():
    results = {}
    for region, host in REGION_HOSTS.items():
        ms = tcp_connect_ms(host)
        results[region] = ms
    print("Client→Region TCP connect median (ms):")
    for r, ms in results.items():
        print(f"  {r}: {ms}ms")


if __name__ == '__main__':
    main()
