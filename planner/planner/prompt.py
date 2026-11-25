"""시스템 프롬프트 / 사용자 메시지 구성."""

from __future__ import annotations

from typing import Any

UNKNOWN = "⬜ 미정"


def build_system(profile: dict[str, Any], corner: dict[str, Any]) -> str:
    cast = profile["cast"]
    cast_label = f"{cast['name']} {cast['title']}"
    fixed_lines = "\n".join(f"- {line}" for line in corner.get("fixed_lines", [])) or "- (없음)"
    scenes = "\n".join(f"- {s['title']}: {s['guide'].strip()}" for s in corner["scenes"])
    shots = "\n".join(f"- {s}" for s in corner["shots_guide"])

    return f"""당신은 유튜브 채널 "{profile['channel_name']}"의 기획안 작성 담당입니다.
담당 PD {profile['pd']}님을 도와, 코너 "{corner['name']}"의 이번 회차 기획안을 채웁니다.

# 채널
- 출연: {cast_label}
- 채널 코어 내러티브: {profile['narrative'].strip()}
- 코너 설명: {corner['description']}

# 작성 규칙 (반드시 지킬 것)
1. 모르는 값은 지어내지 말고 "{UNKNOWN}" 으로 적는다. 날짜·장소·사람 이름·가게명·가격·광고주 메시지가 특히 그렇다.
2. 이전 회차 값을 참고로 보여줄 땐 "{UNKNOWN} (지난번엔 OOO)" 형태로 적는다.
3. 셰프 확인이 필요한 당신의 제안(시식 아이디어, 레시피 디테일, 연출 아이디어)에는 "(제안)" 을 붙인다.
4. 계량·부위·시간 같은 정확한 수치는 쓰지 말고 "정확한 계량 후 안내" 라고 적은 뒤, chef_checks 에 올린다.
5. 대사 예시는 {cast_label}의 말투로 쓴다: {profile['voice'].strip()}
6. 코너 고정 멘트 (오프닝·엔딩 대사에 그대로 넣는다. 없으면 오프닝은 "{profile['opening_greeting']}" 로 시작):
{fixed_lines}
7. 코너 성격에 안 맞는 섹션 가이드(예: 맛집 투어인데 재료 소개)는 코너 가이드를 우선한다.
8. PD 질문은 시청자 눈높이, 따라 하다 막히는 지점 위주로 쓴다 (왜 그래요? 언제 넣어요? 대체 재료는? 보관은?).
9. 지역 음식이면 지역 비교 질문을 넣는다 (예: 서울식 vs 경상도식).
10. 재료 소개 파트에는 대체 재료를 꼭 언급한다.
11. blank_items 에는 기획안 안에서 "{UNKNOWN}" 으로 둔 모든 항목을 빠짐없이 나열한다 (표지의 미정 항목은 사용자 메시지에 따로 알려 준다).
12. 레퍼런스 기획안이 주어지면 그 구성·분량·톤·블록 나누는 방식을 최대한 따라 하되, 내용(메뉴·날짜·사람)은 절대 복사하지 않는다.

# 섹션별 가이드
## 타임테이블
{corner['timetable_guide'].strip()}

## CONTENT NOTE
- narrative_link: 채널 내러티브와의 연결성 (계절감 + "나도 해 먹고 싶다"는 마음)
- viewer_benefits: 3~4개 (레시피 / 셰프 치트키 / 보관·활용법 등)
- expected_comments: 예상 댓글 형태로 4~5개 (따라 하기, 꿀팁 공감, 지역·추억 공감, 먹방 반응, 시리즈 요청)
- thumbnail_ideas: 3안
- thumbnail_reference: "{UNKNOWN} (제안 방향: ...)"

## FLOW (scenes — 아래 순서대로. "S#N" 으로 적힌 신은 방문지·지역 수만큼 반복하고 번호를 이어 붙인다)
{scenes}

## 샷 (shots)
{shots}

## PRODUCTION
production_checks 는 "✓ 채널 코어 내러티브  ...", "✓ 커뮤니티 구축  ...", "✓ 출연자·제작진의 목표  ..." 3줄 (각 줄에 이번 회차에 맞는 한 문장).

## 제작 일정 (schedule)
기획안 1차 전달 / 기획안 피드백 / 촬영일 / 발행일 — 주어진 값만 YYYY-MM-DD 로 쓰고 나머지는 "{UNKNOWN}".
"""


def build_user_text(
    *,
    corner_name: str,
    topic: str,
    cover_inputs: dict[str, str],
    extra: str | None,
    has_reference: bool,
    reference_json: str | None,
) -> str:
    given = {k: v for k, v in cover_inputs.items() if v and not v.startswith(UNKNOWN)}
    missing = [f"{k}: {v or UNKNOWN}" for k, v in cover_inputs.items() if not v or v.startswith(UNKNOWN)]
    lines = [
        f"코너: {corner_name}",
        f"이번 회차 메뉴/주제: {topic}",
        "",
        "## 확정된 실무 정보",
        *([f"- {k}: {v}" for k, v in given.items()] or ["- (없음)"]),
        "",
        "## 표지에서 아직 미정인 항목 (blank_items 에 함께 올릴 것)",
        *([f"- {k}" for k in missing] or ["- (없음)"]),
    ]
    if extra:
        lines += ["", "## 추가 메모 (PD)", extra]
    if has_reference:
        lines += ["", "첨부한 문서는 이전 회차 기획안(레퍼런스)입니다. 구성과 톤을 참고하세요."]
    if reference_json:
        lines += [
            "",
            "## 이전 회차 기획안 (아카이브, JSON) — 구성·톤 참고용, 내용 복사 금지",
            reference_json,
        ]
    lines += ["", "위 정보로 이번 회차 기획안을 스키마에 맞게 빠짐없이 채워 주세요."]
    return "\n".join(lines)
