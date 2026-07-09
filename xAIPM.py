"""
Cross-AI Prompt Manager - Cloud Edition
Design doc: 260709_BluePrint_Cross-AI_Prompt_Manager_v1.3.md

Runtime: Streamlit Community Cloud (or any remote Streamlit server).
"""

import json
import os
import re
import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAVE_DIR = "saved_reports"  
DEFAULT_TARGET_AI = "Claude"
TEMPLATE_FILENAME = "WorkFlowTemplate.md"  
EDITOR_TEMPLATE_FILENAME = "EditorTemplate.md"  

HISTORY_FONT_SIZE = "0.62rem"

AI_CHAT_SITES = {
    "ChatGPT": "https://chatgpt.com",
    "Claude": "https://claude.ai",
    "Gemini": "https://gemini.google.com",
}


# ---------------------------------------------------------------------------
# State initialization (session_state)
# ---------------------------------------------------------------------------
def load_default_prompt_template() -> str:
    """Auto-load WorkFlowTemplate.md from the same folder at startup."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, TEMPLATE_FILENAME)
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass
    return ""


def load_default_editor_template() -> str:
    """Same idea as load_default_prompt_template(), for the Main Editor."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, EDITOR_TEMPLATE_FILENAME)
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass
    return ""


def init_state() -> None:
    if "initial_prompt" not in st.session_state:
        st.session_state["initial_prompt"] = load_default_prompt_template()

    if "editor_text" not in st.session_state:
        st.session_state["editor_text"] = load_default_editor_template()
        
    if "header_ai" not in st.session_state:
        reset_header()

    defaults = {
        "history": [],  
        "_last_uploaded_name": None,
        "setup_complete": False, 
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def sanitize_for_filename(text: str) -> str:
    if not text:
        return "untitled"
    cleaned = re.sub(r'[\\/*?:"<>|\r\n]', "_", text).strip()
    return cleaned or "untitled"


def sanitize_for_yaml(text: str) -> str:
    if not text:
        return ""
    return text.replace("\n", " ").replace(":", "-")


def reset_header() -> None:
    now = datetime.now()
    st.session_state["header_ai"] = DEFAULT_TARGET_AI
    st.session_state["header_date"] = now.strftime("%m-%d")
    st.session_state["header_time"] = now.strftime("%H:%M")
    st.session_state["header_topic"] = ""


# ---------------------------------------------------------------------------
# Client-side clipboard copy
# ---------------------------------------------------------------------------
def clipboard_copy_button(text: str, label: str, key: str, help_text: str = "Copy", bg_color: str = "transparent") -> None:
    safe_text = json.dumps(text or "")
    html_code = f"""
    <html><body style="margin:0;padding:0;background:transparent;">
    <button id="{key}" title="{help_text}" style="
        width:100%; height:35px; margin:0; padding:0.1rem 0.3rem;
        border:1px solid gray; border-radius:0.4rem;
        background-color:{bg_color}; color:inherit; cursor:pointer;
        font-size:1.2rem; line-height:1.0; font-family:inherit;
        display:flex; align-items:center; justify-content:center;">
        {label}
    </button>
    <script>
    const btn_{key} = document.getElementById("{key}");
    const original_{key} = btn_{key}.innerText;
    btn_{key}.addEventListener("mouseenter", () => {{
        btn_{key}.style.filter = "brightness(1.1)";
    }});
    btn_{key}.addEventListener("mouseleave", () => {{
        btn_{key}.style.filter = "none";
    }});
    btn_{key}.addEventListener("click", async () => {{
        try {{
            await navigator.clipboard.writeText({safe_text});
            btn_{key}.innerText = "\u2705";
            setTimeout(() => {{ btn_{key}.innerText = original_{key}; }}, 1200);
        }} catch (err) {{
            btn_{key}.innerText = "\u26a0\ufe0f";
            setTimeout(() => {{ btn_{key}.innerText = original_{key}; }}, 1200);
        }}
    }});
    </script>
    </body></html>
    """
    components.html(html_code, height=35)


# ---------------------------------------------------------------------------
# Callback: Sidebar History checkbox -> Editor Append + Header Reset
# ---------------------------------------------------------------------------
def on_history_check(idx: int, widget_key: str) -> None:
    if not st.session_state.get(widget_key):
        return

    entry = st.session_state["history"][idx]
    block = (
        f"\n\n---\n"
        f"### [{entry['date']} {entry['time']}] {entry['ai']} - {entry['topic']}\n"
        f"{entry['content']}"
    )
    st.session_state["editor_text"] = st.session_state.get("editor_text", "") + block
    reset_header()
    st.session_state[widget_key] = False


# ---------------------------------------------------------------------------
# Callback: Clear / Save
# ---------------------------------------------------------------------------
def do_clear() -> None:
    # 에디터 내용만 지우고 다운로드 캐시는 건드리지 않음
    st.session_state["editor_text"] = ""


def build_report_md(ai: str, header_date: str, time_str: str, topic: str,
                     initial_prompt: str, body: str) -> str:
    return (
        "---\n"
        f"Target_AI: {sanitize_for_yaml(ai)}\n"
        f"Date_Time: {sanitize_for_yaml(header_date)} {sanitize_for_yaml(time_str)}\n"
        f"Topic: {sanitize_for_yaml(topic)}\n"
        "---\n\n"
        "### \U0001F4DD Initial Prompt (Base)\n"
        f"{initial_prompt}\n\n"
        "---\n\n"
        "### \U0001F4A1 Cross-Validation Report (Main Editor)\n"
        f"{body}\n"
    )


def do_save() -> None:
    ai = st.session_state.get("header_ai", "").strip() or DEFAULT_TARGET_AI
    header_date = st.session_state.get("header_date", "").strip() or datetime.now().strftime("%m-%d")
    time_str = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M")
    topic = st.session_state.get("header_topic", "").strip() or "Untitled"
    body = st.session_state.get("editor_text", "")
    initial_prompt = st.session_state.get("initial_prompt", "")

    now = datetime.now()
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_ai = sanitize_for_filename(ai)
    safe_topic = sanitize_for_filename(topic)
    
    unique_id = uuid.uuid4().hex[:6]
    filename = f"{file_timestamp}_{safe_ai}_{safe_topic}_{unique_id}.md"

    md_content = build_report_md(ai, header_date, time_str, topic, initial_prompt, body)

    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}{ext}"
            filepath = os.path.join(SAVE_DIR, filename)
            counter += 1
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        disk_status = ("success", filename)
    except OSError as e:
        disk_status = ("warning", f"Disk write skipped ({e}).")

    st.session_state["history"].insert(
        0,
        {
            "date": header_date,
            "time": time_str,
            "ai": ai,
            "topic": topic,
            "content": body,
            "filename": filename,
        },
    )
    st.session_state["_save_status"] = disk_status


