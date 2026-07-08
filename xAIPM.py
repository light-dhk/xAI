"""
Cross-AI Prompt Manager - MVP
Design doc: 260709_BluePrint_Cross-AI_Prompt_Manager_v1.3.md

Runtime: Windows only, fully local (streamlit run xAIPM.py)
"""

import os
import re
import webbrowser
from datetime import datetime

try:
    import pyperclip
except ImportError:
    pyperclip = None  # Guarded with a None check in do_paste()
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAVE_DIR = "saved_reports"
AI_OPTIONS = ["ChatGPT", "Claude", "Gemini", "Other"]
TEMPLATE_FILENAME = "PromptTemplate.md"  # Auto-loaded at startup if present next to xAIPM.py (Base Prompt Area)
EDITOR_TEMPLATE_FILENAME = "EditorTemplate.md"  # Auto-loaded at startup if present next to xAIPM.py (Main Editor)

# History row font size. Default body text is ~1rem; this is roughly 1/3 of
# that while staying legible. Lower it further (e.g. "0.4rem") if you want it
# even smaller — combined with the nowrap/ellipsis CSS below it will still
# render as a single line either way.
HISTORY_FONT_SIZE = "0.62rem"

# AI chat sites opened as browser tabs on startup.
# Note: the official Anthropic Claude site is claude.ai (not claude.io).
AI_CHAT_URLS = [
    "https://chatgpt.com",
    "https://claude.ai",
    "https://gemini.google.com",
]


# ---------------------------------------------------------------------------
# State initialization (session_state)
# ---------------------------------------------------------------------------
def load_default_prompt_template() -> str:
    """
    Auto-load PromptTemplate.md from the same folder as xAIPM.py at startup.
    Returns an empty string if the file is missing or unreadable (editor starts blank).
    """
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
    """
    Auto-load EditorTemplate.md from the same folder as xAIPM.py at startup.
    Returns an empty string if the file is missing or unreadable.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, EDITOR_TEMPLATE_FILENAME)
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass
    return ""


def open_ai_chat_tabs_once() -> None:
    """
    Open ChatGPT / Claude / Gemini in new browser tabs, once per session.
    Guarded by a session flag because Streamlit reruns the whole script on every
    widget interaction — without the guard, tabs would reopen on every click.
    """
    if not st.session_state.get("_ai_tabs_opened", False):
        for url in AI_CHAT_URLS:
            try:
                webbrowser.open_new_tab(url)
            except Exception:
                pass
        st.session_state["_ai_tabs_opened"] = True


def init_state() -> None:
    # initial_prompt is auto-loaded from PromptTemplate.md once per session only.
    if "initial_prompt" not in st.session_state:
        st.session_state["initial_prompt"] = load_default_prompt_template()

    # editor_text is auto-loaded from EditorTemplate.md once per session, and if
    # non-empty, is also surfaced as a History entry (no saved_reports file is
    # written yet — actual disk save still only happens via the [Save] button;
    # this just previews the template as a History row too).
    if "editor_text" not in st.session_state:
        editor_template = load_default_editor_template()
        st.session_state["editor_text"] = editor_template
        if editor_template:
            st.session_state.setdefault("history", [])
            now = datetime.now()
            st.session_state["history"].insert(
                0,
                {
                    "date": now.strftime("%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "ai": "Template",
                    "topic": "Initial Editor Template",
                    "content": editor_template,
                    "filename": "__editor_template__",
                },
            )

    if "header_ai" not in st.session_state:
        reset_header()

    defaults = {
        "history": [],  # [{date, time, ai, topic, content, filename}, ...] LIFO (index 0 = newest)
        "_last_uploaded_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def sanitize_for_filename(text: str) -> str:
    """Replace characters that would break a filename or YAML frontmatter."""
    if not text:
        return "untitled"
    cleaned = re.sub(r'[\\/*?:"<>|\r\n]', "_", text).strip()
    return cleaned or "untitled"


def sanitize_for_yaml(text: str) -> str:
    """Replace colons/newlines that would break YAML frontmatter parsing."""
    if not text:
        return ""
    return text.replace("\n", " ").replace(":", "-")


def reset_header() -> None:
    """
    Reset Header (AI/date/time/topic). Date/Time default to the current
    date/time for convenience (the user can still edit them); Topic stays
    blank since it's unique per entry. (Shared by init / Reset-on-Append / Clear)
    """
    now = datetime.now()
    st.session_state["header_ai"] = AI_OPTIONS[0]
    st.session_state["header_date"] = now.strftime("%m-%d")
    st.session_state["header_time"] = now.strftime("%H:%M")
    st.session_state["header_topic"] = ""


# ---------------------------------------------------------------------------
# Callback: Sidebar History checkbox -> Editor Append + Header Reset
# ---------------------------------------------------------------------------
def on_history_check(idx: int, widget_key: str) -> None:
    """
    Append only fires the instant the checkbox flips to True, then the checkbox
    is immediately reset back to False so the same entry can be appended again
    later. (Using a checkbox as a momentary "trigger button" rather than a toggle.)
    """
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

    # Reset the checkbox back to False so it can be reused
    st.session_state[widget_key] = False


# ---------------------------------------------------------------------------
# Callback: Paste / Clear / Save
# ---------------------------------------------------------------------------
def do_paste() -> None:
    if pyperclip is None:
        st.session_state["_paste_status"] = (
            "error",
            "The pyperclip module is not installed. Please run 'pip install pyperclip'.",
        )
        return

    try:
        clipboard_text = pyperclip.paste()
    except pyperclip.PyperclipException:
        clipboard_text = ""

    if not clipboard_text:
        st.session_state["_paste_status"] = (
            "warning",
            "Clipboard is empty or does not contain readable text.",
        )
        return

    current = st.session_state.get("editor_text", "")
    separator = "\n\n" if current else ""
    st.session_state["editor_text"] = current + separator + clipboard_text
    st.session_state["_paste_status"] = ("success", "Clipboard content pasted.")


def do_copy_prompt() -> None:
    """Copy the current Initial Prompt content to the system clipboard, so it
    can be quickly pasted into ChatGPT / Claude / Gemini's chat windows."""
    if pyperclip is None:
        st.session_state["_prompt_copy_status"] = (
            "error",
            "The pyperclip module is not installed. Please run 'pip install pyperclip'.",
        )
        return

    try:
        pyperclip.copy(st.session_state.get("initial_prompt", ""))
        st.session_state["_prompt_copy_status"] = ("success", "Initial Prompt copied to clipboard.")
    except pyperclip.PyperclipException as e:
        st.session_state["_prompt_copy_status"] = ("error", f"Copy failed: {e}")


