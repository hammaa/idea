#!/bin/bash
# rc_session.sh — AWS 서버에 Remote Control 클로드 세션을 상주시킨다.
#
# 이름 주의: 모바일 앱 목록에 뜨는 이름은 --remote-control 인자가 아니라
# --remote-control-session-name-prefix (기본값 hostname) 에서 나온다. 둘 다 준다.
#
# 목적: 폰(Claude 모바일 앱 > Code)에서 서버 작업을 직접 시킬 수 있게 하는 것.
# --remote-control 은 "시작할 때" 붙이는 플래그라서, 이미 뜬 세션에는 소급 적용이 안 된다.
# 서버는 헤드리스이므로 screen 안에 띄워 SSH 를 끊어도 살아있게 한다.
#
# 사용법
#   rc_session.sh start    세션 기동 (이미 있으면 그대로 둠)
#   rc_session.sh stop     세션 종료
#   rc_session.sh status   생존 확인 + 화면 상태 덤프
#   rc_session.sh log      기동 로그
#   rc_session.sh attach   붙기 (SSH -t 필요, 빠질 땐 Ctrl+A D)
#   rc_session.sh login    full-scope 로그인 (Remote Control 은 이게 필요)

set -uo pipefail

NAME="${RC_NAME:-idea-aws}"          # 모바일 앱에 표시될 세션 이름
SCR="claude-rc"                      # screen 세션 이름
WORKDIR="${RC_WORKDIR:-$HOME/idea}"  # 세션 시작 디렉토리 (레포 루트)
LOG="$HOME/logs/rc_session.log"
EXITF="$HOME/logs/rc_session.exit"

alive() { screen -ls 2>/dev/null | grep -q "\.${SCR}[[:space:]]"; }

case "${1:-status}" in

start)
    if alive; then
        echo "이미 실행 중: $SCR"
        screen -ls | grep "\.${SCR}"
        exit 0
    fi
    if [ ! -f "$HOME/.claude/.credentials.json" ]; then
        echo "❌ full-scope 자격증명 없음. 먼저 로그인하라:"
        echo "     rc_session.sh login"
        exit 1
    fi
    mkdir -p "$(dirname "$LOG")" "$WORKDIR"

    # 대화형 첫 실행 마법사(테마·로그인 선택)에 걸려 멈추지 않도록 온보딩 플래그 확인
    python3 - <<'PY'
import json, os, shutil, time
p = os.path.expanduser('~/.claude.json')
if os.path.exists(p):
    d = json.load(open(p))
    need = not d.get('hasCompletedOnboarding')
    if need:
        shutil.copy2(p, p + '.bak-' + time.strftime('%Y%m%d-%H%M%S'))
        d['hasCompletedOnboarding'] = True
        d.setdefault('theme', 'dark')
        json.dump(d, open(p, 'w'), indent=2)
        print('   온보딩 플래그 설정함')
PY

    # exec 를 쓰지 않는다: claude 가 죽어도 bash 가 남아 종료코드를 기록하게 한다.
    rm -f "$EXITF"
    TERM=xterm-256color screen -L -Logfile "$LOG" -dmS "$SCR" \
        bash -lc "unset CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_API_KEY; export NODE_OPTIONS='${RC_NODE_OPTIONS:---max-old-space-size=380}'; cd '$WORKDIR'; claude --remote-control '$NAME' --remote-control-session-name-prefix '$NAME'; echo \"__EXIT=\$? at \$(date +%T)\" >> '$EXITF'; sleep 3600"

    sleep 5
    if alive; then
        echo "✅ 기동: screen=$SCR  이름=$NAME  작업디렉토리=$WORKDIR"
        echo "   모바일 Claude 앱 > Code 에서 '$NAME' 확인"
    else
        echo "❌ 기동 실패 — 로그:"
        tail -30 "$LOG" 2>/dev/null
        exit 1
    fi
    ;;

stop)
    alive || { echo "실행 중 아님"; exit 0; }
    screen -S "$SCR" -X quit
    sleep 1
    alive && { echo "❌ 종료 실패"; exit 1; } || echo "✅ 종료됨"
    ;;

status)
    if alive; then
        echo "✅ 실행 중"
        screen -ls | grep "\.${SCR}"
        pgrep -af 'claude --remote-control' | head -3
        screen -S "$SCR" -X hardcopy /tmp/rc_status.txt 2>/dev/null
        sleep 1
        echo "--- 화면 ---"
        grep -v '^$' /tmp/rc_status.txt 2>/dev/null | tail -25
    else
        echo "❌ 실행 중 아님"
        [ -f "$EXITF" ] && { echo "--- 마지막 종료 ---"; tail -5 "$EXITF"; }
        exit 1
    fi
    ;;

log)
    sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g; s/\x1b[()][A-Z0-9]//g; s/\x1b[<>=]//g; s/\r/\n/g' "$LOG" 2>/dev/null \
        | grep -v '^$' | tail -60 || echo "로그 없음: $LOG"
    ;;

attach)
    exec screen -r "$SCR"
    ;;

# full-scope 로그인. 브라우저가 없으므로 URL 을 사람이 열고 코드를 받아와야 한다.
#   rc_session.sh login          → 승인 URL 출력
#   rc_session.sh login <코드>   → 받은 코드 주입
login)
    if [ -n "${2:-}" ]; then
        screen -S claude-login -X stuff "$2\r" 2>/dev/null || { echo "❌ login 세션 없음. 먼저 'login' 을 인자 없이 실행"; exit 1; }
        sleep 8
        if [ -f "$HOME/.claude/.credentials.json" ]; then
            echo "✅ 로그인 완료"
            screen -S claude-login -X quit 2>/dev/null
        else
            echo "❌ 아직 자격증명 없음 — 코드를 확인하라"
            exit 1
        fi
        exit 0
    fi
    screen -S claude-login -X quit 2>/dev/null
    rm -f /tmp/login.log
    TERM=xterm-256color screen -L -Logfile /tmp/login.log -dmS claude-login \
        bash -lc "unset CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_API_KEY; cd \$HOME; claude auth login; sleep 900"
    sleep 6
    echo "--- 아래 URL 을 브라우저로 열고 승인 → 표시되는 코드를 복사 ---"
    strings /tmp/login.log | grep -A8 'visit:' | tr -d '\n' | sed 's/.*visit: //'
    echo
    echo "--- 그다음: rc_session.sh login '<코드>' ---"
    ;;

*)
    sed -n '10,17p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
