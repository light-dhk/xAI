"""
Cross-AI Prompt Manager - MVP
설계서: 260709_BluePrint_Cross-AI_Prompt_Manager_v1.3.md 기준

실행 환경: Windows 전용, 완전 로컬 (streamlit run app.py)
"""

import os
import re
from datetime import datetime

try:
    import pyperclip
except ImportError:
    pyperclip = None  # do_paste()에서 None 체크로 방어
import streamlit as st

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
SAVE_DIR = "saved_reports"
AI_OPTIONS = ["ChatGPT", "Claude 3.5", "Perplexity", "Gemini", "기타"]
PREVIEW_MAX_LEN = 80


# ---------------------------------------------------------------------------
# 상태 초기화 (session_state)
# ---------------------------------------------------------------------------
def init_state() -> None:
    defaults = {
        "history": [],  # [{time, ai, topic, content, filename}, ...] LIFO (index 0 = 최신)
        "editor_text": "",
        "header_ai": AI_OPTIONS[0],
        "header_time": "",
        "header_topic": "",
        "initial_prompt": "",
        "_last_uploaded_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------
def sanitize_for_filename(text: str) -> str:
    """파일명/YAML frontmatter를 깨뜨릴 수 있는 문자를 치환한다."""
    if not text:
        return "untitled"
    cleaned = re.sub(r'[\\/*?:"<>|\r\n]', "_", text).strip()
    return cleaned or "untitled"


def sanitize_for_yaml(text: str) -> str:
    """YAML frontmatter 값에 들어갈 콜론/개행만 최소한으로 치환한다."""
    if not text:
        return ""
    return text.replace("\n", " ").replace(":", "-")


def reset_header() -> None:
    """Header(AI/시간/제목)를 빈 값으로 초기화한다. (Reset-on-Append / Clear 공용)"""
    st.session_state["header_ai"] = AI_OPTIONS[0]
    st.session_state["header_time"] = ""
    st.session_state["header_topic"] = ""


# ---------------------------------------------------------------------------
# 콜백: 사이드바 History 체크박스 -> Editor Append + Header Reset
# ---------------------------------------------------------------------------
def on_history_check(idx: int, widget_key: str) -> None:
    """
    체크박스가 True로 바뀐 순간에만 append를 수행하고,
    같은 항목을 나중에 다시 append할 수 있도록 체크박스 상태를 즉시 False로 되돌린다.
    (체크박스를 '토글 스위치'가 아니라 '순간 실행 버튼'처럼 사용하는 패턴)
    """
    if not st.session_state.get(widget_key):
        return

    entry = st.session_state["history"][idx]
    block = (
        f"\n\n---\n"
        f"### [{entry['time']}] {entry['ai']} - {entry['topic']}\n"
        f"{entry['content']}"
    )
    st.session_state["editor_text"] = st.session_state.get("editor_text", "") + block
    reset_header()

    # 체크박스를 다시 False로 되돌려 반복 사용 가능하게 함
    st.session_state[widget_key] = False


# ---------------------------------------------------------------------------
# 콜백: Paste / Clear / Save
# ---------------------------------------------------------------------------
def do_paste() -> None:
    if pyperclip is None:
        st.session_state["_paste_status"] = (
            "error",
            "pyperclip 모듈이 설치되어 있지 않습니다. 'pip install pyperclip'을 실행해주세요.",
        )
        return

    try:
        clipboard_text = pyperclip.paste()
    except pyperclip.PyperclipException:
        clipboard_text = ""

    if not clipboard_text:
        st.session_state["_paste_status"] = (
            "warning",
            "클립보드가 비어있거나 텍스트를 읽을 수 없습니다.",
        )
        return

    current = st.session_state.get("editor_text", "")
    separator = "\n\n" if current else ""
    st.session_state["editor_text"] = current + separator + clipboard_text
    st.session_state["_paste_status"] = ("success", "클립보드 내용이 붙여넣기 되었습니다.")


def do_clear() -> None:
    st.session_state["editor_text"] = ""
    reset_header()


def do_save() -> None:
    ai = st.session_state.get("header_ai", "").strip() or AI_OPTIONS[0]
    time_str = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M")
    topic = st.session_state.get("header_topic", "").strip() or "무제"
    body = st.session_state.get("editor_text", "")
    initial_prompt = st.session_state.get("initial_prompt", "")

    now = datetime.now()
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_ai = sanitize_for_filename(ai)
    safe_topic = sanitize_for_filename(topic)
    filename = f"{file_timestamp}_{safe_ai}_{safe_topic}.md"

    md_content = (
        "---\n"
        f"Target_AI: {sanitize_for_yaml(ai)}\n"
        f"Date_Time: {sanitize_for_yaml(time_str)}\n"
        f"Topic: {sanitize_for_yaml(topic)}\n"
        "---\n\n"
        "### 📝 Initial Prompt (Base)\n"
        f"{initial_prompt}\n\n"
        "---\n\n"
        "### 💡 Cross-Validation Report (Main Editor)\n"
        f"{body}\n"
    )

    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)

        # 동일 초(second) 내 중복 저장 시 덮어쓰기 방지
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}{ext}"
            filepath = os.path.join(SAVE_DIR, filename)
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
    except OSError as e:
        st.session_state["_save_status"] = ("error", f"저장 실패: {e}")
        return

    # History에 LIFO로 추가 (index 0 = 최신)
    st.session_state["history"].insert(
        0,
        {
            "time": time_str,
            "ai": ai,
            "topic": topic,
            "content": body,
            "filename": filename,
        },
    )
    st.session_state["_save_status"] = ("success", filename)


