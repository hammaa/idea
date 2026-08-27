#!/usr/bin/env python3
"""
왜 "고정 32바이트 청크"가 LZ77에게 지는가 —
실제 데이터에서 한 번의 참조가 몇 바이트를 덮는지 분포를 잰다.

학습셋을 사전처럼 앞에 붙여 놓고, 평가셋의 각 위치에서 가장 긴 과거 매치를 찾는다.
(탐욕 매칭, 4바이트 해시 체인)
"""
import sys
from collections import defaultdict

MINM = 4

def analyze(trainf, testf, label):
    train = open(trainf,'rb').read()
    test  = open(testf,'rb').read()
    buf = train + test
    start = len(train)

    chain = defaultdict(list)
    for i in range(len(buf) - MINM + 1):
        chain[buf[i:i+MINM]].append(i)

    lens, p, covered, nmatch, lits = [], start, 0, 0, 0
    N = len(buf)
    while p < N - MINM:
        best = 0
        for j in chain[buf[p:p+MINM]]:
            if j >= p: break
            l = MINM
            while p + l < N and buf[j+l] == buf[p+l] and l < 100000:
                l += 1
            if l > best: best = l
        if best >= MINM:
            lens.append(best); covered += best; nmatch += 1; p += best
        else:
            lits += 1; p += 1
    lits += N - p

    lens.sort()
    def pct(q): return lens[int(len(lens)*q)] if lens else 0
    over32 = sum(1 for l in lens if l > 32)
    bytes_over = sum(l for l in lens if l > 32)
    print(f"# {label}   평가 {len(test):,}B")
    print(f"  참조 횟수        : {nmatch:,}")
    print(f"  참조가 덮은 바이트: {covered:,}  ({100*covered/len(test):.1f}%)")
    print(f"  리터럴 바이트     : {lits:,}")
    print(f"  매치 길이  평균 {covered/nmatch:.1f}B  중앙값 {pct(0.5)}B  "
          f"p90 {pct(0.9)}B  p99 {pct(0.99)}B  최대 {lens[-1]:,}B")
    print(f"  32바이트를 넘는 매치: {over32:,}건 ({100*over32/nmatch:.1f}%) "
          f"→ 덮은 바이트의 {100*bytes_over/covered:.1f}%")
    print(f"  ※ 고정 32바이트 청크는 이 매치들을 32바이트씩 잘라 써야 한다\n")

analyze('log.train','log.test',   'cloud-init 로그')
analyze('words.train','words.test','영어 단어 목록')
