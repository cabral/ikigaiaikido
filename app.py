import yaml
from yaml.loader import SafeLoader
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime
import re

# Load configuration
# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)

# # Initialize authenticator
# authenticator = stauth.Authenticate(
#     config['credentials'],
#     config['cookie']['name'],
#     config['cookie']['key'],
#     config['cookie']['expiry_days']
# )

# # Login widget
# name, authentication_status, username = authenticator.login()authentication_status = True

authentication_status = True

if authentication_status:
    # --- Main Application ---
    st.title("Transaction Filtering App")

    # Modify the file uploader to accept multiple files
    uploaded_files = st.file_uploader("Upload your CSV files", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        # Encoding selection with default value set to 'iso-8859-1'
        encoding_options = ['utf-8', 'latin1', 'iso-8859-1']
        default_encoding = 'iso-8859-1'
        selected_encoding = st.selectbox(
            "Select File Encoding",
            encoding_options,
            index=encoding_options.index(default_encoding)
        )

        # Initialize an empty DataFrame to store combined data
        df_total = pd.DataFrame()

        # Read and concatenate each uploaded file
        for uploaded_file in uploaded_files:
            # Specify the date columns to parse
            date_columns = ['Accday', 'Transday', 'Valueday']
            df = pd.read_csv(
                uploaded_file,
                skiprows=1,  # Skip the first line with the report header
                encoding=selected_encoding,
                parse_dates=date_columns,
                infer_datetime_format=True
            )
            df_total = pd.concat([df_total, df], ignore_index=True)

        # Convert 'Amount' column to numeric
        df_total['Amount'] = pd.to_numeric(df_total['Amount'], errors='coerce')

        # Add a date range selector
        st.subheader("Filter by Transaction Date")
        min_date = df_total['Transday'].min().date()
        max_date = df_total['Transday'].max().date()
        start_date, end_date = st.date_input(
            "Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )

        # Ensure that both dates are selected
        if start_date and end_date:
            # Filter the DataFrame based on the selected date range
            df_total = df_total[
                (df_total['Transday'] >= pd.to_datetime(start_date)) &
                (df_total['Transday'] <= pd.to_datetime(end_date))
            ]

        # Add a text input for name search
        st.subheader("Search by Sender Names")
        name_input = st.text_input("Enter names to search (separate multiple names with commas)")

        if name_input:
            # Split the input string into a list of names
            name_list = [name.strip() for name in name_input.split(',')]
            # Escape special characters in names
            name_list = [re.escape(name) for name in name_list if name]
            # Create a regex pattern
            pattern = '|'.join(name_list)
            # Filter the DataFrame
            df_total = df_total[df_total['Sendername'].str.contains(pattern, case=False, na=False)]

            # Check if any transactions are found
            if df_total.empty:
                st.warning("No transactions found for the specified names.")

        # Proceed only if there are transactions after filtering
        if not df_total.empty:
            # Amounts available in the 'Amount' column
            amounts_available = df_total['Amount'].dropna().unique()
            amounts_to_filter = st.multiselect(
                "Select Amounts to Filter",
                options=sorted(amounts_available),
                default=[]
            )

            # Adjust the amount filtering logic
            if amounts_to_filter:
                # Filter the DataFrame by Amount
                df_filtered = df_total[df_total['Amount'].isin(amounts_to_filter)]
            else:
                # No amounts selected, include all amounts
                df_filtered = df_total.copy()

            df_result = df_filtered[['Sendername', 'Amount', 'Transday']]

            # Find Sendernames that appear again with different amounts
            sendernames = df_result['Sendername'].unique()
            if amounts_to_filter:
                df_other_amounts = df_total[
                    (df_total['Sendername'].isin(sendernames)) &
                    (~df_total['Amount'].isin(amounts_to_filter))
                ][['Sendername', 'Amount', 'Transday']]
            else:
                # Since all amounts are included, there are no other transactions
                df_other_amounts = pd.DataFrame(columns=['Sendername', 'Amount', 'Transday'])

            # Reset index
            df_result.reset_index(drop=True, inplace=True)
            df_other_amounts.reset_index(drop=True, inplace=True)

            # Display the filtered DataFrames
            st.subheader("Filtered Transactions")
            st.dataframe(df_result)

            st.subheader("Other Transactions by Same Sendernames")
            if not df_other_amounts.empty:
                st.dataframe(df_other_amounts)
            else:
                st.write("No other transactions found for the selected sender names.")

            # Function to convert DataFrame to CSV
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')

            # Download buttons
            csv_filtered = convert_df(df_result)
            st.download_button(
                label="Download Filtered Transactions",
                data=csv_filtered,
                file_name='filtered_transactions.csv',
                mime='text/csv',
            )

            if not df_other_amounts.empty:
                csv_other = convert_df(df_other_amounts)
                st.download_button(
                    label="Download Other Transactions",
                    data=csv_other,
                    file_name='other_transactions.csv',
                    mime='text/csv',
                )
        else:
            st.info("No transactions available after applying the filters.")

    else:
        st.info("Please upload at least one CSV file to proceed.")

    # Logout button
    # authenticator.logout('Logout', 'main')

elif authentication_status == False:
    st.error('Username or password is incorrect')

elif authentication_status == None:
    st.warning('Please enter your username and password')
