# xAIPM_beta.py
# Cross-AI Prompt Manager - Cloud Edition (UI Optimized)

import base64
import io
import json
import os
import uuid
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from streamlit_quill import st_quill
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------
DEFAULT_TARGET_AI = "Claude"
TEMPLATE_FILENAME = "WorkFlowTemplate.md"
BLUEPRINT_TEMPLATE_FILENAME = "BlueprintTemplate.md"
HELP_CONTENT_FILENAME = "HelpContent.md"

AI_CHAT_SITES = {
    "ChatGPT": "https://chatgpt.com",
    "Claude": "https://claude.ai",
    "Gemini": "https://gemini.google.com",
}

QUILL_TOOLBAR = [
    [{"header": [1, 2, 3, False]}],
    ["bold", "italic", "strike", "blockquote"],
    [{"list": "ordered"}, {"list": "bullet"}],
    ["link", "image", "code-block"],
    ["clean"]
]

# ---------------------------------------------------------------------------
# Auto-generated Workflow Diagram (Claude draws it — no user upload needed)
# ---------------------------------------------------------------------------
def _load_diagram_font(size: int, bold: bool = True):
    """시스템에 TrueType 폰트가 있으면 사용하고, 없으면 Pillow 기본 폰트로 대체."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)  # Pillow 10+
    except TypeError:
        return ImageFont.load_default()

def _truncate(text: str, max_len: int = 42) -> str:
    text = (text or "").strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"

def _wrap_text(draw: "ImageDraw.ImageDraw", text: str, font, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def build_workflow_diagram_png(ai1_role: str, ai2_role: str) -> bytes:
    """Cross-AI 교차검증 워크플로우(Parallel Research -> Cross-Validation ->
    Claude Synthesis -> Gemini Report) 개념도를 PNG로 렌더링해서 반환.
    사용자 업로드가 아니라 항상 자동으로 생성됨.
    다크그레이 라운드 카드 배경 + 그림자 처리된 고딕 타이틀."""
    width, height = 1080, 340
    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    # --- 어두운 회색 rounded-edge 카드 배경 (모서리 바깥은 투명) ---
    margin = 10
    draw.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=28, fill="#262A31",
    )

    box_w, box_h = 220, 190
    gap = 44
    start_x = 40
    top_y = 96

    steps = [
        ("STEP 1", "Parallel Multi-AI Research", "Gemini · Claude · ChatGPT", "#E8F0FE", "#1A73E8"),
        ("STEP 2", "Cross-Validation", _truncate(ai2_role or "Cross-check for gaps & contradictions"), "#FEF7E0", "#B26A00"),
        ("STEP 3", "Claude Synthesis", "Consolidate into one report", "#E6F4EA", "#1E7E34"),
        ("STEP 4", "Gemini Report", "Final polished deliverable", "#F3E8FD", "#7627BB"),
    ]

    tag_font = _load_diagram_font(15)
    step_title_font = _load_diagram_font(18)
    sub_font = _load_diagram_font(13, bold=False)
    title_font = _load_diagram_font(26)

    # --- 타이틀: Gothic(볼드 산세리프) + 소프트 드롭섀도우 ---
    title_text = "Cross-AI Cross-Validation Workflow"
    title_pos = (width / 2, 44)
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).text(
        (title_pos[0] + 3, title_pos[1] + 4), title_text, font=title_font,
        fill=(0, 0, 0, 200), anchor="mm",
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3))
    base = Image.alpha_composite(base, shadow_layer)
    draw = ImageDraw.Draw(base)
    draw.text(title_pos, title_text, font=title_font, fill="#F5F6F7", anchor="mm")

    x = start_x
    right_edges = []
    for tag, step_title, sub, fill, border in steps:
        draw.rounded_rectangle([x, top_y, x + box_w, top_y + box_h], radius=16, fill=fill, outline=border, width=3)
        draw.text((x + box_w / 2, top_y + 26), tag, font=tag_font, fill=border, anchor="mm")

        # 타이틀이 박스 폭보다 길면 줄바꿈하되, 줄마다 y좌표를 증가시켜 겹침 방지
        title_lines = _wrap_text(draw, step_title, step_title_font, box_w - 24)[:2]
        line_h = 24
        ty = top_y + 62 - (len(title_lines) - 1) * line_h / 2
        for line in title_lines:
            draw.text((x + box_w / 2, ty), line, font=step_title_font, fill="#202124", anchor="mm")
            ty += line_h

        sub_lines = _wrap_text(draw, sub, sub_font, box_w - 24)[:3]
        sy = top_y + box_h - 18 * len(sub_lines) - 16
        for line in sub_lines:
            draw.text((x + box_w / 2, sy), line, font=sub_font, fill="#5f6368", anchor="mm")
            sy += 18

        right_edges.append((x + box_w, top_y + box_h / 2))
        x += box_w + gap

    for x0, cy in right_edges[:-1]:
        x1 = x0 + gap
        draw.line([x0 + 4, cy, x1 - 12, cy], fill="#D7DCE3", width=3)
        draw.polygon([(x1 - 12, cy - 8), (x1 - 12, cy + 8), (x1, cy)], fill="#D7DCE3")

    buffer = io.BytesIO()
    base.convert("RGBA").save(buffer, format="PNG")
    return buffer.getvalue()

# ---------------------------------------------------------------------------
# State Initialization
# ---------------------------------------------------------------------------
def collapse_blank_lines(text: str) -> str:
    """연속된 빈 줄(2줄 이상)을 1줄로 압축해서 사이드바 표시 줄간격을 줄임."""
    if not text:
        return text
    lines = text.splitlines()
    result = []
    prev_blank = False
    for line in lines:
        is_blank = (line.strip() == "")
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return "\n".join(result)

def compute_workflow_height(text: str, min_px: int = 90, max_px: int = 220) -> int:
    """WorkFlow 텍스트의 실제 줄 수에 맞춰 여백을 최소화한 박스 높이(px)를 계산."""
    line_count = max(1, len((text or "").splitlines()))
    estimated = 24 + line_count * 15  # 0.7rem 폰트 + line-height 1.05 기준 1줄 ≈ 15px
    return max(min_px, min(max_px, estimated))

def load_default_prompt_template() -> str:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, TEMPLATE_FILENAME)
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return collapse_blank_lines(f.read())
    except OSError:
        pass
    return ""

def init_state() -> None:
    if "setup_complete" not in st.session_state:
        st.session_state["setup_complete"] = False
        
    if "history" not in st.session_state:
        st.session_state["history"] = []
        
    if "editor_content" not in st.session_state:
        st.session_state["editor_content"] = ""
        
    if "editor_key" not in st.session_state:
        st.session_state["editor_key"] = str(uuid.uuid4())
        
    if "initial_prompt" not in st.session_state:
        st.session_state["initial_prompt"] = load_default_prompt_template()

    if "_last_uploaded_name" not in st.session_state:
        st.session_state["_last_uploaded_name"] = None
        
    if "header_ai" not in st.session_state:
        reset_header()

def reset_header() -> None:
    now = datetime.now()
    st.session_state["header_ai"] = DEFAULT_TARGET_AI
    st.session_state["header_date"] = now.strftime("%Y-%m-%d")
    st.session_state["header_time"] = now.strftime("%H:%M:%S")
    st.session_state["header_topic"] = ""

# ---------------------------------------------------------------------------
# Core Actions
# ---------------------------------------------------------------------------
def replace_editor_content(html: str) -> None:
    """에디터 내용을 교체하고 st_quill 위젯을 강제로 remount(새 key 발급)함.
    st_quill(value=..., key=...)는 key가 그대로면 value 변경을 무시하므로,
    화면에 새 내용을 반영하려면 반드시 key도 함께 갱신해야 함."""
    st.session_state["editor_content"] = html
    st.session_state["editor_key"] = str(uuid.uuid4())

def do_clear() -> None:
    replace_editor_content("")

def do_save(current_html: str) -> bool:
    """History에 저장만 수행. 에디터 내용을 지우거나 바꾸는 부수효과는 없음."""
    if not current_html or current_html.strip() == "<p><br></p>":
        st.toast("⚠️ Editor is empty!")
        return False

    ai = st.session_state.get("header_ai", "").strip() or DEFAULT_TARGET_AI
    date_str = st.session_state.get("header_date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    time_str = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M:%S")
    topic = st.session_state.get("header_topic", "").strip() or "Untitled"
    
    unique_id = uuid.uuid4().hex[:8]

    record = {
        "id": unique_id,
        "date": date_str,
        "time": time_str,
        "ai": ai,
        "topic": topic,
        "html_content": current_html
    }

    st.session_state["history"].insert(0, record)
    st.toast("✅ Saved to Session History!")
    return True

def load_history_to_editor(record_id: str) -> None:
    record = next((item for item in st.session_state["history"] if item["id"] == record_id), None)
    if record:
        replace_editor_content(record["html_content"])
        st.session_state["header_ai"] = record["ai"]
        st.session_state["header_topic"] = record["topic"]

# ---------------------------------------------------------------------------
# Externalized Blueprint Template (developer-editable, no Python needed)
# ---------------------------------------------------------------------------
DEFAULT_BLUEPRINT_TEMPLATE = """<h2>Cross-AI WorkFlow Blueprint</h2>
<h3>1. System Instructions</h3>
<ul>
    <li><strong>[Role]</strong> You are a research assistant. (Assigned roles: {ai1_role}, {ai2_role})</li>
    <li><strong>[Scope]</strong> Do not infer beyond the specified bounds. Explicitly state "Insufficient evidence" if needed.</li>
    <li><strong>[Format Rules]</strong> Follow the specified style: {report_format}</li>
