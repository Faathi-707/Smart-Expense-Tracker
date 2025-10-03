# Smart Expense Tracker
-------------------------------
Track expenses in your browser with Streamlit. Store data in a CSV. Auto-categorize with rules first, then Google Gemini if available.

### Features
-------------------------------
- Runs locally in your browser using Streamlit
- CSV storage for simple persistence
- Rule based keyword matching and Gemini model call if rules return “Others”
- Bar and pie charts
- Debug panel for quick diagnosis

## Quickstart
    # 1) Python 3.10+ recommended
        python -V

    # 2) Create and activate a virtualenv
        python -m venv .venv
    # macOS/Linux
    source .venv/bin/activate
    # Windows PowerShell
    .venv\Scripts\Activate.ps1

    # 3) Install dependencies
    pip install -U streamlit pandas matplotlib google-genai python-dotenv

    # 4) Set Gemini API key for AI categorization
    # macOS/Linux
    export GEMINI_API_KEY='your-key'

    # Windows PowerShell
    $env:GEMINI_API_KEY='your-key'

    # 5) Run the app
    streamlit run expense_tracker.py

## Dependencies
- streamlit (Builds UI in the browser. Forms, buttons, messages)
- pandas (Loads and saves tables)
- matplotlib (data visualation, charts)
- google-genai # Gemini SDK
- OS (Talks to operating system and Reads environment variables)
- python-dotenv # optional, if you prefer a .env file

## CSV schema
- The app expects these columns:
- Date string or ISO date
- Description text
- Amount number
- Category one of:
    - Food
    - Transportation
    - Entertainment
    - Utilities
    - Shopping
    - Others

## How categorization works
1. Rule pass
    - Exact match
    - Word by word
    - Substring match against a keyword map
2. AI pass
    - Only if rules return “Others” and GEMINI_API_KEY is set
    - Sends only the Description string to Gemini
    - Validates the response against allowed categories

## Acknowledgements

This app started from learning “How to make a Smart Expense Tracker with Python and LLMs” by Happiness Omale on freeCodeCamp.
Link: https://www.freecodecamp.org/news/build-smart-expense-tracker-with-python-and-llms/

The dataset used for this project is from Kaggle: My Expenses Data by Tharun Prabu.
Link: https://www.kaggle.com/datasets/tharunprabu/my-expenses-data 