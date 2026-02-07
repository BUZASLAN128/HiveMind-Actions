#!/usr/bin/env python3
"""
HiveMind Swarm Analyzer - Issue Analysis Agent

This script uses AI models to analyze GitHub issues, create action plans,
and generate prompts for the Coder Agent. It serves as the first step
in the HiveMind Swarm architecture.

Supports: GLM-4, Gemini (configurable via SWARM_MODEL_PROVIDER)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from ai_utils import (
    get_provider,
    load_prompt_template,
    parse_json_response,
    with_retry,
    redact_sensitive_data,
    logger,
    load_rules,
    MAX_RULES_READ_LIMIT,
    get_config,
    metrics
)

class AnalysisResult(BaseModel):
    """Schema for issue analysis results."""
    should_proceed: bool = Field(default=False)
    issue_type: str = Field(default='unclear')
    coder_instructions: str = Field(default='')
    plan: List[str] = Field(default_factory=list)
    files_to_change: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    analysis: str = Field(default='')
    estimated_complexity: str = Field(default='unknown')

# Configuration Constants
DEFAULT_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java'}
DEFAULT_PRIORITY_DIRS = ['app', 'src', 'lib', 'core']

# Exclude patterns - directories to skip during codebase scanning
DEFAULT_EXCLUDE_PATTERNS = [
    'node_modules', '__pycache__', '.git', 'dist', 'build',
    'venv', '.venv', 'env', 'vendor', '.next', '.nuxt',
    'coverage', '.nyc_output', '.pytest_cache', '.tox',
    'eggs', '*.egg-info', '.eggs'
]

# Research mode keywords - triggers codebase analysis even for unclear issues
RESEARCH_KEYWORDS = [
    'incele', 'arastir', 'analiz', 'oneriler', 'gelistirme', 'iyilestirme',
    'research', 'analyze', 'suggest', 'improve', 'review', 'audit'
]


def get_codebase_context(
    root_dir: Path,
    max_files: int = 20,
    max_len: int = MAX_RULES_READ_LIMIT,
    extensions: set = None,
    priority_dirs: list = None,
    exclude_patterns: list = None
) -> str:
    """
    Collects codebase context by reading source files in the project root.

    Args:
        root_dir: Project root directory.
        max_files: Maximum number of files to read.
        max_len: Maximum character length per file.
        extensions: Set of file extensions to scan.
        priority_dirs: List of directories to prioritize.

    Returns:
        String containing the codebase context.
    """
    logger.info(f"Reading codebase context from {root_dir}...")
    context_parts = []
    total_files = 0
    
    # Use defaults from config or constants
    if not extensions:
        config_ext = get_config('extensions')
        extensions = set(config_ext) if config_ext else DEFAULT_EXTENSIONS

    if not priority_dirs:
        priority_dirs = get_config('priority_dirs', DEFAULT_PRIORITY_DIRS)

    if not exclude_patterns:
        exclude_patterns = get_config('exclude_patterns', DEFAULT_EXCLUDE_PATTERNS)
    
    # Prepare extensions for checking
    valid_extensions = tuple(ext if ext.startswith('.') else f".{ext}" for ext in extensions)

    # Scan priority directories first
    for priority in priority_dirs:
        priority_path = root_dir / priority
        if priority_path.exists() and total_files < max_files:
            # Optimized scan: Single traversal
            for file_path in priority_path.rglob("*"):
                if total_files >= max_files:
                    break
                
                # Skip excluded directories
                path_str = str(file_path)
                if any(pattern in path_str for pattern in exclude_patterns):
                    continue

                if file_path.is_file() and file_path.name.endswith(valid_extensions):
                    try:
                        with file_path.open(encoding='utf-8') as f:
                            content = f.read(max_len + 1)

                        if len(content) > max_len:
                            logger.warning(f"File {file_path} truncated to {max_len} chars")
                            content = content[:max_len] + "\n... [TRUNCATED]"

                        relative_path = file_path.relative_to(root_dir)
                        # Use suffix as language identifier (removing dot)
                        lang = file_path.suffix[1:] if file_path.suffix else "txt"
                        context_parts.append(f"### {relative_path}\n```{lang}\n{content}\n```")
                        total_files += 1
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
    
    logger.info(f"Collected context from {total_files} files")
    return "\n".join(context_parts)


# Caching for codebase context
_context_cache: Dict[str, Tuple[str, float]] = {}
CACHE_TTL = 300  # 5 minutes

def get_codebase_context_cached(
    root_dir: Path,
    max_files: int = 20,
    max_len: int = MAX_RULES_READ_LIMIT
) -> str:
    """
    Cached version of get_codebase_context.
    Uses TTL-based cache to avoid repeated file system scans.
    
    Args:
        root_dir: Project root directory
        max_files: Maximum number of files to read
        max_len: Maximum character length per file
        
    Returns:
        Cached or freshly collected codebase context
    """
    import hashlib
    import time
    
    # Generate cache key based on directory and params
    cache_key = f"{root_dir}:{max_files}:{max_len}"
    
    if cache_key in _context_cache:
        content, timestamp = _context_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info("Using cached codebase context")
            return content
    
    # Fetch fresh content
    content = get_codebase_context(root_dir, max_files, max_len)
    _context_cache[cache_key] = (content, time.time())
    
    return content



def is_research_request(issue_data: Dict[str, Any]) -> bool:
    """
    Checks if the issue/comment requests a research/analysis mode.
    
    Args:
        issue_data: Dictionary with issue details
        
    Returns:
        True if this is a research request
    """
    text = (
        issue_data.get('title', '') + ' ' + 
        issue_data.get('body', '') + ' ' + 
        issue_data.get('comment', '')
    ).lower()
    
    # Load keywords from config
    keywords_config = get_config('research_keywords', {})

    # Flatten values if dict (en/tr lists), or use list if direct list
    keywords = []
    if isinstance(keywords_config, dict):
        for kw_list in keywords_config.values():
            if isinstance(kw_list, list):
                keywords.extend(kw_list)
    elif isinstance(keywords_config, list):
        keywords = keywords_config

    # Fallback to constants if config empty
    if not keywords:
         keywords = RESEARCH_KEYWORDS

    return any(keyword.lower() in text for keyword in keywords)


def build_prompt(prompt_template: str, issue_data: Dict[str, Any], context: str, rules: str) -> str:
    """
    Builds the full prompt from template and data.

    Args:
        prompt_template: Prompt template string
        issue_data: Dictionary with issue details
        context: Codebase context string
        rules: Project rules string

    Returns:
        Formatted prompt ready for AI
    """
    return prompt_template.format(
        issue_number=issue_data.get('number', 'N/A'),
        issue_title=issue_data.get('title', 'No Title'),
        issue_body=issue_data.get('body', 'No Description'),
        comment=issue_data.get('comment', ''),
        codebase=context,
        rules=rules
    )


def analyze_issue(provider, prompt: str) -> Dict[str, Any]:
    """
    Generates an issue analysis using the configured AI provider.

    Args:
        provider: ModelProvider instance
        prompt: Formatted prompt to send

    Returns:
        Parsed JSON response as dictionary
    """
    logger.info(f"Analyzing issue with {provider.get_name()}...")
    
    def make_request():
        response = provider.generate(prompt)
        return parse_json_response(response, schema=AnalysisResult)
    
    # Use retry logic for robustness
    result = with_retry(make_request, max_retries=3)
    
    # Safety net: Validate required fields even if schema validation failed
    required_fields = ['should_proceed', 'issue_type', 'coder_instructions']
    for field in required_fields:
        if field not in result:
            logger.warning(f"Missing field '{field}' in response, adding default")
            if field == 'should_proceed':
                result[field] = False
            elif field == 'issue_type':
                result[field] = 'unclear'
            else:
                result[field] = ''
    
    return result


def write_outputs(data: Dict[str, Any]) -> None:
    """
    Writes analysis results to GitHub Actions outputs and files.

    Args:
        data: Analysis data dictionary
    """
    should_proceed = data.get('should_proceed', False)
    issue_type = data.get('issue_type', 'unclear')
    
    # Write to GITHUB_OUTPUT
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"should_proceed={str(should_proceed).lower()}\n")
            f.write(f"issue_type={issue_type}\n")
            f.write(f"plan={json.dumps(data.get('plan', []))}\n")
            f.write(f"files_to_change={json.dumps(data.get('files_to_change', []))}\n")
    
    # Write coder task file
    coder_instructions = data.get('coder_instructions', 'Implement the requested feature.')
    Path('coder_task.txt').write_text(coder_instructions, encoding='utf-8')
    
    # Build summary markdown
    files_list = "\n".join([f"- `{f}`" for f in data.get('files_to_change', [])]) or "- (None)"
    plan_list = "\n".join([f"{i}. {s}" for i, s in enumerate(data.get('plan', []), 1)]) or "- (No plan)"
    risks_list = ', '.join(data.get('risks', ['None']))
    
    type_emoji = {"code_request": "🛠️", "question": "❓", "research": "🔬", "unclear": "⚠️"}.get(issue_type, "📋")
    
    summary = f"""## Gemini Analysis Report

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
    logger.info(f"Outputs written. Type: {issue_type}, Proceed: {should_proceed}")


