#!/usr/bin/env python3
"""E2E Test with Real GLM API - z.ai Platform"""
import os
import sys
sys.path.insert(0, '.')

# Set API key
if len(sys.argv) > 1:
    os.environ['GLM_API_KEY'] = sys.argv[1]

os.environ['SWARM_MODEL_PROVIDER'] = 'glm'

print("=" * 50)
print("E2E TEST: GLM-4.7 on z.ai Platform")
print("=" * 50)

try:
    from ai_utils import get_provider, parse_json_response
    
    print("\n1. Initializing GLM Provider...")
    provider = get_provider()
    print(f"   Provider: {provider.get_name()}")
    
    print("\n2. Sending test prompt...")
    prompt = 'Return ONLY valid JSON: {"status": "ok", "message": "GLM works!"}'
    response = provider.generate(prompt)
    print(f"   Response: {response[:200]}")
    
    print("\n3. Parsing JSON...")
    result = parse_json_response(response)
    print(f"   Parsed: {result}")
    
    print("\n" + "=" * 50)
    print("E2E TEST PASSED!")
    print("=" * 50)

except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
