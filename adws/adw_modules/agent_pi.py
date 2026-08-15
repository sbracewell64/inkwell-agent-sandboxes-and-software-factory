"""Pi coding agent interface — v1's only coding agent.

Builds one strict JSON/print request and delegates all native process work to
the SSSF-owned supervisor. Raw events are durably preserved before parsing or
callback delivery. Sessions and ambient Pi resources are deliberately disabled.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Optional

from .data_types import PiRequest, PiResult
from .pi_json_adapter import PiAdapterRequest, run_pi_json, safe_environment
from .subprocess_supervisor import AttemptBudget, TerminalState
from .utils import now_iso

PI_PATH = os.environ.get("PI_PATH", "pi")

RESULT_SNIPPET_CHARS = 20_000   # tool output rides along whole; clip only guards pathological cases
ARG_VALUE_CHARS = 20_000        # args too — the UI scrolls, it must not be handed cut-off data
LABEL_CHARS = 80                # "bash: <command>" shown as the event name

# The arg that identifies a call at a glance, in the order tools tend to use.
PRIMARY_ARGS = ("command", "path", "file_path", "pattern", "query", "url")


def resolve_model(target: str) -> tuple[str, str]:
    """Require an exact provider/model pair without catalog lookup or fallback."""
    if not isinstance(target, str) or "/" not in target:
        raise ValueError(f"model target {target!r} must be fully qualified as provider/model")
    provider, model_id = target.split("/", 1)
    if not provider or not model_id or any(char in model_id for char in "*?[]"):
        raise ValueError(f"model target {target!r} is not exact")
    return provider, model_id


def _context_tokens(usage: dict) -> int:
    """Tokens occupying the window after a turn.

    Mirrors pi's own `calculateContextTokens` (coding-agent
    `core/compaction/compaction.ts`), which is what pi compacts against and
    shows in its footer: prefer the provider's `totalTokens`, else sum the
    parts. Cache reads count — cached prompt is still prompt.
    """
    total = usage.get("totalTokens") or 0
    if total:
        return int(total)
    return int(sum(usage.get(part) or 0
                   for part in ("input", "output", "cacheRead", "cacheWrite")))


def _text_of(container: dict) -> str:
    """Join the text blocks of anything pi shapes as {content: [...]} — a
    message or a tool result."""
    return "".join(part.get("text", "") for part in container.get("content", []) or []
                   if isinstance(part, dict) and part.get("type") == "text")


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def assistant_message_records(event: dict) -> list[dict]:
    """Thinking and text of one COMPLETE assistant message, as trace records.

    Reads `message_end` ONLY. The stream also carries `message_update` events,
    but those are keystroke-level deltas ("17", "17*23…") — forwarding them
    would fill the trace with fragments. `message_end` is the complete-thought
    unit, and it arrives before the message's tool_execution_end, so these
    records naturally precede the tool_call they narrate.

    Returns up to two records per message: kind="thinking" (the joined thinking
    blocks) and kind="agent_message" (the joined text blocks). `stop_reason`
    distinguishes working narration ("toolUse") from the final answer ("stop").
    """
    if event.get("type") != "message_end":
        return []
    message = event.get("message", {}) or {}
    if message.get("role") != "assistant":
        return []
    stop_reason = message.get("stopReason")
    records = []
    thinking = "".join(part.get("thinking", "") for part in message.get("content", []) or []
                       if isinstance(part, dict) and part.get("type") == "thinking")
    text = _text_of(message)
    for kind, body in (("thinking", thinking), ("agent_message", text)):
        if not body.strip():
            continue
        records.append({
            "kind": kind,
            "label": _clip(" ".join(body.split()), LABEL_CHARS),
            "text": _clip(body, RESULT_SNIPPET_CHARS),
            "stop_reason": stop_reason,
        })
    return records


def _label(tool: str, args: dict) -> str:
    """One-line human name for a tool call: `bash: ls -la src`."""
    value = next((args[key] for key in PRIMARY_ARGS
                  if isinstance(args.get(key), str) and args[key].strip()), "")
    if not value:
        value = next((v for v in args.values() if isinstance(v, str) and v.strip()), "")
    value = " ".join(str(value).split())
    return f"{tool}: {_clip(value, LABEL_CHARS)}" if value else tool


class ToolCallTracker:
    """Folds pi's tool stream into ONE normalized record per completed call.

    pi announces a call as a `toolCall` content block, then emits
    tool_execution_start / _update / _end for it. Only the end carries the
    result, so that is where a record is emitted — one trace event per real
    tool call, the moment it returns, instead of three shapeless ones.

    The record carries the call's real span (`started_at`/`ended_at`), which the
    tracer writes to columns so the UI can lay tool calls on a time axis without
    parsing every payload.
    """

    def __init__(self) -> None:
        self._open: dict[str, dict] = {}

    def observe(self, event: dict) -> Optional[dict]:
        """Returns the record for a finished tool call, else None."""
        etype = event.get("type", "")
        if etype == "message_end":
            for block in event.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "toolCall":
                    self._announce(block.get("id"), block.get("name"),
                                   block.get("arguments"))
            return None
        if etype == "tool_execution_start":
            self._announce(event.get("toolCallId"), event.get("toolName"),
                           event.get("args"))
            return None
        if etype != "tool_execution_end":
            return None

        call_id = str(event.get("toolCallId") or "")
        opened = self._open.pop(call_id, {})
        tool = str(event.get("toolName") or opened.get("tool") or "tool")
        args = event.get("args") or opened.get("args") or {}
        record = {
            "tool": tool,
            "tool_call_id": call_id,
            "args": {key: _clip(value, ARG_VALUE_CHARS) if isinstance(value, str) else value
                     for key, value in args.items()},
            "ok": not event.get("isError", False),
            "label": _label(tool, args),
        }
        result_text = _text_of(event.get("result") or {})
        if result_text:
            record["result_snippet"] = _clip(result_text, RESULT_SNIPPET_CHARS)
        record["ended_at"] = now_iso()
        if opened.get("clock"):
            record["duration_ms"] = int((time.monotonic() - opened["clock"]) * 1000)
        if opened.get("started_at"):
            record["started_at"] = opened["started_at"]
        return record

    def _announce(self, call_id, tool, args) -> None:
        """First sighting starts the clock; a later sighting only fills gaps."""
        if not call_id:
            return
        known = self._open.get(str(call_id), {})
        self._open[str(call_id)] = {
            "tool": tool or known.get("tool", ""),
            "args": args or known.get("args", {}),
            "started_at": known.get("started_at") or now_iso(),   # wall clock, for the row
            "clock": known.get("clock") or time.monotonic(),      # monotonic, for duration
        }


def run(request: PiRequest, on_event: Optional[Callable[[dict], None]] = None,
        on_spawn: Optional[Callable[[int], None]] = None,
        on_exit: Optional[Callable[[int], None]] = None,
        budget: Optional[AttemptBudget] = None) -> PiResult:
    """Run one strict Pi JSON/print attempt through the owned supervisor."""
    provider, model_id = resolve_model(request.model)
    if request.extensions:
        raise ValueError("Pi extensions are disabled by the strict adapter contract")
    terminal = run_pi_json(
        PiAdapterRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            provider_model=f"{provider}/{model_id}",
            thinking=request.thinking,
            tools=request.tools,
            cwd=str(Path(request.cwd).resolve()),
            raw_event_path=request.raw_output_path,
            pi_argv0=PI_PATH,
            timeout_seconds=request.timeout_seconds,
            term_grace_seconds=request.term_grace_seconds,
            max_stdout_bytes=request.max_stdout_bytes,
            max_stderr_bytes=request.max_stderr_bytes,
            max_event_bytes=request.max_event_bytes,
            total_attempt_budget=request.total_attempt_budget,
            environment=safe_environment(),
        ),
        budget=budget,
        on_event=on_event,
        on_spawn=on_spawn,
        on_exit=on_exit,
    )
    result = PiResult(
        text=terminal.text,
        returncode=terminal.returncode or 0,
        session_id=request.session_id,
        tokens=terminal.usage.total_tokens,
        cost=terminal.usage.total_cost,
        terminal=terminal.as_dict(),
    )
    result.usage.input_tokens = terminal.usage.input_tokens
    result.usage.output_tokens = terminal.usage.output_tokens
    result.usage.cache_read_tokens = terminal.usage.cache_read_tokens
    result.usage.cache_write_tokens = terminal.usage.cache_write_tokens
    result.usage.reasoning_tokens = terminal.usage.reasoning_tokens
    result.usage.total_tokens = terminal.usage.total_tokens
    result.usage.total_cost = terminal.usage.total_cost
    if terminal.terminal_state != TerminalState.SUCCEEDED:
        reason = terminal.reason.code if terminal.reason else "unclassified-terminal-failure"
        detail = terminal.reason.detail if terminal.reason else "Pi did not produce a successful terminal result"
        raise RuntimeError(f"Pi attempt {reason}: {detail}")
    return result
