#!/usr/bin/env python3
"""사전 크기 / 압축 레벨이 '해제 속도'에 영향을 주는가?"""
import os, subprocess, tempfile, shutil, time, statistics

WORK = tempfile.mkdtemp(prefix='speed_')
DEVNULL = subprocess.DEVNULL
def run(cmd, **kw):
    kw.setdefault('stdout', DEVNULL)
    kw.setdefault('stderr', DEVNULL)
    return subprocess.run(cmd, **kw)

def timeit(fn, n=5):
    ts = []
    for _ in range(n):
        t = time.perf_counter(); fn(); ts.append(time.perf_counter() - t)
    return min(ts)          # 최소값 = 노이즈 최소

# ─────────────────────────────────────────────────────────
# 실험 A. 압축 레벨 vs 압축/해제 시간 (큰 파일 하나)
# ─────────────────────────────────────────────────────────
big = os.path.join(WORK, 'big.bin')
data = open('/usr/share/dict/words','rb').read()
open(big,'wb').write(data)
size = len(data)

print("=== 실험 A. 압축 레벨을 올리면 해제도 느려지는가? ===")
print(f"대상: words {size:,} 바이트\n")
print(f"{'레벨':<8}{'압축크기':>12}{'압축시간':>11}{'해제시간':>11}"
      f"{'압축속도':>12}{'해제속도':>12}")
print("-" * 68)

for lvl in [1, 9, 19]:
    out = os.path.join(WORK, f'l{lvl}.zst')
    ct = timeit(lambda: run(['zstd', f'-{lvl}', '-q', '-f', big, '-o', out]), n=3)
    csize = os.path.getsize(out)
    dt = timeit(lambda: run(['zstd', '-d', '-c', '-q', out]))
    print(f"-{lvl:<7}{csize:>12,}{ct*1000:>10.0f}ms{dt*1000:>10.0f}ms"
          f"{size/ct/1e6:>10.0f}MB/s{size/dt/1e6:>10.0f}MB/s")

# ─────────────────────────────────────────────────────────
# 실험 B. 사전 크기 vs 해제 시간 (작은 레코드 다수)
# ─────────────────────────────────────────────────────────
REC = os.path.join(WORK, 'rec'); os.makedirs(REC)
lines = open('/var/log/cloud-init.log','rb').read().split(b'\n')
recs, buf = [], b''
for ln in lines:
    buf += ln + b'\n'
    if len(buf) >= 400: recs.append(buf); buf = b''
recs = recs * 12                                  # 타이밍 안정용으로 복제
for i, r in enumerate(recs):
    open(os.path.join(REC, f'r{i:05d}.bin'),'wb').write(r)
files = sorted(os.listdir(REC))
half = len(files)//2
train = [os.path.join(REC,f) for f in files[:half]]
test  = [os.path.join(REC,f) for f in files[half:]]
raw = sum(os.path.getsize(f) for f in test)

print(f"\n\n=== 실험 B. 사전이 커지면 해제가 느려지는가? ===")
print(f"대상: {len(test):,}개 레코드, 합계 {raw:,} 바이트 (평균 {raw//len(test)} 바이트)\n")
print(f"{'사전 크기':<16}{'압축 결과':>12}{'원본대비':>10}{'해제시간':>11}{'해제속도':>12}")
print("-" * 63)

def bench(dict_path, label):
    outdir = os.path.join(WORK, 'out_' + label.replace(' ','_'))
    os.makedirs(outdir, exist_ok=True)
    args = ['-D', dict_path] if dict_path else []
    outs = []
    for f in test:
        o = os.path.join(outdir, os.path.basename(f) + '.zst')
        run(['zstd','-19','-q','-f'] + args + [f, '-o', o]); outs.append(o)
    tot = sum(os.path.getsize(o) for o in outs)
    dt = timeit(lambda: run(['zstd','-d','-c','-q'] + args + outs,
                            stdout=subprocess.DEVNULL))
    print(f"{label:<16}{tot:>12,}{tot/raw*100:>9.1f}%{dt*1000:>10.0f}ms"
          f"{raw/dt/1e6:>10.1f}MB/s")

bench(None, "사전 없음")
for kb in [4, 32, 110]:
    dp = os.path.join(WORK, f'd{kb}.dict')
    r = run(['zstd','--train'] + train + ['-o', dp, f'--maxdict={kb*1024}','-q'])
    if os.path.exists(dp):
        bench(dp, f"{os.path.getsize(dp)//1024}KB 사전")

shutil.rmtree(WORK, ignore_errors=True)
