#!/usr/bin/env python3
"""사전을 어디서 뽑느냐 / 사전 크기를 계산에 넣느냐 — 정직한 비교."""
import os, subprocess, tempfile, shutil, random

WORK = tempfile.mkdtemp(prefix='honest_')
REC = os.path.join(WORK,'rec'); os.makedirs(REC)
def run(c, **k): return subprocess.run(c, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, **k)

lines = open('/var/log/cloud-init.log','rb').read().split(b'\n')
recs, buf = [], b''
for ln in lines:
    buf += ln + b'\n'
    if len(buf) >= 400: recs.append(buf); buf = b''
recs = recs * 6
for i,r in enumerate(recs):
    open(os.path.join(REC,f'r{i:05d}.bin'),'wb').write(r)

files = sorted(os.listdir(REC))
random.seed(7); random.shuffle(files)
half = len(files)//2
train = [os.path.join(REC,f) for f in files[:half]]      # 학습 전용
test  = [os.path.join(REC,f) for f in files[half:]]      # 평가 전용 (학습 미사용)
raw = sum(os.path.getsize(f) for f in test)

def csize(paths, dict_path=None):
    args = ['-D', dict_path] if dict_path else []
    return sum(len(run(['zstd','-19','-c','-q']+args, stdin=open(p,'rb')).stdout)
               for p in paths)

def train_dict(samples, name, kb=32):
    dp = os.path.join(WORK, name)
    run(['zstd','--train']+samples+['-o',dp,f'--maxdict={kb*1024}','-q'])
    return dp, (os.path.getsize(dp) if os.path.exists(dp) else 0)

print(f"평가셋: {len(test)}개 레코드, {raw:,} 바이트 (평균 {raw//len(test)}B)\n")

d_other, sz_other = train_dict(train, 'other.dict')     # ① 다른 샘플로 학습
d_self,  sz_self  = train_dict(test,  'self.dict')      # ② 압축 대상 자신으로 학습

no_dict   = csize(test)
with_othr = csize(test, d_other)
with_self = csize(test, d_self)

print("=" * 76)
print("A. 사전을 어디서 뽑았나 — 그리고 사전 크기를 계산에 넣으면?")
print("=" * 76)
print(f"{'방식':<40}{'압축본':>11}{'+사전':>11}{'원본대비':>10}")
print("-" * 76)
print(f"{'사전 없음':<40}{no_dict:>11,}{'—':>11}{no_dict/raw*100:>9.1f}%")
print(f"{'① 다른 샘플로 학습 (사전 미포함)':<40}{with_othr:>11,}{'—':>11}"
      f"{with_othr/raw*100:>9.1f}%")
print(f"{'① 다른 샘플로 학습 (사전 1회 포함)':<40}{with_othr:>11,}"
      f"{with_othr+sz_other:>11,}{(with_othr+sz_other)/raw*100:>9.1f}%")
print(f"{'② 대상 자신으로 학습 (사전 반드시 동봉)':<40}{with_self:>11,}"
      f"{with_self+sz_self:>11,}{(with_self+sz_self)/raw*100:>9.1f}%")
print(f"\n  사전 크기: 다른샘플 {sz_other:,}B / 자기자신 {sz_self:,}B")

print("\n" + "=" * 76)
print("B. 사전 비용을 몇 건에 나눠 쓰느냐 — 손익분기")
print("=" * 76)
per_nodict = no_dict / len(test)
per_dict   = with_othr / len(test)
save = per_nodict - per_dict
be = sz_other / save
print(f"  레코드당 사전없음 : {per_nodict:>7.1f} 바이트")
print(f"  레코드당 사전사용 : {per_dict:>7.1f} 바이트")
print(f"  레코드당 절약     : {save:>7.1f} 바이트")
print(f"  사전 크기         : {sz_other:>7,} 바이트")
print(f"  => 손익분기       : 약 {be:.0f}건\n")

print(f"{'압축 건수':>10}{'사전없음':>12}{'사전+압축본':>14}{'유불리':>10}")
print("-" * 48)
for n in [10, 50, 100, int(be), 500, 2000, 10000]:
    a = per_nodict * n
    b = per_dict * n + sz_other
    print(f"{n:>10,}{a:>12,.0f}{b:>14,.0f}{('✅ 이득' if b<a else '❌ 손해'):>12}")

shutil.rmtree(WORK, ignore_errors=True)
