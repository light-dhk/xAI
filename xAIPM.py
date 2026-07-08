"""
Cross-AI Prompt Manager - Cloud Edition
Design doc: 260709_BluePrint_Cross-AI_Prompt_Manager_v1.3.md

Runtime: Streamlit Community Cloud (or any remote Streamlit server).

Why this version differs from the original "local" build:
  - Streamlit Cloud runs 100% of this script on a remote Linux container,
    not on the user's PC. Anything that assumed "this machine == the user's
    machine" (webbrowser.open_new_tab, pyperclip, permanent disk writes)
    silently does nothing useful there, because it acts on the SERVER's
    display/clipboard/disk instead of the user's.
  - Fixes applied:
      1. AI chat tabs -> st.link_button (runs in the user's own browser)
      2. Copy -> browser Clipboard API via a small JS snippet
         (components.html actually executes in the user's browser, so
         navigator.clipboard.writeText() writes to the USER's clipboard)
      3. Paste -> removed as a button; a normal <textarea> already accepts
         native Ctrl+V/Cmd+V from the user's OS clipboard with zero code
      4. Save -> disk write is now best-effort only (kept for convenience
         during a single live session) + st.download_button so the user
         gets a real, permanent copy on their own PC immediately. Also adds
         a "download all history" backup button, since session_state and
         any on-disk files are wiped on reboot/redeploy/sleep.
"""

import json
import os
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SAVE_DIR = "saved_reports"  # NOTE: ephemeral on Streamlit Cloud - see docstring
AI_OPTIONS = ["ChatGPT", "Claude", "Gemini", "Other"]
TEMPLATE_FILENAME = "PromptTemplate.md"  # Auto-loaded at startup if present next to this file (Base Prompt Area)
EDITOR_TEMPLATE_FILENAME = "EditorTemplate.md"  # Auto-loaded at startup if present next to this file (Main Editor)

HISTORY_FONT_SIZE = "0.62rem"

# AI chat sites, opened via link buttons that run in the USER's browser
# (not webbrowser.open_new_tab, which would only affect the server).
AI_CHAT_SITES = {
    "ChatGPT": "https://chatgpt.com",
    "Claude": "https://claude.ai",
    "Gemini": "https://gemini.google.com",
}


