#!/usr/bin/env python3
"""
HiveMind Swarm Reviewer - Code Review Agent

This script uses AI models to analyze code changes (diffs) generated
by the Coder Agent, evaluating them against Project Golden Rules and
general code quality standards.

Features:
- Multi-model support (GLM-4, Gemini)
- Flexible approval logic (score-based)
- Robust JSON parsing
- Auto-labeling
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field

from ai_utils import (
    get_provider,
    load_prompt_template,
    parse_json_response,
    with_retry,
    redact_sensitive_data,
    logger,
    load_rules,
    MAX_DIFF_READ_LIMIT,
    get_config,
    metrics
)

class ReviewResult(BaseModel):
    """Schema for code review results."""
    approved: bool = Field(default=False)
    score: int = Field(default=5)
    verdict: str = Field(default='UNKNOWN')
    project_compliance: bool = Field(default=False)
    security_ok: bool = Field(default=True)
    positives: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)

def get_diff_content(filepath: str = 'coder_changes.diff') -> str:
    """
    Reads the diff content from the specified file path.
    Truncates large diffs and adds notice.
    """
    try:
        with open(filepath, 'r', encoding="utf-8") as f:
            content = f.read(MAX_DIFF_READ_LIMIT + 1)
            if len(content) > MAX_DIFF_READ_LIMIT:
                logger.warning(f"Diff truncated because it exceeds {MAX_DIFF_READ_LIMIT} chars")
                return content[:MAX_DIFF_READ_LIMIT] + "\n\n... [DIFF TRUNCATED DUE TO SIZE LIMIT] ..."
            return content
    except FileNotFoundError:
        logger.warning(f"Diff file not found: {filepath}")
        return "No changes found"




def build_prompt(template: str, diff: str, rules: str) -> str:
    """Formats the prompt template with diff and rules."""
    return template.replace("${{ diff }}", diff).replace("${{ rules }}", rules)


def generate_review(provider, prompt: str) -> Dict[str, Any]:
    """
    Generates code review using the configured AI provider.

    Args:
        provider: ModelProvider instance
        prompt: Formatted review prompt

    Returns:
        Parsed JSON review data
    """
    logger.info(f"Generating review with {provider.get_name()}...")
    
    def make_request():
        response = provider.generate(prompt)
        return parse_json_response(response, schema=ReviewResult)
    
    result = with_retry(make_request, max_retries=5)
    
    # Safety net: ensure required keys exist even if Pydantic validation failed or was partial
    defaults = {
        'approved': False,
        'score': 5,
        'verdict': 'UNKNOWN',
        'project_compliance': False,
        'security_ok': True,
        'positives': [],
        'issues': [],
        'suggestions': [],
        'labels': []
    }
    
    for key, default in defaults.items():
        if key not in result:
            logger.warning(f"Missing key '{key}', using default: {default}")
            result[key] = default
    
    return result


def calculate_approval(review_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Flexible approval logic based on score and security.

    Approval Rules (Configurable):
    - Security issues: Always reject
    - Score >= min_score_approve (default 8): Approve
    - Score >= min_score_conditional (default 6): Approve if compliant and <= max_issues_conditional (default 2)
    - Otherwise: Reject

    Args:
        review_data: Review JSON from AI

    Returns:
        Tuple of (approved: bool, reason: str)
    """
    # Load thresholds from config
    min_approve = get_config('reviewer.min_score_approve', 8)
    min_conditional = get_config('reviewer.min_score_conditional', 6)
    max_issues = get_config('reviewer.max_issues_conditional', 2)

    # Safe extraction helpers
    def get_score(data):
        val = data.get("score")
        if isinstance(val, (int, float)):
            return val
        return 0

    def get_bool(data, key, default=False):
        val = data.get(key)
        if isinstance(val, bool):
            return val
        return default

    def get_list(data, key):
        val = data.get(key)
        if isinstance(val, list):
            return val
        return []

    score = get_score(review_data)
    security_ok = get_bool(review_data, "security_ok", False)
    project_compliance = get_bool(review_data, "project_compliance", False)
    issues = get_list(review_data, "issues")
    
    # Critical: Security always first
    if not security_ok:
        return False, "Security issues detected - immediate attention required"
    
    # High score: approve with suggestions
    if score >= min_approve:
        return True, "Approved - excellent quality"
    
    # Medium score: conditional approval
    if min_conditional <= score < min_approve:
        if project_compliance and len(issues) <= max_issues:
            return True, f"Approved with {len(issues)} minor issues to address"
        return False, f"Score {score}/10 with {len(issues)} issues - improvements needed"
    
    # Low score: reject
    return False, f"Score {score}/10 - significant improvements required"


