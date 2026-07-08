\# Prior Art Search Cross-Validation Workflow

\### Using Multiple AI Services (Claude / Gemini / ChatGPT)



\## Purpose

To reduce the risk of missed or biased results in prior art (novelty/FTO) searches by running \*\*parallel searches across multiple AI services\*\*, then \*\*cross-validating and consolidating\*\* the results into a single reliable report.



---



\## 0. Prerequisites



| Item | Description |

|---|---|

| Invention Disclosure | Draft claims, technical problem, key features, drawings (if any) |

| Keyword Set | Core technical terms, synonyms, IPC/CPC classification candidates |

| Search Scope | Patent DB (Google Patents, KIPRIS, Espacenet, USPTO) + non-patent literature (papers, web) |

| Output Format | Comparison table + individual/consolidated reports |



---



\## 1. Initial Parallel Search Phase



\*\*Goal:\*\* Have each AI perform an independent search using the \*same input prompt\*, without cross-referencing each other's results (to preserve independence and avoid anchoring bias).



\### 1-1. Standardized Prompt Template (used identically across all 3 AIs)

```

\[Role] You are a patent search expert.

\[Task] Search for prior art relevant to the following invention.

\[Invention Summary] {insert}

\[Core Claim Elements] {insert as bullet list}

\[Keywords] {insert}

\[Output Required]

&nbsp;1. List of candidate prior art (patents + non-patent literature)

&nbsp;2. For each: title, publication number/source, date, relevant excerpt, relevance score (1-5)

&nbsp;3. Brief note on which claim element(s) it reads on

&nbsp;4. Search strategy used (queries, databases, limitations)

```



\### 1-2. Assign Search Emphasis by Role (to increase coverage rather than pure redundancy)



| AI | Suggested Emphasis | Rationale |

|---|---|---|

| \*\*Claude\*\* | Deep reading \& claim-element mapping, nuanced interpretation of borderline references | Strong at careful text analysis and reasoning about claim scope |

| \*\*Gemini\*\* | Broad web/patent search, non-English \& Asian-language prior art (JP/KR/CN), Google Patents integration | Strong search/indexing breadth, especially non-English sources |

| \*\*ChatGPT\*\* | Alternative technical-field / analogous-art search, adjacent industries, academic/non-patent literature | Good at lateral/analogical thinking across domains |



> Even though roles differ, \*\*each AI should still receive the identical base prompt\*\* — the role emphasis is an \*additional instruction appended\*, not a replacement, so results remain comparable.



\### 1-3. Output to Save (per AI)

\- Raw response (verbatim)

\- List of search queries actually used (ask the AI to disclose them)

\- Candidate reference list with metadata



---



\## 2. Role Division for Verification Phase



