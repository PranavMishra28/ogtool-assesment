#!/usr/bin/env python3
"""
Configuration validation and edge case testing script.
This script validates the configuration and tests edge cases for all extractors.
"""

import json
import logging
import os
from pathlib import Path


def validate_config():
    """Validate the configuration file."""
    print("=== Validating Configuration ===")
    
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        # Check required top-level keys
        required_keys = ["sources", "extractors"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config key: {key}")
                return False
        
        # Check source configurations
        expected_sources = ["blog", "pdf", "substack", "github"]
        for source in expected_sources:
            if source not in config["sources"]:
                print(f"⚠️  Missing source config: {source}")
            else:
                print(f"✅ Source config found: {source}")
        
        # Check extractor configurations
        expected_extractors = ["generic_blog", "pdf", "github"]
        for extractor in expected_extractors:
            if extractor not in config["extractors"]:
                print(f"⚠️  Missing extractor config: {extractor}")
            else:
                print(f"✅ Extractor config found: {extractor}")
        
        print("✅ Configuration validation completed")
        return True
        
    except FileNotFoundError:
        print("❌ config.json file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating config: {e}")
        return False


def enhance_config():
    """Enhance config.json with additional robust settings."""
    print("\n=== Enhancing Configuration ===")
    
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        # Add missing configurations with robust defaults
        enhancements = {
            "timeout_settings": {
                "request_timeout": 30,
                "download_timeout": 300,
                "max_retries": 3
            },
            "content_filtering": {
                "min_content_length": 100,
                "max_content_length": 1000000,
                "remove_ads": True,
                "remove_navigation": True
            },
            "error_handling": {
                "continue_on_error": True,
                "log_errors": True,
                "max_errors_per_source": 5
            },
            "rate_limiting": {
                "requests_per_minute": 30,
                "delay_between_requests": [1, 3]
            }
        }
        
        # Add enhancements if not present
        for key, value in enhancements.items():
            if key not in config:
                config[key] = value
                print(f"✅ Added enhancement: {key}")
        
        # Enhance extractor-specific configs
        if "generic_blog" in config["extractors"]:
            blog_config = config["extractors"]["generic_blog"]
            if "content_selectors" not in blog_config:
                blog_config["content_selectors"] = [
                    "article", ".post", ".entry", ".blog-post", 
                    "main", ".content", ".post-content", ".entry-content"
                ]
            if "exclude_selectors" not in blog_config:
                blog_config["exclude_selectors"] = [
                    "nav", "header", "footer", ".sidebar", ".ads", 
                    ".comments", ".related-posts", ".social-share"
                ]
        
        if "pdf" in config["extractors"]:
            pdf_config = config["extractors"]["pdf"]
            if "text_extraction_method" not in pdf_config:
                pdf_config["text_extraction_method"] = "pypdf2"  # or "pdfplumber" for better extraction
            if "chapter_detection_enabled" not in pdf_config:
                pdf_config["chapter_detection_enabled"] = True
        
        if "github" in config["extractors"]:
            github_config = config["extractors"]["github"]
            if "include_types" not in github_config:
                github_config["include_types"] = ["readme", "docs", "wiki"]
            if "exclude_patterns" not in github_config:
                github_config["exclude_patterns"] = ["node_modules", ".git", "__pycache__"]
        
        # Save enhanced config
        with open("config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration enhanced successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error enhancing config: {e}")
        return False


def test_edge_cases():
    """Test various edge cases for robustness."""
    print("\n=== Testing Edge Cases ===")
    
    edge_cases = [
        # Invalid URLs
        ("http://", "Invalid URL format"),
        ("https://", "Invalid URL format"),
        ("ftp://example.com", "Unsupported protocol"),
        
        # Non-existent resources
        ("https://nonexistent-domain-xyz123.com", "Non-existent domain"),
        ("file_does_not_exist.pdf", "Non-existent file"),
        ("empty_file.md", "Empty file"),
        
        # Large content (would need actual testing)
        # ("very_large_file.pdf", "Large file handling"),
        
        # Special characters
        ("https://example.com/article-with-üñíçødé", "Unicode in URL"),
        
        # Rate limiting scenarios
        # Would need actual implementation to test
    ]
    
    try:
        from tech_content_extractor import TechContentExtractor
        extractor = TechContentExtractor()
        
        print("Testing edge cases (some failures are expected):")
        
        for source, description in edge_cases:
            print(f"Testing {description}: {source}")
            try:
                # Check if any extractor claims it can handle this
                handlers = []
                for ext in extractor.manager.extractors:
                    if ext.can_handle(source):
                        handlers.append(ext.__class__.__name__)
                
                if handlers:
                    print(f"   Handlers: {handlers}")
                    # Try extraction (expected to fail gracefully)
                    items = extractor.extract_from_source(source)
                    print(f"   Result: {len(items)} items extracted")
                else:
                    print(f"   No handlers (expected)")
                    
            except Exception as e:
                print(f"   Exception: {type(e).__name__}: {e}")
        
        print("✅ Edge case testing completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during edge case testing: {e}")
        return False


def create_test_files():
    """Create test files for comprehensive testing."""
    print("\n=== Creating Test Files ===")
    
    try:
        # Create empty markdown file for testing
        Path("empty_file.md").write_text("", encoding='utf-8')
        
        # Create markdown file with special characters
        special_content = """# Test Document with Special Characters

This document contains üñíçødé characters and other special symbols.

## Section with émojis 🚀

Content with **bold** and *italic* formatting.
"""
        Path("unicode_test.md").write_text(special_content, encoding='utf-8')
        
        print("✅ Test files created")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test files: {e}")
        return False


def cleanup_test_files():
    """Clean up test files."""
    test_files = ["empty_file.md", "unicode_test.md", "test_output.json"]
    
    for file in test_files:
        try:
            if os.path.exists(file):
                os.unlink(file)
        except Exception as e:
            print(f"Warning: Could not delete {file}: {e}")


def main():
    """Run configuration validation and edge case tests."""
    print("Starting configuration validation and edge case testing...")
    
    tests = [
        ("Configuration Validation", validate_config),
        ("Configuration Enhancement", enhance_config),
        ("Test File Creation", create_test_files),
        ("Edge Case Testing", test_edge_cases),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "="*50)
    print("CONFIGURATION & EDGE CASE TEST SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)}")
    
    # Cleanup
    cleanup_test_files()
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ All validation tests passed!' if success else '❌ Some tests failed.'}")
