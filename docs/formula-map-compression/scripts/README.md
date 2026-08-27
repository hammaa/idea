# 측정 스크립트

이 디렉토리의 스크립트가 상위 문서들의 **모든 수치의 근거**다. 전부 재현 가능하다.

| 스크립트 | 문서 | 측정 내용 |
|---|---|---|
| `blockscan.py` | [03](../03-실측-수식맵-검증.md) | 256바이트 블록 중 단순 수식으로 표현 가능한 비율 |
| `polyfit.py` | [04](../04-수식은-항상-존재한다.md) | 임의 256바이트를 지나는 다항식 구성 + 계수 저장 비용 |
| `runscan.py` | [05](../05-수식-하나가-10바이트.md) | 길이 10 이상 상수·등차 구간이 전체의 몇 % |
| `varlen.py` | [06](../06-가변길이-실제구현.md) | 가변 길이 수식 매칭 압축기 구현 (A: 수식만 / B: +참조) |
| `dicttest.py` | [07](../07-학습사전-실측.md) | `zstd --train` 학습 사전 효과 |
| `speedtest.py` | [08](../08-해제속도-실측.md) | 압축 레벨·사전 크기별 압축/해제 속도 |
| `dictinspect.py` | [09](../09-사전의-내부구조.md) | 사전 바이너리 해부 + 실제 매칭 시연 |
| `honest.py` | [10](../10-사전은-어디서-오나.md) | 사전 출처·비용을 포함한 정직한 회계, 손익분기 |
| `prep.py` | [11](../11-거대한-사전.md) | 코퍼스 준비 — 학습셋/평가셋 분리 (시드 20260827 고정) |
| `chunkdict.py` | [11](../11-거대한-사전.md) | 고정 청크 사전을 2^8~2^20 엔트리로 스윕 (적중률·인덱스 엔트로피) |
| `maxdict.py` | [11](../11-거대한-사전.md) | `zstd --maxdict` 1KB→16MB 스윕 (실제 도구의 포화 지점) |
| `matchlen.py` | [11](../11-거대한-사전.md) | LZ77 매치 길이 분포 — 고정 32바이트가 왜 지는가 |
| `specialize.py` | [11](../11-거대한-사전.md) | 같은 예산: 큰 사전 1개 vs 좁은 사전 여러 개 |

## 실행

```bash
python3 blockscan.py <파일...>      # 인자로 대상 파일 지정
python3 runscan.py <파일...>
python3 varlen.py <파일...>
python3 polyfit.py                  # 대상 경로가 코드에 고정
python3 dicttest.py                 # zstd 필요
python3 speedtest.py                # zstd 필요
python3 dictinspect.py              # zstd 필요
python3 honest.py                   # zstd 필요

# 11번 (아래 순서대로)
python3 prep.py                     # 먼저 실행 — 코퍼스 생성
PYTHONHASHSEED=0 python3 chunkdict.py log.train log.test "로그"
python3 maxdict.py                  # zstd 필요, 수 분 소요
python3 matchlen.py
python3 specialize.py               # zstd 필요
```

`chunkdict.py`는 청크 해시 재현성을 위해 **`PYTHONHASHSEED=0`으로 실행해야 한다.**
`prep.py`가 만든 `words.train/test`, `log.train/test`, `bin.train/test`를 나머지가 사용한다.

측정 환경: idea-aws (Amazon Linux 2023, t4g.small / ARM aarch64 2 vCPU), Python 3.9.
샘플 데이터는 시스템 파일(`/usr/share/dict/words`, `/var/log/cloud-init.log`, `/usr/bin/*`)을 사용하므로
**다른 환경에서는 수치가 달라진다.** 경향은 동일하다.
