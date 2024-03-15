import pandas as pd

def load_and_prepare_data(file_path):
    column_names = ['Date', 'Party', 'Amount', 'TransactionType']
    df = pd.read_csv(file_path, names=column_names, header=None)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = df['Amount'].str.replace(',', '').astype(float)
    return df

def filter_deposits_and_withdrawals(df, start_date, end_date):
    modified_end_date = pd.to_datetime(end_date) + pd.Timedelta(days=15)
    deposits_df = df[(df['TransactionType'] == 'Deposited') & (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= modified_end_date)]
    withdrawals_df = df[(df['TransactionType'] == 'Withdrew') & (df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= modified_end_date)]
    return deposits_df, withdrawals_df

def match_transactions(deposits_df, withdrawals_df, end_date):
    transactions_summary = []

    for i, withdrawal_row in withdrawals_df.iterrows():
        if withdrawal_row['Date'].date() > pd.to_datetime(end_date).date() + pd.Timedelta(days=15):
            continue  # Skip withdrawals beyond 15 days of the end_date
        eligible_deposit_date = withdrawal_row['Date'] - pd.Timedelta(days=15)
        eligible_deposits = deposits_df[(deposits_df['Date'] >= eligible_deposit_date) & 
                                        (deposits_df['Date'] <= withdrawal_row['Date']) & 
                                        (deposits_df['Amount'] == withdrawal_row['Amount'])]
        
        eligible_deposits_grouped = eligible_deposits.groupby(['Party', 'Amount']).agg({'Date':'min'}).reset_index()
        withdrawals_grouped = withdrawal_row.to_frame().T.groupby(['Party', 'Amount']).agg({'Date':'min'}).reset_index()

        for _, deposit_row in eligible_deposits_grouped.iterrows():
            for _, withdraw_row in withdrawals_grouped.iterrows():
                transactions_summary.append((deposit_row['Party'], deposit_row['Amount'], deposit_row['Date'], withdraw_row['Party'], withdraw_row['Date']))
                
    # Consolidate matched transactions and count occurrences
    transaction_counts = {}
    for deposit_party, amount, deposit_date, withdraw_party, withdraw_date in transactions_summary:
        key = (deposit_party, amount, deposit_date, withdraw_party, withdraw_date)
        transaction_counts[key] = transaction_counts.get(key, 0) + 1

    # Generate final consolidated transactions
    consolidated_transactions = []
    for (deposit_party, amount, deposit_date, withdraw_party, withdraw_date), count in transaction_counts.items():
        consolidated_transactions.append(f"{deposit_party} deposited Rs. {amount*count} on {deposit_date.date()}. "
                                         f"and {withdraw_party} withdrew Rs.{amount*count} on {withdraw_date.date()}. "
                                         f"So this could mean that {withdraw_party} got {amount*count} donation.")

    return consolidated_transactions

if __name__ == '__main__':
    file_path = 'donation_data.csv'  # Specify the path to the CSV file
    df = load_and_prepare_data(file_path)
    
    start_date = '2019-07-05'
    end_date = '2019-07-10'
    
    deposits_df, withdrawals_df = filter_deposits_and_withdrawals(df, start_date, end_date)
    consolidated_transactions = match_transactions(deposits_df, withdrawals_df, end_date)
    
    for transaction in consolidated_transactions:
        print(transaction)
