#!/usr/bin/env python3
"""
Example script demonstrating how to use the TechKnowledgeExtractor.
"""

from tech_knowledge_extractor import TechKnowledgeExtractor

def example_interviewing_io_blog():
    """Process interviewing.io blog as an example."""
    extractor = TechKnowledgeExtractor()
    extractor.process_interviewing_io_blog()
    extractor.save_output("interviewing_io_blog_output.json")
    print("Example completed! Check interviewing_io_blog_output.json")

def example_interview_guides():
    """Process interviewing.io interview guides as an example."""
    extractor = TechKnowledgeExtractor()
    extractor.process_interviewing_io_interview_guides()
    extractor.save_output("interview_guides_output.json")
    print("Example completed! Check interview_guides_output.json")

def example_quill_blog():
    """Process quill.co blog as an example to test robustness."""
    extractor = TechKnowledgeExtractor()
    extractor.process_generic_blog("https://quill.co/blog")
    extractor.save_output("quill_blog_output.json")
    print("Example completed! Check quill_blog_output.json")

def example_substack():
    """Process a Substack newsletter as an example."""
    extractor = TechKnowledgeExtractor()
    extractor.process_substack("https://shreycation.substack.com")
    extractor.save_output("substack_output.json")
    print("Example completed! Check substack_output.json")

if __name__ == "__main__":
    print("Running example: interviewing.io blog")
    example_interviewing_io_blog()
    
    print("\nRunning example: interviewing.io interview guides")
    example_interview_guides()
    
    print("\nRunning example: quill.co blog (testing robustness)")
    example_quill_blog()
    
    print("\nRunning example: Substack newsletter")
    example_substack()
