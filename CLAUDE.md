# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a personal idea-tracking and research repository, not a software project. It contains no source code, build system, or tests. Content is written primarily in Korean.

The repo's purpose (per README.md): capture ideas, then research and document each one — planning, design, market analysis, revenue structure, methods, and sales forecasts.

## Intended structure

Per the README, the repo is meant to be organized as:

- `docs/` — a top-level directory containing a document that manages/lists all ideas
- `docs/<idea-name>/` — one directory per idea, each containing documents such as:
  - `README.md` — overview of the idea
  - Planning (기획)
  - Design (설계)
  - Market analysis (시장 분석)
  - Revenue structure and methods (수익 구조 및 수익 방법)
  - Sales forecast (매출 예측)

Note: as of now, the `docs/` directory does not exist yet. When adding a new idea, check whether `docs/` and its idea-list document already exist before assuming their layout — create them following the pattern above if this is the first idea being added.

## Working in this repo

- There is no code to build, lint, or test — work here is authoring/organizing Markdown documents.
- Keep new content consistent with the existing Korean-language style unless the user requests otherwise.
- When creating a new idea directory, follow the document breakdown above (overview, planning, design, market analysis, revenue structure/methods, sales forecast) rather than inventing a different structure.

## Standing rules

- **Always persist as documents.** Any idea, plan, or piece of research discussed in conversation must be written into the appropriate file under `docs/` (not left only in chat). Use the idea directory structure above; update `docs/README.md`'s idea list whenever an idea is added, renamed, or removed.
- **Always commit and push immediately.** After creating or updating any document in this repo, run `git add`, `git commit`, and `git push` right away in the same turn — do not batch changes or wait for the user to ask. This repo has no CI/build to break, so this is pre-authorized and does not need per-change confirmation. Write concise commit messages (Korean or English) describing what idea/document changed.
