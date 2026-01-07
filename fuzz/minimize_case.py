#!/usr/bin/env python3
"""Simple minimizer: given a crash case index, try to remove parts of the payload
while preserving the server crash (status >= 500 or exception).

This is a greedy, byte/char-removal minimizer (not optimal but useful for demos).
"""
import time
import requests
import sys


def load_case(index=0):
    with open('fuzz/crash_cases.txt', 'rb') as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    if not lines:
        raise SystemExit('No crash cases found')
    if index < 0 or index >= len(lines):
        raise SystemExit('index out of range')
    line = lines[index].decode('utf-8', errors='replace')
    parts = line.split('\t', 2)
    payload = parts[2] if len(parts) > 2 else ''
    return payload


def test_crash(payload, target):
    url = target.rstrip('/') + '/echo'
    try:
        r = requests.post(url, json={'data': payload}, timeout=3)
        return r.status_code >= 500
    except Exception:
        return True


def minimize(payload, target):
    s = payload
    n = len(s)
    # try deleting chunks of decreasing size
    chunk = max(1, n // 2)
    while chunk >= 1:
        i = 0
        changed = False
        while i < len(s):
            cand = s[:i] + s[i+chunk:]
            if cand == s:
                i += 1
                continue
            if test_crash(cand, target):
                s = cand
                changed = True
                # don't advance i so we test further removals at same offset
            else:
                i += 1
        if not changed:
            chunk //= 2
    return s


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--index', type=int, default=0)
    p.add_argument('--target', default='http://127.0.0.1:8000')
    args = p.parse_args()

    payload = load_case(args.index)
    print('Original payload repr:', repr(payload))
    if not test_crash(payload, args.target):
        print('Original payload does not reproduce a crash against target; aborting.')
        sys.exit(2)

    start = time.time()
    minimized = minimize(payload, args.target)
    dur = time.time() - start
    print('Minimization finished in %.2fs' % dur)
    print('Minimized repr:', repr(minimized))

    with open('fuzz/minimized_cases.txt', 'a', encoding='utf-8') as f:
        f.write(f'ORIG\t{payload}\nMIN\t{minimized}\n')
    print('Wrote minimized case to fuzz/minimized_cases.txt')


if __name__ == '__main__':
    main()
