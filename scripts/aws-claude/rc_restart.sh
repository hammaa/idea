#!/bin/bash
# rc_restart.sh — Remote Control 세션을 재시작한다 (버전 갱신 반영용).
#
# 왜 필요한가:
#   claude 바이너리가 업데이트돼도 "이미 떠 있는 프로세스"는 옛 버전을 계속 물고 있다.
#   심볼릭 링크만 새 버전을 가리킬 뿐이라, 반영하려면 프로세스를 다시 띄워야 한다.
#
# 왜 분리 실행이 필요한가:
#   세션 안에서 돌고 있는 클로드가 자기 자신을 죽이면 재시작할 주체가 사라진다.
#   그래서 이 스크립트는 반드시 setsid/nohup 으로 떼어내서 실행해야 한다.
#
# 사용법
#   scripts/aws-claude/rc_restart.sh              지금 재시작 (전경 — 세션 밖에서만)
#   setsid nohup scripts/aws-claude/rc_restart.sh 20 >/dev/null 2>&1 &
#                                                 20초 뒤 재시작 (세션 안에서 쓸 때)

set -uo pipefail

DELAY="${1:-5}"                       # 시작 전 대기 (초)
HERE="$(cd "$(dirname "$0")" && pwd)"
RC="$HERE/rc_session.sh"
SCR="claude-rc"
LOG="$HOME/logs/rc_restart.log"
TRIES=3                               # start 재시도 횟수
WAIT_ALIVE=40                         # 기동 후 생존 확인 대기 (초)

mkdir -p "$(dirname "$LOG")"
say() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# 주의: pgrep -f 는 screen 래퍼와 bash -lc 까지 잡는다.
# 실제 claude 프로세스(comm=claude)만 골라야 /proc/PID/exe 로 버전을 읽을 수 있다.
rc_pid() {
    local p
    for p in $(pgrep -x claude 2>/dev/null); do
        if tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q -- '--remote-control'; then
            echo "$p"; return 0
        fi
    done
    return 1
}
rc_ver()  { local p; p="$(rc_pid)"; [ -n "$p" ] && readlink "/proc/$p/exe" 2>/dev/null | xargs -r basename; }
alive()   { screen -ls 2>/dev/null | grep -q "\.${SCR}[[:space:]]"; }

say "──────── 재시작 시작 (${DELAY}초 대기) ────────"
BEFORE_VER="$(rc_ver)"; BEFORE_PID="$(rc_pid)"
say "이전: PID=${BEFORE_PID:-없음}  버전=${BEFORE_VER:-알수없음}"
say "디스크 버전: $(readlink -f "$HOME/.local/bin/claude" | xargs -r basename)"
sleep "$DELAY"

# ── 1. 종료 ──
say "종료 중…"
"$RC" stop >>"$LOG" 2>&1
sleep 3
if alive; then
    say "⚠️ screen 이 남아 있음 — 강제 종료"
    screen -S "$SCR" -X quit 2>/dev/null
    pkill -f 'claude --remote-control' 2>/dev/null
    sleep 3
fi
STILL_PID="$(rc_pid)"
if alive || [ -n "$STILL_PID" ]; then
    say "⚠️ 종료 확인 실패 (screen=$(alive && echo 있음 || echo 없음) pid=${STILL_PID:-없음})"
else
    say "종료 확인 완료 — screen 없음, 프로세스 없음"
fi

# ── 2. 기동 (재시도 포함) ──
OK=0
for i in $(seq 1 "$TRIES"); do
    say "기동 시도 $i/$TRIES…"
    "$RC" start >>"$LOG" 2>&1

    # 프롬프트에 걸려 멈추는 경우를 대비한 방어적 Enter
    sleep 6
    screen -S "$SCR" -X stuff $'\r' 2>/dev/null

    # 생존 확인
    for _ in $(seq 1 "$WAIT_ALIVE"); do
        if alive && [ -n "$(rc_pid)" ]; then OK=1; break; fi
        sleep 1
    done
    [ "$OK" = 1 ] && break
    say "❌ 시도 $i 실패 — 로그 꼬리:"
    tail -15 "$HOME/logs/rc_session.log" 2>/dev/null | sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -v '^$' | tee -a "$LOG"
    sleep 5
done

# ── 3. 결과 ──
if [ "$OK" = 1 ]; then
    sleep 4
    AFTER_PID="$(rc_pid)"; AFTER_VER="$(rc_ver)"
    say "✅ 기동 성공"
    say "이후: PID=$AFTER_PID  버전=${AFTER_VER:-알수없음}"
    if [ -n "$BEFORE_VER" ] && [ -n "$AFTER_VER" ]; then
        if [ "$BEFORE_VER" != "$AFTER_VER" ]; then
            say "🎉 버전 갱신됨: $BEFORE_VER → $AFTER_VER"
        else
            say "ℹ️ 버전 동일 ($AFTER_VER) — 디스크에 새 버전이 없었던 것"
        fi
    fi
    say "메모리: $(free -m | awk 'NR==2{print $3\"MB 사용 / \"$2\"MB\"}')"
    say "모바일 Claude 앱 > Code 에서 세션 이름 확인할 것"
else
    say "❌❌ 재시작 실패 — Remote Control 세션이 없는 상태다."
    say "   SSH 로 접속해 직접 복구할 것:"
    say "     ~/idea/scripts/aws-claude/rc_session.sh status"
    say "     ~/idea/scripts/aws-claude/rc_session.sh start"
    say "     (자격증명 문제면) ~/idea/scripts/aws-claude/rc_session.sh login"
fi
say "──────── 끝 ────────"
