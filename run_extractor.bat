@echo off
REM Tech Knowledge Extractor Batch Script

echo Technical Knowledge Extractor
echo ----------------------------

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is required but not installed. Please install Python and try again.
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    
    REM Activate virtual environment
    call venv\Scripts\activate
    
    REM Install required packages
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    REM Activate virtual environment
    call venv\Scripts\activate
)

echo.
echo Available options:
echo 1. Process all sources (interviewing.io, nilmamano.com, etc.)
echo 2. Process interviewing.io blog
echo 3. Process interviewing.io company guides
echo 4. Process interviewing.io interview guides
echo 5. Process nilmamano.com DS^&A blog posts
echo 6. Process PDF file
echo 7. Process Substack newsletter
echo 8. Process generic blog
echo 9. Run example script
echo 10. Exit

set /p option="Enter option number: "

if "%option%"=="1" (
    echo.
    set /p gdrive="Enter Google Drive link for PDF (leave empty to skip): "
    echo.
    echo Processing all sources...
    if "%gdrive%"=="" (
        python tech_knowledge_extractor.py --all
    ) else (
        python tech_knowledge_extractor.py --all --gdrive "%gdrive%"
    )
) else if "%option%"=="2" (
    echo.
    echo Processing interviewing.io blog...
    python tech_knowledge_extractor.py --source "https://interviewing.io/blog"
) else if "%option%"=="3" (
    echo.
    echo Processing interviewing.io company guides...
    python tech_knowledge_extractor.py --source "https://interviewing.io/topics#companies"
) else if "%option%"=="4" (
    echo.
    echo Processing interviewing.io interview guides...
    python tech_knowledge_extractor.py --source "https://interviewing.io/learn#interview-guides"
) else if "%option%"=="5" (
    echo.
    echo Processing nilmamano.com DS^&A blog posts...
    python tech_knowledge_extractor.py --source "https://nilmamano.com/blog/category/dsa"
) else if "%option%"=="6" (
    echo.
    set /p pdf_path="Enter path to PDF file: "
    echo.
    echo Processing PDF file...
    python tech_knowledge_extractor.py --source "%pdf_path%"
) else if "%option%"=="7" (
    echo.
    set /p substack="Enter Substack URL: "
    echo.
    echo Processing Substack newsletter...
    python tech_knowledge_extractor.py --source "%substack%"
) else if "%option%"=="8" (
    echo.
    set /p blog_url="Enter blog URL: "
    echo.
    echo Processing generic blog...
    python tech_knowledge_extractor.py --source "%blog_url%"
) else if "%option%"=="9" (
    echo.
    echo Running example script...
    python example_extractor.py
) else if "%option%"=="10" (
    echo.
    echo Exiting...
    goto end
) else (
    echo.
    echo Invalid option!
)

:end
REM Deactivate virtual environment
call venv\Scripts\deactivate
