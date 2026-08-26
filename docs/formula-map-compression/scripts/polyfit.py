#!/usr/bin/env python3
"""임의의 256바이트를 통과하는 '수식'(다항식)은 항상 존재한다.
   그런데 그 수식을 적어두는 비용이 원본보다 크다는 것을 실증한다."""

P = 257  # 소수 (바이트값 0..255를 모두 담으려면 256보다 커야 함)

def newton_coeffs(y):
    """x=0,1,2,...,n-1 을 지나는 다항식의 뉴턴 계수 (mod P)"""
    n = len(y)
    c = list(y)
    for j in range(1, n):
        for i in range(n - 1, j - 1, -1):
            c[i] = (c[i] - c[i-1]) * pow(j, P-2, P) % P
    return c

def evaluate(c, x):
    """뉴턴 형식 다항식 평가"""
    acc, term = 0, 1
    for i, ci in enumerate(c):
        acc = (acc + ci * term) % P
        term = term * (x - i) % P
    return acc

# 실제 파일에서 256바이트 블록 하나를 가져온다
data = open('/usr/share/dict/words', 'rb').read()[4096:4096+256]
print(f"원본 블록 : {len(data)}바이트")
print(f"내용 미리보기: {data[:40]!r}")

coeffs = newton_coeffs(list(data))

# 검증: 정말 모든 점을 통과하는가
ok = all(evaluate(coeffs, x) == data[x] for x in range(256))
print(f"\n수식이 256바이트를 전부 재현하는가? -> {ok}")

# 수식을 적어두는 비용
nonzero = sum(1 for c in coeffs if c != 0)
bits_per_coeff = 9          # 0..256 을 담으려면 9비트 필요
cost_bits = len(coeffs) * bits_per_coeff
print(f"\n--- 비용 계산 ---")
print(f"계수 개수        : {len(coeffs)}개 (0이 아닌 계수 {nonzero}개)")
print(f"계수 1개당 필요  : {bits_per_coeff}비트 (값 범위 0~256)")
print(f"수식 저장 비용   : {cost_bits}비트 = {cost_bits/8:.0f}바이트")
print(f"원본 크기        : {len(data)*8}비트 = {len(data)}바이트")
print(f"\n=> 수식이 원본보다 {cost_bits/8 - len(data):.0f}바이트 더 크다 "
      f"({cost_bits/(len(data)*8)*100:.1f}%)")
