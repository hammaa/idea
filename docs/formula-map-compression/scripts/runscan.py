#!/usr/bin/env python3
"""길이 10 이상의 '수식 구간'(상수 / 등차수열)이 전체 바이트의 몇 %인지 측정.
   + 같은 파일에서 gzip(LZ77)이 실제로 몇 바이트를 한 토큰으로 커버하는지 비교."""
import sys, os, zlib, subprocess

MINRUN = 10

def formula_coverage(data):
    """delta가 일정한 최대 구간을 찾아 길이 MINRUN 이상인 바이트 수를 센다."""
    n = len(data)
    if n < 2:
        return 0, 0
    const_bytes = arith_bytes = 0
    i = 0
    while i < n - 1:
        d = (data[i+1] - data[i]) % 256
        j = i + 1
        while j < n - 1 and (data[j+1] - data[j]) % 256 == d:
            j += 1
        runlen = j - i + 1              # 이 등차 구간의 바이트 수
        if runlen >= MINRUN:
            if d == 0:
                const_bytes += runlen
            else:
                arith_bytes += runlen
        i = j
    return const_bytes, arith_bytes

def gzip_match_stats(data):
    """deflate가 만든 결과 크기로부터 토큰당 평균 커버 바이트를 역산."""
    comp = zlib.compress(data, 9)
    return len(comp)

print(f"{'파일':<26}{'크기':>11}{'상수구간':>10}{'등차구간':>10}"
      f"{'수식커버':>9}{'손익분기':>9}{'gzip':>8}")
print("-" * 84)
print(f"{'':<26}{'':>11}{'':>10}{'':>10}{'(12.7%↑)':>9}{'':>9}{'':>8}")
print("-" * 84)

for path in sys.argv[1:]:
    try:
        data = open(path, 'rb').read()
    except Exception:
        continue
    if len(data) < 4096:
        continue
    c, a = formula_coverage(data)
    cov = (c + a) / len(data) * 100
    g = gzip_match_stats(data)
    verdict = "✅본전↑" if cov >= 12.7 else "❌미달"
    print(f"{os.path.basename(path)[:25]:<26}{len(data):>11,}"
          f"{c/len(data)*100:>9.1f}%{a/len(data)*100:>9.1f}%"
          f"{cov:>8.1f}%{verdict:>9}{g/len(data)*100:>7.1f}%")
