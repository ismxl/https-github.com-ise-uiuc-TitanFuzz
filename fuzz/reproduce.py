#!/usr/bin/env python3
"""Read a crash case from `fuzz/crash_cases.txt` and POST it to `/echo` to reproduce."""
import sys
import requests


def load_case(index=0):
    with open('fuzz/crash_cases.txt', 'rb') as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    if not lines:
        raise SystemExit('No crash cases found in fuzz/crash_cases.txt')
    if index < 0 or index >= len(lines):
        raise SystemExit(f'index out of range (0..{len(lines)-1})')
    line = lines[index].decode('utf-8', errors='replace')
    parts = line.split('\t', 2)
    payload = parts[2] if len(parts) > 2 else ''
    return payload


def main():
    import argparse

    p = argparse.ArgumentParser(description='Reproduce crash case by index')
    p.add_argument('--index', type=int, default=0)
    p.add_argument('--target', default='http://127.0.0.1:8000')
    args = p.parse_args()

    payload = load_case(args.index)
    print('Payload (repr):', repr(payload))
    url = args.target.rstrip('/') + '/echo'
    try:
        r = requests.post(url, json={'data': payload}, timeout=5)
    except Exception as e:
        print('Request exception:', e)
        sys.exit(2)

    print('Status code:', r.status_code)
    print('Response body:')
    print(r.text)

    if r.status_code >= 500:
        with open('fuzz/reproduced_case.txt', 'w', encoding='utf-8') as f:
            f.write(payload)
        print('Saved reproducer to fuzz/reproduced_case.txt')


if __name__ == '__main__':
    main()
