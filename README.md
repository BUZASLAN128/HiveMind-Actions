# HiveMind Actions

Serverless multi-agent automation for GitHub Actions: Analyst plans, Coder implements, Reviewer verifies, and self-correction closes the loop.

## Quick Links

- Repository: https://github.com/BUZASLAN128/HiveMind-Actions
- Actions: https://github.com/BUZASLAN128/HiveMind-Actions/actions
- Analyst Workflow: https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-analyst.yml
- Coder Workflow: https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-coder.yml
- Reviewer Workflow: https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-reviewer.yml
- Releases: https://github.com/BUZASLAN128/HiveMind-Actions/releases
- Latest Tag: https://github.com/BUZASLAN128/HiveMind-Actions/releases/tag/v2.1.1

[![Analyst Workflow](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-analyst.yml/badge.svg)](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-analyst.yml)
[![Coder Workflow](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-coder.yml/badge.svg)](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-coder.yml)
[![Reviewer Workflow](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-reviewer.yml/badge.svg)](https://github.com/BUZASLAN128/HiveMind-Actions/actions/workflows/agent-reviewer.yml)

## What It Does

HiveMind Actions turns a repository into an autonomous collaboration flow:

- Analyst converts issue intent into implementable plans.
- Coder executes the plan and opens/updates PRs.
- Reviewer checks code quality, security, and project rules.
- Reviewer can trigger self-correction when PR quality is insufficient.

## 1-Minute Quickstart

1. Copy these paths into your repository:
   - `.github/workflows/`
   - `.github/scripts/`
   - `.github/prompts/`
   - `.github/swarm_rules.md`
   - `.github/config.json`
2. Add required secrets and variables in `Settings -> Secrets and variables -> Actions`.
3. Create an issue and comment `@analyst`.
4. Analyst runs, dispatches Coder (`workflow_dispatch`), Coder opens PR, Reviewer evaluates PR.

## Configuration Matrix (Source of Truth)

### Secrets and Variables

| Name | Required | Used By | Purpose |
|---|---|---|---|
| `GLM_API_KEY` | Yes (if provider=`glm`) | `agent-analyst.yml`, `agent-reviewer.yml` | GLM provider access |
| `GEMINI_API_KEY` | Yes (if provider=`gemini`) | `agent-analyst.yml`, `agent-reviewer.yml` | Gemini provider access |
| `JULES_API_KEY` | Yes | `agent-coder.yml`, `agent-reviewer.yml` | Coder execution + reviewer self-correction calls |
| `APP_ID` | Optional | `agent-reviewer.yml` | GitHub App auth for branded bot identity |
| `APP_PRIVATE_KEY` | Optional | `agent-reviewer.yml` | Pair for `APP_ID` |
| `SWARM_MODEL_PROVIDER` | Optional (`glm` default) | `agent-analyst.yml`, `agent-reviewer.yml` | Select active model provider |

### Workflow Permission Expectations

| Workflow | Key Permissions |
|---|---|
| `agent-analyst.yml` | `actions: write`, issue/comment read-write |
| `agent-coder.yml` | contents and PR write scopes for automation |
| `agent-reviewer.yml` | pull request review/comment write scopes |

## Trigger Matrix

| Workflow | Trigger | Notes |
|---|---|---|
| `agent-analyst.yml` | `issue_comment` (`@analyst` or `@analyze`) | Entry point for tasks |
| `agent-coder.yml` | `workflow_dispatch` | Dispatched by Analyst; centralized execution |
| `agent-reviewer.yml` | `pull_request` (`opened`, `synchronize`, `ready_for_review`) | Reviews and may trigger self-correction |

## Version and Release Policy

Current public tags:

- `v2.0.0`
- `v2.1.0`
- `v2.1.1`

Preparation target: `v2.2.0`.

SemVer policy:

- `MAJOR`: breaking workflow/protocol changes.
- `MINOR`: new capabilities without breaking current setup.
- `PATCH`: bugfixes and reliability improvements.

Tag vs Release:

- **Tag** marks source state (`git tag`).
- **GitHub Release** is distribution metadata (notes, changelog mapping, assets if added).

For `v2.2.0`, prepare changelog + release notes first, then create a proper GitHub Release from the tag.

## Download and Release Channel

- Releases page: https://github.com/BUZASLAN128/HiveMind-Actions/releases
- Changelog source: `CHANGELOG.md`
- Release checklist: `RELEASE_CHECKLIST.md`

Recommended release content:

- Summary of workflow-level changes
- Breaking/non-breaking classification
- Security or behavior-impact notes
- Upgrade guidance from previous tag

## Troubleshooting

### Missing API key errors

- Verify `GLM_API_KEY` or `GEMINI_API_KEY` based on `SWARM_MODEL_PROVIDER`.
- Verify `JULES_API_KEY` exists for coder/reviewer handoff.

### Analyst does not trigger

- Ensure comment is on an issue and includes `@analyst` or `@analyze`.
- Ensure commenter has required repository permissions.

### Coder not running after Analyst

- Confirm `agent-analyst.yml` can dispatch workflow (`actions: write`).
- Check Actions logs for `workflow_dispatch` payload and inputs.

### Reviewer self-correction not firing

- Confirm `JULES_API_KEY` is configured.
- Confirm PR body/comments contain expected session markers.
- Check reviewer logs for continuity lookup and API call errors.

## FAQ

### Should I use GLM or Gemini?

- Use `glm` for default coding-focused flow.
- Use `gemini` if your environment/team prefers Gemini behavior and key management.

### Do I need a GitHub App for this to work?

No. GitHub App setup (`APP_ID`, `APP_PRIVATE_KEY`) is optional for branding/identity improvements.

### Is this only for large repositories?

No. It works for small repositories too, and becomes more valuable as task/review load increases.

## Roadmap (Short)

- Improve release automation and notes generation
- Add reliability metrics dashboarding for workflow outcomes
- Expand documentation for enterprise permission models
- Improve test strategy split (unit vs e2e vs provider-gated)

## Contributing and Security

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Project license: [LICENSE](LICENSE)