# ---------------------------------------------------------------------------
# Popup Wizard: Setup Cross-Check Workflow (Streamlit 1.34+ Required)
# ---------------------------------------------------------------------------
@st.dialog("🚀 초기 설정: WorkFlow & 프롬프트 생성기", width="large")
def setup_wizard_popup():
    st.markdown("선행기술 및 시장동향 조사를 위한 **AI 크로스체크 프로세스**를 설정합니다.")
    
    topic = st.text_input("🔍 조사 주제", placeholder="예: 2026년 글로벌 전고체 배터리 시장 동향", key="wizard_topic")
    
    col1, col2 = st.columns(2)
    with col1:
        ai1_role = st.selectbox("🤖 선발대 세부 역할 (수집)", [
            "자료 검색 및 광범위한 트렌드 요약", 
            "최신 뉴스 및 통계 데이터 수집", 
            "핵심 기술 및 원리 분석"
        ])
    with col2:
        ai2_role = st.selectbox("⚖️ 검증 세부 역할 (교차검증)", [
            "제공된 자료의 비판적 검토 및 논리적 모순 체크", 
            "경쟁사 대비 약점 분석 및 한계점 지적", 
            "데이터 팩트 체크 및 누락된 시각 보완"
        ])
        
    report_format = st.text_input("📑 인용 스타일 / 세부 포맷", value="마크다운 3단락 (핵심 요약, 세부 분석, 결론 및 전망)", key="wizard_format")

    st.divider()
    if st.button("프롬프트 자동 생성 및 시작", type="primary", use_container_width=True):
        if not topic:
            st.error("조사 주제를 입력해주세요!")
        else:
            generated_prompt = f"""# Cross-AI WorkFlow Blueprint

## 1. 시스템 지시사항 (System Instructions)
- **[역할]** 너는 사회과학 및 관련 분야 체계적 문헌고찰 경험이 있는 연구 보조원이다. (추가 부여 역할: {ai1_role}, {ai2_role})
- **[범위/권한]** 명시된 시기·지역·분야를 벗어난 추론 금지. 출처에 없는 내용은 "근거 부족"으로 명시. 확신 없는 주장은 단정하지 말 것.
- **[제약]** 특정 이론적 입장을 강요하지 말 것. 원문 그대로 인용 금지, 반드시 패러프레이즈 할 것.
- **[포맷 규칙]** 표/불릿 활용, 인용 스타일은 요청 시 지정된 것을 따름. (지정 포맷: {report_format})

## 2. 조사 주제
- **{topic}**

## 3. 크로스체크 프로세스 (AI 역할 분담 및 워크플로우)

**[Step 1: 병렬 리서치] - Gemini, Claude, ChatGPT 공통 수행**
- 3개의 AI는 위 주제에 대하여 독립적으로 초기 데이터와 트렌드를 조사한다.
- 각자의 응답 창에 지시사항에 맞게 패러프레이징 된 기본 조사 내용을 요약하여 출력한다.

**[Step 2: 취합/검증 및 보고서 설계] - Claude 전담 수행**
- Step 1에서 생성된 다른 AI(Gemini, ChatGPT)의 조사 결과물들을 Claude에게 전달한다.
- Claude는 모든 자료를 종합하여 논리적 모순을 비판적으로 교차 검증하고 누락된 팩트를 보완한다.
- 검증된 최종 내용을 바탕으로 Markdown(.md) 형식의 상세한 보고서(설계도)를 작성한다.

**[Step 3: 최종 장표 이미지 생성] - Gemini 전담 수행**
- Step 2에서 완성된 Claude의 마크다운 보고서 설계를 Gemini에게 전달한다.
- Gemini는 해당 보고서를 기반으로, 전체 내용을 시각적으로 요약하는 1장짜리 발표용 장표 이미지를 생성한다.
"""
            st.session_state["editor_text"] = generated_prompt
            
            now = datetime.now()
            st.session_state["header_ai"] = "WorkFlow Blueprint"
            st.session_state["header_topic"] = topic
            st.session_state["header_date"] = now.strftime("%m-%d")
            st.session_state["header_time"] = now.strftime("%H:%M")
            
            do_save()
            
            st.session_state["setup_complete"] = True
            st.rerun()


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------
def render_ai_links() -> None:
    links_html = " &nbsp;\u00b7&nbsp; ".join(
        f'<a href="{url}" target="_blank" style="color:#1a73e8; text-decoration:underline;">{name}</a>'
        for name, url in AI_CHAT_SITES.items()
    )
    st.markdown(
        f"""<div style="
            text-align:right; white-space:nowrap; overflow:hidden;
            font-size:0.9rem; padding-top:1.4rem;
        ">{links_html}</div>""",
        unsafe_allow_html=True,
    )


