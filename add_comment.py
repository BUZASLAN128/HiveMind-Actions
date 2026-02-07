import pathlib

p = pathlib.Path(".github/scripts/swarm_analyzer.py")
content = p.read_text(encoding="utf-8")

old_snippet = """                    try:
                        with file_path.open(encoding='utf-8') as f:
                            content = f.read(max_len)"""

new_snippet = """                    try:
                        # Optimization: Use read(limit) to avoid loading entire file into memory
                        with file_path.open(encoding='utf-8') as f:
                            content = f.read(max_len)"""

if old_snippet in content:
    content = content.replace(old_snippet, new_snippet)
    p.write_text(content, encoding="utf-8")
    print("Added comment to get_codebase_context")
else:
    print("Could not find get_codebase_context snippet")
