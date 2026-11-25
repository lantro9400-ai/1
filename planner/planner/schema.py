"""기획안 구조 정의.

`PlanDraft` 는 Claude 가 채우는 부분(structured outputs 스키마로 그대로 사용),
`Plan` 은 거기에 프로그램이 직접 채우는 표지 정보(촬영 날짜·장소 등)를 더한 최종본.
표지의 실무 정보는 모델이 지어내지 못하도록 코드에서만 채운다.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TimeSlot(BaseModel):
    time: str = Field(description="예: 10:00~10:30 또는 0:00~0:30")
    activity: str
    note: str = Field(description="비고. 없으면 빈 문자열")


class ThumbnailIdea(BaseModel):
    copy_text: str = Field(description="썸네일 문구")
    visual: str = Field(description="화면 구성")


class SceneBlock(BaseModel):
    name: str = Field(description="블록 이름. 예: 재료 소개, 소고기 장조림")
    line_examples: list[str] = Field(description="대사 예시 / 대사 포인트 불릿")
    pd_questions: list[str] = Field(description="PD 질문 혹은 역할")


class Scene(BaseModel):
    title: str = Field(description="예: S#2 겨울 밥도둑 소고기 두 그릇")
    summary: str = Field(description="이 신에서 다루는 내용 한두 문장")
    composition: list[str] = Field(description="구성 순서. 예: [재료 소개, 장조림, 무국]")
    blocks: list[SceneBlock]
    image_note: str = Field(description="필요한 이미지/자료. 모르면 ⬜ 미정")


class Shot(BaseModel):
    camera: str = Field(description="예: main cam, sub 1, sub 2-1")
    description: str


class ScheduleItem(BaseModel):
    step: str = Field(description="기획안 1차 전달 / 기획안 피드백 / 촬영일 / 발행일")
    date: str = Field(description="모르면 ⬜ 미정")


class ChefCheck(BaseModel):
    item: str = Field(description="확인할 내용")
    reason: str = Field(description="왜 확인이 필요한지")


class PlanDraft(BaseModel):
    title: str = Field(description="제목(가안)")
    alt_titles: list[str] = Field(description="다른 제목안 2개")
    theme_name: str = Field(description="회차 테마명 (S#2 제목에 쓰임)")
    timetable: list[TimeSlot]
    narrative_link: str = Field(description="채널 내러티브와의 연결성 (계절감 + 나도 해 먹고 싶다는 마음)")
    viewer_benefits: list[str] = Field(description="시청자에게 줄 수 있는 것 3~4개")
    expected_comments: list[str] = Field(description="기대하는 시청자 반응, 예상 댓글 형태 4~5개")
    thumbnail_ideas: list[ThumbnailIdea] = Field(description="썸네일 후보 3안")
    cast_role: str = Field(description="출연자의 역할")
    pd_role: str = Field(description="PD의 역할")
    thumbnail_reference: str = Field(description="썸네일 레퍼런스. '⬜ 미정 (제안 방향: ...)' 형태")
    scenes: list[Scene]
    shots: list[Shot]
    production_checks: list[str] = Field(description="최종 체크: 채널 코어 내러티브 / 커뮤니티 구축 / 출연자·제작진의 목표 각각 한 줄")
    schedule: list[ScheduleItem]
    blank_items: list[str] = Field(description="비워 둔(⬜ 미정) 항목 목록")
    chef_checks: list[ChefCheck] = Field(description="셰프님 확인이 필요한 부분")


class CoverInfo(BaseModel):
    channel_name: str
    pd: str
    director: str
    publish_date: str
    shoot_date: str
    location: str
    call_time: str
    parking: str
    extras: dict[str, str] = Field(default_factory=dict)  # 코너별 추가 표지 항목 (영상포맷, 브랜드명 ...)
    studio: str = ""


class Plan(PlanDraft):
    corner: str
    topic: str
    cover: CoverInfo
    review_status: str = "⬜ 미정"
    generated_at: str = ""