def render_sidebar_history() -> None:
    st.markdown("### \U0001F4DA History")

    if not st.session_state["history"]:
        st.caption("No saved history yet.")
        return

    for idx, entry in enumerate(st.session_state["history"]):
        label = f"{entry['date']}.{entry['time']}.{entry['ai']}.{entry['topic']}"
        widget_key = f"hist_chk_{entry['filename']}"

        col_chk, col_label = st.columns([1, 8])
        with col_chk:
            st.checkbox(
                "",
                key=widget_key,
                value=False,
                on_change=on_history_check,
                args=(idx, widget_key),
                label_visibility="collapsed",
            )
        with col_label:
            st.markdown(
                f"""<div style='
                    padding-top:0.55rem;
                    font-size:{HISTORY_FONT_SIZE};
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                '>{label}</div>""",
                unsafe_allow_html=True,
            )


def render_base_prompt_area() -> None:
    col_label, col_upload, col_copy = st.columns([3, 1, 1])
    with col_label:
        st.markdown("**xAI WorkFlow**")
    with col_upload:
        with st.popover("\U0001F4C2", help="Load Template (.md)"):
            uploaded_file = st.file_uploader(
                "Load a different WorkFlow template (.md)",
                type=["md"],
                key="_uploader",
            )
            if uploaded_file is not None and uploaded_file.name != st.session_state["_last_uploaded_name"]:
                try:
                    st.session_state["initial_prompt"] = uploaded_file.read().decode("utf-8")
                    st.session_state["_last_uploaded_name"] = uploaded_file.name
                except UnicodeDecodeError:
                    st.warning("Please check the file encoding (UTF-8 recommended).")
    with col_copy:
        clipboard_copy_button(
            st.session_state.get("initial_prompt", ""),
            label="\U0001F4CB",
            key="copy_prompt_btn",
            help_text="Copy WorkFlow Content"
        )

    if st.session_state.get("_last_uploaded_name") is None and st.session_state.get("initial_prompt"):
        st.caption(f"Auto-loaded from `{TEMPLATE_FILENAME}`")

    with st.container(key="workflow_textarea_container"):
        st.text_area(
            "xAI WorkFlow",
            key="initial_prompt",
            height=250,
            placeholder="Enter the base data or initial instructions to send to every AI.",
            label_visibility="collapsed",
        )


