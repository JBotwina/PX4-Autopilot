---
name: px4-docs-answer
description: Answer PX4 user and maintainer questions by scraping supplied documentation URLs, turning difficult docs into step-by-step guidance, and optionally searching the current PX4-Autopilot checkout for real files, build targets, scripts, CMake logic, Kconfig settings, and contribution processes that support the answer. Use for PX4 support replies, forum or GitHub discussions, hardware board-support questions, firmware/porting process explanations, and requests to ground documentation advice in codebase evidence.
---

# PX4 Docs Answer

Use this skill to turn PX4 documentation and local repository evidence into a practical answer the user can send in a discussion. Favor a clear sequence of actions over a documentation summary.

## Workflow

1. Restate the user's actual question in one sentence.
2. Gather documentation evidence from every supplied URL and recursively follow relevant links from the first page.
   - Run `scripts/gather_docs_context.py <url>` from this skill directory.
   - Add `--query "<user question>" --crawl-depth 2 --max-pages 12 --crawl-scope docs-site` when one page links to process pages that are likely needed.
   - If the URL maps to a local `docs/en/...` file in the checkout, the helper will prefer the local markdown copy and avoid unnecessary network drift.
3. Use subagents for recursive documentation research when they are available and the first page fans out into several plausible links.
   - Keep the final answer in the parent agent.
   - Split links by topic or path prefix, for example "hardware porting pages", "development setup pages", "contribution process pages", and "QGroundControl or firmware update pages".
   - Give each subagent a bounded brief: read its assigned links, recursively follow only links that help answer the user question, search local code only if the link claims map to real PX4 files/processes, and return concise evidence with citations.
   - Do not ask subagents to rewrite the final user-facing answer. Ask for findings, source URLs or file paths, and unresolved caveats.
4. Search the current checkout when the user asks for codebase evidence, when the answer should mention real PX4 processes, or when docs reference build files, board files, scripts, CMake, Kconfig, or tests.
   - Use the helper with one or more `--codebase-query` options for quick evidence.
   - Use direct `rg` follow-ups for deeper inspection once promising files are identified.
5. Read the most relevant files before answering. Do not rely only on search snippets or subagent summaries for technical claims that are central to the answer.
6. Answer with a step-by-step guide. Include concrete file paths, commands, PR targets, and review evidence where useful.
7. Cite sources inline for every important process requirement. Prefer official PX4 docs URLs for user-facing claims, and add local file paths when codebase evidence is useful. Separate confirmed facts from inferences.

## Helper

From the repo root:

```sh
python3 .agents/skills/px4-docs-answer/scripts/gather_docs_context.py \
  https://docs.px4.io/main/en/hardware/board_support_guide \
  --query "new flight controller official PX4 board support firmware process" \
  --crawl-depth 2 \
  --crawl-scope docs-site \
  --max-pages 12 \
  --codebase-query "firmware.prototype" \
  --codebase-query "default.px4board" \
  --codebase-query "PX4_BOARD_DIR"
```

The helper prints:

- Documentation text, using local markdown when a `docs.px4.io/main/en/...` URL exists under `docs/en/...`.
- Same-site docs links recursively, prioritized by query terms when `--query` is supplied. Use `--crawl-scope section` for a tighter crawl, `docs-site` for the same docs version/language, `same-host` for generic docs sites, and `any` only when the link graph is small and trusted.
- Optional `rg` results from the current checkout, restricted by default to likely PX4 process directories.

Use the helper as a context-gathering shortcut, not as the final authority. Open and read the relevant source files after the helper points to them.

## Subagent Research Template

When subagent tools are available in the current runtime, spawn explorers with prompts like:

```text
Use the PX4 docs-answer workflow to research this slice of a support question.

User question: <question>
Assigned docs links:
- <url-or-path>
- <url-or-path>

Follow links recursively only when they help answer the question. Prefer local docs under docs/en when present. Search the PX4-Autopilot checkout for concrete files or processes if a docs claim mentions build targets, board files, CMake, Kconfig, scripts, PR workflow, or firmware flashing. Return:
1. Key findings as short bullets.
2. Source URLs or local file paths for each finding.
3. Any caveats or missing evidence.

Do not draft the final reply.
```

Merge subagent results by source quality: primary PX4 docs and local repository files first, then examples or external PRs, then inferred guidance.

If subagent tools are not available, do the same recursive traversal in the main agent and keep `--max-pages` conservative.

## Board Support Questions

For questions like "How do we get our flight controller officially supported by PX4?", read `references/board-support-replies.md` after gathering docs. It contains the answer shape, required evidence, and high-value local paths for board target support.

The usual response should explain:

- Start without private permission: build a board target and work through public GitHub PRs.
- Create a dedicated target under `boards/<vendor>/<model>/`, even for hardware close to an FMU design.
- Reserve a unique board ID in PX4-Bootloader and put it in `firmware.prototype`.
- Use a unique USB VID/PID; do not copy another vendor.
- Fly the hardware on the current PX4 release and link logs from `logs.px4.io`.
- Open a PX4-Autopilot PR containing board support code, board documentation, and flight-log evidence.
- Maintain the target after merge; manufacturer-supported boards remain the manufacturer's responsibility.

## Answer Style

Prefer this structure:

1. Direct answer: one short paragraph.
2. Step-by-step process: numbered list with commands/files where applicable.
3. What to include in the PR or next message.
4. Useful references: docs URLs and local source paths.
5. Optional caveats: only when they prevent mistakes, such as board ID conflicts, VID/PID misuse, unsupported bootloader protocol, or missing flight logs.

Use inline citations in the numbered steps, not only a final reference list. Cite the specific PX4 docs page that supports each requirement, for example board target creation, board ID reservation, VID/PID uniqueness, flight-log evidence, PR contents, and maintenance responsibility.

Avoid dumping raw docs text. Convert it into the next actions the requester can take.
