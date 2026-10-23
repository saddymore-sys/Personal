# Load Packages
import streamlit as st
import pandas as pd
import numpy as np
from functions import generate_amortization_schedule
import plotly
import plotly.express as px


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


with col0:
    st.subheader("Select Loan Type")
    selected_loan_type = st.selectbox("Choose a loan type:", Loan_Type)

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

    # Input 3: Tenure Type Selection
    tenure_type = st.radio("Tenure Type", ["Years", "Months"], horizontal=True)

    if tenure_type == "Years":
        tenure_years = st.slider("Tenure (Years)", min_value=1, max_value=30, value=5)
        n_months = tenure_years * 12
    else:
        n_months = st.slider("Tenure (Months)", min_value=1, max_value=360, value=60)


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


