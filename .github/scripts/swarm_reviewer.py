
"""
This script uses the Gemini AI model to analyze code changes (diffs) generated
by the Coder Agent, evaluating them against Project Golden Rules and general
code quality standards. It produces a review comment and an approval status.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from google import genai
from ai_utils import setup_generative_ai, load_prompt_template, logger, load_rules, redact_sensitive_data, load_config



def get_diff_content(filepath: str = 'coder_changes.diff') -> str:
    """
    Reads the diff content from the specified file path.
    Adds a notice if truncated to inform the AI.
    """
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        limit = 30000
        if len(content) > limit:
            return content[:limit] + "\n\n... [DIFF TRUNCATED DUE TO SIZE LIMIT] ..."
        return content
    except FileNotFoundError:
        return "No changes found"


def format_prompt(prompt_template: str, diff_content: str, rules: str) -> str:
    """
    Formats the prompt template with diff content, rules, and issue context.
    """
    issue_title = os.getenv('ISSUE_TITLE', 'N/A')
    issue_body = os.getenv('ISSUE_BODY', 'No description provided.')

    return (prompt_template
            .replace("${{ diff }}", diff_content)
            .replace("${{ rules }}", rules)
            .replace("${{ issue_title }}", issue_title)
            .replace("${{ issue_body }}", issue_body))

def generate_review(client: genai.Client, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a code review from the Gemini AI model using the provided prompt.

    Args:
        client (genai.Client): The Gemini AI client to use.
        prompt (str): The full prompt to send to the AI.
        config (Dict[str, Any]): Dictionary containing configuration values.

    Returns:
        Dict[str, Any]: A dictionary containing the JSON response from the AI.

    Raises:
        json.JSONDecodeError: If the response from the AI is not valid JSON.
    """
    model_name = config.get("ai_model", "gemini-2.0-flash")
    logger.info("🤖 Generating code review with Gemini AI...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    result_text = response.text.strip()

    logger.debug(f"Raw AI Response:\n{result_text}")

    # Robust JSON parsing
    try:
        # Find the start and end of the JSON block, even with markdown wrappers
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise json.JSONDecodeError("No JSON object found in the response.", result_text, 0)

        json_part = result_text[json_start:json_end]
        data = json.loads(json_part)
        
        # Defensive check for required keys
        required_keys = ['score', 'issues']
        if not all(key in data for key in required_keys):
            raise KeyError(f"Missing one or more required keys in JSON response: {required_keys}")

        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from AI. Error: {e}\nRaw Response:\n{result_text}")
        # Return a default error structure to prevent workflow crash
        return {
            "approved": False,
            "score": 0,
            "issues": [f"Failed to parse AI response: {e}"],
            "positives": [],
            "suggestions": [],
            "project_compliance": False,
            "security_ok": False,
            "verdict": "REJECTED (Parsing Error)",
            "labels": ["bug", "review-failed"]
        }
    except KeyError as e:
        logger.error(f"Missing required key in AI response. Error: {e}\nRaw Response:\n{result_text}")
        # Return a default error structure to prevent workflow crash
        return {
            "approved": False,
            "score": 0,
            "issues": [f"AI response was missing a required key: {e}"],
            "positives": [],
            "suggestions": [],
            "project_compliance": False,
            "security_ok": False,
            "verdict": "REJECTED (Missing Key)",
            "labels": ["bug", "review-failed"]
        }

def format_review_comment(data: Dict[str, Any]) -> str:
    """
    Formats a markdown comment using the data from the AI model.

    Args:
        data: JSON data from the AI model.

    Returns:
        Formatted comment text in markdown.
    """
    positives = "\n".join([f"- {p}" for p in data.get("positives", [])]) if data.get("positives") else "- No specific positives mentioned."
    issues = "\n".join([f"- {i}" for i in data.get("issues", [])]) if data.get("issues") else "- No issues detected. Good job! 👏"
    suggestions = "\n".join([f"- {s}" for s in data.get("suggestions", [])]) if data.get("suggestions") else "- No additional suggestions."

    return f"""## 🔎 Gemini Code Review

**Score:** {data.get('score', 'N/A')}/10
**Verdict:** {data.get('verdict', 'N/A')}
**Project Compliance:** {'✅' if data.get('project_compliance') else '❌'}
**Security:** {'✅' if data.get('security_ok') else '❌'}

### ✅ Positives
{positives}

### ⚠️ Issues
{issues}

### 💡 Suggestions
{suggestions}
"""

def write_outputs(approved: bool, comment: str, labels: List[str] = None) -> None:
    """
    Writes outputs to GitHub Actions.
    """
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding="utf-8") as f:
            f.write(f"approved={str(approved).lower()}\n")
            if labels:
                # Join labels with comma for use in workflow
                f.write(f"labels={','.join(labels)}\n")

    comment = redact_sensitive_data(comment)
    Path("review_comment.md").write_text(comment, encoding="utf-8")

def main() -> None:
    """
    Main function: reads the diff, creates the prompt, generates review,
    and outputs results.
    """
    try:
        logger.info("▶️ Starting code review process...")
        
        # 🔑 Explicit API Key check for faster debugging
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
            logger.error("❌ GEMINI_API_KEY is not set in environment variables.")
            write_outputs(approved=False, comment="Critical error: AI API Key is missing.")
            sys.exit(1)

        client = setup_generative_ai()

        diff_content = get_diff_content()
        if diff_content == "No changes found":
            logger.warning("🚨 No diff content found to review. Aborting.")
            write_outputs(approved=False, comment="No changes found to review.")
            return

        config = load_config()
        prompt_template = load_prompt_template(Path(".github/prompts/swarm_reviewer.prompt"))
        rules = load_rules()
        formatted_prompt = format_prompt(prompt_template, diff_content, rules)

        review_data = generate_review(client, formatted_prompt, config)

        # Stricter decision mechanism
        min_score = config.get("min_review_score", 8)
        score = review_data.get("score", 0)
        issues_found = len(review_data.get("issues", []))

        # Approval requires a score >= min_score AND zero issues.
        approved = score >= min_score and issues_found == 0

        comment = format_review_comment(review_data)
        labels = review_data.get('labels', [])
        write_outputs(approved, comment, labels)

        logger.info(f"🏁 Review completed! Approved: {approved}")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"❌ Could not parse AI response or missing keys: {e}", exc_info=True)
        write_outputs(approved=False, comment=f"Error processing AI response: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}", exc_info=True)
        write_outputs(approved=False, comment=f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during review: {e}", exc_info=True)
        write_outputs(approved=False, comment=f"Critical error during review: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
