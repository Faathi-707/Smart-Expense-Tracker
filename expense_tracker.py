import streamlit as st #Builds UI in the browser. Forms, buttons, messages
import pandas as pd #Loads and saves tables
import matplotlib.pyplot as plt #data visualation, charts 
import os #Talks to OS Reads environment variables.
from google import genai #Google’s Gemini client for AI calls.

# =========================================================================================================
# Config
# =========================================================================================================
CSV_PATH = "expense_data_1.csv"
ALLOWED_CATEGORIES = {"Food", "Transportation", "Entertainment", "Utilities", "Shopping", "Others"}

# Set matplotlib to use a font that supports English characters
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

#Gemini client initialization
def initialize_gemini_client():  
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:  ##debugging
        st.sidebar.error(" GEMINI_API_KEY environment variable not set")
        st.sidebar.markdown("""           
        **To fix this:**
        1. Get API key from [Google AI Studio](https://aistudio.google.com/)
        2. Set environment variable:
        ```bash
        export GEMINI_API_KEY='your-actual-key-here'
        ```
        3. Restart Streamlit
        """)
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        # Try available models in priority order
        working_models = [
            "gemini-1.5-flash",    # Most widely available
            "gemini-1.0-pro",      # Fallback option
            "gemini-1.5-pro",      # Less common
            "gemini-2.0-flash"     # Newest but limited availability
        ]
        
        working_model = None
        for model in working_models:
            try:
                test_response = client.models.generate_content(
                    model=model,
                    contents="Say 'OK'"
                )
                working_model = model
                st.sidebar.success(f"Connected using: {model}")
                break
            except:
                continue
        
        if working_model:
            return {"client": client, "model": working_model}
        else:
            st.sidebar.error(" No working models found")
            return None
            
    except Exception as e:
        st.sidebar.error(f" Failed to initialize Gemini: {str(e)}")
        return None

# Initialize client
client_info = initialize_gemini_client()

# =========================================================================================================
# Data helpers
# =========================================================================================================
def load_data():
    """Load data from CSV with consistent column names"""
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            # Clean column names
            df.columns = df.columns.str.strip()
            # Ensure consistent column names
            if 'Note' in df.columns and 'Description' not in df.columns:
                df = df.rename(columns={'Note': 'Description'})
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])
    else:
        return pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])

def save_data(df: pd.DataFrame, csv_path: str) -> None:  #save_data(df, path)Writes the table back to CSV without the index column.Keeps the file clean for Excel and future reads.
    try:
        df.to_csv(csv_path, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def add_expense_row(df: pd.DataFrame, date, description: str, amount: float, category: str) -> pd.DataFrame: #Builds a single new row as a dict. Ensures types are clean. Amount is float. Category uses title case. Appends to the existing table.
    row = {
        "Date": str(date),
        "Description": description.strip(),
        "Amount": float(amount),
        "Category": category.strip().title(),
    }
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)

# =========================================================================================================
# Category prediction
# =========================================================================================================
KEYWORD_TO_CAT = {
    "cake": "Food", "bakery": "Food", "dessert": "Food", "bike": "Transportation",
    "bicycle": "Transportation", "cycle": "Transportation", "shawarma": "Food", 
    "burger": "Food", "pizza": "Food", "lunch": "Food", "dinner": "Food", 
    "breakfast": "Food", "groceries": "Food", "coffee": "Food", "tea": "Food", 
    "restaurant": "Food", "cafe": "Food", "food": "Food", "meal": "Food",
    "taxi": "Transportation", "bus": "Transportation", "fuel": "Transportation", 
    "petrol": "Transportation", "parking": "Transportation", "uber": "Transportation",
    "lyft": "Transportation", "train": "Transportation", "metro": "Transportation",
    "movie": "Entertainment", "cinema": "Entertainment", "game": "Entertainment", 
    "netflix": "Entertainment", "spotify": "Entertainment", "concert": "Entertainment",
    "electricity": "Utilities", "water": "Utilities", "wifi": "Utilities", 
    "internet": "Utilities", "phone": "Utilities", "gas": "Utilities", 
    "clothes": "Shopping", "shoes": "Shopping", "amazon": "Shopping", 
    "mall": "Shopping", "makeup": "Shopping",
}

def rule_based_category(text: str) -> str:       #Tries Exact match. Word-by-word match. Substring match. Fallback is “Others”.
    if not text or not isinstance(text, str):
        return "Others"
    
    text_lower = text.lower().strip()
    
    # Check for exact matches first
    if text_lower in KEYWORD_TO_CAT:
        return KEYWORD_TO_CAT[text_lower]
    
    # Check individual words
    words = text_lower.split()
    for word in words:
        if word in KEYWORD_TO_CAT:
            return KEYWORD_TO_CAT[word]
    
    # Substring match as fallback which means it extracts a specific part of a larger string
    for kw, cat in KEYWORD_TO_CAT.items():
        if kw in text_lower:
            return cat
    
    return "Others"

