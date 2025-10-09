#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.llm import translate

def test_translation():
    """Test the translation function"""
    try:
        # Test translating English to Chinese
        text = "Hello, this is a test note for translation."
        target_language = "Chinese"
        
        print(f"Original text: {text}")
        print(f"Target language: {target_language}")
        print("Translating...")
        
        translated_text = translate(text, target_language)
        
        print(f"Translated text: {translated_text}")
        print("Translation successful!")
        
    except Exception as e:
        print(f"Translation failed: {str(e)}")

if __name__ == "__main__":
    test_translation()