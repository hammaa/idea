#!/usr/bin/env python3
"""가변 길이 수식 매칭 압축기 — 원안 그대로 구현.

A안: 수식 토큰만 (상수 / 등차수열, 맞는 데까지 최대 확장)
B안: A안 + '앞에 나온 데이터 참조' 수식 하나 추가  (= LZ77)

토큰 인코딩 (원안의 4바이트보다 넉넉하게 잡음):
  리터럴 런 : [플래그1][길이8][원본 8×len]        =  9 + 8L 비트
  수식 토큰 : [플래그1][길이8][증가분8]           = 17 비트   (delta=0이면 상수)
  참조 토큰 : [플래그1][길이8][거리16]            = 25 비트   (B안 전용)
"""
import sys, os, zlib

FORMULA_BITS = 17
MATCH_BITS   = 25
MAXLEN       = 255

def arith_runlen(d, i, limit):
    """i에서 시작하는 등차수열의 최대 길이"""
    n = len(d)
    if i + 1 >= n:
        return 1, 0
    delta = (d[i+1] - d[i]) % 256
    j = i + 1
    while j + 1 < n and j - i + 1 < limit and (d[j+1] - d[j]) % 256 == delta:
        j += 1
    return j - i + 1, delta

def compress(data, use_match):
    n = len(data)
    bits = 0
    lit = 0            # 누적 중인 리터럴 바이트 수
    i = 0
    stats = {"formula": 0, "match": 0, "lit_bytes": 0,
             "formula_bytes": 0, "match_bytes": 0}
    table = {}         # 3바이트 해시 -> 위치 목록 (B안)

    def flush():
        nonlocal bits, lit
        while lit > 0:
            chunk = min(lit, MAXLEN)
            bits += 9 + 8 * chunk
            lit -= chunk

    while i < n:
        best_len, best_kind, best_gain = 0, None, 0

        # --- 수식 후보: 등차수열 (delta=0 이면 상수) ---
        flen, _ = arith_runlen(data, i, MAXLEN)
        if flen >= 3:                       # 3바이트 미만이면 손해
            gain = flen * 8 - FORMULA_BITS
            if gain > best_gain:
                best_len, best_kind, best_gain = flen, "formula", gain

        # --- 참조 후보: 앞에 나온 동일 구간 (B안) ---
        if use_match and i + 3 <= n:
            key = data[i:i+3]
            for pos in reversed(table.get(key, ())[-32:]):
                dist = i - pos
                if dist > 65535:
                    break
                L = 0
                while (L < MAXLEN and i + L < n
                       and data[pos + L] == data[i + L]):
                    L += 1
                if L >= 4:
                    gain = L * 8 - MATCH_BITS
                    if gain > best_gain:
                        best_len, best_kind, best_gain = L, "match", gain

        if best_kind:
            flush()
            bits += FORMULA_BITS if best_kind == "formula" else MATCH_BITS
            stats[best_kind] += 1
            stats[best_kind + "_bytes"] += best_len
            step = best_len
        else:
            lit += 1
            stats["lit_bytes"] += 1
            step = 1

        if use_match:
            for k in range(i, min(i + step, n - 2)):
                table.setdefault(data[k:k+3], []).append(k)
        i += step

    flush()
    return (bits + 7) // 8, stats

print(f"{'파일':<24}{'크기':>10}{'A:수식만':>11}{'B:+참조':>11}{'gzip':>10}")
print("-" * 68)

rows = []
for path in sys.argv[1:]:
    try:
        data = open(path, 'rb').read()[:1_000_000]
    except Exception:
        continue
    if len(data) < 4096:
        continue
    a, sa = compress(data, use_match=False)
    b, sb = compress(data, use_match=True)
    g = len(zlib.compress(data, 9))
    name = os.path.basename(path)[:23]
    print(f"{name:<24}{len(data):>10,}{a/len(data)*100:>10.1f}%"
          f"{b/len(data)*100:>10.1f}%{g/len(data)*100:>9.1f}%")
    rows.append((name, len(data), sa, sb))

print()
print("=== A안(수식만) 내역: 수식 토큰이 커버한 바이트 비율 ===")
for name, size, sa, sb in rows:
    cov = sa["formula_bytes"] / size * 100
    print(f"  {name:<24} 수식토큰 {sa['formula']:>7,}개  "
          f"커버 {sa['formula_bytes']:>9,}바이트 ({cov:>5.1f}%)  "
          f"리터럴 {sa['lit_bytes']:>9,}바이트")

print()
print("=== B안: 수식 vs 참조 각각의 기여 ===")
for name, size, sa, sb in rows:
    print(f"  {name:<24} 수식 {sb['formula_bytes']:>9,}바이트  "
          f"참조 {sb['match_bytes']:>9,}바이트  "
          f"리터럴 {sb['lit_bytes']:>9,}바이트")