# ---------------------------------------------------------------------------
# State initialization (session_state)
# ---------------------------------------------------------------------------
def load_default_prompt_template() -> str:
    """
    Auto-load PromptTemplate.md from the same folder as this script at startup.
    Works fine on Streamlit Cloud AS LONG AS the .md file is committed to the
    GitHub repo alongside this script (it's then part of the cloned code, not
    something written at runtime).
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
        "_last_saved_content": None,
        "_last_saved_filename": None,
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
    st.session_state["header_ai"] = AI_OPTIONS[0]
    st.session_state["header_date"] = now.strftime("%m-%d")
    st.session_state["header_time"] = now.strftime("%H:%M")
    st.session_state["header_topic"] = ""


# ---------------------------------------------------------------------------
# Client-side clipboard copy (replaces pyperclip)
# ---------------------------------------------------------------------------
def clipboard_copy_button(text: str, label: str, key: str) -> None:
    """
    Renders a button that copies `text` into the USER's OS clipboard using the
    browser's Clipboard API (navigator.clipboard.writeText). Because
    components.html runs inside an iframe in the user's own browser (not on
    the server), this actually works on Streamlit Cloud - unlike pyperclip,
    which only ever touched the server container's (nonexistent, irrelevant)
    clipboard.

    Requires HTTPS (Streamlit Cloud serves over HTTPS by default, so this is
    fine there). On plain HTTP it would silently fail with a permissions
    error, which the try/except below surfaces as "Copy failed".
    """
    safe_text = json.dumps(text or "")
    html_code = f"""
    <button id="{key}" style="
        width:100%; padding:0.5rem; border-radius:8px; border:1px solid rgba(49,51,63,0.2);
        background-color:rgb(240,242,246); cursor:pointer; font-size:0.9rem; font-family:inherit;">
        {label}
    </button>
    <script>
    const btn_{key} = document.getElementById("{key}");
    btn_{key}.addEventListener("click", async () => {{
        try {{
            await navigator.clipboard.writeText({safe_text});
            btn_{key}.innerText = "\u2705 Copied!";
            setTimeout(() => {{ btn_{key}.innerText = "{label}"; }}, 1500);
        }} catch (err) {{
            btn_{key}.innerText = "\u26a0\ufe0f Copy failed";
            setTimeout(() => {{ btn_{key}.innerText = "{label}"; }}, 1500);
        }}
    }});
    </script>
    """
    components.html(html_code, height=45)


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
    st.session_state["editor_text"] = ""
    reset_header()


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
    ai = st.session_state.get("header_ai", "").strip() or AI_OPTIONS[0]
    header_date = st.session_state.get("header_date", "").strip() or datetime.now().strftime("%m-%d")
    time_str = st.session_state.get("header_time", "").strip() or datetime.now().strftime("%H:%M")
    topic = st.session_state.get("header_topic", "").strip() or "Untitled"
    body = st.session_state.get("editor_text", "")
    initial_prompt = st.session_state.get("initial_prompt", "")

    now = datetime.now()
    file_timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_ai = sanitize_for_filename(ai)
    safe_topic = sanitize_for_filename(topic)
    filename = f"{file_timestamp}_{safe_ai}_{safe_topic}.md"

    md_content = build_report_md(ai, header_date, time_str, topic, initial_prompt, body)

    # Best-effort disk write. On Streamlit Cloud this file lives only on the
    # container's ephemeral disk and will be lost on reboot/redeploy/sleep -
    # it is NOT a substitute for the download button below, just a same-
    # session convenience (e.g. if you spin up a shell in "Manage app").
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
        disk_status = ("warning", f"Disk write skipped ({e}) - use the download button to keep your copy.")

    # Always add to History (session memory) and stage the download,
    # regardless of whether the disk write above succeeded - the download
    # button is the REAL save as far as the user's own PC is concerned.
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
    st.session_state["_last_saved_content"] = md_content
    st.session_state["_last_saved_filename"] = filename
    st.session_state["_save_status"] = disk_status


# ---------------------------------------------------------------------------
# UI rendering
# ---------------------------------------------------------------------------
def render_ai_launcher() -> None:
    """
    Row of link buttons that open each AI chat site in a NEW TAB IN THE
    USER'S OWN BROWSER. This replaces webbrowser.open_new_tab(), which only
    ever opened tabs inside the server container (invisible to the user and
    pointless, since the container has no display or browser installed).
    """
    cols = st.columns(len(AI_CHAT_SITES))
    for col, (name, url) in zip(cols, AI_CHAT_SITES.items()):
        with col:
            st.link_button(f"\U0001F517 {name}", url, use_container_width=True)


def render_sidebar_history() -> None:
    st.markdown("### \U0001F4DA History")

    if not st.session_state["history"]:
        st.caption("No saved history yet.")
        return

    # Backup-all button: since session_state (and any ephemeral disk file)
    # disappears on container reboot/redeploy/sleep, give the user one click
    # to pull everything down to their own PC before that happens.
    all_md = "\n\n".join(
        build_report_md(
            e["ai"], e["date"], e["time"], e["topic"],
            st.session_state.get("initial_prompt", ""), e["content"],
        )
        for e in st.session_state["history"]
    )
    st.download_button(
        "\U0001F4E5 Backup all history (.md)",
        data=all_md,
        file_name=f"xAIPM_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.caption("Session data is lost on app restart/redeploy - back up often.")
    st.divider()

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
    col_label, col_upload = st.columns([4, 1])
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

    if st.session_state.get("_last_uploaded_name") is None and st.session_state.get("initial_prompt"):
        st.caption(f"Auto-loaded from `{TEMPLATE_FILENAME}`")

    st.text_area(
        "Initial Prompt / Base Data",
        key="initial_prompt",
        height=100,
        placeholder="Enter the base data or initial instructions to send to every AI.",
        label_visibility="collapsed",
    )

    # Client-side clipboard copy - works on Streamlit Cloud (see docstring
    # on clipboard_copy_button for why pyperclip did not).
    clipboard_copy_button(
        st.session_state.get("initial_prompt", ""),
        label="\U0001F4CB Copy Initial Prompt",
        key="copy_prompt_btn",
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

    col_clear, col_copy, col_save = st.columns(3)
    with col_clear:
        st.button("\U0001F5D1\ufe0f Clear", on_click=do_clear, use_container_width=True)
    with col_copy:
        clipboard_copy_button(
            st.session_state.get("editor_text", ""),
            label="\U0001F4C4 Copy Editor",
            key="copy_editor_btn",
        )
    with col_save:
        st.button("\U0001F4BE Save", on_click=do_save, type="primary", use_container_width=True)

    st.caption(
        "\U0001F4A1 To paste, just click inside the box below and press "
        "Ctrl+V (Cmd+V on Mac) - your browser handles this natively."
    )

    if "_save_status" in st.session_state:
        status, msg = st.session_state.pop("_save_status")
        if status == "success":
            st.toast(f"\u2705 Saved to server session: {msg}")
        else:
            st.toast(f"\u26A0\ufe0f {msg}")

    st.text_area(
        "Editor",
        key="editor_text",
        height=560,
        placeholder="Paste an AI reply, or select a previous entry from History on the left to append it.",
    )

    # The REAL save, as far as the user's own PC is concerned: a direct
    # download of the report just generated. Rendered right after Save is
    # clicked so the user can immediately pull a permanent copy.
    if st.session_state.get("_last_saved_content"):
        st.download_button(
            f"\U0001F4E5 Download last saved report ({st.session_state['_last_saved_filename']})",
            data=st.session_state["_last_saved_content"],
            file_name=st.session_state["_last_saved_filename"],
            mime="text/markdown",
            use_container_width=True,
        )


def render_help_button() -> None:
    with st.popover("\u2753 Help"):
        st.markdown(
            f"""