# ---------------------------------------------------------------------------
# UI 렌더링
# ---------------------------------------------------------------------------
def render_sidebar_history() -> None:
    st.markdown("### 📚 History")

    if not st.session_state["history"]:
        st.caption("아직 저장된 이력이 없습니다.")
        return

    for idx, entry in enumerate(st.session_state["history"]):
        label = f"[{entry['time']}][{entry['ai']}] {entry['topic']}"
        preview = entry["content"].strip().replace("\n", " ")
        if len(preview) > PREVIEW_MAX_LEN:
            preview = preview[:PREVIEW_MAX_LEN] + "..."

        widget_key = f"hist_chk_{entry['filename']}"
        with st.container(border=True):
            col_chk, col_body = st.columns([1, 5])
            with col_chk:
                st.checkbox(
                    "",
                    key=widget_key,
                    value=False,
                    on_change=on_history_check,
                    args=(idx, widget_key),
                    label_visibility="collapsed",
                )
            with col_body:
                st.markdown(f"**{label}**")
                with st.expander("미리보기", expanded=False):
                    st.markdown(preview if preview else "_(내용 없음)_")


def render_base_prompt_area() -> None:
    st.markdown("## 📄 Base Prompt Area")

    uploaded_file = st.file_uploader(
        "프롬프트 템플릿 불러오기 (.md)", type=["md"], key="_uploader"
    )
    if uploaded_file is not None and uploaded_file.name != st.session_state["_last_uploaded_name"]:
        try:
            st.session_state["initial_prompt"] = uploaded_file.read().decode("utf-8")
            st.session_state["_last_uploaded_name"] = uploaded_file.name
        except UnicodeDecodeError:
            st.warning("파일 인코딩을 확인해주세요 (UTF-8 권장).")

    st.text_area(
        "Initial Prompt / 원본 데이터",
        key="initial_prompt",
        height=150,
        placeholder="여러 AI에게 공통으로 던질 원본 데이터 또는 기초 지시문을 입력하세요.",
    )


def render_main_editor() -> None:
    st.markdown("## ✉️ Main Editor")

    col_ai, col_time, col_topic = st.columns([2, 1, 3])
    with col_ai:
        st.selectbox("Target AI", AI_OPTIONS, key="header_ai")
    with col_time:
        st.text_input("Time", key="header_time", placeholder="예: 14:32")
    with col_topic:
        st.text_input("Topic", key="header_topic", placeholder="대화 주제 / 제목")

    col_clear, col_paste, col_save = st.columns(3)
    with col_clear:
        st.button("🗑️ Clear", on_click=do_clear, use_container_width=True)
    with col_paste:
        st.button("📋 Paste", on_click=do_paste, use_container_width=True)
    with col_save:
        st.button("💾 Save", on_click=do_save, type="primary", use_container_width=True)

    # Paste / Save 결과 피드백 (toast)
    if "_paste_status" in st.session_state:
        status, msg = st.session_state.pop("_paste_status")
        st.toast(("✅ " if status == "success" else "⚠️ ") + msg)

    if "_save_status" in st.session_state:
        status, msg = st.session_state.pop("_save_status")
        if status == "success":
            st.toast(f"✅ 저장 완료: {msg}")
        else:
            st.toast(f"⚠️ {msg}")

    st.text_area(
        "Editor",
        key="editor_text",
        height=420,
        placeholder="AI 답변을 Paste 하거나, 좌측 History에서 이전 항목을 선택해 이어붙이세요.",
    )


def render_custom_css() -> None:
    """색상/폰트 외 카드형 UI를 위한 최소 범위 CSS."""
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
        }
        div.stButton > button {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 메인 엔트리포인트
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Cross-AI Prompt Manager",
        page_icon="🛠️",
        layout="wide",
    )
    init_state()
    render_custom_css()

    with st.sidebar:
        render_sidebar_history()

    st.title("🛠️ Cross-AI Prompt Manager")
    render_base_prompt_area()
    st.divider()
    render_main_editor()


if __name__ == "__main__":
    main()