def predict_category(description: str) -> str:
    """Try rules first. If you get a category, stop. If rules return “Others” and Gemini is available,
      send a short instruction prompt asking for a single category. Read resp.text, normalize capitalisation, 
      and validate against ALLOWED_CATEGORIES."""
    
    # Always try rules first (fast and free)
    rule_cat = rule_based_category(description)
    if rule_cat != "Others":
        return rule_cat
    
    # Only use Gemini if rules didn't work AND client is available
    if client_info is None:
        return "Others"

    prompt = f"""
Categorize this expense: "{description}"
Choose exactly one: Food, Transportation, Entertainment, Utilities, Shopping, Others.
Return only the category word.
If unsure, return "Others".
"""
    try:
        # USE THE WORKING MODEL FROM INITIALIZATION
        resp = client_info["client"].models.generate_content(
            model=client_info["model"],  # Use the proven working model
            contents=prompt
        )
        raw = resp.text.strip()
        gemini_cat = raw.splitlines()[0].strip().title()
        st.sidebar.info(f" Gemini categorized '{description}' as: {gemini_cat}")
        return gemini_cat if gemini_cat in ALLOWED_CATEGORIES else "Others"
        
    except Exception as e:
        st.sidebar.error(f"Gemini API call failed: {e}")
        return "Others"
        
# =========================================================================================================
# Streamlit app flow 
# =========================================================================================================
data = load_data()

st.title("Smart Expense Tracker") # Title

# API status
if client_info: #sidebar show status
    st.sidebar.success(" Gemini API: Connected")
else:
    st.sidebar.warning(" Gemini API: Not available - using rules only") 

with st.form("expense_form"): #form to add an expense
    date = st.date_input("Date")
    description = st.text_input("Description", placeholder="e.g., bike, cake, movie...")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f", step=1.0)

    # Auto-prediction
    predicted_category = ""
    if description:
        predicted_category = predict_category(description)
        if predicted_category:
            st.info(f" Auto-predicted: **{predicted_category}**")

    category = st.text_input(
        "Category", 
        value=predicted_category,
        help="Allowed categories: Food, Transportation, Entertainment, Utilities, Shopping, Others"
    )

    submitted = st.form_submit_button("Add Expense") # On submit, validate inputs, append the row, save CSV, then rerun UI to refresh.

    if submitted:
        if not description.strip():
            st.error("Please enter a description")
        elif amount <= 0:
            st.error("Amount must be greater than 0")
        else:
            final_cat = category.strip().title() if category.strip().title() in ALLOWED_CATEGORIES else "Others"
            data = add_expense_row(data, date, description, amount, final_cat)
            save_data(data, CSV_PATH)
            st.success(f" Added: {description} - ${amount:.2f} ({final_cat})")
            st.rerun()

# =========================================================================================================
# Bars and charts
# =========================================================================================================
# Display data and charts
st.subheader("All Expenses")
if not data.empty:
    st.dataframe(data)
else:
    st.info("No expenses recorded yet.")

if not data.empty and 'Category' in data.columns and 'Amount' in data.columns:
    # Clean the data before plotting
    plot_data = data.copy()
    plot_data['Category'] = plot_data['Category'].fillna('Unknown')
    plot_data['Amount'] = pd.to_numeric(plot_data['Amount'], errors='coerce').fillna(0)
    
    category_totals = plot_data.groupby("Category")["Amount"].sum()
    
    # Only plot if we have valid data
    if not category_totals.empty and category_totals.sum() > 0:
        st.subheader("Expense Breakdown by Category")
        
        # Bar Chart with better styling
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = category_totals.sort_values(ascending=False).plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
        ax.set_ylabel("Amount ($)", fontsize=12)
        ax.set_xlabel("Category", fontsize=12)
        ax.set_title("Expenses by Category", fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

        # Pie Chart with better styling
        st.subheader("Category Distribution")
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        
        # Filter out very small slices to avoid clutter
        threshold = category_totals.sum() * 0.02  # 2% threshold
        main_categories = category_totals[category_totals >= threshold]
        other_sum = category_totals[category_totals < threshold].sum()
        
        if other_sum > 0:
            main_categories['Others'] = other_sum
        
        # Create pie chart
        colors = plt.cm.Set3(range(len(main_categories)))
        wedges, texts, autotexts = ax2.pie(
            main_categories.values, 
            labels=main_categories.index, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Improve text appearance
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        for text in texts:
            text.set_fontsize(11)
        
        ax2.set_title("Expense Distribution", fontsize=14, fontweight='bold')
        st.pyplot(fig2)
        
        # Also show a simple table as backup
        st.subheader("Category Summary")
        summary_df = category_totals.sort_values(ascending=False).reset_index()
        summary_df.columns = ['Category', 'Total Amount']
        summary_df['Percentage'] = (summary_df['Total Amount'] / summary_df['Total Amount'].sum() * 100).round(1)
        st.dataframe(summary_df)
        
    else:
        st.warning("No valid expense data to display in charts.")

# =========================================================================================================
# Debug info
# =========================================================================================================
with st.expander("Debug Info"):
    st.write("API Key exists:", bool(os.getenv("GEMINI_API_KEY")))
    st.write("Client initialized:", client_info is not None)
    st.write("Data shape:", data.shape)