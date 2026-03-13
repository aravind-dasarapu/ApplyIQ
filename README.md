# HireReady

I built this because preparing a job application properly takes forever. Not the applying part — the part before that. Reading the JD carefully, figuring out where your resume actually matches and where it doesn't, identifying what you'd need to learn before you'd be competitive, and then writing a cover letter that isn't generic. Done right, that's 2-3 hours per application. I wanted to automate it.

HireReady takes your resume and a job description, runs them through a pipeline of 5 AI agents, and spits out a full analysis report — resume breakdown, JD breakdown, gap analysis, a learning plan with free resources, and a tailored cover letter. The whole thing runs in under 10 minutes.

---

## How it works

The pipeline runs sequentially — each agent's output feeds into the next one that needs it, rather than every agent starting from scratch.

```
Resume → [embed into ChromaDB] → retrieve context
                                        ↓
                              Resume Analyst Agent
                                        ↓
                               JD Analyzer Agent
                                        ↓
                     Gap Finder Agent  (gets both above as context)
                                        ↓
                    Skills Advisor Agent (gets gap analysis)
                                        ↓
               Cover Letter Writer Agent (gets resume + JD + gap analysis)
                                        ↓
                              output/report.md
```

**Why RAG for the resume?**
Stuffing the entire resume as raw text into every prompt gets noisy. Instead, the resume gets chunked and embedded into ChromaDB using `all-MiniLM-L6-v2`. Each agent retrieves only the most relevant sections for its task — the gap finder doesn't need your education section the same way the cover letter writer does.

**Why sequential and not parallel?**
The gap analysis genuinely needs both the resume analysis and JD analysis to exist first. Same with the cover letter — it's a bad cover letter if the agent doesn't know where the gaps are. Parallelising the first two makes sense, but the rest of the chain needs to be sequential. For a prototype this size, sequential for everything was the simpler call.

**LLM: Cerebras**
I used Cerebras over OpenAI mainly for speed. The sequential pipeline means you're waiting on 5 LLM calls back to back — Cerebras inference is fast enough that the total runtime stays under 10 minutes. Temperature is set to 0.3 across all agents to keep outputs consistent and structured.

---

## Output

The pipeline generates a markdown report at `output/report.md` with 5 sections:

1. Resume Analysis — skills, experience, education, career level
2. JD Analysis — must-haves, nice-to-haves, responsibilities, culture hints
3. Gap Analysis — match score, strong matches, critical gaps, priority actions
4. Learning Plan — free resources only, 30-day sprint, portfolio project idea
5. Cover Letter — ready to send, no placeholders, no clichés

---

## Setup

```bash
git clone https://github.com/aravind-dasarapu/hireready
cd hireready
pip install -r requirements.txt
```

Create a `.env` file:
```
CEREBRAS_API_KEY=your_key_here
```

Run:
```bash
python main.py
```

You'll be prompted to paste your resume text and the job description. The pipeline kicks off from there.

---

## Stack

- **CrewAI** — agent orchestration
- **ChromaDB** — vector store for resume embeddings
- **sentence-transformers (all-MiniLM-L6-v2)** — embedding model
- **Cerebras LLM** — inference
- **Python** — everything else

---

## What I'd improve

The biggest limitation right now is that the resume input is plain text — copy-pasting from a PDF loses formatting and sometimes garbles sections. A proper PDF parser as the first step would fix that. I'd also add a confidence score to the gap analysis rather than a rough percentage, and honestly the skills advisor prompt could be tighter — it sometimes recommends resources that are behind paywalls despite being told not to.

This was built as a prototype to learn CrewAI and RAG properly. It does what it's supposed to do.
