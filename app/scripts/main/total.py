import pandas as pd
import numpy as np
from datetime import datetime
import scripts.main.importer as importer
import scripts.main.config as config

def total_money_data(data: dict):

    checking_account = __latest_account_balance(data, '360')
    savings_account = __latest_account_balance(data, 'Konto Oszczędnościowe Profit')
    cash = __latest_account_balance(data, 'Gotówka')
    ppk = __latest_account_balance(data, 'PKO PPK')

    inv = data['investment'].loc[data['investment']['Active'] == True]
    inv = inv['Start Amount'].sum()

    stock_buy = data['stock'].loc[data['stock']['Operation'] == 'Buy']
    stock_buy = stock_buy['Total Value'].sum()
    # TODO check how much stock units I have Broker-Title pair buy-sell
    total = checking_account + savings_account + cash + ppk + inv + stock_buy

    return pd.DataFrame([
        {'Type': 'Checking Account', 'Total': checking_account, 'Percentage': checking_account/total},
        {'Type': 'Savings Account', 'Total': savings_account, 'Percentage': savings_account/total},
        {'Type': 'Cash', 'Total': cash, 'Percentage': cash/total},
        {'Type': 'PPK', 'Total': ppk, 'Percentage': ppk/total},
        {'Type': 'Investments', 'Total': inv, 'Percentage': inv/total},
        {'Type': 'Stocks', 'Total': stock_buy, 'Percentage': stock_buy/total}
    ])

def __latest_account_balance(data: dict, type: str) -> float:
    
    #TODO filter by account type, not name, and if more than one sum it
    df = data['account'].loc[data['account']['Account'] == type]
    if not df.empty:
        return df['Balance'].iloc[-1]
    return 0.00

def update_total_money(accounts: pd.DataFrame, updated_dates: pd.Series, file_type = 'account'):
    total = importer.load_data(importer.FileType.TOTAL)

    investment = importer.load_data(importer.FileType.INVESTMENT)
    stock = importer.load_data(importer.FileType.STOCK)
    # TODO two categories - retire and all total money
    
    total = __clean_overlapping_days(total, updated_dates.min())
    total_new_lines = __calc_totals(accounts, updated_dates)
    total = pd.concat([total, total_new_lines]).reset_index(drop=True)
    total.to_csv(config.mankoo_file_path('total'), index=False)
    return total

def __clean_overlapping_days(total: pd.DataFrame, min_date: datetime):
    return total.drop(total[total['Date'] >= min_date].index)

def __calc_totals(accounts: pd.DataFrame, updated_dates: pd.Series):
    accounts_dates = accounts[accounts['Date'] > updated_dates.min()]['Dates']
    updated_dates = updated_dates.append(accounts_dates, ignore_index=True)
    updated_dates = updated_dates.drop_duplicates().sort_values()

    result_list = []
    
#    TODO replace with better approach, e.g.
    # https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
    for date in updated_dates.iterrows():
        row_dict = {'Date': date, 'Total': balance_for_day(accounts, date) + cash_for_day(accounts, date) + 'investment' + 'stock'}
        result_list.append(row_dict)
        
    return pd.DataFrame(result_list)
    

def balance_for_day(accounts: pd.DataFrame, date: datetime):
    account_names = accounts['Account'].unique()

    result = 0
    for account_name in account_names:
        result = result + __get_balance_for_day_or_earlier(accounts, account_name, date)
    return result

def __get_balance_for_day_or_earlier(accounts: pd.DataFrame, account_name: str, date: datetime):

    only_single_account = accounts[accounts['Account'] == account_name]
    only_specific_dates_accounts = only_single_account[only_single_account['Date'] >= date]
    
    return only_specific_dates_accounts['Balance'].iloc[-1]

def cash_for_day(accounts: pd.DataFrame, date: datetime):
    cash_lines = accounts[accounts['Type'] == 'cash']
    cash_specific_day = cash_lines[cash_lines['Date'] >= date]

    return cash_specific_day['Balance'].iloc[-1]