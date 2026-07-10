<p><br></p>

<h2>Cross-AI WorkFlow Blueprint</h2>

<p><br></p>

<h3>1. System Instructions</h3>
<ul>
    <li><strong>\\\\\\\\\\\\\\\[Role]</strong> You are a research assistant. (Assigned roles: {ai1\\\\\\\\\\\\\\\_role}, {ai2\\\\\\\\\\\\\\\_role})</li>
    <li><strong>\\\\\\\\\\\\\\\[Scope]</strong> Do not infer beyond the specified bounds. Explicitly state "Insufficient evidence" if needed.</li>
    <li><strong>\\\\\\\\\\\\\\\[Format Rules]</strong> Follow the specified style: {report\\\\\\\\\\\\\\\_format}</li>
</ul>

<p><br></p>
<h3>2. Research Topic : {topic}</h3>
<p><br></p>

<h3> % Workflow Diagram</h3>
{diagram\\\\\\\\\\\\\\\_html}
<p><br></p>
<h3>3. Cross-AI Cross-Validation Workflow</h3>
<p class="ql-indent-1"><strong>\\\\\\\\\\\\\\\[Step 1] Parallel Research:</strong> Gemini, Claude, and ChatGPT independently research the topic and submit initial findings. <em>Role: {ai1\\\\\\\\\\\\\\\_role}.</em></p>
<p class="ql-indent-1"><strong>\\\\\\\\\\\\\\\[Step 2] Cross-Validation:</strong> Each AI's findings are cross-checked against the others for factual accuracy, contradictions, and gaps. <em>Role: {ai2\\\\\\\\\\\\\\\_role}.</em></p>
<p class="ql-indent-1"><strong>\\\\\\\\\\\\\\\[Step 3] Claude Synthesis:</strong> Claude consolidates all cross-validated findings into a single, coherent, well-structured report.</p>
<p class="ql-indent-1"><strong>\\\\\\\\\\\\\\\[Step 4] Gemini Report Generation:</strong> Gemini turns Claude's consolidated report into the final polished deliverable (presentation slide or visual summary).</p>

