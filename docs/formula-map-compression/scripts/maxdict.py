#!/usr/bin/env python3
"""
실제 도구로 같은 질문을 묻는다: 사전을 계속 키우면 계속 좋아지는가?

zstd --train 의 --maxdict 을 1KB → 16MB 까지 스윕하고,
학습에 쓰지 않은 레코드로만 압축률을 잰다.
(zstd 를 파일마다 부르지 않고 한 번에 여러 파일을 넘겨 속도를 확보)
"""
import os, shutil, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REC  = 400
MAXDICTS = [1024, 4096, 16384, 32768, 65536, 112640, 262144,
            1048576, 4194304, 16777216]

def make_records(src, outdir, limit=None):
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    data = open(src,'rb').read(); n = 0
    for i in range(0, len(data) - REC, REC):
        open(f'{outdir}/{n:06d}','wb').write(data[i:i+REC]); n += 1
        if limit and n >= limit: break
    return n

def total(files, outdir, args):
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    subprocess.run(['zstd','-19','-q','--output-dir-flat',outdir] + args + files,
                   capture_output=True)
    s = sum(os.path.getsize(f) for f in glob.glob(f'{outdir}/*'))
    shutil.rmtree(outdir, ignore_errors=True)
    return s

def run(label, trainsrc, testsrc, lim=1500):
    tr, te, od = f'{HERE}/_tr', f'{HERE}/_te', f'{HERE}/_od'
    ntr = make_records(trainsrc, tr, lim)
    nte = make_records(testsrc,  te, lim)
    tests = sorted(glob.glob(f'{te}/*'))
    trains = sorted(glob.glob(f'{tr}/*'))
    raw = sum(os.path.getsize(f) for f in tests)
    base = total(tests, od, [])

    print(f"# {label}")
    print(f"#   학습 {ntr:,}건 / 평가 {nte:,}건 = {raw:,}B  (완전 분리)")
    print(f"#   사전 없이 zstd -19 : {base:,}B  ({100*base/raw:.1f}%)\n")
    print(f"{'요청 maxdict':>13} {'실제 사전':>11} {'압축본':>11} {'원본대비':>9} "
          f"{'사전포함':>9} {'레코드당':>9}")
    print("-" * 74)

    prev = None
    for md in MAXDICTS:
        d = f'{HERE}/_d{md}'
        subprocess.run(['zstd','--train'] + trains + ['-o', d, f'--maxdict={md}'],
                       capture_output=True)
        if not os.path.exists(d):
            print(f"{md:>12,}B   ← 학습 실패 (샘플에서 뽑아낼 내용이 부족)")
            continue
        actual = os.path.getsize(d)
        c = total(tests, od, ['-D', d])
        mark = "  ⚠️ 더 나빠짐" if (prev is not None and c > prev) else ""
        prev = c
        print(f"{md:>12,}B {actual:>10,}B {c:>10,}B {100*c/raw:>8.1f}% "
              f"{100*(c+actual)/raw:>8.1f}% {c/nte:>8.1f}B{mark}")
        os.remove(d)
    print()
    shutil.rmtree(tr, ignore_errors=True); shutil.rmtree(te, ignore_errors=True)

run("cloud-init 로그 레코드 (400B)", f'{HERE}/log.train', f'{HERE}/log.test')
run("영어 단어 목록 레코드 (400B)", f'{HERE}/words.train', f'{HERE}/words.test')