def render_editor_actions() -> None:
    col_label, col_clear, col_copy, col_save = st.columns([10, 1, 1, 1], vertical_alignment="center")
    with col_label:
        st.markdown("<span style='font-size: 1.5em; font-weight: bold;'>Editor Window</span>", unsafe_allow_html=True)
    with col_clear:
        with st.container(key="clear_btn_box"):
            st.button("\U0001F5D1\ufe0f", key="_clear_btn", on_click=do_clear,
                       use_container_width=True, help="Clear editor (Header kept)")
    with col_copy:
        clipboard_copy_button(
            st.session_state.get("editor_text", ""),
            label="\U0001F4C4",
            key="copy_editor_btn",
            help_text="Copy Editor Content",
            bg_color="#2ecc71",
        )
    with col_save:
        with st.container(key="save_btn_box"):
            st.button("\U0001F4BE", key="_save_btn", on_click=do_save, type="primary",
                       use_container_width=True, help="Save entry to history")

    if "_save_status" in st.session_state:
        status, msg = st.session_state.pop("_save_status")
        if status == "success":
            st.toast(f"\u2705 Saved to server session: {msg}")
        else:
            st.toast(f"\u26A0\ufe0f {msg}")


def render_main_editor() -> None:
    col_ai, col_date, col_time, col_topic = st.columns([1, 1, 1, 3])
    with col_ai:
        st.text_input("Target AI", key="header_ai", placeholder="e.g. Claude")
    with col_date:
        st.text_input("Date", key="header_date", placeholder="e.g. 07-08")
    with col_time:
        st.text_input("Time", key="header_time", placeholder="e.g. 14:32")
    with col_topic:
        st.text_input("Topic", key="header_topic", placeholder="Conversation topic / title")

    render_editor_actions()

    with st.container(key="main_editor_container"):
        st.text_area(
            "Editor",
            key="editor_text",
            height=590,
            placeholder="Paste an AI reply, or select a previous entry from History on the left to append it.",
            label_visibility="collapsed"
        )

    # -----------------------------------------------------------------------
    # 항상 표시되는 최신 상태 다운로드 버튼
    # -----------------------------------------------------------------------
    current_ai = st.session_state.get("header_ai", "").strip() or DEFAULT_TARGET_AI
    current_date = st.session_state.get("header_date", "").strip() or datetime.now().strftime("%m-%d")
    current_time = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M")
    current_topic = st.session_state.get("header_topic", "").strip() or "Untitled"
    current_initial_prompt = st.session_state.get("initial_prompt", "")
    current_body = st.session_state.get("editor_text", "")

    # 실시간 입력 데이터를 바탕으로 다운로드용 마크다운 동적 생성
    current_md = build_report_md(current_ai, current_date, current_time, current_topic, current_initial_prompt, current_body)
    
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_ai = sanitize_for_filename(current_ai)
    safe_topic = sanitize_for_filename(current_topic)
    unique_id = uuid.uuid4().hex[:6]
    dynamic_filename = f"{file_timestamp}_{safe_ai}_{safe_topic}_{unique_id}.md"

    st.download_button(
        label="DOWNLOAD",
        data=current_md,
        file_name=dynamic_filename,
        mime="text/markdown",
        use_container_width=True,
        help="Download the current editor content to your PC"
    )


