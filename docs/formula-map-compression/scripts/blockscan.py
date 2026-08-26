#!/usr/bin/env python3
"""256바이트 블록 중 '단순 수식'으로 표현 가능한 비율 측정."""
import sys, os, subprocess, collections

BLK = 256

def classify(b):
    if len(b) < BLK:
        return "tail"
    # 1. 상수 (RLE로 잡힘)
    if b.count(b[0]) == len(b):
        return "constant"
    # 2. 등차수열 (delta 필터로 잡힘)
    d = (b[1] - b[0]) % 256
    if all((b[i+1] - b[i]) % 256 == d for i in range(len(b)-1)):
        return "arithmetic"
    # 3. 짧은 주기 반복 (주기 <= 16)
    for p in range(1, 17):
        if all(b[i] == b[i % p] for i in range(len(b))):
            return f"periodic"
    return "none"

def scan(path):
    try:
        data = open(path, 'rb').read()
    except Exception:
        return None
    if len(data) < BLK * 20:
        return None
    c = collections.Counter()
    for i in range(0, len(data) - BLK + 1, BLK):
        c[classify(data[i:i+BLK])] += 1
    total = sum(c.values())
    hit = total - c["none"]
    return path, len(data), total, hit, c

def comp(path, tool, args):
    try:
        out = subprocess.run([tool] + args, stdin=open(path,'rb'),
                             capture_output=True, timeout=120)
        return len(out.stdout) if out.returncode == 0 else None
    except Exception:
        return None

print(f"{'파일':<34}{'크기':>10}{'블록':>8}{'수식적중':>10}{'적중률':>8}"
      f"{'gzip':>8}{'zstd':>8}{'xz':>8}")
print("-" * 94)

for path in sys.argv[1:]:
    r = scan(path)
    if not r:
        continue
    p, size, total, hit, c = r
    rate = hit / total * 100
    g = comp(p, "gzip", ["-9c"])
    z = comp(p, "zstd", ["-19", "-c", "-q"])
    x = comp(p, "xz", ["-9c"])
    def pct(v):
        return f"{v/size*100:.1f}%" if v else "-"
    print(f"{os.path.basename(p)[:33]:<34}{size:>10,}{total:>8,}{hit:>10,}"
          f"{rate:>7.1f}%{pct(g):>8}{pct(z):>8}{pct(x):>8}")