def main() -> None:
    """Main function: analyzes the issue, creates a plan, and saves results."""
    try:
        metrics.reset()

        # Get AI provider
        provider = get_provider()
        
        # Collect issue data from environment
        issue_data = {
            'number': os.environ.get('ISSUE_NUMBER', 'N/A'),
            'title': os.environ.get('ISSUE_TITLE', 'No Title'),
            'body': os.environ.get('ISSUE_BODY', 'No Description').replace('\r', ''),
            'comment': os.environ.get('TRIGGERING_COMMENT', ''),
        }
        
        logger.info(f"Starting analysis for Issue #{issue_data['number']}: '{issue_data['title']}'...")
        
        # Check if this is a research request
        research_mode = is_research_request(issue_data)
        if research_mode:
            logger.info("Research mode detected - will analyze codebase for improvements")
        
        # Build context - for research mode, get more files
        project_root = Path.cwd()
        # Use config for max_files default
        default_max_files = get_config('limits.max_files_context', 20)
        max_files = 50 if research_mode else default_max_files
        codebase_context = get_codebase_context(project_root, max_files=max_files)
        rules = load_rules()
        
        # For research mode, enhance the prompt with research instructions
        if research_mode and not codebase_context.strip():
            # Force scan all code files if priorit dirs are empty
            logger.info("Priority dirs empty, scanning root for source files...")
            codebase_context = get_codebase_context(
                project_root, 
                max_files=50, 
                priority_dirs=['.github/scripts', '.github/workflows', '.']
            )
        
        # Load and format prompt
        prompt_path = project_root / ".github" / "prompts" / "swarm_analyzer.prompt"
        prompt_template = load_prompt_template(prompt_path)
        
        # For research mode, add extra context to prompt
        if research_mode:
            research_instruction = """
## RESEARCH MODE ACTIVE
The user wants you to analyze this codebase and suggest improvements.
Even if the request is vague, you SHOULD proceed with should_proceed=true.
Set issue_type to "research" and provide:
- Code quality improvements
- Missing features that would be valuable
- Security enhancements
- Performance optimizations
- Best practices that are not followed

DO NOT reject this as unclear. Analyze and provide actionable suggestions.
"""
            formatted_prompt = build_prompt(prompt_template, issue_data, codebase_context, rules)
            formatted_prompt = research_instruction + "\n" + formatted_prompt
        else:
            formatted_prompt = build_prompt(prompt_template, issue_data, codebase_context, rules)
        
        # Analyze
        analysis_data = analyze_issue(provider, formatted_prompt)
        
        # For research mode, force should_proceed if AI still says no
        if research_mode and not analysis_data.get('should_proceed', False):
            logger.info("Research mode: overriding should_proceed to True")
            analysis_data['should_proceed'] = True
            analysis_data['issue_type'] = 'research'
        
        write_outputs(analysis_data)
        
        should_proceed = analysis_data.get('should_proceed', False)
        logger.info(f"Analysis complete! Should proceed: {should_proceed}")
        logger.info(f"Metrics: {metrics.summary()}")
        
        if not should_proceed:
            logger.warning("AI decided this issue cannot be resolved automatically.")
    
    except ValueError as e:
        logger.error(f"Value error: {e}")
        # Write failure output
        write_outputs({
            'should_proceed': False,
            'issue_type': 'error',
            'analysis': str(e),
            'coder_instructions': 'Error occurred during analysis.'
        })
        logger.info(f"Metrics: {metrics.summary()}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        logger.info(f"Metrics: {metrics.summary()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