Once initial parallel results are collected, reassign roles for \*\*cross-checking\*\* (each AI reviews another's findings — never its own):



| Step | Verifier | Reviews | Task |

|---|---|---|---|

| 2-1 | Gemini | Claude's list | Verify existence/accuracy of cited patents (numbers, dates, real vs. hallucinated) |

| 2-2 | ChatGPT | Gemini's list | Verify claim-element mapping logic, check for overlooked interpretations |

| 2-3 | Claude | ChatGPT's list | Verify technical relevance, check if "adjacent field" refs are actually analogous |



\### Verification Prompt Template

```

\[Role] You are a patent examiner reviewing another analyst's prior art list.

\[Input] {paste other AI's reference list + claim elements}

\[Task]

&nbsp;1. Confirm each reference actually exists (flag if unverifiable/suspected hallucination)

&nbsp;2. Check publication number, date, and applicant/assignee accuracy

&nbsp;3. Re-assess relevance score independently — do you agree or disagree, and why?

&nbsp;4. Identify any reference that appears to be missing from this list

```



⚠️ \*\*Important:\*\* AI-generated citations (patent numbers, paper titles) must always be independently confirmed against a real database (Google Patents, KIPRIS, Espacenet) — do not trust any AI's citation at face value.



---



\## 3. Consolidation (Aggregation) Phase



\*\*Goal:\*\* Merge the three independent + cross-verified lists into one master table, resolving conflicts.



\### 3-1. Master Comparison Table Structure



| Ref. ID | Found by (Claude/Gemini/GPT) | Verified by | Pub. No. | Date | Relevance (avg score) | Claim elements matched | Consensus? (Y/N/Disputed) | Notes |

|---|---|---|---|---|---|---|---|---|



\### 3-2. Conflict Resolution Rules

\- \*\*Consensus (found by 2+ AI, verified real):\*\* High confidence → include as primary prior art

\- \*\*Single-AI find, verified real:\*\* Include, flag as "unique find" — often valuable, since one AI caught what others missed

\- \*\*Disputed relevance score (variance ≥ 2 points):\*\* Flag for human reviewer / patent attorney judgment

\- \*\*Unverifiable / hallucinated citation:\*\* Discard, but log as a "search miss" for process improvement



\### 3-3. Gap Analysis

Ask a 4th, fresh pass (any AI) with a summarizing prompt:

```

Given this final consolidated list of prior art and the claim elements below,

identify any claim element NOT clearly addressed by any reference found so far.

Suggest search angles or keywords to close this gap.

```

This catches blind spots shared by all three AIs (e.g., same keyword bias).



---



\## 4. Report Writing Phase



\### 4-1. Report Structure

1\. \*\*Executive Summary\*\* — overall novelty risk assessment, key findings

2\. \*\*Search Methodology\*\* — databases, keywords, AI tools \& roles used, search dates

3\. \*\*Consolidated Prior Art Table\*\* (from Section 3-1)

4\. \*\*Detailed Analysis per Reference\*\* — claim-element mapping, relevant excerpts/figures

5\. \*\*Cross-Validation Notes\*\* — where AIs agreed/disagreed, and how resolved

6\. \*\*Gaps \& Limitations\*\* — unverified claims, search scope limitations, recommended further search

7\. \*\*Conclusion / Recommendation\*\* — proceed to filing / amend claims / further search needed



\### 4-2. Report Drafting Split

| Task | Recommended Tool |

|---|---|

| Draft narrative sections (Summary, Methodology, Conclusion) | Any AI, but human-edited |

| Table formatting \& data consolidation | Spreadsheet tool or Claude/GPT for structuring |

| Final fact-check of all citations | Human (patent attorney/agent) — mandatory, not optional |



---



\## 5. Workflow Diagram (Summary)



```

&nbsp;       ┌─────────────┐   ┌─────────────┐   ┌─────────────┐

&nbsp;       │   Claude    │   │   Gemini    │   │   ChatGPT   │

&nbsp;       │ (deep read/ │   │ (broad/     │   │ (analogous  │

&nbsp;       │ claim map)  │   │ non-English)│   │  fields)    │

&nbsp;       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘

&nbsp;              │  Phase 1: Independent Parallel Search

&nbsp;              ▼                 ▼                 ▼

&nbsp;       ┌─────────────────────────────────────────────────┐

&nbsp;       │        Phase 2: Cross-Verification (rotated)      │

&nbsp;       │   Gemini→checks Claude / GPT→checks Gemini /       │

&nbsp;       │   Claude→checks GPT                                │

&nbsp;       └───────────────────────┬───────────────────────────┘

&nbsp;                                ▼

&nbsp;       ┌─────────────────────────────────────────────────┐

&nbsp;       │  Phase 3: Consolidation + Conflict Resolution      │

&nbsp;       │        + Gap Analysis (4th pass)                   │

&nbsp;       └───────────────────────┬───────────────────────────┘

&nbsp;                                ▼

&nbsp;       ┌─────────────────────────────────────────────────┐

&nbsp;       │  Phase 4: Report Writing + Human Fact-Check        │

&nbsp;       │       (Patent attorney/agent sign-off)             │

&nbsp;       └─────────────────────────────────────────────────┘

```



---



\## 6. Key Principles



\- \*\*Independence first:\*\* Never let one AI see another's results during Phase 1 — this preserves the value of cross-validation.

\- \*\*Rotate verification roles:\*\* No AI verifies its own output.

\- \*\*Trust but verify citations:\*\* All AI-cited patent/paper references must be checked against a real database before inclusion in any report.

\- \*\*Humans own the final call:\*\* AI accelerates search and reduces blind spots, but novelty/FTO judgment and legal risk assessment should be confirmed by a qualified patent professional.

