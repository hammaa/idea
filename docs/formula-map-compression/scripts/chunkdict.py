#!/usr/bin/env python3
"""
"4바이트 인덱스면 21억 개 사전 엔트리" — 원안을 그대로 구현해 사전 크기를 스윕한다.

원안: 고정 길이 청크(16B/32B)를 아주 많이 사전에 담고, 인덱스 번호 하나로 대체한다.
측정: 사전 엔트리 수 N을 2^8 ~ 2^20 까지 늘려가며
      (1) 적중률  (2) 압축 결과  (3) 인덱스 사용 분포의 엔트로피 H
사전은 학습셋에서만 뽑고, 평가는 학습에 쓰지 않은 데이터로만 한다.

인코딩은 원안에 최대한 유리하게:
  - 적중  : 플래그 1비트 + 인덱스
  - 미적중: 리터럴 "런" 하나당 헤더 9비트 + 바이트당 8비트 (바이트마다 플래그를 물리지 않음)

실행: PYTHONHASHSEED=0 python3 chunkdict.py <train> <test> "<라벨>"
"""
import sys, math, os, gzip, subprocess
from collections import Counter

CHUNK_SIZES = [16, 32]
DICT_SIZES  = [2**k for k in (8, 10, 12, 14, 16, 18, 20)]

def encode(test, table, CH, idx_bits):
    """탐욕 매칭. (적중 수, 리터럴 바이트 수, 리터럴 런 수, 인덱스 사용 분포)"""
    use = Counter()
    p, matched, lit_bytes, runs = 0, 0, 0, 0
    in_run = False
    L = len(test)
    while p <= L - CH:
        j = table.get(hash(test[p:p+CH]))
        if j is not None:
            use[j] += 1; matched += 1; p += CH; in_run = False
        else:
            lit_bytes += 1; p += 1
            if not in_run: runs += 1; in_run = True
    if p < L:
        lit_bytes += L - p
        if not in_run: runs += 1
    return matched, lit_bytes, runs, use

def report(train, test, label):
    L = len(test)
    gz = len(gzip.compress(test, 9))
    zs = int(subprocess.run(['zstd','-19','-c'], input=test,
                            capture_output=True).stdout.__len__())
    print(f"# 코퍼스: {label}   학습 {len(train):,}B / 평가 {len(test):,}B")
    print(f"#   기준선  gzip -9 {100*gz/L:.1f}%   zstd -19 {100*zs/L:.1f}%   (사전 없이)\n")

    for CH in CHUNK_SIZES:
        cnt = Counter()
        for i in range(0, len(train) - CH):
            cnt[hash(train[i:i+CH])] += 1
        distinct = len(cnt)
        ranked = [h for h, _ in cnt.most_common(max(DICT_SIZES))]
        del cnt

        # 자기검증: 학습셋 자신을 압축하면 적중률이 높아야 한다 (구현이 맞는지 확인)
        selftab = {h: i for i, h in enumerate(ranked[:65536])}
        sm, _, _, _ = encode(train, selftab, CH, 16)
        print(f"## 청크 {CH}바이트   학습셋 내 서로 다른 청크 {distinct:,}개")
        print(f"   [자기검증] 사전 65,536개로 *학습셋 자신*을 덮으면 적중 {100*sm*CH/len(train):.1f}%")
        print(f"{'사전엔트리':>11} {'사전크기':>12} {'인덱스':>6} {'적중바이트':>10} "
              f"{'고정인덱스':>10} {'엔트로피':>9} {'실효H':>7} {'상위4096%':>9}")
        print("-" * 92)

        for N in DICT_SIZES:
            table = {h: i for i, h in enumerate(ranked[:N])}
            idx_bits = math.ceil(math.log2(N))
            matched, lit_bytes, runs, use = encode(test, table, CH, idx_bits)

            fixed = matched * (1 + idx_bits) + runs * 9 + lit_bytes * 8
            tot = sum(use.values())
            H = -sum((c/tot)*math.log2(c/tot) for c in use.values()) if tot else 0.0
            ent = matched * (1 + H) + runs * 9 + lit_bytes * 8
            top = sum(c for _, c in use.most_common(4096))
            print(f"{N:>11,} {N*CH:>11,}B {idx_bits:>5}b {100*matched*CH/L:>9.1f}% "
                  f"{100*(fixed/8)/L:>9.1f}% {100*(ent/8)/L:>8.1f}% "
                  f"{H:>6.1f}b {100*top/tot if tot else 0:>8.1f}%")
        print()

report(open(sys.argv[1],'rb').read(), open(sys.argv[2],'rb').read(),
       sys.argv[3] if len(sys.argv) > 3 else sys.argv[1])
