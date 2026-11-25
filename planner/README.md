# 풍류천재 기획안 자동 작성기

코너명 + 이번 회차 메뉴/주제만 넣으면, 지난 기획안(레퍼런스)과 같은 구성으로 모든 항목을 채운 기획안 텍스트를 만들어 줍니다.
결과는 회사 기획안 플랫폼에 섹션별로 옮겨 적기 쉽게 `라벨: 값` 형태의 텍스트(`plan.md`)로 나옵니다.

코너: **치트키**(요리 레시피) · **풍류유람기**(지역 맛집 투어) · **마감주**(요리 + 안주 먹방)

## 처음 한 번 설정

```bash
cd planner
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # Claude API 키
```

`references/` 폴더에 코너별 지난 기획안 PDF를 넣어 두면 자동으로 레퍼런스로 씁니다 (파일 이름 = 코너명):

```
references/치트키.pdf
references/풍류유람기.pdf
references/마감주.pdf
```

이미지로만 된 PDF(텍스트 복사 안 되는 것)도 그대로 읽습니다.

## 사용법

```bash
# 최소 입력
python -m planner new --corner 치트키 --topic "소고기 장조림, 경상도식 소고기무국"

# 정해진 실무 정보가 있으면 같이
python -m planner new --corner 풍류유람기 --topic "통영 굴 & 시장 투어 (가게: 굴향토집, 서호시장)" \
    --shoot-date 2026-12-10 --call-time "9시 40분" --location "경남 통영시" --director "김동환, 류채영" \
    --publish-date 2026-12-24 --schedule "기획안 1차 전달 12/1, 피드백 12/2"

# 마감주: 표지 추가 항목은 --set 으로
python -m planner new --corner 마감주 --topic "냉털 두부김치, 감자전" --set 브랜드명=무가 --set 광고상품=-
```

결과는 `archive/날짜_코너_주제/` 에 저장됩니다.

| 파일 | 용도 |
|---|---|
| `plan.md` | 기획안 텍스트. 플랫폼에 옮겨 적을 내용 |
| `plan.json` | 같은 내용의 구조화 데이터. 다음 회차 레퍼런스로 `--ref archive/.../plan.json` |

기타 옵션:
- `--note "..."`: 콘셉트, 꼭 넣을 내용 등 PD 메모
- `--ref 파일`: 특정 기획안(PDF/PNG/JPG/plan.json)을 레퍼런스로 지정 (여러 번 가능)
- `--dry-run`: API 호출 없이 Claude에게 보낼 프롬프트만 확인
- `python -m planner render archive/.../plan.json`: plan.json을 손으로 고친 뒤 plan.md 다시 만들기

## 작성 규칙 (자동 적용)

- 모르는 값은 `⬜ 미정`. 지난 회차 값이 있으면 `⬜ 미정 (지난번엔 임태성)`
- 셰프 확인이 필요한 제안은 `(제안)`, 계량·부위는 "정확한 계량 후 안내"
- 맨 끝에 **비워 둔 항목**과 **셰프님 확인이 필요한 부분** 목록

## 고칠 곳

| 바꾸고 싶은 것 | 파일 |
|---|---|
| 채널명, PD, 말투, 채널 내러티브 | `profiles/pungnyu.yaml` |
| 코너별 구성·고정 멘트·지난 회차 값·샷 구성 | `corners/<코너>.yaml` |
| 새 코너 추가 | `corners/` 에 yaml 하나 복사해서 추가 |
| 출력 텍스트 모양 | `planner/templates/plan.md.j2` |

예시 결과: `examples/sample_output/plan.md` (치트키 "소고기 장조림 & 경상도식 소고기무국" 편, 손으로 작성한 샘플)
