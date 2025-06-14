#!/usr/bin/env python3
"""
Example script to demonstrate the usage of ContentIngestionTool.
"""

import json
from content_ingestion import ContentIngestionTool

def example_blog_processing():
    """Process a sample blog post."""
    tool = ContentIngestionTool(team_id="aline123")
    tool.process_source("https://blog.interviewing.io/how-to-become-a-data-scientist/")
    
    output = tool.generate_output()
    print(f"Processed {len(output['items'])} blog items.")
    
    # Save the output to a file
    with open('blog_example_output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("Blog processing complete. Output saved to blog_example_output.json")

def example_substack_processing():
    """Process a sample Substack newsletter."""
    tool = ContentIngestionTool(team_id="aline123")
    tool.process_source("https://lethain.com/")  # Will Larson's Substack
    
    output = tool.generate_output()
    print(f"Processed {len(output['items'])} Substack items.")
    
    # Save the output to a file
    with open('substack_example_output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("Substack processing complete. Output saved to substack_example_output.json")

if __name__ == "__main__":
    print("Running content ingestion examples...")
    
    # Uncomment the example you want to run
    example_blog_processing()
    # example_substack_processing()
    
    print("Examples complete!")
