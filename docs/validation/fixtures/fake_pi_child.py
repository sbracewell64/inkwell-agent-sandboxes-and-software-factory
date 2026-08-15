#!/usr/bin/env python3
"""Deterministic fake Pi process; never contacts a model or provider."""

import json
import os
import signal
import subprocess
import sys
import time


def emit(value):
    print(json.dumps(value), flush=True)


def success():
    emit({"type": "session", "version": 3, "id": "fake", "cwd": os.getcwd()})
    message = {
        "role": "assistant",
        "provider": "fixture",
        "model": "deterministic",
        "thinkingLevel": "high",
        "content": [{"type": "text", "text": "typed-success-marker"}],
        "stopReason": "stop",
        "usage": {
            "input": 3,
            "output": 5,
            "cacheRead": 7,
            "cacheWrite": 11,
            "reasoning": 2,
            "totalTokens": 26,
            "cost": {"total": 0.125},
        },
    }
    emit({"type": "message_end", "message": message})
    emit({"type": "agent_end", "messages": [message]})


def terminal_first_success():
    message = {
        "role": "assistant",
        "provider": "fixture",
        "model": "deterministic",
        "thinkingLevel": "high",
        "content": [{"type": "text", "text": "typed-success-marker"}],
        "stopReason": "stop",
        "usage": {"input": 1, "output": 1, "totalTokens": 2, "cost": {"total": 0.0}},
    }
    emit({"type": "message_end", "message": message})
    emit({"type": "agent_end", "messages": [message]})
    emit({"type": "status", "status": "post-terminal"})


def main():
    mode = sys.argv[-1]
    if mode in {"success", "stdin-consumption"}:
        if mode == "stdin-consumption":
            # This consumes a driving parent's tail if the supervisor regresses
            # from DEVNULL to inherited stdin.
            sys.stdin.buffer.read()
        success()
    elif mode == "structured-error":
        message = {
            "role": "assistant",
            "provider": "fixture",
            "model": "deterministic",
            "content": [],
            "stopReason": "error",
            "errorMessage": "deterministic provider rejection",
        }
        emit({"type": "message_end", "message": message})
        emit({"type": "agent_end", "messages": [message]})
    elif mode == "terminal-first-success":
        terminal_first_success()
    elif mode == "malformed":
        print("{not-json", flush=True)
        emit({"type": "agent_end", "messages": []})
    elif mode == "missing-terminal":
        emit({"type": "message_end", "message": {"role": "assistant", "content": [], "stopReason": "stop"}})
    elif mode == "duplicate-terminal":
        success()
        emit({"type": "agent_end", "messages": []})
    elif mode == "hidden-retry":
        emit({"type": "auto_retry_start", "attempt": 1, "maxAttempts": 1, "delayMs": 0, "errorMessage": "fake"})
        emit({"type": "auto_retry_end", "success": True, "attempt": 1})
        success()
    elif mode == "timeout":
        time.sleep(30)
    elif mode == "ignored-term":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(30)
    elif mode.startswith("descendant:"):
        pid_path = mode.split(":", 1)[1]
        child = subprocess.Popen(
            [sys.executable, "-c", "import os,time; os.setsid(); time.sleep(30)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        with open(pid_path, "w", encoding="utf-8") as handle:
            handle.write(str(child.pid))
        time.sleep(0.3)
    elif mode.startswith("instant-descendant:"):
        pid_path = mode.split(":", 1)[1]
        child = subprocess.Popen(
            [sys.executable, "-c", "import os,time; os.setsid(); time.sleep(30)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        with open(pid_path, "w", encoding="utf-8") as handle:
            handle.write(str(child.pid))
    elif mode.startswith("late-fork:"):
        pid_path = mode.split(":", 1)[1]

        def fork_on_term(_signum, _frame):
            child = subprocess.Popen(
                [sys.executable, "-c", "import os,time; os.setsid(); time.sleep(30)"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            with open(pid_path, "w", encoding="utf-8") as handle:
                handle.write(str(child.pid))
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, fork_on_term)
        time.sleep(30)
    elif mode == "overflow":
        sys.stdout.buffer.write(b"x" * 200000)
        sys.stdout.buffer.flush()
        time.sleep(30)
    elif mode == "slow-success":
        time.sleep(0.4)
        success()
    else:
        print(f"unknown fixture mode: {mode}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
