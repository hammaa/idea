#!/usr/bin/env python3
"""
사전을 키우는 대신 '여러 개로 쪼개서 골라 쓰면' 어떻게 되는가.

같은 총 예산(64KB)을 두고 비교:
  A. 섞인 데이터로 학습한 사전 1개 (64KB)
  B. 종류별 사전 2개 (각 32KB) + 레코드마다 맞는 것 선택
평가는 두 종류가 섞인, 학습에 안 쓴 레코드로만.
"""
import os, shutil, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__)); REC = 400

def recs(src, outdir, tag, limit):
    data = open(src,'rb').read(); n = 0
    for i in range(0, len(data) - REC, REC):
        open(f'{outdir}/{tag}{n:06d}','wb').write(data[i:i+REC]); n += 1
        if n >= limit: break
    return n

def total(files, args):
    od = f'{HERE}/_od'; shutil.rmtree(od, ignore_errors=True); os.makedirs(od)
    subprocess.run(['zstd','-19','-q','--output-dir-flat',od]+args+files,
                   capture_output=True)
    s = sum(os.path.getsize(f) for f in glob.glob(f'{od}/*'))
    shutil.rmtree(od, ignore_errors=True); return s

def train(files, out, md):
    subprocess.run(['zstd','--train']+files+['-o',out,f'--maxdict={md}'],
                   capture_output=True)
    return os.path.getsize(out) if os.path.exists(out) else 0

for d in ('_tr','_te'): shutil.rmtree(f'{HERE}/{d}', ignore_errors=True); os.makedirs(f'{HERE}/{d}')
LIM = 180
recs('log.train',  f'{HERE}/_tr','L',LIM); recs('words.train',f'{HERE}/_tr','W',LIM)
recs('log.test',   f'{HERE}/_te','L',LIM); recs('words.test', f'{HERE}/_te','W',LIM)

te   = sorted(glob.glob(f'{HERE}/_te/*'))
teL  = sorted(glob.glob(f'{HERE}/_te/L*')); teW = sorted(glob.glob(f'{HERE}/_te/W*'))
trAll= sorted(glob.glob(f'{HERE}/_tr/*'))
trL  = sorted(glob.glob(f'{HERE}/_tr/L*')); trW = sorted(glob.glob(f'{HERE}/_tr/W*'))
raw  = sum(os.path.getsize(f) for f in te)

sA = train(trAll, f'{HERE}/_dA', 65536)
sL = train(trL,   f'{HERE}/_dL', 32768)
sW = train(trW,   f'{HERE}/_dW', 32768)

base = total(te, [])
A    = total(te, ['-D', f'{HERE}/_dA'])
B    = total(teL,['-D', f'{HERE}/_dL']) + total(teW,['-D', f'{HERE}/_dW'])

print(f"평가: 로그 {len(teL)}건 + 단어 {len(teW)}건 = {raw:,}B (학습과 완전 분리)\n")
print(f"{'방식':<34} {'사전':>10} {'압축본':>10} {'원본대비':>9} {'사전포함':>9}")
print("-"*76)
print(f"{'사전 없음':<32} {'—':>10} {base:>9,}B {100*base/raw:>8.1f}% {100*base/raw:>8.1f}%")
print(f"{'A. 섞어서 학습한 큰 사전 1개':<24} {sA:>9,}B {A:>9,}B {100*A/raw:>8.1f}% {100*(A+sA)/raw:>8.1f}%")
print(f"{'B. 종류별 작은 사전 2개 + 선택':<23} {sL+sW:>9,}B {B:>9,}B {100*B/raw:>8.1f}% {100*(B+sL+sW)/raw:>8.1f}%")
print(f"\nB가 A 대비 압축본 {100*(A-B)/A:.1f}% 더 작음 (같은 64KB 예산, 선택 비트는 사전 ID 몇 바이트)")
for f in ('_dA','_dL','_dW'): os.path.exists(f'{HERE}/{f}') and os.remove(f'{HERE}/{f}')
shutil.rmtree(f'{HERE}/_tr', ignore_errors=True); shutil.rmtree(f'{HERE}/_te', ignore_errors=True)
