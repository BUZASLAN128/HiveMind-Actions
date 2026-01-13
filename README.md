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

2.  **Create GitHub App (Mandatory for Bot-to-Bot Mentions):**
    - Create a [GitHub App](https://github.com/settings/apps/new).
    - Permissions: `Contents: R/W`, `Issues: R/W`, `Pull Requests: R/W`.
    - Generate a **Private Key** and note the **App ID**.
    - Install the App to your repository.

3.  **Set Secrets:**
    - `GEMINI_API_KEY`: Your Google Gemini API Key.
    - `JULES_API_KEY`: (Optional) API Key for the coding agent (Coder).
    - `APP_ID`: The ID of your newly created GitHub App.
    - `APP_PRIVATE_KEY`: The contents of the `.pem` private key file.

4.  **Configure Rules:**
    - Edit `.github/swarm_rules.md` to define your **Golden Rules** (e.g., "No Float", "Use TypeScript").

## 🦁 Features

### 1. Singleton Status Report
HiveMind avoids notification spam by maintaining **ONE** single status comment in the Issue thread. It updates in real-time as agents progress through the task.

### 2. Beast Mode 2.0 (Push Inspector)
Immediate security and quality feedback on every push.
- **Commit Comments:** The Reviewer agent reviews your push and comments directly on the commit.
- **🚨 Critical Issue Auto-Creation:** If the Reviewer detects a high-risk security flaw or a breaking logic error, it **automatically creates a GitHub Issue** to alert the team immediately.

### 3. Autonomous Self-Correction
If the Reviewer rejects a Coder's PR, HiveMind enters a self-correction loop (up to 5 retries). The Reviewer mentions the Coder agent, passing the feedback, and the Coder attempts to fix the issue automatically.

## 🤝 Open Source & Project Agnostic
HiveMind is designed to work with any repository. By updating `.github/swarm_rules.md`, you can tailor the AI's "brain" to follow your specific architectural patterns and security standards.

## 📜 License
MIT
# Final Verification
