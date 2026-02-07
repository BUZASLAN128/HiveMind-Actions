import pathlib

p = pathlib.Path(".github/scripts/swarm_analyzer.py")
content = p.read_text(encoding="utf-8")

old_code = """    try:
        content = Path(filepath).read_text(encoding="utf-8")
        logger.info("Loaded project rules")
        return content"""

new_code = """    try:
        limit = 50000
        with Path(filepath).open(encoding="utf-8") as f:
            content = f.read(limit)
            if len(content) == limit:
                logger.warning(f"Rules file {filepath} truncated to {limit} chars")
        logger.info("Loaded project rules")
        return content"""

if old_code in content:
    content = content.replace(old_code, new_code)
    p.write_text(content, encoding="utf-8")
    print("Replaced load_rules body")
else:
    print("Could not find old code block")
    # Print a snippet to debug if needed
    start = content.find("def load_rules")
    if start != -1:
        print("Found def load_rules at index", start)
        print("Surrounding code:")
        print(content[start:start+300])
