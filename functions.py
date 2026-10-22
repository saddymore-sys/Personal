import pandas as pd
import numpy as np

# Calculate Amortization Schedule

def generate_amortization_schedule(principal, monthly_rate, total_payments ):
    # 1. Setup inputs and variables
    # monthly_rate = annual_rate / 12
    monthly_rate = monthly_rate
    total_payments = total_payments

    # 2. Calculate the fixed monthly payment (PMT formula)
    monthly_payment = (
        principal
        * (monthly_rate * (1 + monthly_rate) ** total_payments)
        / ((1 + monthly_rate) ** total_payments - 1)
    )

    # 3. Initialize lists to store monthly data
    periods = range(1, total_payments + 1)
    interest_paid = []
    principal_paid = []
    remaining_balance = []

    current_balance = principal

    # 4. Loop through each month to compute the breakdown
    for period in periods:
        interest = current_balance * monthly_rate
        principal_component = monthly_payment - interest

        # Handle the final payment rounding if necessary
        if current_balance < principal_component:
            principal_component = current_balance
            monthly_payment = principal_component + interest

        current_balance -= principal_component

        interest_paid.append(interest)
        principal_paid.append(principal_component)
        remaining_balance.append(max(0, current_balance))

    # 5. Create the pandas DataFrame
    df = pd.DataFrame(
        {
            "Month": periods,
            "Payment": monthly_payment,
            "Principal": principal_paid,
            "Interest": interest_paid,
            "Remaining Balance": remaining_balance,
        }
    )

    # Round columns to 2 decimal places for financial formatting
    return df.round(2)