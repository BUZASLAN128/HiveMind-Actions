
#!/usr/bin/env python3
"""
This script uses the Gemini AI model to analyze a GitHub issue, create an action plan,
and generate a prompt for the Coder Agent.

It serves as the first step in the HiveMind Swarm architecture.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from google import genai
from ai_utils import setup_generative_ai, load_prompt_template, logger

def get_codebase_context(root_dir: Path, max_files: int = 20, max_len: int = 2000) -> str:
    """
    Collects codebase context by reading Python files in the project root.

    Args:
        root_dir: Project root directory.
        max_files: Maximum number of files to read.
        max_len: Maximum character length per file.

    Returns:
        String containing the codebase context.
    """
    logger.info(f"📂 Reading codebase context from {root_dir}...")
    context_parts = []

    # Prioritize scanning the 'app' directory if it exists
    app_dir = root_dir / "app"
    if app_dir.exists():
        py_files = list(app_dir.rglob("*.py"))
        for file_path in py_files[:max_files]:
            try:
                content = file_path.read_text(encoding='utf-8')[:max_len]
                relative_path = file_path.relative_to(root_dir)
                context_parts.append(f"### {relative_path}\n```python\n{content}\n```")
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

    return "\n".join(context_parts)

def load_rules(filepath: str = '.github/swarm_rules.md') -> str:
    """Reads project rules from the configuration file."""
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "No project rules found."

def load_and_format_prompt(prompt_path: Path, issue_data: Dict[str, Any], context: str, rules: str) -> str:
    """
    Loads a prompt template and formats it with issue data and codebase context.

    Args:
        prompt_path (Path): Prompt şablon dosyasının yolu.
        issue_data (Dict[str, Any]): Issue başlığı, numarası ve gövdesini içeren bir sözlük.
        context (str): Kod tabanı bağlamı.

    Returns:
        str: Formatlanmış ve gönderilmeye hazır prompt.
    """
    prompt_template = load_prompt_template(prompt_path)
    return prompt_template.format(
        issue_number=issue_data.get('number', 'N/A'),
        issue_title=issue_data.get('title', 'No Title'),
        issue_body=issue_data.get('body', 'No Description'),
        comment=issue_data.get('comment', ''),
        codebase=context,
        rules=rules
    )

def analyze_issue(client: genai.Client, prompt: str) -> Dict[str, Any]:
    """
    Generates an issue analysis from the AI model using the provided prompt.

    Args:
        client: genai.Client to use.
        prompt: Formatted prompt to send to AI.

    Returns:
        AI'dan gelen JSON yanıtını içeren bir sözlük.
    """
    logger.info("🤖 Analyzing issue with Gemini AI...")
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    result_text = response.text.strip()

    if '```json' in result_text:
        result_text = result_text.split('```json')[1].split('```')[0]
    elif '```' in result_text:
        result_text = result_text.split('```')[1].split('```')[0]

    return json.loads(result_text.strip())

def write_outputs(data: Dict[str, Any]) -> None:
    """
    Writes analysis results to GitHub Actions outputs and temporary files.

    Args:
        data: Analizden elde edilen verileri içeren sözlük.
    """
    should_proceed = data.get('should_proceed', False)
    issue_type = data.get('issue_type', 'unclear')
    
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"should_proceed={str(should_proceed).lower()}\n")
            f.write(f"issue_type={issue_type}\n")
            f.write(f"plan={json.dumps(data.get('plan', []))}\n")
            f.write(f"files_to_change={json.dumps(data.get('files_to_change', []))}\n")

    Path('coder_task.txt').write_text(data.get('coder_instructions', 'Implement the requested feature.'), encoding='utf-8')

    # Newline char defined outside f-string for Python 3.12+ compatibility
    newline = '\n'
    files_list = newline.join([f"- `{f}`" for f in data.get('files_to_change', [])]) or "- (None)"
    plan_list = newline.join([f"{i}. {s}" for i, s in enumerate(data.get('plan', []), 1)]) or "- (No plan)"
    risks_list = ', '.join(data.get('risks', ['None']))
    
    # Emoji based on issue type
    type_emoji = {"code_request": "🛠️", "question": "❓", "unclear": "⚠️"}.get(issue_type, "📋")
    
    summary = f"""## 🔍 Gemini Analysis Report

{type_emoji} **Issue Type:** {issue_type.upper()}

**Analysis:** {data.get('analysis', 'N/A')}

**Files to Change:**
{files_list}

**Plan:**
{plan_list}

**Estimated Complexity:** {data.get('estimated_complexity', 'unknown')}
**Risks:** {risks_list}
"""
    Path('analysis_summary.md').write_text(summary, encoding='utf-8')
    logger.info(f"✅ Analysis outputs returned. Issue Type: {issue_type}, Proceed: {should_proceed}")

def main() -> None:
    """
    Main function: analyzes the issue, creates a plan, and saves results.
    """
    try:
        client = setup_generative_ai()

        issue_data = {
            'number': os.environ.get('ISSUE_NUMBER', 'N/A'),
            'title': os.environ.get('ISSUE_TITLE', 'No Title'),
            'body': os.environ.get('ISSUE_BODY', 'No Description'),
            'comment': os.environ.get('TRIGGERING_COMMENT', ''),
        }

        logger.info(f"▶️ Starting analysis for Issue #{issue_data['number']}: '{issue_data['title']}'...")

        project_root = Path.cwd()
        codebase_context = get_codebase_context(project_root)
        rules = load_rules()

        prompt_path = project_root / ".github" / "prompts" / "swarm_analyzer.prompt"
        formatted_prompt = load_and_format_prompt(prompt_path, issue_data, codebase_context, rules)

        analysis_data = analyze_issue(client, formatted_prompt)
        write_outputs(analysis_data)

        should_proceed = analysis_data.get('should_proceed', False)
        logger.info(f"🏁 Analysis complete! Should proceed: {should_proceed}")
        if not should_proceed:
            logger.warning("AI decided this issue cannot be resolved automatically.")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"❌ Could not parse AI response or missing keys: {e}", exc_info=True)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"❌ Required file not found: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # GitHub Actions'tan gelen ISSUE_BODY'deki CR karakterlerini temizle
    if 'ISSUE_BODY' in os.environ:
        os.environ['ISSUE_BODY'] = os.environ['ISSUE_BODY'].replace('\r', '')
    main()