def render_help_button() -> None:
    with st.popover("\u2753 Help", help="Show Help Guide"):
        st.markdown(
            f"""
**Quick Guide (Cloud Edition)**
- **AI links**: Click ChatGPT / Claude / Gemini to open in a new tab.
- **xAI WorkFlow**: Shared instructions/base data sent to every AI.
- **History**: Check the box to append that entry into the Editor.
- **Main Editor**: 
  - \U0001F5D1\ufe0f Clear (Clears text only), \U0001F4C4 Copy (Copies text), \U0001F4BE Save (Adds to history).
  - Click Editor box and press Ctrl+V/Cmd+V to paste.
  - Use DOWNLOAD button at the bottom to save the current editor text.
"""
        )


def render_custom_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
        }
        div.stDownloadButton > button, div.stLinkButton > a {
            border-radius: 8px;
        }
        
        /* 모든 버튼 및 팝오버 높이를 35px로 정확히 일치시키고 크기 균형 조정 */
        div.stButton > button, div.stPopover > button {
            padding: 0.1rem 0.3rem !important;
            min-height: unset !important;
            height: 35px !important;
            font-size: 1.2rem !important;
            border-radius: 0.4rem !important;
        }
        
        /* [Clear] 버튼의 배경색을 skyblue 로 변경 */
        .st-key-clear_btn_box div.stButton > button {
            background-color: skyblue !important;
            border: 1px solid gray !important;
            color: black !important;
            box-shadow: none !important;
        }
        .st-key-save_btn_box div.stButton > button {
            background-color: #3498db !important;
            border: 1px solid gray !important;
            color: white !important;
        }
        .st-key-clear_btn_box div.stButton > button:hover,
        .st-key-save_btn_box div.stButton > button:hover {
            filter: brightness(1.1);
        }
        
        /* 좌측 WorkFlow 창 내용의 폰트 크기를 8pt 수준(약 0.68rem)으로 축소하고 줄간격 강제 제거 */
        .st-key-workflow_textarea_container div[data-testid="stTextArea"] textarea {
            font-size: 0.68rem !important;
            line-height: 1.0 !important;
            padding: 0.4rem !important;
        }
        
        /* 에디터 윈도우가 너무 올라와 겹치던 문제를 해결하기 위해 마진을 약 5mm(19px) 아래로 조정 */
        .st-key-main_editor_container {
            margin-top: -5px !important;
        }
        
        [data-testid="stAppViewContainer"] .block-container {
            padding-top: 1.5rem;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Cross-AI Prompt Manager",
        page_icon="\U0001F6E0\ufe0f",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    
    # 최초 진입 시 Setup 팝업 띄우기
    if not st.session_state.get("setup_complete"):
        setup_wizard_popup()

    render_custom_css()

    with st.sidebar:
        render_base_prompt_area()
        st.divider()
        render_sidebar_history()

    col_title, col_links, col_help = st.columns(
        [6, 2.5, 0.8], vertical_alignment="top"
    )
    with col_title:
        st.title("\U0001F6E0\ufe0f Cross-AI Prompt Manager")
    with col_links:
        render_ai_links()
    with col_help:
        st.markdown("<div style='height:0.7cm;'></div>", unsafe_allow_html=True)
        render_help_button()

    render_main_editor()


if __name__ == "__main__":
    main()