</ul>
<p><br></p>
<h3>2. Research Topic : {topic}</h3>
<p><br></p>
<h3>Workflow Diagram</h3>
{diagram_html}
<p><br></p>
<h3>3. Cross-AI Cross-Validation Workflow</h3>
<p><strong>[Step 1] Parallel Research:</strong> Gemini, Claude, and ChatGPT independently research the topic and submit initial findings. <em>Role: {ai1_role}.</em></p>
<p><strong>[Step 2] Cross-Validation:</strong> Each AI's findings are cross-checked against the others for factual accuracy, contradictions, and gaps. <em>Role: {ai2_role}.</em></p>
<p><strong>[Step 3] Claude Synthesis:</strong> Claude consolidates all cross-validated findings into a single, coherent, well-structured report.</p>
<p><strong>[Step 4] Gemini Report Generation:</strong> Gemini turns Claude's consolidated report into the final polished deliverable (presentation slide or visual summary).</p>
"""

def load_blueprint_template() -> str:
    """BlueprintTemplate.md 파일이 있으면 그걸 사용(개발자가 Python 코드 없이 수정 가능),
    없으면 코드 내장 기본값 사용. 사용 가능한 placeholder:
    {ai1_role} {ai2_role} {report_format} {topic} {diagram_html}"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, BLUEPRINT_TEMPLATE_FILENAME)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass
    return DEFAULT_BLUEPRINT_TEMPLATE

