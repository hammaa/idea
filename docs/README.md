# 아이디어 목록

이 문서는 `docs/` 디렉토리 내 아이디어 목록을 관리합니다.
아이디어 하나당 `docs/<아이디어-이름>/` 디렉토리를 생성하고,
개요(README), 기획, 설계, 시장분석, 수익 구조 및 수익 방법, 매출 예측 문서를 정리합니다.

## 목록

| 아이디어 | 디렉토리 | 상태 | 비고 |
|---|---|---|---|
| 프롬프트 팩 (Prompt Pack) | [prompt-pack/](prompt-pack/) | 아이디어 (검증 전) | 미리 만든 프롬프트 체인 + HTML 산출물 서비스. 고정 마감에서 역산하는 "제약 역산 엔진"으로 재정의 |
| 수식 맵 압축 (Formula Map Compression) | [formula-map-compression/](formula-map-compression/) | ❌ 원안 기각 / ✅ 올바른 형태 실측 완료 | 수식 맵 번호로 많은 바이트를 대체하는 압축. 범용 무손실은 수학적 불가능(개수 세기)이나, 맵을 데이터에서 학습시키면 성립 — `zstd --train`으로 gzip 대비 69.3% 절감 실측 (문서 10개) |

## 문서 규모

| 아이디어 | 문서 수 | 최근 갱신 |
|---|:-:|---|
| prompt-pack | 7 | 2026-08-26 |
| formula-map-compression | 11 + 측정 스크립트 8 | 2026-08-26 |

> 일자별 진행 내역은 [dev-docs/changelog/](../dev-docs/changelog/) 참조.
