# AWS 서버

> idea 레포 아이디어 리서치/작업용 AWS EC2 서버 정보

---

## 서버 접속 정보

| 항목 | 값 |
|------|-----|
| **호스트** | idea-aws (서버 호스트명 = `idea-aws`, Windows hosts 파일 등록, 43.203.241.72) |
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

### ⚠️ 세션 이름이 호스트명으로 뜨던 문제 (2026-09-05 해결)

`--remote-control '<이름>'` 으로 이름을 줘도 모바일 앱 목록에는 **호스트명**
(`ip-172-31-14-156.ap-northeast-2.compute.internal`)이 표시됐다.

원인은 별도 플래그였다:

```
--remote-control-session-name-prefix <prefix>   기본값: hostname
```

앱 목록에 뜨는 이름은 이 **프리픽스**에서 나오고, 지정하지 않으면 호스트명이 그대로 쓰인다.

두 군데를 모두 잡았다:

| 조치 | 내용 |
|---|---|
| 스크립트 | `rc_session.sh` 기동 명령에 `--remote-control-session-name-prefix "$NAME"` 추가 |
| 호스트명 | `hostnamectl set-hostname idea-aws` + `/etc/cloud/cloud.cfg` 의 `preserve_hostname: true` (EC2 는 재부팅 시 cloud-init 이 호스트명을 되돌리므로 이 설정이 없으면 원복된다) |

호스트명까지 바꾼 이유는, 프리픽스를 놓친 경로(수동 기동 등)에서도 `idea-aws` 로 뜨게 하기 위해서다.
`/etc/hosts` 에 `127.0.0.1 idea-aws` 도 추가해 이름 해석 실패를 막았다.

### ⚠️ 버전 갱신은 재시작해야 반영된다

`claude` 바이너리가 업데이트돼도 **이미 떠 있는 프로세스는 옛 버전을 계속 물고 있다.**
심볼릭 링크(`~/.local/bin/claude`)만 새 버전을 가리킬 뿐이다.

```bash
# 지금 돌고 있는 프로세스의 실제 버전 확인
PID=$(for p in $(pgrep -x claude); do tr '\0' ' ' < /proc/$p/cmdline | grep -q -- --remote-control && echo $p; done)
readlink /proc/$PID/exe          # 실행 중인 버전
readlink -f ~/.local/bin/claude  # 디스크에 있는 버전
```

**실제 사례 (2026-09-05):** 8/26에 뜬 세션이 **2.1.246**을 물고 있었는데
8/27에 디스크가 **2.1.247**로 갱신돼 있었다. 재시작 전까지 열흘간 옛 버전으로 돌았다.

### ⚠️ claude 는 자동 업데이트 후 기동 인자를 잃는다

재시작 직후엔 `claude --remote-control 'idea-aws'` 로 떠 있지만, 자동 업데이트가 걸리면
**클로드가 스스로 재실행(exec)하면서 기동 인자를 버린다.** 남는 모습은 이렇다:

```
656644 screen  SCREEN ... bash -lc "... claude --remote-control 'idea-aws' ..."
656646 bash    (래퍼 — 여기엔 원래 인자가 그대로 남아 보인다)
656671 claude  /home/ec2-user/.local/bin/claude --permission-mode auto   ← 인자 소실
```

**여기서 두 가지가 깨진다:**

| 증상 | 원인 |
|---|---|
| 앱 목록에 호스트명이 뜬다 | 이름 인자가 사라진 뒤 `/rc` 로 재연결 → 기본값(호스트명) 사용 |
| `rc_restart.sh` 가 `버전=알수없음` 을 찍는다 | `--remote-control` 문자열로 프로세스를 찾던 `rc_pid()` 가 실패 |

**대응:**

- `rc_pid()` 를 인자 매칭이 아니라 **screen 세션의 자손 추적**으로 변경 (screen PID → bash → claude).
- 호스트명 자체를 `idea-aws` 로 바꿔, 인자가 날아가도 기본 이름이 `idea-aws` 가 되게 함.

`ps -eo pid,ppid,comm,args | grep claude` 로 래퍼(bash)가 아니라 **comm=claude 인 프로세스**의
인자를 봐야 실제 상태를 알 수 있다.

관리 스크립트: [scripts/aws-claude/rc_restart.sh](../../scripts/aws-claude/rc_restart.sh)

```bash
# 세션 밖(SSH)에서
~/idea/scripts/aws-claude/rc_restart.sh

# ⚠️ 세션 안에서 클로드가 자기 자신을 재시작할 때는 반드시 분리 실행
setsid nohup ~/idea/scripts/aws-claude/rc_restart.sh 20 >/dev/null 2>&1 &
```

**왜 분리 실행이 필요한가:** 세션 안에서 돌고 있는 클로드가 자기를 죽이면
재시작 명령을 실행할 주체가 같이 사라진다. 반드시 `setsid`/`nohup` 으로 떼어내야 한다.

스크립트는 stop → start 후 **최대 40초간 생존을 확인**하고, 실패하면 3회까지 재시도한다.
프롬프트에 걸린 경우를 대비해 방어적으로 Enter 도 보낸다. 결과는 `~/logs/rc_restart.log`.

**재시작 전 확인할 것:**

| 항목 | 확인 방법 |
|---|---|
| 자격증명 | `ls -la ~/.claude/.credentials.json` — 없으면 `rc_session.sh login` 먼저 |
| 폴더 신뢰 | `~/.claude.json` 의 `projects["/home/ec2-user/idea"].hasTrustDialogAccepted` 가 `true` 인지 |

**둘 중 하나라도 안 되어 있으면 재시작 후 세션이 안 뜨고, 그때는 SSH 로만 복구된다.**

---

## GitHub / 레포지터리 권한

서버 전용 SSH 배포 키(`~/.ssh/id_ed25519`, ed25519)를 생성해 GitHub `hammaaa/idea` 레포의 **Deploy keys** 에 쓰기 권한(Allow write access)으로 등록했다. 개인 계정 자격증명을 서버에 두지 않기 위해, 이 레포 전용 키만 사용한다.

```bash
# 서버에서 이미 설정된 clone (참고용, 재설치 시)
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519' git clone git@github.com:hammaa/idea.git ~/idea
```

서버의 `~/.ssh/config` 에 `github.com` 기본 identity 로 등록해두면 `GIT_SSH_COMMAND` 없이도 바로 `git pull` / `git push` 가능.

---

*최종 업데이트: 2026-09-05*
