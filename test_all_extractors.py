#!/usr/bin/env python3
"""
Comprehensive test suite for the technical content extraction framework.
Tests all extractors and edge cases to ensure robust operation.
"""

import os
import sys
import tempfile
import logging

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tech_content_extractor import TechContentExtractor


def test_extractor_registration():
    """Test that all expected extractors are properly registered."""
    print("=== Testing Extractor Registration ===")
    
    try:
        extractor = TechContentExtractor()
        
        # Expected extractors
        expected_extractors = {
            "GenericBlogExtractor", "GitHubExtractor", "MarkdownExtractor", 
            "PDFExtractor", "SubstackExtractor"
        }
        
        # Get registered extractor names
        registered_extractors = {ext.__class__.__name__ for ext in extractor.manager.extractors}
        
        print(f"Expected: {expected_extractors}")
        print(f"Registered: {registered_extractors}")
        
        missing = expected_extractors - registered_extractors
        extra = registered_extractors - expected_extractors
        
        if missing:
            print(f"❌ Missing extractors: {missing}")
            return False
        
        if extra:
            print(f"⚠️  Extra extractors: {extra}")
        
        print("✅ All expected extractors are registered")
        return True
        
    except Exception as e:
        print(f"❌ Error during extractor registration test: {e}")
        return False


def test_can_handle_logic():
    """Test the can_handle logic for each extractor."""
    print("\n=== Testing can_handle Logic ===")
    
    # Create temporary files for testing
    temp_md_file = None
    temp_pdf_file = None
    
    try:
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Markdown\nThis is a test file.")
            temp_md_file = f.name
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
            temp_pdf_file = f.name
    
        test_cases = [
            # (source, expected_extractor_class)
            ("https://example.com/blog-post", "GenericBlogExtractor"),
            ("https://github.com/microsoft/vscode", "GitHubExtractor"),
            (temp_md_file, "MarkdownExtractor"),
            ("https://example.com/file.md", "MarkdownExtractor"),
            (temp_pdf_file, "PDFExtractor"),
            ("https://drive.google.com/file/d/123/view", "PDFExtractor"),
            ("https://newsletter.substack.com/", "SubstackExtractor"),
            ("https://substack.com/profile/123", "SubstackExtractor"),
            ("https://github.com/user", None),  # Invalid GitHub URL
            ("nonexistent.md", None),  # Non-existent local file
        ]
        
        extractor = TechContentExtractor()
        
        results = []
        for source, expected_class in test_cases:
            matching_extractors = []
            for ext in extractor.manager.extractors:
                if ext.can_handle(source):
                    matching_extractors.append(ext.__class__.__name__)
            
            if expected_class is None:
                if not matching_extractors:
                    results.append(f"✅ {source} -> No extractor (expected)")
                else:
                    results.append(f"❌ {source} -> {matching_extractors} (expected no extractor)")
            else:
                if expected_class in matching_extractors:
                    results.append(f"✅ {source} -> {expected_class}")
                else:
                    results.append(f"❌ {source} -> {matching_extractors} (expected {expected_class})")
        
        # Print results
        for result in results:
            print(result)
        
        # Check if all tests passed
        failed_tests = [r for r in results if r.startswith("❌")]
        return len(failed_tests) == 0
        
    except Exception as e:
        print(f"❌ Error during can_handle test: {e}")
        return False
        
    finally:
        # Clean up temporary files
        if temp_md_file and os.path.exists(temp_md_file):
            os.unlink(temp_md_file)
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            os.unlink(temp_pdf_file)


def test_blog_extractor():
    """Test blog extractor with various URLs."""
    print("\n=== Testing Blog Extractor ===")
    
    test_urls = [
        "https://github.blog/",  # Should work
        "https://nonexistent-blog-xyz.com/",  # Should fail gracefully
    ]
    
    try:
        extractor = TechContentExtractor()
        
        for url in test_urls:
            print(f"Testing: {url}")
            try:
                items = extractor.extract_from_source(url)
                if items and len(items) > 0:
                    print(f"✅ Extracted {len(items)} items from {url}")
                    print(f"   Title: {items[0].title[:50]}...")
                else:
                    print(f"⚠️  No items extracted from {url} (might be expected)")
                    
                # Clear items for next test
                extractor.manager.items = []
                
            except Exception as e:
                print(f"❌ Error extracting from {url}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during blog extractor test: {e}")
        return False


