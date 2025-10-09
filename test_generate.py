#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.llm import extract_structured_notes
import json

def test_generate_note():
    """Test the generate note functionality"""
    try:
        # Test generating note from various inputs
        test_cases = [
            "Meeting with John tomorrow 3pm discuss project",
            "Badminton tmr 5pm @polyu",
            "Doctor appointment Monday 10am annual checkup",
            "Buy groceries milk eggs bread vegetables",
            "Call mom birthday party planning next weekend"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i} ---")
            print(f"Input: {text}")
            
            # Test in English
            result = extract_structured_notes(text, "English")
            print(f"Generated (English): {result}")
            
            try:
                parsed = json.loads(result)
                print(f"Title: {parsed.get('Title', 'N/A')}")
                print(f"Notes: {parsed.get('Notes', 'N/A')}")
                print(f"Tags: {parsed.get('Tags', [])}")
            except json.JSONDecodeError:
                print("Failed to parse JSON")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_generate_note()