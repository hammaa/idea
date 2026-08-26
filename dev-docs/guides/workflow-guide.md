# 작업 흐름 가이드 (런북)

> trader 레포(`dev-docs/guides/workflow-guide.md`, 별도 로컬 저장소)의 작업 흐름 규칙을 이 레포(아이디어 트래커)에 맞게 가져온 문서.
> [CLAUDE.md](../../CLAUDE.md) "Standing rules"가 이 문서를 요약한 것이므로, 둘이 어긋나면 이 문서가 상세본이다.

---

## 평소 작업 — 아이디어/조사 진행 시

1. 새 아이디어나 조사 내용은 채팅에만 남기지 말고 **그 자리에서** `docs/<아이디어-이름>/`에 문서로 저장한다
   (개요·기획·설계·시장분석·수익구조/방법·매출예측).
2. 아이디어를 추가·개명·삭제할 때마다 `docs/README.md`의 아이디어 목록을 같이 갱신한다.
3. 인프라/도구 변경(예: AWS 서버 설정)도 `docs/aws/` 등 적절한 위치에 문서로 남긴다.

---

## Commit & Push — 예외 없이, 항상 즉시

> trader 레포는 "오늘 정리" 할 때만 승인 없이 자동 push였지만, **이 레포는 다르다.**

문서를 만들거나 고치는 **모든 순간**, commit뿐 아니라 push까지 그 자리에서 끝낸다. 하루 끝까지 모아두지 않는다. 승인 대기·배치 없음 — 이 레포에는 깨질 CI/빌드가 없으므로 매번 즉시 실행이 사전 승인되어 있다.

```bash
git add <변경파일>
git commit -m "설명"
git push
```

---

## 🌙 하루 정리 ("오늘일 정리해")

사용자가 "오늘일 정리해"라고 하면 아래 순서로 진행한다.

### A. Changelog 작성 → `dev-docs/changelog/YYYY-MM-DD.md`

오늘 만들거나 고친 문서, 진행한 조사, 인프라/도구 변경 내역을 정리한다. (trader 레포처럼 별도의 거래분석 문서는 없으므로 전부 이 changelog 하나에 담는다.)

### B. 아이디어 목록 최신화

`docs/README.md`의 아이디어 목록이 실제 `docs/<아이디어-이름>/` 상태와 맞는지 확인하고 갱신한다.

### C. Commit & Push

changelog를 포함해 오늘 변경된 모든 문서를 commit하고 바로 push한다. (위 "Commit & Push" 규칙과 동일 — 별도 승인 불필요.)

---

## 참고 — 인프라

- AWS 서버 접속/운영: [docs/aws/SERVER.md](../../docs/aws/SERVER.md)
- Remote Control 세션 관리 스크립트: [scripts/aws-claude/rc_session.sh](../../scripts/aws-claude/rc_session.sh)