def do_copy_editor() -> None:
    """Copy the entire Editor content to the system clipboard."""
    if pyperclip is None:
        st.session_state["_editor_copy_status"] = (
            "error",
            "The pyperclip module is not installed. Please run 'pip install pyperclip'.",
        )
        return

    try:
        pyperclip.copy(st.session_state.get("editor_text", ""))
        st.session_state["_editor_copy_status"] = ("success", "Editor content copied to clipboard.")
    except pyperclip.PyperclipException as e:
        st.session_state["_editor_copy_status"] = ("error", f"Copy failed: {e}")


def do_clear() -> None:
    st.session_state["editor_text"] = ""
    reset_header()


def do_save() -> None:
    ai = st.session_state.get("header_ai", "").strip() or AI_OPTIONS[0]
    header_date = st.session_state.get("header_date", "").strip() or datetime.now().strftime("%m-%d")
    time_str = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M")
    topic = st.session_state.get("header_topic", "").strip() or "Untitled"
    body = st.session_state.get("editor_text", "")
    initial_prompt = st.session_state.get("initial_prompt", "")

    now = datetime.now()
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")  # actual system time, for filename uniqueness only
    safe_ai = sanitize_for_filename(ai)
    safe_topic = sanitize_for_filename(topic)
    filename = f"{file_timestamp}_{safe_ai}_{safe_topic}.md"

    md_content = (
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

    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)

        # Prevent silent overwrite when saving twice within the same second
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}{ext}"
            filepath = os.path.join(SAVE_DIR, filename)
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
    except OSError as e:
        st.session_state["_save_status"] = ("error", f"Save failed: {e}")
        return

    # Add to History as LIFO (index 0 = newest)
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
    st.session_state["_save_status"] = ("success", filename)


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------
def render_sidebar_history() -> None:
    st.markdown("### \U0001F4DA History")

    if not st.session_state["history"]:
        st.caption("No saved history yet.")
        return

    # Compact one-line rows: checkbox + "date.time.AI.topic" — no separate
    # preview/expander, since checking the box already loads the full content
    # into the editor.
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
        st.markdown("**Initial Prompt / Base Data**")
    with col_upload:
        with st.popover("\U0001F4E4"):
            uploaded_file = st.file_uploader(
                "Load a different template (.md)",
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
        st.button(
            "\U0001F4CB",
            key="_copy_prompt_btn",
            on_click=do_copy_prompt,
            help="Copy Initial Prompt to clipboard",
            use_container_width=True,
        )

    if st.session_state.get("_last_uploaded_name") is None and st.session_state.get("initial_prompt"):
        st.caption(f"Auto-loaded from `{TEMPLATE_FILENAME}`")

    if "_prompt_copy_status" in st.session_state:
        status, msg = st.session_state.pop("_prompt_copy_status")
        st.toast(("\u2705 " if status == "success" else "\u26A0\ufe0f ") + msg)

    st.text_area(
        "Initial Prompt / Base Data",
        key="initial_prompt",
        height=100,
        placeholder="Enter the base data or initial instructions to send to every AI.",
        label_visibility="collapsed",
    )


def render_main_editor() -> None:
    col_ai, col_date, col_time, col_topic = st.columns([1, 1, 1, 3])
    with col_ai:
        st.selectbox("Target AI", AI_OPTIONS, key="header_ai")
    with col_date:
        st.text_input("Date", key="header_date", placeholder="e.g. 07-08")
    with col_time:
        st.text_input("Time", key="header_time", placeholder="e.g. 14:32")
    with col_topic:
        st.text_input("Topic", key="header_topic", placeholder="Conversation topic / title")

    col_clear, col_paste, col_copy, col_save = st.columns(4)
    with col_clear:
        st.button("\U0001F5D1\ufe0f Clear", on_click=do_clear, use_container_width=True)
    with col_paste:
        st.button("\U0001F4CB Paste", on_click=do_paste, use_container_width=True)
    with col_copy:
        st.button("\U0001F4C4 Copy", on_click=do_copy_editor, use_container_width=True)
    with col_save:
        st.button("\U0001F4BE Save", on_click=do_save, type="primary", use_container_width=True)

    # Paste / Copy / Save result feedback (toast)
    if "_paste_status" in st.session_state:
        status, msg = st.session_state.pop("_paste_status")
        st.toast(("\u2705 " if status == "success" else "\u26A0\ufe0f ") + msg)

    if "_editor_copy_status" in st.session_state:
        status, msg = st.session_state.pop("_editor_copy_status")
        st.toast(("\u2705 " if status == "success" else "\u26A0\ufe0f ") + msg)

    if "_save_status" in st.session_state:
        status, msg = st.session_state.pop("_save_status")
        if status == "success":
            st.toast(f"\u2705 Saved: {msg}")
        else:
            st.toast(f"\u26A0\ufe0f {msg}")

    st.text_area(
        "Editor",
        key="editor_text",
        height=560,
        placeholder="Paste an AI reply, or select a previous entry from History on the left to append it.",
    )


def render_help_button() -> None:
    """Quick in-app guide. See MANUAL.md (next to this app) for full details."""
    with st.popover("\u2753 Help"):
        st.markdown(
            f"""
**Quick Guide**

- **Base Prompt Area** (sidebar, top): shared instructions/base data sent to
  every AI. Auto-loads `{TEMPLATE_FILENAME}` if it's next to this app.
  `\U0001F4E4` uploads a different `.md` template; `\U0001F4CB` copies the
  current text to the clipboard.
- **History** (sidebar, bottom): saved sessions, newest on top, one line each
  (`date.time.AI.topic`). Check the box to append that entry into the Editor.
- **Main Editor**:
  - *Target AI / Date / Time / Topic* — labels for the current entry.
    Date/Time default to now; they reset whenever you append a History item
    or click Clear.
  - `\U0001F5D1\ufe0f Clear` — reset the Editor and the header fields.
  - `\U0001F4CB Paste` — insert clipboard content into the Editor.
  - `\U0001F4C4 Copy` — copy the whole Editor content to the clipboard.
  - `\U0001F4BE Save` — write a `.md` report to `{SAVE_DIR}/` and add it to History.

Full guide: `MANUAL.md` (same folder as this app).
"""
        )


def render_custom_css() -> None:
    """Minimal CSS for card-like widgets, on top of color/font theming."""
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
        }
        div.stButton > button {
            border-radius: 8px;
        }
        /* Pull the page content up — Streamlit's default top padding pushes
           the title down noticeably. */
        [data-testid="stAppViewContainer"] .block-container {
            padding-top: 1.5rem;
        }
        /* Same trim for the sidebar, so Base Prompt Area sits higher and
           History gets more vertical room below it. */
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
    open_ai_chat_tabs_once()
    render_custom_css()

    with st.sidebar:
        render_base_prompt_area()
        st.divider()
        render_sidebar_history()

    col_title, col_help = st.columns([6, 1], vertical_alignment="center")
    with col_title:
        st.title("\U0001F6E0\ufe0f Cross-AI Prompt Manager")
    with col_help:
        render_help_button()
    render_main_editor()


if __name__ == "__main__":
    main()
