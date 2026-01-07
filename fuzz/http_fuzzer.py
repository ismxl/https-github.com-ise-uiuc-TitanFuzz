#!/usr/bin/env python3
"""Simple HTTP fuzzer that POSTs mutated inputs to /echo and logs crashes."""
import json
import random
import string
import time
import sys
from urllib.parse import urljoin

import requests


def mutate(seed: str) -> str:
    s = list(seed)
    for _ in range(random.randint(1, max(1, len(s)))):
        i = random.randrange(max(1, len(s)))
        op = random.choice(('flip', 'insert', 'delete'))
        if op == 'flip' and s:
            s[i % len(s)] = random.choice(string.printable)
        elif op == 'insert':
            s.insert(i, random.choice(string.printable))
        elif op == 'delete' and s:
            s.pop(i % len(s))
    # occasionally inject the crash trigger
    if random.random() < 0.02:
        s.insert(0, 'CRASH')
    return ''.join(s)


def main(target='http://127.0.0.1:8000', iters=10000, delay=0.01):
    url = urljoin(target, '/echo')
    corpus = ['hello', '1234', '{"a":1}', 'A'*10]
    found = set()
    for i in range(iters):
        seed = random.choice(corpus)
        data = mutate(seed)
        try:
            r = requests.post(url, json={'data': data}, timeout=2)
        except Exception as e:
            print(f'[!] Exception when sending input #{i}: {e}', file=sys.stderr)
            found.add(('exception', str(e), data[:200]))
            # save reproducible case to file
            with open('fuzz/crash_cases.txt', 'a') as f:
                f.write(f'EXC\t{e}\t{data}\n')
            continue
        if r.status_code >= 500:
            print(f'[!] Server error #{i}: {r.status_code} for payload len {len(data)}')
            found.add(('500', r.status_code, data[:200]))
            with open('fuzz/crash_cases.txt', 'a') as f:
                f.write(f'500\t{r.status_code}\t{data}\n')
        # small delay to avoid overwhelming target
        time.sleep(delay)

    if found:
        print('\nFound issues:')
        for item in found:
            print(item)
    else:
        print('\nNo issues found (in this short run).')


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--target', default='http://127.0.0.1:8000')
    p.add_argument('--iters', type=int, default=2000)
    p.add_argument('--delay', type=float, default=0.01)
    args = p.parse_args()
    main(target=args.target, iters=args.iters, delay=args.delay)
