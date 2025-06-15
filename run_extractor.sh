#!/bin/bash
# Tech Knowledge Extractor Shell Script

echo "Technical Knowledge Extractor"
echo "----------------------------"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install required packages
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

echo ""
echo "Available options:"
echo "1. Process all sources (interviewing.io, nilmamano.com, etc.)"
echo "2. Process interviewing.io blog"
echo "3. Process interviewing.io company guides"
echo "4. Process interviewing.io interview guides"
echo "5. Process nilmamano.com DS&A blog posts"
echo "6. Process PDF file"
echo "7. Process Substack newsletter"
echo "8. Process generic blog"
echo "9. Run example script"
echo "10. Exit"

read -p "Enter option number: " option

if [ "$option" = "1" ]; then
    echo ""
    read -p "Enter Google Drive link for PDF (leave empty to skip): " gdrive
    echo ""
    echo "Processing all sources..."
    if [ -z "$gdrive" ]; then
        python3 tech_knowledge_extractor.py --all
    else
        python3 tech_knowledge_extractor.py --all --gdrive "$gdrive"
    fi
elif [ "$option" = "2" ]; then
    echo ""
    echo "Processing interviewing.io blog..."
    python3 tech_knowledge_extractor.py --source "https://interviewing.io/blog"
elif [ "$option" = "3" ]; then
    echo ""
    echo "Processing interviewing.io company guides..."
    python3 tech_knowledge_extractor.py --source "https://interviewing.io/topics#companies"
elif [ "$option" = "4" ]; then
    echo ""
    echo "Processing interviewing.io interview guides..."
    python3 tech_knowledge_extractor.py --source "https://interviewing.io/learn#interview-guides"
elif [ "$option" = "5" ]; then
    echo ""
    echo "Processing nilmamano.com DS&A blog posts..."
    python3 tech_knowledge_extractor.py --source "https://nilmamano.com/blog/category/dsa"
elif [ "$option" = "6" ]; then
    echo ""
    read -p "Enter path to PDF file: " pdf_path
    echo ""
    echo "Processing PDF file..."
    python3 tech_knowledge_extractor.py --source "$pdf_path"
elif [ "$option" = "7" ]; then
    echo ""
    read -p "Enter Substack URL: " substack
    echo ""
    echo "Processing Substack newsletter..."
    python3 tech_knowledge_extractor.py --source "$substack"
elif [ "$option" = "8" ]; then
    echo ""
    read -p "Enter blog URL: " blog_url
    echo ""
    echo "Processing generic blog..."
    python3 tech_knowledge_extractor.py --source "$blog_url"
elif [ "$option" = "9" ]; then
    echo ""
    echo "Running example script..."
    python3 example_extractor.py
elif [ "$option" = "10" ]; then
    echo ""
    echo "Exiting..."
    exit 0
else
    echo ""
    echo "Invalid option!"
fi

# Deactivate virtual environment
deactivate