**Quick Guide (Cloud Edition)**

- **AI launcher** (top row): opens ChatGPT / Claude / Gemini in new tabs in
  *your own browser*. (On Streamlit Cloud the server can't open tabs on your
  PC for you, so this is a click instead of an automatic action.)
- **Base Prompt Area** (sidebar, top): shared instructions/base data sent to
  every AI. Auto-loads `{TEMPLATE_FILENAME}` if it's committed to the repo
  next to this app. `\U0001F4E4` uploads a different `.md` template.
  `\U0001F4CB Copy Initial Prompt` copies to *your* clipboard (via your
  browser, not the server).
- **History** (sidebar, bottom): saved sessions for this browser session
  only, newest on top. Check the box to append that entry into the Editor.
  **This is lost if the app restarts/redeploys/sleeps** - use
  `\U0001F4E5 Backup all history` regularly.
- **Main Editor**:
  - *Target AI / Date / Time / Topic* - labels for the current entry.
  - `\U0001F5D1\ufe0f Clear` - reset the Editor and header fields.
  - `\U0001F4C4 Copy Editor` - copy the whole Editor content to *your*
    clipboard.
  - To paste an AI's reply: click the Editor box and press Ctrl+V/Cmd+V.
  - `\U0001F4BE Save` - adds the entry to History (this session only) and
    unlocks the `\U0001F4E5 Download last saved report` button right below
    the Editor - **click that to keep a permanent copy on your own PC.**

Full guide: `MANUAL.md` (same folder as this app), if present.
"""
        )


def render_custom_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
        }
        div.stButton > button, div.stDownloadButton > button, div.stLinkButton > a {
            border-radius: 8px;
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

    render_ai_launcher()
    render_main_editor()


if __name__ == "__main__":
    main()