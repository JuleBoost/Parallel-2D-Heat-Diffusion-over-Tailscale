# LLM log

All LLM use in this project is recorded here, as the course requires (Section 12).

| Who | Tool / model | When | What |
|---|---|---|---|
| Julien Boustany | Claude (claude.ai app, model Claude Opus 5.5), agentic chat with tools on Julien's computer | 20–27 Nov 2026 | Cluster setup guidance (Multipass, Tailscale, SSH, Open MPI), all code (`heat.cpp`, ping-pong, scripts, `bench.py`, `analyze.py`), Tasks 3.5 / 4.1 / 6.7 / 7.2, the summary report and the slides |
| Jad Allam | *(fill in: tool, model, dates)* | | Background-notes Tasks 1.1–5.5 |
| Marc Germani | *(fill in: tool, model, dates)* | | Background-notes Tasks 6.1–8.2 |

## Files to put in this folder

- `julien_claude_chat.*` — the complete export of Julien's Claude conversation (every prompt and response, including tool calls). Export it from claude.ai and place it here.
- One export per teammate conversation, named `<member>_<tool>_<date>.*`.

## Agents and subagents

Julien's conversation ran as a single agent: no subagents were started, so there are no subagent transcripts. No `AGENTS.md` / `CLAUDE.md` file was used; the chat export above is the log.
