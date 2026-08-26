#!/usr/bin/env python3
"""학습된 사전을 열어서 '바이트 패턴이 실제로 어떻게 생겼는지' 보여준다."""
import os, subprocess, tempfile, shutil, struct

WORK = tempfile.mkdtemp(prefix='inspect_')
REC = os.path.join(WORK, 'rec'); os.makedirs(REC)
def run(c, **k): return subprocess.run(c, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, **k)

# 로그를 레코드로 쪼개 사전 학습
lines = open('/var/log/cloud-init.log','rb').read().split(b'\n')
recs, buf = [], b''
for ln in lines:
    buf += ln + b'\n'
    if len(buf) >= 400: recs.append(buf); buf = b''
for i, r in enumerate(recs):
    open(os.path.join(REC, f'r{i:05d}.bin'),'wb').write(r)
files = sorted(os.listdir(REC))
train = [os.path.join(REC,f) for f in files[:len(files)//2]]
test_file = os.path.join(REC, files[-1])

dp = os.path.join(WORK,'t.dict')
run(['zstd','--train'] + train + ['-o', dp, '--maxdict=32768','-q'])
raw = open(dp,'rb').read()

# ── 1. 사전 파일의 구조 ──────────────────────────────────
magic, dict_id = struct.unpack('<II', raw[:8])
print("=" * 74)
print("1. 사전 파일의 구조")
print("=" * 74)
print(f"  전체 크기      : {len(raw):,} 바이트")
print(f"  매직 넘버      : 0x{magic:08X}  (zstd 사전 표식)")
print(f"  사전 ID        : {dict_id}  (압축본이 '어느 사전인지' 가리키는 번호)")
print(f"  앞부분         : 엔트로피 테이블(허프만/FSE) + 반복 오프셋 힌트")
print(f"  나머지 전부    : ★ 그냥 '바이트 덩어리' — 이게 패턴 본체")

# 사전 콘텐츠(뒷부분)를 대략 잡는다: 인쇄가능 문자가 길게 이어지는 첫 지점부터
content_start = 0
for i in range(len(raw) - 64):
    win = raw[i:i+64]
    if sum(32 <= b < 127 for b in win) >= 60:
        content_start = i; break
content = raw[content_start:]

print(f"\n  → 패턴 본체 시작 위치: 약 {content_start:,} 바이트 지점"
      f" (이후 {len(content):,} 바이트)")

# ── 2. 사전 안에 실제로 뭐가 들어있나 ────────────────────
print("\n" + "=" * 74)
print("2. 사전 안의 내용 (사람이 읽을 수 있게 출력)")
print("=" * 74)
sample = content[:600]
txt = ''.join(chr(b) if 32 <= b < 127 else ('⏎' if b==10 else '·') for b in sample)
for i in range(0, len(txt), 96):
    print("  " + txt[i:i+96])
print("\n  → 표도, 목록도, 구분자도 없다. 조각들이 그냥 이어붙어 있다.")

# ── 3. 실제 매칭 시연 ────────────────────────────────────
print("\n" + "=" * 74)
print("3. 실제 매칭 — 처음 보는 레코드를 사전에 맞춰본다")
print("=" * 74)
rec = open(test_file,'rb').read()
print(f"  대상 레코드: {os.path.basename(test_file)} ({len(rec)} 바이트, 학습에 미사용)\n")

i, matched, segs = 0, 0, []
while i < len(rec):
    best_len, best_pos = 0, -1
    maxtry = min(120, len(rec) - i)
    for L in range(maxtry, 3, -1):           # 긴 것부터 시도
        pos = content.find(rec[i:i+L])
        if pos >= 0:
            best_len, best_pos = L, pos; break
    if best_len >= 4:
        segs.append((rec[i:i+best_len], best_pos, best_len))
        matched += best_len; i += best_len
    else:
        segs.append((rec[i:i+1], None, 1)); i += 1

shown = 0
for seg, pos, L in segs:
    if pos is None: continue
    disp = ''.join(chr(b) if 32<=b<127 else ('⏎' if b==10 else '·') for b in seg)
    print(f"  {L:>3}바이트  사전 {pos:>6}번 위치  │ {disp[:62]}")
    shown += 1
    if shown >= 14: print("  ... (이하 생략)"); break

lit = sum(1 for s,p,l in segs if p is None)
print(f"\n  매칭된 바이트  : {matched}/{len(rec)} ({matched/len(rec)*100:.1f}%)")
print(f"  매칭 토큰 수   : {sum(1 for s,p,l in segs if p is not None)}개")
print(f"  못 맞춘 바이트 : {lit}개 (원본 그대로 전송)")

shutil.rmtree(WORK, ignore_errors=True)
