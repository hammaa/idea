# AWS 서버

> idea 레포 아이디어 리서치/작업용 AWS EC2 서버 정보

---

## 서버 접속 정보

| 항목 | 값 |
|------|-----|
| **호스트** | idea-aws (Windows hosts 파일 등록, 43.203.241.72) |
| **리전** | ap-northeast-2 (서울) |
| **키 페어** | hammaaa_aws.pem |
| **사용자** | ec2-user |

### SSH 접속

```bash
ssh -i C:/Users/hamma/.ssh/hammaaa_aws.pem ec2-user@idea-aws
```

---

## 서버 사양

| 항목 | 스펙 |
|------|------|
| **인스턴스 타입** | t4g.small (ARM, aarch64) |
| **vCPU** | 2 core |
| **RAM** | 2GB |
| **Storage** | 20GB |
| **OS** | Amazon Linux 2023 (aarch64) |

---

## 설치 현황 (2026-08-26)

- [x] SSH 접속 확인
- [x] git 설치 (dnf)
- [x] claude CLI 설치 (네이티브 바이너리, `curl -fsSL https://claude.ai/install.sh | bash` — Node.js 불필요)
- [x] GitHub 배포용 SSH 키 생성 (`~/.ssh/id_ed25519`, 코멘트 `idea-aws-deploy-key`) 후 `hammaaa/idea` 레포에 Deploy key(쓰기 권한)로 등록
- [x] `~/idea` 에 레포 클론
- [x] Remote Control 세션용 full-scope 로그인 (`claude auth login`)
- [x] Remote Control 세션 기동 (모바일 Claude 앱 > Code 목록에 `idea-aws` 로 표시)

---

## Remote Control 세션

`screen` 안에 `claude --remote-control` 을 상주시켜, SSH 연결을 끊어도 살아있게 하고 모바일 Claude 앱에서 바로 붙을 수 있게 한다.

관리 스크립트: [scripts/aws-claude/rc_session.sh](../../scripts/aws-claude/rc_session.sh)

```bash
# 서버에서 실행
~/rc_session.sh start    # 세션 기동 (최초 1회는 login 먼저 필요)
~/rc_session.sh status   # 생존 확인
~/rc_session.sh log      # 기동 로그
~/rc_session.sh attach   # SSH -t 로 접속 후 화면에 붙기 (빠질 땐 Ctrl+A D)
~/rc_session.sh stop     # 종료
~/rc_session.sh login    # full-scope 로그인 (최초 1회, 계정 등록 필요 — Remote Control은 setup-token 방식 불가)
```

세션 작업 디렉토리는 `~/idea` (레포 루트)로 고정되어 있다 (`RC_WORKDIR` 로 변경 가능).

---

## GitHub / 레포지터리 권한

서버 전용 SSH 배포 키(`~/.ssh/id_ed25519`, ed25519)를 생성해 GitHub `hammaaa/idea` 레포의 **Deploy keys** 에 쓰기 권한(Allow write access)으로 등록했다. 개인 계정 자격증명을 서버에 두지 않기 위해, 이 레포 전용 키만 사용한다.

```bash
# 서버에서 이미 설정된 clone (참고용, 재설치 시)
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519' git clone git@github.com:hammaa/idea.git ~/idea
```

서버의 `~/.ssh/config` 에 `github.com` 기본 identity 로 등록해두면 `GIT_SSH_COMMAND` 없이도 바로 `git pull` / `git push` 가능.

---

*최종 업데이트: 2026-08-26*
