#!/usr/bin/env python3
"""
Set live network latency override matrix for the graph-based model.

Usage:
  python set_network_latency.py --url http://127.0.0.1:5055 \
    --ttl 3600 \
    us-east-1,eu-west-1=92 us-east-1,us-west-2=70 eu-west-1,us-east-1=92

To clear:
  python set_network_latency.py --url http://127.0.0.1:5055 --clear
"""
import argparse
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:5055', help='Backend base URL')
    parser.add_argument('--ttl', type=int, default=3600, help='TTL seconds for override')
    parser.add_argument('--clear', action='store_true', help='Clear override')
    parser.add_argument('pairs', nargs='*', help='Pairs in form from,to=ms')
    args = parser.parse_args()

    endpoint = args.url.rstrip('/') + '/api/network-latency'

    if args.clear:
        resp = requests.post(endpoint, json={'clear': True})
        print(resp.status_code, resp.text)
        return

    matrix = {}
    for p in args.pairs:
        if '=' not in p or ',' not in p:
            print(f"Skipping invalid pair '{p}'. Expected from,to=ms")
            continue
        left, ms = p.split('=', 1)
        a, b = left.split(',', 1)
        matrix[f"{a.strip()},{b.strip()}"] = float(ms)

    if not matrix:
        print('No valid pairs provided.')
        return

    payload = { 'matrix': matrix, 'ttl_seconds': args.ttl }
    resp = requests.post(endpoint, json=payload)
    print(resp.status_code, resp.text)


if __name__ == '__main__':
    main()
