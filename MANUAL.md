# Cross-AI Prompt Manager — User Manual

A local, semi-automated workspace for cross-validating answers from multiple
web-based AIs (ChatGPT, Claude, Gemini, Perplexity, ...) and merging the
results into a single Markdown report — no API billing required.

---

## 1. Requirements & Setup

- **OS:** Windows only. The app relies on the local clipboard, which only
  works reliably when the Streamlit server and your browser are on the same
  machine.
- **Run locally:** this app must be started with `streamlit run xAIPM.py` on
  your own PC (not deployed to a remote/cloud server) — that's what lets the
  clipboard bridge work in the first place.

**Install dependencies:**
```
pip install -r requirements.txt
```

**Start the app:**
```
streamlit run xAIPM.py
```

**Optional files** (place them in the same folder as `xAIPM.py`):
| File | Effect |
|---|---|
| `PromptTemplate.md` | Auto-loaded into the **Base Prompt Area** every time the app starts. |
| `EditorTemplate.md` | Auto-loaded into the **Main Editor** at startup, and also added as the first **History** row. |

Neither file is required — the app works fine without them, starting blank.

---

## 2. Layout Overview

```
┌───────────────────┬─────────────────────────────────────┐
│  Sidebar           │  Main Editor                        │
│  ┌───────────────┐ │  Target AI | Date | Time | Topic     │
│  │ Base Prompt    │ │  [Clear] [Paste] [Copy] [Save]       │
│  │ Area           │ │  ┌─────────────────────────────┐    │
│  ├───────────────┤ │  │ Editor (large text area)     │    │
│  │ History        │ │  │                              │    │
│  │ (LIFO list)    │ │  └─────────────────────────────┘    │
│  └───────────────┘ │                                       │
└───────────────────┴─────────────────────────────────────┘
```

On startup, the app also opens **ChatGPT**, **Claude**, and **Gemini** in new
browser tabs, so you can immediately copy your question into each of them.

---

## 3. Base Prompt Area (sidebar, top)

Holds the instruction or source data you want to send identically to every
AI (e.g. the original prior-art text, or your research question).

- **Title row:** the "Initial Prompt / Base Data" label doubles as the
  section header, with two buttons on the right:
  - `📤` — opens a small uploader to load a different `.md` template file.
  - `📋` — copies the current Initial Prompt text to the clipboard, so you
    can paste it directly into ChatGPT / Claude / Gemini.
- If `PromptTemplate.md` was auto-loaded, a caption confirms it.
- The text box below is fully editable — treat it as a live draft.

---

## 4. History (sidebar, bottom)

Every saved report appears here as a single line, **newest on top**:

```
07-08.14:32.ChatGPT.Patent search results
```
Format: `date.time.AI.topic` + a checkbox.

- **Checking the box** appends that entry's full content into the Editor
  (with a separator and a small header line showing its date/time/AI/topic),
  then automatically unchecks itself so you can reuse it later.
- There's no separate preview/expander — checking the box *is* the preview,
  since it loads the full text straight into the Editor.
- History is **session-only**: it resets when you restart the app. The
  underlying `.md` files are not deleted — see section 7.

---

## 5. Main Editor

### Header fields
| Field | Notes |
|---|---|
| Target AI | Which AI this entry's content came from. |
| Date | Free text, defaults to today's date (`MM-DD`). Editable. |
| Time | Free text, defaults to the current time (`HH:MM`). Editable. |
| Topic | Free text title/summary for this entry. Stays blank until you type it. |

Date and Time are pre-filled with "now" every time the header resets (app
start, after appending a History item, or after Clear) — you can edit them
before saving if the entry actually happened earlier.

### Buttons
| Button | Action |
|---|---|
| 🗑️ Clear | Empties the Editor and resets all header fields. |
| 📋 Paste | Reads your system clipboard and appends it to the Editor. |
| 📄 Copy | Copies the entire Editor content to the clipboard. |
| 💾 Save | Writes a `.md` report to `saved_reports/` and adds a row to History. |

### Typical workflow
1. Type or paste your question into **Base Prompt Area**, then click `📋` to
   copy it.
2. Switch to the ChatGPT / Claude / Gemini tab, paste (Ctrl+V), and get an
   answer.
3. Select the answer text in the browser, copy it (Ctrl+C).
4. Back in this app, click **Paste** to drop it into the Editor.
5. Fill in **Target AI / Topic** (Date/Time are already filled in).
6. Repeat steps 2–5 for each AI you want to cross-check — each Paste appends
   below the previous one, building a combined report.
7. Click **Save** once you're done. This:
   - Writes `saved_reports/{timestamp}_{AI}_{topic}.md`
   - Adds the entry to History (top of the list)
8. Need to go back to something you saved earlier? Check its box in History
   to load it back into the Editor and keep building on it.

---

## 6. Saved File Format

Each save produces a Markdown file like:

```markdown
---
Target_AI: ChatGPT
Date_Time: 07-08 14:32
Topic: Patent search results
---

### 📝 Initial Prompt (Base)
<contents of Base Prompt Area at save time>

---

### 💡 Cross-Validation Report (Main Editor)
<contents of the Editor at save time>
```

Filename pattern: `{YYYYMMDD_HHMMSS}_{TargetAI}_{Topic}.md`
(A numeric suffix like `_1`, `_2` is added automatically if two saves happen
within the same second, so nothing is silently overwritten.)

---

## 7. Where Your Data Lives

| What | Where | Persists after closing the app? |
|---|---|---|
| Saved reports | `saved_reports/` folder next to `xAIPM.py` | ✅ Yes |
| History list (sidebar) | In-memory only | ❌ No — resets on restart |
| Base Prompt / Editor drafts | In-memory only | ❌ No — save before closing if you want to keep it |

To review past work, just open the relevant `.md` file in
`saved_reports/` directly — the filename already tells you the date, AI, and
topic.

---

## 8. Troubleshooting

**Paste/Copy does nothing, or shows a warning toast**
- "pyperclip module is not installed" → run `pip install pyperclip`.
- "Clipboard is empty or does not contain readable text" → make sure you
  copied plain text (not an image) right before clicking Paste.

**A saved file didn't appear where I expected**
- Files are always written to `saved_reports/` **relative to where you
  launched `streamlit run xAIPM.py` from** — check you're running it from
  the same folder each time.

**Browser tabs for ChatGPT/Claude/Gemini didn't open, or opened again
unexpectedly**
- They only open once per session automatically, right when the app starts.
  Refreshing the page starts a new session and will reopen them again — this
  is expected behavior, not a bug.

**The theme/colors don't look right**
- Check that `.streamlit/config.toml` is in the same folder as `xAIPM.py`,
  and that your installed Streamlit version supports the theming options
  used (`pip show streamlit`; see `requirements.txt` for the minimum
  version).
