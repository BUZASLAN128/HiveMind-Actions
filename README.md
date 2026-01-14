# 🧠 HiveMind Actions 2.0

> **The First "Serverless" Swarm AI for GitHub Actions.**  
> Turn your repository into a self-healing, multi-agent AI workspace with zero infrastructure cost.

[![Live Issue #1](https://img.shields.io/badge/HiveMind-Live_Issue_%231-blue?style=for-the-badge&logo=github)](https://github.com/BUZASLAN128/HiveMind-Actions/issues/1) 
[![Live PR #25](https://img.shields.io/badge/HiveMind-Live_PR_%2325-success?style=for-the-badge&logo=github)](https://github.com/BUZASLAN128/HiveMind-Actions/pull/25)

---

## 🌟 What is this?
**HiveMind** is not just a bot. It's a **collaborative AI Swarm** that lives inside your GitHub Actions. 
It enables **Analyst**, **Coder**, and **Reviewer** agents to work together, autonomously planning, coding, reviewing, and **fixing their own mistakes** without your intervention.

Think of it as having a **Senior Developer** (Jules) and a **Staff Engineer** (Reviewer) working 24/7 on your repo, for free (using Gemini Free Tier).

---

## 🔥 Why HiveMind? (Killer Features)

### 1. ♾️ Autonomous Self-Correction Loop
The most powerful feature. If the **Reviewer** agent finds a bug or security flaw in a PR:
1. It **REJECTS** the PR.
2. It talks directly to **Jules** (the Coder) via API.
3. Jules **fixes the code** and pushes a new commit.
4. The Reviewer **re-evaluates** the fix.
5. This loop continues until the code is perfect. **You sleep, they work.**

### 2. 🧠 Smart Context & Golden Rules
HiveMind doesn't just "guess". It follows your **Golden Rules** defined in `.github/swarm_rules.md`.
- Have a specific architectural style? Write it down.
- Want to ban `any` type in TypeScript? Add a rule.
- The Swarm **strictly enforces** your standards.

### 3. 🛡️ Beast Mode (Proactive Security)
HiveMind acts as an **always-on security guard**.
- Pushed code to `any`? The Reviewer inspects it instantly.
- Found a critical vulnerability? It autonomously **opens an Issue** and assigns it to the team.
- No security hole goes unnoticed.

### 4. ⚡ Competitive Intelligence (Smart Actions)
We built features that rival paid tools like CodeRabbit or CodiumAI:
- **Smart Ignore:** Automatically skips junk files (`package-lock.json`, `dist/`, `*.min.js`) to save tokens and reduce noise.
- **Auto-Labeler:** AI analyzes your PR and tags it automatically (`bug`, `feature`, `security`, `refactor`).
- **Token Optimization:** Uses efficient diff parsing to handle large PRs without breaking the bank.

### 5. 🚀 Zero-Config (Serverless)
No servers to manage. No Docker containers to host.
- Runs entirely on **GitHub Actions runners**.
- Uses **Google Gemini 2.0 Flash** (Fast & Free).
- Just copy the workflow files and you're done.

---

## 🤖 The Swarm Agents

| Agent | Icon | Role | Superpower |
|-------|------|------|------------|
| **Analyst** | 🔍 | Architect | Breaks down complex issues into step-by-step plans. |
| **Coder (Jules)** | 🐝 | Droneworker | Writes code, fixes bugs, and handles git operations autonomously. |
| **Reviewer** | 🔎 | Quality Gate | Enforces rules, checks security, and **blocks bad PRs**. |

---

## 🛠️ Installation

### Step 1: Clone the Brain
Copy these folders to your repository:
```bash
.github/workflows/
.github/scripts/
.github/prompts/
.github/swarm_rules.md
```

### Step 2: Add Secrets
Go to **Settings > Secrets and variables > Actions** and add:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `JULES_API_KEY`: API Key for the Coder Agent trigger.

### Step 3: Define Roles
Edit `.github/swarm_rules.md` to set your project's constitution.

---

## 🎨 Bot Customization & Branding

Want your AI to look professional? You can customize the bot's identity.

### Option A: Zero Config (Default)
Uses the standard `github-actions[bot]`.
- **Pros:** No setup required.
- **Cons:** Generic avatar.

### Option B: Custom Brand (Pro)
Use your own App Name and Logo (e.g., `EnesBot`).

1. Create a [GitHub App](https://github.com/settings/apps/new)
2. Permissions: `Contents: Read & Write`, `Issues: Read & Write`, `Pull Requests: Read & Write`
3. Generate **Private Key** and get **App ID**.
4. Add Secrets: `APP_ID` and `APP_PRIVATE_KEY`.

**Result:** Your bot comments with **your logo** (like the one we generated!) and name.

---

## 🤝 Contributing & Support
We love community contributions!
- See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
- **Rules:** All PRs must pass the AI Reviewer checks.
- **Contact:** [buzaslan.ea@gmail.com](mailto:buzaslan.ea@gmail.com)

---

## 📜 License
MIT - Free to fork, free to use, free to conquer.

