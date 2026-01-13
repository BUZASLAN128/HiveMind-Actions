
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
from ai_utils import setup_generative_ai, load_prompt_template, logger


def get_diff_content(filepath: str = 'coder_changes.diff') -> str:
    """
    Reads the diff content from the specified file path.

    Args:
        filepath: Path to the diff file.

    Returns:
        The content of the file, or "No changes found" if not found.
    """
    try:
        return Path(filepath).read_text(encoding="utf-8")[:30000]
    except FileNotFoundError:
        return "No changes found"

def load_rules(filepath: str = '.github/swarm_rules.md') -> str:
    """Reads project rules from the file."""
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "No specific project rules found. Apply general Clean Code principles."

def format_prompt(prompt_template: str, diff_content: str, rules: str) -> str:
    """
    Formats the prompt template with diff content and rules.
    """
    return prompt_template.replace("${{ diff }}", diff_content).replace("${{ rules }}", rules)

def generate_review(client: genai.Client, prompt: str) -> Dict[str, Any]:
    """
    Generates a code review from the Gemini AI model using the provided prompt.

    Args:
        client (genai.Client): The Gemini AI client to use.
        prompt (str): The full prompt to send to the AI.

    Returns:
        Dict[str, Any]: A dictionary containing the JSON response from the AI.

    Raises:
        json.JSONDecodeError: AI'dan gelen yanıt geçerli bir JSON değilse.
    """
    logger.info("🤖 Generating code review with Gemini AI...")
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    result_text = response.text.strip()

    logger.debug(f"Raw AI Response:\n{result_text}")

    # JSON bloğunu güvenli bir şekilde çıkar
    try:
        if '```json' in result_text:
            json_part = result_text.split('```json')[1].split('```')[0]
        elif '```' in result_text:
            json_part = result_text.split('```')[1].split('```')[0]
        else:
            json_part = result_text
        return json.loads(json_part.strip())
    except (IndexError, json.JSONDecodeError) as e:
        logger.error(f"Could not parse JSON from AI response: {e}\nResponse: {result_text}")
        raise

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

def write_outputs(approved: bool, comment: str) -> None:
    """
    Writes the approval status and comment to GitHub Actions outputs.

    Args:
        approved: Whether the code is approved.
        comment: The review comment to write.
    """
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding="utf-8") as f:
            f.write(f"approved={str(approved).lower()}\n")

    Path("review_comment.md").write_text(comment, encoding="utf-8")

def main() -> None:
    """
    Main function: reads the diff, creates the prompt, generates review,
    and outputs results.
    """
    try:
        logger.info("▶️ Starting code review process...")
        client = setup_generative_ai()

        diff_content = get_diff_content()
        if diff_content == "No changes found":
            logger.warning("🚨 No diff content found to review. Aborting.")
            write_outputs(approved=False, comment="No changes found to review.")
            return

        prompt_template = load_prompt_template(Path(".github/prompts/swarm_reviewer.prompt"))
        rules = load_rules()
        formatted_prompt = format_prompt(prompt_template, diff_content, rules)

        review_data = generate_review(client, formatted_prompt)

        # Decision mechanism: Both 'approved' and 'project_compliance' must be true
        approved = review_data.get('approved', False) and review_data.get('project_compliance', False)

        comment = format_review_comment(review_data)
        write_outputs(approved, comment)

        logger.info(f"🏁 Review completed! Approved: {approved}")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"❌ Could not parse AI response or missing keys: {e}", exc_info=True)
        write_outputs(approved=False, comment=f"Error processing AI response: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during review: {e}", exc_info=True)
        write_outputs(approved=False, comment=f"Critical error during review: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