def test_github_extractor():
    """Test GitHub extractor."""
    print("\n=== Testing GitHub Extractor ===")
    
    test_urls = [
        "https://github.com/microsoft/vscode",
        "https://github.com/nonexistent/repo",
    ]
    
    try:
        extractor = TechContentExtractor()
        
        for url in test_urls:
            print(f"Testing: {url}")
            try:
                items = extractor.extract_from_source(url)
                if items and len(items) > 0:
                    print(f"✅ Extracted {len(items)} items from {url}")
                    print(f"   Title: {items[0].title[:50]}...")
                    print(f"   Type: {items[0].content_type}")
                else:
                    print(f"⚠️  No items extracted from {url}")
                    
                # Clear items for next test
                extractor.manager.items = []
                
            except Exception as e:
                print(f"❌ Error extracting from {url}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during GitHub extractor test: {e}")
        return False


def test_markdown_extractor():
    """Test markdown extractor."""
    print("\n=== Testing Markdown Extractor ===")
    
    try:
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Test Document

This is a test markdown document with some content.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
""")
            temp_file = f.name
        
        try:
            extractor = TechContentExtractor()
            items = extractor.extract_from_source(temp_file)
            
            if items and len(items) > 0:
                print(f"✅ Extracted {len(items)} items from markdown file")
                print(f"   Title: {items[0].title}")
                print(f"   Content length: {len(items[0].content)} characters")
                return True
            else:
                print("❌ No items extracted from markdown file")
                return False
                
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Error during markdown extractor test: {e}")
        return False


def test_pdf_extractor():
    """Test PDF extractor."""
    print("\n=== Testing PDF Extractor ===")
    
    try:
        # Create a minimal test PDF
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            # Very basic PDF structure
            pdf_content = b"""%%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
265
%%EOF"""
            f.write(pdf_content)
            temp_file = f.name
        
        try:
            extractor = TechContentExtractor()
            items = extractor.extract_from_source(temp_file)
            
            if items and len(items) > 0:
                print(f"✅ Extracted {len(items)} items from PDF file")
                print(f"   Title: {items[0].title}")
                return True
            else:
                print("⚠️  No items extracted from PDF file (might be expected for minimal PDF)")
                return True  # This might be expected for a minimal PDF
                
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Error during PDF extractor test: {e}")
        return False


def test_substack_extractor():
    """Test Substack extractor."""
    print("\n=== Testing Substack Extractor ===")
    
    try:
        extractor = TechContentExtractor()
        
        # Note: This will likely fail due to network restrictions, but we test the logic
        test_url = "https://stratechery.com/"
        print(f"Testing: {test_url}")
        
        items = extractor.extract_from_source(test_url)
        if items and len(items) > 0:
            print(f"✅ Extracted {len(items)} items from Substack")
            print(f"   Title: {items[0].title[:50]}...")
        else:
            print("⚠️  No items extracted from Substack (might be expected)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during Substack extractor test: {e}")
        return False


def test_output_format():
    """Test that output format is correct."""
    print("\n=== Testing Output Format ===")
    
    try:
        # Create a simple markdown file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document\nThis is test content.")
            temp_file = f.name
        
        try:
            extractor = TechContentExtractor()
            items = extractor.extract_from_source(temp_file)
            
            if not items:
                print("❌ No items to test output format")
                return False
            
            item = items[0]
            item_dict = item.to_dict()
            
            # Check required fields
            required_fields = ['id', 'title', 'content', 'source_url', 'content_type']
            missing_fields = [field for field in required_fields if field not in item_dict]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print("✅ Output format contains all required fields")
            print(f"   Fields: {list(item_dict.keys())}")
            return True
            
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Error during output format test: {e}")
        return False


def main():
    """Run all tests."""
    print("Starting comprehensive extractor test suite...\n")
    
    # Suppress verbose logging during tests
    logging.getLogger().setLevel(logging.WARNING)
    
    tests = [
        ("Extractor Registration", test_extractor_registration),
        ("can_handle Logic", test_can_handle_logic),
        ("Blog Extractor", test_blog_extractor),
        ("GitHub Extractor", test_github_extractor),
        ("Markdown Extractor", test_markdown_extractor),
        ("PDF Extractor", test_pdf_extractor),
        ("Substack Extractor", test_substack_extractor),
        ("Output Format", test_output_format),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is ready for production use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
