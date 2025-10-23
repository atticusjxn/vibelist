#!/usr/bin/env python3
"""Test script to check Grok API sentiment analysis with live search"""

import logging
import os
import requests
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

def test_raw_api_call():
    """Test raw API call to see exact error"""
    api_key = os.getenv("XAI_API_KEY")

    # Try different search_parameters formats
    payloads_to_test = [
        # Test 1: Without mode parameter
        {
            "model": "grok-4-fast",
            "messages": [{"role": "user", "content": "Search live X for NVDA stock sentiment. Return JSON with post_count and sentiment_score."}],
            "max_tokens": 400,
            "temperature": 0.3,
            "search_parameters": {
                "query": "NVDA stock min_faves:50",
                "num_sources": 10
            }
        },
        # Test 2: With mode "auto"
        {
            "model": "grok-4-fast",
            "messages": [{"role": "user", "content": "Search live X for NVDA stock sentiment. Return JSON with post_count and sentiment_score."}],
            "max_tokens": 400,
            "temperature": 0.3,
            "search_parameters": {
                "query": "NVDA stock min_faves:50",
                "num_sources": 10,
                "mode": "auto"
            }
        },
        # Test 3: Just enable search (boolean)
        {
            "model": "grok-4-fast",
            "messages": [{"role": "user", "content": "Search live X for NVDA stock sentiment. Return JSON with post_count and sentiment_score."}],
            "max_tokens": 400,
            "temperature": 0.3,
            "search_parameters": {
                "enabled": True,
                "query": "NVDA stock min_faves:50"
            }
        }
    ]

    payload = payloads_to_test[0]  # Start with first test

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Testing payload:")
    print(json.dumps(payload, indent=2))
    print("\n")

    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    return response

def main():
    """Test sentiment analysis for a single popular stock"""

    print("\n" + "="*80)
    print("Testing Grok API with live search_parameters...")
    print("="*80 + "\n")

    result = test_raw_api_call()


if __name__ == "__main__":
    main()
