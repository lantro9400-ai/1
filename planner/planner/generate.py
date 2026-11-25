"""Claude API 호출 → PlanDraft."""

from __future__ import annotations

import sys
from typing import Any

import anthropic

from .schema import PlanDraft

MODEL = "claude-opus-5-5"


def generate_draft(
    *,
    system: str,
    user_text: str,
    ref_blocks: list[dict[str, Any]],
    model: str = MODEL,
    effort: str = "high",
) -> PlanDraft:
    client = anthropic.Anthropic()
    content: list[dict[str, Any]] = [*ref_blocks, {"type": "text", "text": user_text}]

    print(f"⏳ {model} 로 기획안 작성 중... (1~3분 걸릴 수 있어요)", file=sys.stderr)
    # 긴 출력이라 스트리밍 + structured outputs(Pydantic) 로 스키마를 강제한다.
    # fallbacks: 안전 분류기가 드물게 요청을 거절하면 서버가 다른 모델로 자동 재시도.
    with client.beta.messages.stream(
        model=model,
        max_tokens=64000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        output_format=PlanDraft,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
    ) as stream:
        message = stream.get_final_message()

    if message.stop_reason == "refusal":
        raise SystemExit("모델이 요청을 거절했습니다. 입력 내용을 확인해 주세요.")
    if message.stop_reason == "max_tokens":
        raise SystemExit("출력이 길이 한도에서 잘렸습니다. 다시 시도하거나 메뉴 수를 줄여 주세요.")

    text = "".join(b.text for b in message.content if b.type == "text")
    usage = message.usage
    print(f"✅ 완료 (입력 {usage.input_tokens:,} / 출력 {usage.output_tokens:,} 토큰, 모델 {message.model})", file=sys.stderr)
    return PlanDraft.model_validate_json(text)
