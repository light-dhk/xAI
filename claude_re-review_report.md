# Cross-Validation 재검토 리포트 — Claude ↔ Gemini (app.py)

## 절차
초안(Claude) → 체크리스트 기반 리뷰(Gemini) → 타당성 재검토(Claude) → 선별 반영

## 판정 결과

| 항목 | Gemini 판정 | Claude 재검토 | 반영 여부 |
|---|---|---|---|
| A-3. pyperclip ImportError 방어 | ISSUE | 타당함 (Minor) | ✅ 반영 |
| A-4. 동일 초(second) 저장 시 덮어쓰기 | ISSUE | 타당함 | ✅ 반영 |
| A-5. History 위젯 key에 idx 포함 | ISSUE (Major) | 타당함 | ✅ 반영 |
| B. pyperclip 포괄적 except 처리 | ISSUE | 타당함 (Minor) | ✅ 반영 |
| C. `config.toml`의 `[theme.sidebar]` / Google Fonts URL 문법 | ISSUE (Major) | **기각 (Gemini 오류)** | ❌ 반영 안 함 |

## 기각 사유 상세 — C번 (테마 설정)

Gemini는 다음 두 가지가 "Streamlit 비공식/미지원 문법"이라고 주장했습니다:
1. `[theme.sidebar]` 섹션 자체가 존재하지 않는다
2. `font`에 `"FontName:URL"` 형식으로 Google Fonts를 지정할 수 없다

**검증 결과, 둘 다 사실이 아닙니다.** Streamlit 공식 문서 확인:
- `docs.streamlit.io/develop/concepts/configuration/theming-customize-colors-and-borders` — `[theme.sidebar]` 테이블을 이용해 사이드바 배경/텍스트/보더 색상을 앱 본문과 별도로 지정하는 것이 공식 기능으로 명시되어 있음.
- `docs.streamlit.io/develop/concepts/configuration/theming-customize-fonts` — Google Fonts/Adobe Fonts 등 외부 폰트 서비스를 `{font_name}:{css_url}` 형식의 단일 문자열로 지정하는 방법이 공식 가이드로 존재함.
- GitHub 이슈 기록상 `[theme.sidebar]` 관련 기능은 2025년 중반(Streamlit 1.46대)부터 이미 사용되고 있었음 — 즉 오래된 최신 기능이 아니라 어느 정도 안정화된 기능.

**추정 원인:** Gemini의 학습 데이터 시점이 이 테마 시스템 업데이트 이전에 멈춰 있어 발생한 오류로 보입니다. 애초에 설계서 검토 단계에서 우리가 "LLM 리뷰어의 지적을 맹신하지 않는다"는 원칙을 세운 이유가 정확히 이런 케이스 때문이었습니다 — 그대로 반영하지 않고 기각합니다.

## 추가로 Claude가 자체 발견한 사항 (Gemini 체크리스트 범위 밖)

- `requirements.txt`의 `streamlit>=1.38` 핀이 `[theme.sidebar]`가 안정적으로 지원되는 버전(1.46+)보다 낮게 설정되어 있었음. 그대로 두면 오래된 Streamlit 버전에서 테마 설정 일부가 무시될 위험이 있어 `>=1.48`로 상향 조정.

## 반영된 코드 변경 요약

1. **`import pyperclip`** → `try/except ImportError`로 감싸고, 모듈 부재 시 `do_paste()`에서 사용자에게 명확한 안내 메시지(toast) 표시
2. **`do_paste()`** → 포괄적 `except Exception` 대신 `pyperclip.PyperclipException`으로 예외 범위 좁힘
3. **`do_save()`** → 파일 저장 직전 `while os.path.exists(filepath)` 루프로 동일 초 충돌 시 `_1`, `_2` ... 접미사 자동 부여
4. **`render_sidebar_history()`** → `widget_key`에서 `idx` 제거, `entry['filename']`만으로 키 생성 (파일명이 타임스탬프 포함으로 이미 유일함)
5. **`requirements.txt`** → `streamlit>=1.38` → `streamlit>=1.48`

## 결론
Critical 이슈 0개, Major 이슈 1개는 기각(근거 있음), 나머지 Minor 이슈 4개는 모두 반영 완료. 코드는 현재 설계서 v1.3 기준으로 안정화된 상태입니다.