def format_review_comment(data: Dict[str, Any], approved: bool, reason: str) -> str:
    """
    Formats a markdown review comment.

    Args:
        data: Review data from AI
        approved: Final approval decision
        reason: Approval/rejection reason

    Returns:
        Formatted markdown comment
    """
    positives = "\n".join([f"- {p}" for p in data.get("positives", [])]) or "- No specific positives mentioned."
    issues = "\n".join([f"- {i}" for i in data.get("issues", [])]) or "- No issues detected."
    suggestions = "\n".join([f"- {s}" for s in data.get("suggestions", [])]) or "- No additional suggestions."
    
    verdict_emoji = "✅" if approved else "❌"
    status = "APPROVED" if approved else "CHANGES REQUESTED"
    
    return f"""## HiveMind Code Review

**Score:** {data.get('score', 'N/A')}/10
**Verdict:** {verdict_emoji} {status}
**Project Compliance:** {'✅' if data.get('project_compliance') else '❌'}
**Security:** {'✅' if data.get('security_ok') else '⚠️ ATTENTION NEEDED'}

> {reason}

### Positives
{positives}

### Issues
{issues}

### Suggestions
{suggestions}
"""


def write_outputs(approved: bool, comment: str, labels: List[str] = None) -> None:
    """
    Writes outputs to GitHub Actions and files.

    Args:
        approved: Approval decision
        comment: Review comment markdown
        labels: Optional list of labels to apply
    """
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding="utf-8") as f:
            f.write(f"approved={str(approved).lower()}\n")
            if labels:
                f.write(f"labels={','.join(labels)}\n")
    
    # Redact sensitive data before writing
    safe_comment = redact_sensitive_data(comment)
    Path("review_comment.md").write_text(safe_comment, encoding="utf-8")
    logger.info(f"Review written. Approved: {approved}")


def main() -> None:
    """Main function: reads diff, generates review, outputs results."""
    try:
        logger.info("Starting code review process...")
        metrics.reset()
        
        # Get provider
        provider = get_provider()
        
        # Read diff
        diff_content = get_diff_content()
        if diff_content == "No changes found":
            logger.warning("No diff content found to review")
            write_outputs(
                approved=False,
                comment="No changes found to review."
            )
            return
        
        # Load prompt and rules
        prompt_template = load_prompt_template(Path(".github/prompts/swarm_reviewer.prompt"))
        rules = load_rules()
        formatted_prompt = build_prompt(prompt_template, diff_content, rules)
        
        # Generate review
        review_data = generate_review(provider, formatted_prompt)
        
        # Calculate approval with flexible logic
        approved, reason = calculate_approval(review_data)
        
        # Format and write output
        comment = format_review_comment(review_data, approved, reason)
        labels = review_data.get('labels', [])
        write_outputs(approved, comment, labels)
        
        logger.info(f"Review completed! Approved: {approved} ({reason})")
        logger.info(f"Metrics: {metrics.summary()}")
    
    except ValueError as e:
        logger.error(f"Parsing error: {e}")
        write_outputs(
            approved=False,
            comment=f"Error during review: {e}"
        )
        logger.info(f"Metrics: {metrics.summary()}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        write_outputs(
            approved=False,
            comment=f"Critical error during review: {e}"
        )
        logger.info(f"Metrics: {metrics.summary()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
