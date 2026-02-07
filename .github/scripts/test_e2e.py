#!/usr/bin/env python3
"""E2E Test with Real AI APIs (GLM & Gemini)"""
import os
import sys
sys.path.insert(0, '.')

from ai_utils import get_provider, parse_json_response

# Handle command line arguments for API keys
if len(sys.argv) > 1:
    os.environ['GLM_API_KEY'] = sys.argv[1]
if len(sys.argv) > 2:
    os.environ['GEMINI_API_KEY'] = sys.argv[2]

def test_provider(provider_name):
    print("\n" + "=" * 50)
    print(f"E2E TEST: {provider_name.upper()}")
    print("=" * 50)
    
    # Set provider
    os.environ['SWARM_MODEL_PROVIDER'] = provider_name
    
    # Check if key is available
    key_var = 'GLM_API_KEY' if provider_name == 'glm' else 'GEMINI_API_KEY'
    if not os.getenv(key_var):
        print(f"SKIPPING: {key_var} not found.")
        return

    try:
        print(f"\n1. Initializing {provider_name.upper()} Provider...")
        provider = get_provider()
        print(f"   Provider: {provider.get_name()}")

        print("\n2. Sending test prompt...")
        prompt = 'Return ONLY valid JSON: {"status": "ok", "message": "API works!"}'

        # Test system prompt if possible
        system_prompt = "You are a JSON generator."
        response = provider.generate(prompt, system_prompt=system_prompt)
        print(f"   Response: {response[:200]}")

        print("\n3. Parsing JSON...")
        result = parse_json_response(response)
        print(f"   Parsed: {result}")

        if result.get('status') == 'ok':
            print(f"\nSUCCESS: {provider_name.upper()} Test Passed!")
        else:
            print(f"\nWARNING: Unexpected JSON content: {result}")

    except Exception as e:
        print(f"\nERROR: {e}")
        # We don't exit here so other tests can run
        pass

if __name__ == "__main__":
    test_provider('glm')
    test_provider('gemini')
    
    print("\n" + "=" * 50)
    print("E2E TESTS COMPLETED")
    print("=" * 50)