# ---------------------------------------------------------------------------
# Initial Setup Wizard (Pop-up)
# ---------------------------------------------------------------------------
@st.dialog("🚀 Initial Setup: WorkFlow & Prompt Generator", width="large")
def setup_wizard_popup():
    st.markdown(
        "Set up the **Cross-AI Cross-Validation Workflow**: "
        "**Parallel Research → Cross-Validation → Claude Synthesis → Gemini Report**."
    )
    topic = st.text_input("🔍 Research Topic", placeholder="e.g., 2026년 글로벌 전고체 배터리 시장 동향", key="wizard_topic")
    col1, col2 = st.columns(2)
    with col1:
        ai1_role = st.selectbox("🤖 Step 1: Parallel Research Role", [
            "Data search and comprehensive trend summary",
            "Collect latest news and statistical data",
            "Analyze core technologies and principles"
        ])
    with col2:
        ai2_role = st.selectbox("⚖️ Step 2: Cross-Validation Role", [
            "Critical review of provided data and logical contradiction check",
            "Analyze weaknesses compared to competitors and point out limitations",
            "Fact-check data and supplement missing perspectives"
        ])
    report_format = st.text_input("📑 Citation Style / Detail Format", value="3-paragraph Markdown (Key Summary, Detailed Analysis, Conclusion)")
    st.caption("🖼️ A Cross-AI workflow diagram will be auto-generated and embedded in the Blueprint below.")

    st.divider()
    if st.button("Generate Prompt & Start", use_container_width=True):
        if not topic:
            st.error("Please enter a research topic!")
        else:
            diagram_png = build_workflow_diagram_png(ai1_role, ai2_role)
            diagram_b64 = base64.b64encode(diagram_png).decode("utf-8")
            diagram_html = f'<p><img src="data:image/png;base64,{diagram_b64}" style="max-width:100%; border-radius:6px;" /></p>'

            template = load_blueprint_template()
            fill_values = {
                "ai1_role": ai1_role,
                "ai2_role": ai2_role,
                "report_format": report_format,
                "topic": topic,
                "diagram_html": diagram_html,
            }
            try:
                generated_html = template.format(**fill_values)
            except (KeyError, IndexError, ValueError) as e:
                st.warning(f"⚠️ BlueprintTemplate.md formatting error ({e}) — falling back to default template.")
                generated_html = DEFAULT_BLUEPRINT_TEMPLATE.format(**fill_values)

            replace_editor_content(generated_html)
            st.session_state["header_ai"] = "WorkFlow Blueprint"
            st.session_state["header_topic"] = topic
            now = datetime.now() + timedelta(seconds=1)  # 초기 팝업 첫 History 항목: Time을 1초 뒤로
            st.session_state["header_date"] = now.strftime("%Y-%m-%d")
            st.session_state["header_time"] = now.strftime("%H:%M:%S")
            do_save(generated_html)
            st.session_state["setup_complete"] = True
            st.rerun()

