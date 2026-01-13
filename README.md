# 🧠 HiveMind Actions

> **The First "Serverless" Swarm AI for GitHub Actions.**  
> Turn your repository into a self-healing, multi-agent AI workspace with zero infrastructure cost.

![Swarm Status Report](https://via.placeholder.com/800x400?text=HiveMind+Status+Report+UI)

## 🌟 What is this?
**HiveMind** is an advanced, multi-agent workflow system that runs entirely on **GitHub Actions**. It transforms your Issue and PR management into an autonomous AI coordination game using Google Gemini.

- **Singleton Reporting:** No more spam. One Issue Comment to rule them all.
- **Beast Mode (Continuous Inspection):** Push to `dev`, get a commit review in seconds.
- **Swarm Protocol:** Analyst plans, Coder codes, Reviewer inspects. All synchronized.

## 🚀 Agents

| Agent | Icon | Role | Trigger |
|-------|------|------|---------|
| **Analyst** | 🔍 | Orchestrator & Planner | `@hivemind` (or `@analyst`) in Issue Comment |
| **Coder** | 🤖 | Implementation & PR | Auto-triggered by Analyst |
| **Reviewer** | 🔎 | Code Quality & Security | PR Open / Push to `dev` |

## 🛠️ Installation

1.  **Copy Files:**
    - Copy `.github/workflows/` to your repo.
    - Copy `.github/scripts/` to your repo.
    - Copy `.github/prompts/` to your repo.

2.  **Set Secrets:**
    - `GEMINI_API_KEY`: Your Google Gemini API Key.
    - `CODER_API_KEY`: (Optional) API Key for the coding agent tool (if separate).

3.  **Configure Rules:**
    - Edit `.github/swarm_rules.md` to define your **Golden Rules** (e.g., "No Float", "Use TypeScript").

## 🦁 Features

### 1. Singleton Status Report
Instead of spamming the issue with 10 different comments ("I started", "I finished", "Results here"), HiveMind maintains **ONE** single comment.
- Analyst creates it.
- Coder updates it.
- Reviewer finalizes it.
- If the report gets lost upstream, Analyst deletes the old one and brings it to the bottom!

### 2. Beast Mode (Push Inspector)
Want immediate feedback without opening a PR?
- Just `git push origin dev`.
- The Reviewer agent detects the push (Beast Mode).
- Calculates the diff locally.
- Posts a **Commit Comment** directly on the code line or commit.

## 🤝 Application
This framework is designed to be **Project Agnostic**.
Just change `.github/swarm_rules.md` and the agents will adapt to your coding standards immediately.

## 📜 License
MIT
