#!/usr/bin/env python3
"""'10만 개 수식 맵'의 현실판 = 데이터에서 학습한 사전.
   작은 레코드 수천 개에 대해 사전 유무를 비교한다."""
import os, subprocess, shutil, tempfile, random

SRC = '/var/log/cloud-init.log'
WORK = tempfile.mkdtemp(prefix='dicttest_')
REC = os.path.join(WORK, 'records')
os.makedirs(REC)

# 1) 로그를 작은 레코드(파일)로 쪼갠다 — 실제 서비스의 로그 한 줄/JSON 응답 한 건에 해당
lines = open(SRC, 'rb').read().split(b'\n')
records, buf = [], b''
for ln in lines:
    buf += ln + b'\n'
    if len(buf) >= 400:
        records.append(buf); buf = b''
if buf:
    records.append(buf)

for i, r in enumerate(records):
    open(os.path.join(REC, f'r{i:05d}.bin'), 'wb').write(r)

files = sorted(os.listdir(REC))
random.seed(42)
train_set = random.sample(files, len(files) // 2)      # 절반으로 학습
test_set  = [f for f in files if f not in set(train_set)]  # 나머지로 평가

total_raw = sum(os.path.getsize(os.path.join(REC, f)) for f in test_set)
print(f"레코드 총 {len(files)}개 (학습 {len(train_set)} / 평가 {len(test_set)})")
print(f"평가셋 원본 크기 : {total_raw:,} 바이트")
print(f"레코드 평균 크기 : {total_raw//len(test_set):,} 바이트\n")

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)

# 2) 사전 학습  ← '10만 개 수식'을 데이터에서 뽑아내는 단계
dict_path = os.path.join(WORK, 'trained.dict')
r = run(['zstd', '--train'] + [os.path.join(REC, f) for f in train_set]
        + ['-o', dict_path, '--maxdict=110000', '-q'])
dict_size = os.path.getsize(dict_path) if os.path.exists(dict_path) else 0
print(f"학습된 사전 크기 : {dict_size:,} 바이트  (양쪽이 미리 공유 → 전송량 미포함)\n")

# 3) 개별 압축 비교
def total_size(args):
    tot = 0
    for f in test_set:
        p = os.path.join(REC, f)
        out = run(['zstd', '-19', '-c', '-q'] + args, stdin=open(p, 'rb'))
        tot += len(out.stdout)
    return tot

no_dict   = total_size([])
with_dict = total_size(['-D', dict_path])

# gzip 개별 압축도 비교
gz = 0
for f in test_set:
    p = os.path.join(REC, f)
    out = run(['gzip', '-9c'], stdin=open(p, 'rb'))
    gz += len(out.stdout)

print(f"{'방식':<34}{'크기':>12}{'원본대비':>10}")
print("-" * 58)
print(f"{'원본 (무압축)':<34}{total_raw:>12,}{'100.0%':>10}")
print(f"{'gzip -9 (개별)':<34}{gz:>12,}{gz/total_raw*100:>9.1f}%")
print(f"{'zstd -19 사전없이 (개별)':<34}{no_dict:>12,}{no_dict/total_raw*100:>9.1f}%")
print(f"{'zstd -19 + 학습사전 (개별)':<34}{with_dict:>12,}{with_dict/total_raw*100:>9.1f}%")
print()
print(f"=> 사전 도입 효과: {no_dict:,} -> {with_dict:,} 바이트 "
      f"({(1-with_dict/no_dict)*100:.1f}% 추가 절감)")
print(f"=> gzip 대비     : {(1-with_dict/gz)*100:.1f}% 더 작음")

shutil.rmtree(WORK, ignore_errors=True)