# ---------------------------------------------------------------------------
# HTML Exporter
# ---------------------------------------------------------------------------
def generate_standalone_html() -> str:
    history_json = json.dumps(st.session_state["history"], ensure_ascii=False)
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xAIPM Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 2rem; background: #f9f9f9; }}
        .report-card {{ background: #fff; border-radius: 8px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eaeaea; }}
        .meta-header {{ border-bottom: 2px solid #f0f0f0; padding-bottom: 1rem; margin-bottom: 1.5rem; font-size: 0.9rem; color: #666; }}
        .meta-header h2 {{ margin: 0 0 0.5rem 0; color: #111; font-size: 1.5rem; }}
        .content img {{ max-width: 100%; height: auto; border-radius: 4px; }}
        .content pre {{ background: #f4f4f4; padding: 1rem; border-radius: 4px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ccc; margin: 0; padding-left: 1rem; color: #555; }}
    </style>
</head>
<body>
    <h1>📋 Cross-AI Research Report</h1>
    <p><em>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</em></p>
    <hr>
    <div id="content-container"></div>
    <script type="application/json" id="xaipm-data">{history_json}</script>
    <script>
        const rawData = document.getElementById('xaipm-data').textContent;
        const historyData = JSON.parse(rawData);
        const container = document.getElementById('content-container');
        if (historyData.length === 0) {{ container.innerHTML = "<p>No data recorded in this session.</p>"; }} 
        else {{
            historyData.forEach(item => {{
                const card = document.createElement('div'); card.className = 'report-card';
                card.innerHTML = `<div class="meta-header"><h2>${{item.topic || 'Untitled'}}</h2><strong>AI:</strong> ${{item.ai}} &nbsp;|&nbsp; <strong>Date:</strong> ${{item.date}} ${{item.time}}</div><div class="content">${{item.html_content}}</div>`;
                container.appendChild(card);
            }});
        }}
    </script>
</body>
</html>
"""
    return html_template

# ---------------------------------------------------------------------------
# UI Rendering Modules
# ---------------------------------------------------------------------------
def render_base_prompt_area() -> None:
    col_label, col_upload = st.columns([3, 1.2])
    with col_label:
        st.markdown("**xAI WorkFlow**")
    with col_upload:
        with st.popover("📁", help="Load Template (.md)"):
            uploaded_file = st.file_uploader("Load a different WorkFlow template (.md)", type=["md"], key="_uploader")
            if uploaded_file is not None and uploaded_file.name != st.session_state["_last_uploaded_name"]:
                try:
                    st.session_state["initial_prompt"] = collapse_blank_lines(uploaded_file.read().decode("utf-8"))
                    st.session_state["_last_uploaded_name"] = uploaded_file.name
                except UnicodeDecodeError:
                    st.warning("Please check file encoding.")

    if st.session_state.get("_last_uploaded_name") is None and st.session_state.get("initial_prompt"):
        st.caption(f"Auto-loaded from `{TEMPLATE_FILENAME}`")

    st.text_area(
        "xAI WorkFlow Base Text",
        key="initial_prompt",
        height=compute_workflow_height(st.session_state.get("initial_prompt", "")),
        placeholder="Enter base workflow guidelines here...",
        label_visibility="collapsed",
    )

def render_multipart_copy_button(html_content: str) -> None:
    safe_html = json.dumps(html_content or "")
    # JS 버튼의 스타일도 Streamlit 기본 버튼(흰색 배경, 회색 테두리)과 동일하게 맞춤
    html_code = f"""
    <html><body style="margin:0;padding:0;background:transparent;">
    <button id="copy-btn" title="Copy as Rich Text" style="
        width:100%; height:35px; border:1px solid rgba(49, 51, 63, 0.2); border-radius:0.4rem;
        background-color:#ffffff; color:#31333F; cursor:pointer; font-size:0.85rem; font-family:sans-serif;
        display:flex; align-items:center; justify-content:center; padding: 0.25rem 0.5rem; white-space:nowrap;">
        📋 Copy
    </button>
    <script>
    const btn = document.getElementById("copy-btn");
    btn.addEventListener("mouseover", () => {{ btn.style.borderColor = "#ff4b4b"; btn.style.color = "#ff4b4b"; }});
    btn.addEventListener("mouseout", () => {{ btn.style.borderColor = "rgba(49, 51, 63, 0.2)"; btn.style.color = "#31333F"; }});
    btn.addEventListener("click", async () => {{
        try {{
            const rawHtml = {safe_html};
            const tempDiv = document.createElement("div"); tempDiv.innerHTML = rawHtml;
            const plainText = tempDiv.innerText;
            const blobHtml = new Blob([rawHtml], {{ type: "text/html" }});
            const blobText = new Blob([plainText], {{ type: "text/plain" }});
            const clipboardItem = new ClipboardItem({{ "text/html": blobHtml, "text/plain": blobText }});
            await navigator.clipboard.write([clipboardItem]);
            btn.innerText = "✅ Done"; setTimeout(() => {{ btn.innerText = "📋 Copy"; }}, 1500);
        }} catch (err) {{
            btn.innerText = "⚠️ Err"; setTimeout(() => {{ btn.innerText = "📋 Copy"; }}, 1500);
        }}
    }});
    </script>
    </body></html>
    """
    components.html(html_code, height=35)

def inject_dynamic_editor_resize(bottom_reserve_px: int = 90, min_height_px: int = 320) -> None:
    """CSS의 calc(100vh - Xpx)는 화면/사이드바 상태에 따라 오차가 생길 수 있어,
    실제 렌더링 후 남은 공간을 JS로 재계산해 Quill iframe 높이에 덮어씀."""
    components.html(
        f"""
        <script>
        function resizeQuillEditor() {{
            try {{
                const doc = window.parent.document;
                const frame = doc.querySelector('iframe[title="streamlit_quill"]');
                if (!frame) return;
                const rect = frame.getBoundingClientRect();
                const viewportHeight = window.parent.innerHeight;
                let newHeight = viewportHeight - rect.top - {bottom_reserve_px};
                if (newHeight < {min_height_px}) newHeight = {min_height_px};
                frame.style.height = newHeight + "px";
            }} catch (err) {{ /* cross-origin or not mounted yet: ignore */ }}
        }}
        resizeQuillEditor();
        setTimeout(resizeQuillEditor, 200);
        setTimeout(resizeQuillEditor, 600);
        window.parent.addEventListener('resize', resizeQuillEditor);
        </script>
        """,
        height=0,
    )

DEFAULT_HELP_CONTENT = """**Quick Guide (Rich Text MVP)**
- **AI links**: Click ChatGPT / Claude / Gemini to open in a new tab.
- **xAI WorkFlow**: Shared instructions/base data loaded in the sidebar.
- **Setup Wizard**: Generates a Cross-AI Blueprint following Parallel Research → Cross-Validation → Claude Synthesis → Gemini Report, with an auto-generated workflow diagram embedded automatically (no upload needed).
- **History**: Click any saved card on the left sidebar to restore it to the editor.
- **Main Editor**: 
  - 🧹 Clear (Wipes editor canvas), 💾 Save Session (Pushes into session memory).
  - Use **DownLoad(HTML)** below the editor to backup your records to local PC.
"""

def load_help_content() -> str:
    """HelpContent.md 파일이 있으면 그걸 사용(개발자가 Python 코드 없이 수정 가능),
    없으면 코드 내장 기본값 사용."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, HELP_CONTENT_FILENAME)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass
    return DEFAULT_HELP_CONTENT

def render_help_button() -> None:
    with st.popover("❓ Help", help="Show Help Guide"):
        st.markdown(load_help_content())

# ---------------------------------------------------------------------------
# Main Application Entry
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="xAIPM (Rich Text)", page_icon="🛠️", layout="wide")
    init_state()

    # header_ai/date/time/topic 위젯이 생성되기 전에 반드시 먼저 처리해야 함.
    # (위젯 인스턴스화 이후에는 st.session_state[해당 key] 재할당이 예외를 발생시킴)
    if st.session_state.pop("_pending_header_reset", False):
        reset_header()

    if not st.session_state.get("setup_complete"):
        setup_wizard_popup()

    # --- 통합 CSS 주입 ---
    st.markdown("""
        <style>
        /* 1. 전체 상하 여백 축소 + Streamlit 상단 툴바에 타이틀이 가리지 않도록 여유 확보(5mm 추가 하강) */
        .block-container { padding-top: 2.7rem !important; padding-bottom: 1rem !important; }
        
        /* 2. 모든 버튼의 기본 높이 및 폰트 통일 (Clear/Copy 등 라벨 줄바꿈 방지) */
        .stButton>button, .stDownloadButton>button { 
            height: 35px !important; 
            border-radius: 6px !important; 
            padding: 0.25rem 0.5rem !important;
            white-space: nowrap !important;
        }
        .stButton>button p, .stDownloadButton>button p {
            font-size: 0.85rem !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        /* 3. 사이드바 History 버튼 글자 크기 축소 (줄바꿈 방지) */
        [data-testid="stSidebar"] .stButton>button p {
            font-size: 0.75rem !important;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* 3-1. History 박스 내부 여백 축소 + 박스 사이 간격 축소 */
        .st-key-history_list_wrap .stButton>button {
            height: 26px !important;
            padding: 0.1rem 0.4rem !important;
            justify-content: flex-start !important;
        }
        /* 라벨을 감싸는 요소가 버전에 따라 p / div[stMarkdownContainer] 등으로 달라서
           둘 다 잡고, width:100%로 박스를 채워야 text-align이 실제로 보임 */
        .st-key-history_list_wrap .stButton>button div[data-testid="stMarkdownContainer"],
        .st-key-history_list_wrap .stButton>button p {
            width: 100% !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }
        .st-key-history_list_wrap div[data-testid="stElementContainer"],
        .st-key-history_list_wrap div[data-testid="element-container"] {
            margin-bottom: 0.15rem !important;
        }
        
        /* 4. 좌측 WorkFlow 텍스트 영역 폰트크기 축소 + 줄간격/여백 최소화 */
        .st-key-initial_prompt textarea {
            font-size: 0.7rem !important;
            line-height: 1.05 !important;
            padding: 0.3rem 0.4rem !important;
        }

        /* 4-1. 상단 ChatGPT | Claude | Gemini 링크: 일반 하이퍼링크 스타일(밑줄) */
        .xaipm-ai-link {
            color: #1a73e8 !important;
            text-decoration: underline !important;
            font-weight: 500 !important;
        }
        .xaipm-ai-link:hover {
            color: #0b57d0 !important;
            text-decoration: underline !important;
        }
        .xaipm-ai-link:visited {
            color: #6b2fb3 !important;
        }
        
        /* 5. 에디터 높이를 브라우저 해상도에 맞춰 헤더~버튼바 사이를 꽉 채우도록 확장
              (주의: streamlit_quill 컴포넌트의 실제 iframe title 은 'streamlit_quill' 이지
               'streamlit_quill.st_quill'이 아님 — 이전 선택자는 아무 요소와도 매치되지 않았음) */
        iframe[title="streamlit_quill"] {
            height: calc(100vh - 330px) !important;
            min-height: 320px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Sidebar ---
    with st.sidebar:
        render_base_prompt_area()
        st.divider()
        st.markdown("### 💾 Session History")
        
        if not st.session_state["history"]:
            st.caption("No history in this session yet.")
        else:
            with st.container(key="history_list_wrap"):
                for item in st.session_state["history"]:
                    label = f"{item['time']}_{item['ai']}_{item['topic']}"
                    if st.button(f"📄 {label}", key=f"btn_{item['id']}", use_container_width=True):
                        load_history_to_editor(item['id'])
                        st.rerun()

    # --- Main Header Layout ---
    col_title, col_links, col_help = st.columns([6, 3, 1], vertical_alignment="top")
    with col_title:
        # 타이틀 위아래 마진 제거하여 공간 최소화
        st.markdown("<h1 style='margin-top: 0; margin-bottom: -0.5rem;'>🛠️ Cross-AI Prompt Manager</h1>", unsafe_allow_html=True)
    with col_links:
        links_html = " &nbsp;|&nbsp; ".join(f'<a href="{url}" target="_blank" class="xaipm-ai-link">{name}</a>' for name, url in AI_CHAT_SITES.items())
        st.markdown(f"<div style='text-align:right; padding-top: 0.5rem;'>{links_html}</div>", unsafe_allow_html=True)
    with col_help:
        st.markdown("<div style='height: 0.2rem;'></div>", unsafe_allow_html=True)
        render_help_button()

    # 회색 구분선(st.divider) 삭제됨

    # --- Editor Metadata Ribbon ---
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True) # 헤더와 폼 사이 미세 조정
    col_ai, col_date, col_time, col_topic = st.columns([2, 2, 2, 6])
    with col_ai:
        st.text_input("Target AI", key="header_ai", placeholder="e.g. Claude")
    with col_date:
        st.text_input("Date", key="header_date")
    with col_time:
        st.text_input("Time", key="header_time")
    with col_topic:
        st.text_input("Topic", key="header_topic", placeholder="Research topic...")

    # --- Rich Text Editor Setup ---
    # 겹침 현상 해결: margin-bottom을 0.2rem으로 변경하여 에디터 박스 밖으로 텍스트를 안전하게 분리
    st.markdown("<div style='color: gray; font-size: 0.85rem; font-weight: bold; margin-top: 0.5rem; margin-bottom: 0.2rem;'>Editor</div>", unsafe_allow_html=True)
    
    current_content = st_quill(
        value=st.session_state["editor_content"],
        placeholder="Paste AI response here (Ctrl+V for images, markdown, and text)...",
        html=True,
        toolbar=QUILL_TOOLBAR,
        key=st.session_state["editor_key"]
    )
    inject_dynamic_editor_resize()

    # --- Action Bar ---
    # 버튼 이름을 변경하고 type="primary"를 제거하여 흰색/회색 스타일로 통일
    col_download, col_empty, col_clear, col_copy, col_save = st.columns([2.5, 3.6, 1.4, 1.5, 2.0], vertical_alignment="center")
    with col_download:
        download_html = generate_standalone_html()
        st.download_button(
            label="📥 DownLoad(HTML)",
            data=download_html,
            file_name=f"xAIPM_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            use_container_width=True
            # type="primary" 제거됨
        )
    with col_clear:
        if st.button("🧹 Clear", use_container_width=True):
            do_clear()
            st.rerun()
    with col_copy:
        render_multipart_copy_button(current_content)
    with col_save:
        if st.button("💾 Save Session", use_container_width=True): # type="primary" 제거됨
            if do_save(current_content):
                do_clear()
                st.session_state["_pending_header_reset"] = True
                st.rerun()

if __name__ == "__main__":
    main()