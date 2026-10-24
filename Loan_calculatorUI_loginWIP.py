# Load Packages
import streamlit as st
import pandas as pd
import numpy as np
from functions import generate_amortization_schedule
import plotly
import plotly.express as px
import sqlite3

# Create a login page
# --- DATABASE SETUP ---
DB_NAME = "users.db"
DB_ENQUIRY = "enquiry.db" 


def init_db():
    """Creates the user table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            mobile TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()



def init_enquiry_db():
    """Creates the enquiry table if it doesn't exist."""
    conn = sqlite3.connect(DB_ENQUIRY)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT ,
            enquiry_at TEXT NOT NULL ,
            principal NUMERIC NOT NULL,
            interest_rate NUMERIC NOT NULL,
            tenure_in_months INTEGER NOT NULL,
            PRIMARY KEY (user_id, enquiry_at)  
            )
    """
    )
    conn.commit()
    conn.close()


def add_user(user_id, mobile):
    """Stores a new user in the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (user_id, mobile) VALUES (?, ?)",
            (user_id, mobile),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # User ID already exists


def verify_user(user_id, mobile):
    """Checks if the User ID and Mobile Number match the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE user_id = ? AND mobile = ?",
        (user_id, mobile),
    )
    result = c.fetchone()
    conn.close()
    return result is not None


# Initialize DB on startup
init_db()
init_enquiry_db()

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""

# --- APP ROUTING ---
# 1. Show Main Dashboard if logged in
if st.session_state.logged_in:

    st.title(f"👋 Welcome to the Dashboard, {st.session_state.user_id}!")

    # Input UI Parameters
    input_data = pd.read_excel('Input.xlsx',sheet_name='AvgIntRate',header=0)
    Loan_Type = input_data['Loan Type'].tolist()


    # Set page configuration
    st.set_page_config(page_title="Loan EMI Calculator", page_icon="💰", layout="centered")

    # Main Title
    st.title("💰 Interactive Loan EMI Calculator")
    st.markdown("Adjust the parameters below to see your monthly repayment schedule instantly.")

    # Create 3 columns for Inputs and Outputs
    col0, col1, col2 = st.columns([1,1.2, 1.2])
    if "col2_active" not in st.session_state:
        st.session_state.col2_active = False
    


    with col0:        
        st.subheader("Select Loan Type")
        selected_loan_type = st.selectbox("Choose a loan type:", Loan_Type)
        st.session_state.col2_active = False

    with col1:
                
        st.subheader("Loan Parameters for "+ selected_loan_type)
        
        # Input 1: Principal Amount
        principal = st.number_input(
            "Loan Amount (₹)", 
            min_value=10000, 
            max_value=100000000, 
            value=1000000, 
            # step=50000,
            step=1000,
            format="%d"
        )
        st.session_state.col2_active = False

        int_slid_val = input_data.loc[input_data['Loan Type'] == selected_loan_type, 'AvgIntRate'].values[0]
        int_slid_val_min = input_data.loc[input_data['Loan Type'] == selected_loan_type, 'Range Min'].values[0]
        int_slid_val_max = input_data.loc[input_data['Loan Type'] == selected_loan_type, 'Range Max'].values[0]

    
        # Input 2: Interest Rate (Annual)
        annual_rate = st.slider(
            "Annual Interest Rate (%)", 
            min_value=int_slid_val_min*100, 
            max_value=int_slid_val_max*100, 
            value=int_slid_val*100,
            step=.01
        )/100
        st.session_state.col2_active = False

        # Input 3: Tenure Type Selection
        tenure_type = st.radio("Tenure Type", ["Years", "Months"], horizontal=True)
        st.session_state.col2_active = False

        if tenure_type == "Years":
            tenure_years = st.slider("Tenure (Years)", min_value=1, max_value=30, value=5)
            n_months = tenure_years * 12
        else:
            n_months = st.slider("Tenure (Months)", min_value=1, max_value=360, value=60)

        if st.button("Calculate EMI", use_container_width=True):
            st.session_state.col2_active = True
            current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = sqlite3.connect(DB_ENQUIRY)
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (user_id, enquiry_at,principal,interest_rate,tenure_in_months) VALUES (?, ?, ?, ?, ?)",
                (st.session_state.user_id, current_time, principal, annual_rate, n_months),
            )
            conn.commit()
            conn.close()


    if st.session_state.col2_active:

        # EMI Calculation Logic
        if annual_rate > 0 and n_months > 0:
            # Monthly interest rate
            r_monthly = (annual_rate / 12) 
            
            # Standard EMI Formula Execution
            emi = (principal * r_monthly * ((1 + r_monthly) ** n_months)) / (((1 + r_monthly) ** n_months) - 1)
            
            total_amount = emi * n_months
            total_interest = total_amount - principal
        else:
            emi, total_interest, total_amount = 0, 0, 0



        # Display Outputs in the Second Column
        with col2:
            st.subheader("Repayment Breakdown")
            
            # Display Key Metrics using styled containers
            st.metric(label="Monthly EMI", value=f"₹{emi:,.2f}")
            st.metric(label="Principal Amount", value=f"₹{principal:,.2f}")
            st.metric(label="Total Interest Payable", value=f"₹{total_interest:,.2f}")
            st.markdown("---")
            st.metric(label="Total Amount (Principal + Interest)", value=f"₹{total_amount:,.2f}")

        # 2. Second row: 2 columns for the graphs
        g1, g2 = st.columns(2)
        with g1:
            # add Graphical Representation of EMI Breakdown
            dfout = {
                'Category': ['Principal Amount', 'Interest'],
                'Values': [principal, total_interest],
            }
            # Define your custom colors (Blue and Red)
            color_map = {'Principal Amount': "#1f77b4", 'Interest': "#d62728"}
            

            fig = px.pie(
                dfout,
                names='Category',
                values='Values',
                color='Category',              # CRITICAL: Required for color_discrete_map to function
                color_discrete_map=color_map,  # Applies the specific colors
                hole=0.6,                      # Setting a hole turns a pie chart into a donut chart
            )

            # Customize layout (optional)
            fig.update_traces(textposition='inside', textinfo='percent')

            # Display the chart in Streamlit
            st.subheader("Principal vs Interest Breakdown")
            
            # UPDATED: Replaced deprecated use_container_width with the new width parameter
            st.plotly_chart(fig, width="stretch") 



        df_schedule = generate_amortization_schedule(
            principal=principal, monthly_rate=r_monthly, total_payments=n_months
        )
        df_schedule['Year'] = (df_schedule['Month'] - 1) // 12 + 1
        df_schedule_summary = df_schedule.groupby('Year').agg(
            Principal=('Principal', 'sum'),
            Interest=('Interest', 'sum')
        ).reset_index()

        color_map_ammort = {'Principal': "#1f77b4", 'Interest': "#d62728"}


        with g2:
            if tenure_type == "Years":
                fig_ammort = px.bar(
                        df_schedule_summary,
                        x="Year",
                        y=["Principal", "Interest"],
                        # title="Amortization by "+tenure_type,
                        color_discrete_map=color_map_ammort,
                        )
                st.subheader("Amortization by "+tenure_type)
                st.plotly_chart(fig_ammort, width="stretch")
                
            else:
                fig_ammort = px.bar(
                        df_schedule,
                        x="Month",
                        y=["Principal", "Interest"],
                        # title="Amortization by "+tenure_type,
                        color_discrete_map=color_map_ammort,
                        )
                st.subheader("Amortization by "+tenure_type)
                st.plotly_chart(fig_ammort, width="stretch")
                



        # Optional: Context Warning for Users
        st.caption("Note: This calculation uses a fixed interest rate model. Actual bank rates may vary based on compounding intervals and processing fees.")
        

    # Sidebar Logout Button
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.rerun()

# 2. Show Login / Registration View if not logged in
else:
    st.title("🔒 Secure Entry Portal")

    # Toggle between Login and Sign Up
    page_mode = st.radio("Choose an option:", ["Login", "Register / Sign Up"])

    if page_mode == "Login":
        st.subheader("Login to your Account")

        with st.form("login_form"):
            user_id = st.text_input("User ID")
            mobile = st.text_input("Mobile Number", type="password")
            submit_btn = st.form_submit_button("Login")

            if submit_btn:
                if user_id and mobile:
                    if verify_user(user_id, mobile):
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Mobile Number.")
                else:
                    st.warning("Please fill in both fields.")

    else:
        st.subheader("Create a New Account")

        with st.form("register_form"):
            new_user_id = st.text_input("Choose User ID")
            new_mobile = st.text_input("Mobile Number")
            register_btn = st.form_submit_button("Register")

            if register_btn:
                if new_user_id and new_mobile:
                    # Simple validation helper
                    if len(new_mobile) < 10 or not new_mobile.isdigit():
                        st.error("Please enter a valid mobile number.")
                    elif add_user(new_user_id, new_mobile):
                        st.success(
                            "Account created successfully! Switch to 'Login' to sign in."
                        )
                    else:
                        st.error(
                            "User ID already exists. Please choose another one."
                        )
                else:
                    st.warning("Please fill in both fields.")





