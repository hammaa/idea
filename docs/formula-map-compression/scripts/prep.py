#!/usr/bin/env python3
"""코퍼스 준비: 학습셋/평가셋을 완전히 분리한다 (셔플 후 분할)."""
import random, os, sys

random.seed(20260827)          # 재현 가능하게 고정

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- 코퍼스 1: 영어 단어 목록 (텍스트, 4.9MB) ----
words = open('/usr/share/dict/linux.words','rb').read().split(b'\n')
random.shuffle(words)
half = len(words)//2
open(f'{OUT}/words.train','wb').write(b'\n'.join(words[:half]))
open(f'{OUT}/words.test','wb').write(b'\n'.join(words[half:]))

# ---- 코퍼스 2: cloud-init 로그를 레코드로 분할 (07번과 동일 계열) ----
log = open('/var/log/cloud-init.log','rb').read()
lines = log.split(b'\n')
# 8줄씩 묶어 한 "레코드"로 (한 건씩 전송되는 상황을 모사)
recs = [b'\n'.join(lines[i:i+8]) for i in range(0, len(lines), 8)]
recs = [r for r in recs if len(r) > 50]
random.shuffle(recs)
h = len(recs)//2
os.makedirs(f'{OUT}/rec_train', exist_ok=True)
os.makedirs(f'{OUT}/rec_test',  exist_ok=True)
for i,r in enumerate(recs[:h]): open(f'{OUT}/rec_train/{i:05d}','wb').write(r)
for i,r in enumerate(recs[h:]): open(f'{OUT}/rec_test/{i:05d}','wb').write(r)

print(f"words.train {os.path.getsize(f'{OUT}/words.train'):>9,} B")
print(f"words.test  {os.path.getsize(f'{OUT}/words.test'):>9,} B")
print(f"rec_train   {len(recs[:h]):>5} 건  {sum(len(r) for r in recs[:h]):>9,} B")
print(f"rec_test    {len(recs[h:]):>5} 건  {sum(len(r) for r in recs[h:]):>9,} B")

# ---- 코퍼스 3: 로그 (반복이 많은 데이터 = 원안에 가장 유리한 조건) ----
loglines = open('/var/log/cloud-init.log','rb').read().split(b'\n')
random.shuffle(loglines)
h2 = len(loglines)//2
open(f'{OUT}/log.train','wb').write(b'\n'.join(loglines[:h2]))
open(f'{OUT}/log.test','wb').write(b'\n'.join(loglines[h2:]))
print(f"log.train   {os.path.getsize(f'{OUT}/log.train'):>9,} B")
print(f"log.test    {os.path.getsize(f'{OUT}/log.test'):>9,} B")

# ---- 코퍼스 4: 바이너리 (libc 앞뒤 절반) ----
lib = open('/usr/lib64/libc.so.6','rb').read()
open(f'{OUT}/bin.train','wb').write(lib[:len(lib)//2])
open(f'{OUT}/bin.test','wb').write(lib[len(lib)//2:])
print(f"bin.train   {os.path.getsize(f'{OUT}/bin.train'):>9,} B")
print(f"bin.test    {os.path.getsize(f'{OUT}/bin.test'):>9,} B")
