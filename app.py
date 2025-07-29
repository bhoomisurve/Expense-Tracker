import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional

# Set page config
st.set_page_config(
    page_title='Personal Expense Tracker', 
    page_icon='💰',
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

def create_table():
    """Create the expenses table if it doesn't exist"""
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount REAL,
                note TEXT
            )
        ''')
    conn.commit()
    conn.close()

def add_expense(date: str, category: str, amount: float, note: str) -> bool:
    """Add a new expense to the database"""
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)',
                 (date, category, amount, note))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding expense: {e}")
        return False

def view_expenses() -> pd.DataFrame:
    """Retrieve all expenses from the database"""
    conn = sqlite3.connect('expenses.db')
    df = pd.read_sql_query('SELECT * FROM expenses ORDER BY date DESC', conn)
    conn.close()
    return df

def delete_expense(expense_id: int) -> bool:
    """Delete an expense by ID"""
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting expense: {e}")
        return False

def get_expense_stats(df: pd.DataFrame) -> dict:
    """Calculate expense statistics"""
    if df.empty:
        return {}
    
    total_expenses = df['amount'].sum()
    avg_expense = df['amount'].mean()
    max_expense = df['amount'].max()
    expense_count = len(df)
    
    return {
        'total': total_expenses,
        'average': avg_expense,
        'maximum': max_expense,
        'count': expense_count
    }

def main():
    # Initialize database
    create_table()
    
    # Main header
    st.markdown('<h1 class="main-header">💰 Personal Expense Tracker</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Add Expense", "View Expenses", "Analytics"])
    
    if page == "Add Expense":
        show_add_expense_page()
    elif page == "View Expenses":
        show_view_expenses_page()
    else:
        show_analytics_page()

def show_add_expense_page():
    """Display the add expense page"""
    st.header("➕ Add New Expense")
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("expense_form", clear_on_submit=True):
            # Date input with default as today
            expense_date = st.date_input(
                "📅 Date", 
                value=date.today(),
                max_value=date.today()
            )
            
            # Enhanced category selection
            categories = [
                "🍕 Food & Dining",
                "🚗 Transport",
                "🏠 Utilities",
                "🎬 Entertainment",
                "🛍️ Shopping",
                "🏥 Healthcare",
                "📚 Education",
                "💼 Business",
                "🎁 Gifts",
                "📱 Technology",
                "🏋️ Fitness",
                "✈️ Travel",
                "📋 Other"
            ]
            
            category = st.selectbox("📂 Category", categories)
            
            # Amount input with validation
            amount = st.number_input(
                "💵 Amount (₹)", 
                min_value=0.01, 
                format="%.2f",
                step=1.0
            )
            
            # Note input
            note = st.text_area(
                "📝 Note (Optional)", 
                placeholder="Add a description for this expense...",
                max_chars=200
            )
            
            # Submit button
            submitted = st.form_submit_button("💾 Add Expense", use_container_width=True)
            
            if submitted and amount > 0:
                # Clean category name (remove emoji)
                clean_category = category.split(' ', 1)[1] if ' ' in category else category
                
                if add_expense(expense_date.strftime("%Y-%m-%d"), clean_category, amount, note):
                    st.success("✅ Expense added successfully!")
                    st.balloons()
                else:
                    st.error("❌ Failed to add expense. Please try again.")
    
    with col2:
        st.info("💡 **Tips:**\n\n• Add expenses daily for better tracking\n• Use descriptive notes\n• Choose appropriate categories\n• Keep receipts for reference")

def show_view_expenses_page():
    """Display the view expenses page"""
    st.header("📊 Expense History")
    
    df = view_expenses()
    
    if df.empty:
        st.info("📝 No expenses recorded yet. Add some expenses to see your data here!")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filter Options")
    
    # Date range filter
    df['date'] = pd.to_datetime(df['date'])
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    date_range = st.sidebar.date_input(
        "📅 Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Category filter
    categories = df['category'].unique().tolist()
    selected_categories = st.sidebar.multiselect(
        "📂 Filter by Categories",
        categories,
        default=categories
    )
    
    # Amount range filter
    min_amount = float(df['amount'].min())
    max_amount = float(df['amount'].max())
    amount_range = st.sidebar.slider(
        "💵 Amount Range (₹)",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount),
        step=1.0
    )
    
    # Apply filters
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[
            (df['date'].dt.date >= start_date) &
            (df['date'].dt.date <= end_date) &
            (df['category'].isin(selected_categories)) &
            (df['amount'] >= amount_range[0]) &
            (df['amount'] <= amount_range[1])
        ]
    else:
        df_filtered = df[
            (df['category'].isin(selected_categories)) &
            (df['amount'] >= amount_range[0]) &
            (df['amount'] <= amount_range[1])
        ]
    
    # Show statistics
    stats = get_expense_stats(df_filtered)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Spent", f"₹{stats['total']:,.2f}")
        with col2:
            st.metric("📊 Average Expense", f"₹{stats['average']:,.2f}")
        with col3:
            st.metric("📈 Highest Expense", f"₹{stats['maximum']:,.2f}")
        with col4:
            st.metric("📋 Total Entries", stats['count'])
    
    st.markdown("---")
    
    # Display filtered data
    if df_filtered.empty:
        st.warning("🔍 No expenses found with the selected filters.")
    else:
        # Format the dataframe for better display
        display_df = df_filtered.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        display_df = display_df.rename(columns={
            'id': 'ID',
            'date': 'Date',
            'category': 'Category',
            'amount': 'Amount',
            'note': 'Note'
        })
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export option
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_analytics_page():
    """Display the analytics page"""
    st.header("📈 Expense Analytics")
    
    df = view_expenses()
    
    if df.empty:
        st.info("📝 No data available for analysis. Add some expenses first!")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Time period selector
    period = st.selectbox(
        "📅 Select Analysis Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
    )
    
    # Filter by period
    today = datetime.now().date()
    if period == "Last 7 Days":
        start_date = today - timedelta(days=7)
    elif period == "Last 30 Days":
        start_date = today - timedelta(days=30)
    elif period == "Last 90 Days":
        start_date = today - timedelta(days=90)
    else:
        start_date = df['date'].min().date()
    
    df_period = df[df['date'].dt.date >= start_date]
    
    if df_period.empty:
        st.warning(f"🔍 No expenses found for {period.lower()}.")
        return
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Expense Distribution by Category")
        category_data = df_period.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        if not category_data.empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.Set3(range(len(category_data)))
            wedges, texts, autotexts = ax.pie(
                category_data.values, 
                labels=category_data.index, 
                autopct='%1.1f%%',
                startangle=90,
                colors=colors
            )
            ax.set_title(f"Expenses by Category - {period}", fontsize=14, fontweight='bold')
            
            # Make percentage text more readable
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            st.pyplot(fig)
            plt.clf()
    
    with col2:
        st.subheader("📊 Top 5 Categories")
        top_categories = category_data.head(5)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(top_categories)), top_categories.values, color='skyblue')
        ax.set_xlabel('Categories')
        ax.set_ylabel('Amount (₹)')
        ax.set_title(f'Top 5 Expense Categories - {period}')
        ax.set_xticks(range(len(top_categories)))
        ax.set_xticklabels(top_categories.index, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, value in zip(bars, top_categories.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01,
                   f'₹{value:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    
    # Daily spending trend
    st.subheader("📈 Daily Spending Trend")
    daily_expenses = df_period.groupby(df_period['date'].dt.date)['amount'].sum()
    
    if len(daily_expenses) > 1:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(daily_expenses.index, daily_expenses.values, marker='o', linewidth=2, markersize=6)
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount (₹)')
        ax.set_title(f'Daily Spending Trend - {period}')
        ax.grid(True, alpha=0.3)
        
        # Format y-axis to show currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    
    # Summary statistics
    st.subheader("📋 Summary Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Spent", f"₹{df_period['amount'].sum():,.2f}")
        st.metric("📊 Average Daily", f"₹{df_period['amount'].sum() / len(df_period['date'].dt.date.unique()):,.2f}")
    
    with col2:
        st.metric("📈 Highest Single Expense", f"₹{df_period['amount'].max():,.2f}")
        st.metric("📉 Lowest Single Expense", f"₹{df_period['amount'].min():,.2f}")
    
    with col3:
        st.metric("📝 Total Transactions", len(df_period))
        st.metric("🏷️ Categories Used", df_period['category'].nunique())

if __name__ == "__main__":
    main()