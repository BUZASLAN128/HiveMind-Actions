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

### Step 1: Copy Files
```bash
# Copy these folders to your repo:
.github/workflows/
.github/scripts/
.github/prompts/
.github/swarm_rules.md
```

### Step 2: Set Required Secrets
| Secret | Required | Description |
|--------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for AI reviews |
| `JULES_API_KEY` | ✅ Yes | Jules REST API key for self-correction loop |

### Step 3 (Optional): Custom Branding
See [Bot Customization](#-bot-customization) section below.

### Step 4: Configure Rules
Edit `.github/swarm_rules.md` to define your **Golden Rules** (e.g., "No Float", "Use TypeScript").

## 🦁 Features

### 1. Singleton Status Report
HiveMind avoids notification spam by maintaining **ONE** single status comment in the Issue thread. It updates in real-time as agents progress through the task.

### 2. Beast Mode 2.0 (Push Inspector)
Immediate security and quality feedback on every push.
- **Commit Comments:** The Reviewer agent reviews your push and comments directly on the commit.
- **🚨 Critical Issue Auto-Creation:** If the Reviewer detects a high-risk security flaw or a breaking logic error, it **automatically creates a GitHub Issue** to alert the team immediately.

### 3. Autonomous Self-Correction
If the Reviewer rejects a Coder's PR, HiveMind enters a self-correction loop (up to 5 retries). The Reviewer sends feedback to Jules via REST API, and Jules attempts to fix the issue automatically.

## 🎨 Bot Customization

### Default: Using GITHUB_TOKEN
By default, HiveMind uses the built-in `GITHUB_TOKEN` for all operations. This works out of the box with no additional setup.

**Limitation:** Comments will show as `github-actions[bot]` instead of custom branding.

### Optional: Custom GitHub App (Branding)
For custom bot identity and branding, create your own GitHub App:

1. Create a [GitHub App](https://github.com/settings/apps/new)
2. Set permissions: `Contents: R/W`, `Issues: R/W`, `Pull Requests: R/W`
3. Generate a **Private Key** and note the **App ID**
4. Install the App to your repository
5. Add these secrets:

| Secret | Description |
|--------|-------------|
| `APP_ID` | Your GitHub App ID |
| `APP_PRIVATE_KEY` | Contents of the `.pem` private key file |

**Result:** Comments will show as `your-app-name[bot]` with custom avatar!

## 🤝 Open Source & Project Agnostic
HiveMind is designed to work with any repository. By updating `.github/swarm_rules.md`, you can tailor the AI's "brain" to follow your specific architectural patterns and security standards.

## 📜 License
MIT
