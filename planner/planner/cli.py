"""기획안 자동 완성 CLI.

사용 예:
  python -m planner new --corner 치트키 --topic "소고기 장조림, 경상도식 소고기무국" \\
      --ref 지난기획안.pdf --shoot-date 2026-12-03 --call-time 10:00
  python -m planner render archive/2026-11-25_치트키_소고기-장조림/plan.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from .config import ARCHIVE_DIR, REFERENCES_DIR, load_corner, load_profile
from .prompt import UNKNOWN, build_system, build_user_text
from .reference import reference_blocks, reference_json_text
from .render import render_markdown
from .schema import CoverInfo, Plan, PlanDraft

COVER_LABELS = {
    "director": "촬영감독",
    "publish_date": "발행일",
    "shoot_date": "촬영 날짜",
    "location": "촬영 장소",
    "call_time": "콜타임",
    "parking": "주차 안내",
}


def _cover_value(key: str, given: str | None, previous: dict[str, str]) -> str:
    if given:
        return given
    if key in previous:
        return f"{UNKNOWN} (지난번엔 {previous[key]})"
    return UNKNOWN


def build_cover(args: argparse.Namespace, profile: dict, corner: dict) -> CoverInfo:
    previous = corner.get("previous_values") or {}
    values = {k: _cover_value(k, getattr(args, k), previous) for k in COVER_LABELS}

    given_extras = dict(kv.split("=", 1) for kv in (args.set or []))
    extras: dict[str, str] = {}
    for item in corner.get("cover_extras") or []:
        label = item["label"]
        if label in given_extras:
            extras[label] = given_extras.pop(label)
        elif "default" in item:
            extras[label] = item["default"]
        elif "previous" in item:
            extras[label] = f"{UNKNOWN} (지난번엔 {item['previous']})"
        else:
            extras[label] = UNKNOWN
    extras.update(given_extras)  # 코너에 정의 안 된 항목도 그대로 표지에 추가
    return CoverInfo(
        channel_name=profile["channel_name"], pd=profile["pd"], studio=profile.get("studio", ""), extras=extras, **values
    )


def _slug(text: str) -> str:
    first = re.split(r"[,&/·]", text)[0]
    return re.sub(r"[^\w가-힣]+", "-", first).strip("-")[:40] or "plan"


def write_outputs(plan: Plan, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "plan.md").write_text(render_markdown(plan), encoding="utf-8")
    print(f"📄 저장: {out_dir}/plan.md (기획안), plan.json (다음 회차 레퍼런스용)")


def cmd_new(args: argparse.Namespace) -> None:
    profile = load_profile(args.channel)
    corner = load_corner(args.corner)
    cover = build_cover(args, profile, corner)

    refs = [Path(r) for r in args.ref or []]
    default_ref = REFERENCES_DIR / f"{corner['name']}.pdf"
    if not refs and not args.no_default_ref and default_ref.exists():
        refs = [default_ref]
        print(f"📎 기본 레퍼런스 사용: {default_ref.name}", file=sys.stderr)
    for r in refs:
        if not r.exists():
            raise SystemExit(f"레퍼런스 파일을 찾을 수 없습니다: {r}")

    cover_inputs = {label: getattr(cover, key) for key, label in COVER_LABELS.items()} | cover.extras
    note = "\n".join(x for x in [args.note, f"제작 일정: {args.schedule}" if args.schedule else None] if x)
    system = build_system(profile, corner)
    user_text = build_user_text(
        corner_name=corner["name"],
        topic=args.topic,
        cover_inputs=cover_inputs,
        extra=note or None,
        has_reference=any(r.suffix.lower() != ".json" for r in refs),
        reference_json=reference_json_text(refs),
    )

    if args.dry_run:
        print("===== SYSTEM =====\n" + system + "\n===== USER =====\n" + user_text)
        print(f"\n(레퍼런스 첨부 블록 {len(reference_blocks(refs))}개)")
        return

    from .generate import generate_draft  # API 키 없이도 dry-run/render 가 되도록 지연 import

    draft = generate_draft(
        system=system, user_text=user_text, ref_blocks=reference_blocks(refs), model=args.model, effort=args.effort
    )
    plan = finalize(draft, corner["name"], args.topic, cover)

    out_dir = Path(args.out) if args.out else ARCHIVE_DIR / f"{datetime.now():%Y-%m-%d}_{corner['name']}_{_slug(args.topic)}"
    write_outputs(plan, out_dir)
    print(f"⬜ 비워 둔 항목 {len(plan.blank_items)}개 / 셰프님 확인 {len(plan.chef_checks)}개")


def finalize(draft: PlanDraft, corner: str, topic: str, cover: CoverInfo) -> Plan:
    plan = Plan(
        **draft.model_dump(),
        corner=corner,
        topic=topic,
        cover=cover,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    # 표지 미정 항목은 모델 출력과 무관하게 비워 둔 항목 목록 맨 앞에 보장
    cover_fields = {label: getattr(cover, key) for key, label in COVER_LABELS.items()} | cover.extras
    missing = [f"{label}: {value}" for label, value in cover_fields.items() if value.startswith(UNKNOWN)]
    rest = [b for b in plan.blank_items if not any(b.startswith(label) for label in cover_fields)]
    plan.blank_items = missing + rest
    return plan


def cmd_render(args: argparse.Namespace) -> None:
    """plan.json 을 손으로 고친 뒤 plan.md 만 다시 만들 때."""
    path = Path(args.plan_json)
    plan = Plan.model_validate(json.loads(path.read_text(encoding="utf-8")))
    write_outputs(plan, path.parent)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="planner", description="유튜브 콘텐츠 기획안 자동 완성")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="새 기획안 작성")
    new.add_argument("--corner", required=True, help="코너명 (corners/ 폴더의 파일 이름, 예: 치트키)")
    new.add_argument("--topic", required=True, help='이번 회차 메뉴/주제 (예: "소고기 장조림, 경상도식 소고기무국")')
    new.add_argument("--channel", default="pungnyu", help="채널 프로필 (profiles/ 폴더의 파일 이름)")
    new.add_argument("--ref", action="append", help="레퍼런스 기획안 PDF/PNG/JPG 또는 archive 의 plan.json (여러 번 지정 가능). 없으면 references/<코너>.pdf 사용")
    new.add_argument("--shoot-date", dest="shoot_date")
    new.add_argument("--call-time", dest="call_time")
    new.add_argument("--location")
    new.add_argument("--director", help="촬영감독")
    new.add_argument("--publish-date", dest="publish_date")
    new.add_argument("--parking", help="주차 안내")
    new.add_argument("--set", action="append", metavar="라벨=값", help='코너별 추가 표지 항목 (예: --set 브랜드명=무가)')
    new.add_argument("--no-default-ref", action="store_true", help="references/<코너>.pdf 자동 첨부 끄기")
    new.add_argument("--schedule", help='제작 일정 메모 (예: "1차 전달 11/27, 피드백 11/28")')
    new.add_argument("--note", help="PD 추가 메모 (콘셉트, 꼭 넣을 내용 등)")
    new.add_argument("--out", help="저장 폴더 (기본: archive/날짜_코너_주제)")
    new.add_argument("--model", default="claude-opus-5-5")
    new.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    new.add_argument("--dry-run", action="store_true", help="API 호출 없이 프롬프트만 출력")
    new.set_defaults(func=cmd_new)

    render = sub.add_parser("render", help="plan.json 을 고친 뒤 plan.md 다시 만들기")
    render.add_argument("plan_json")
    render.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
