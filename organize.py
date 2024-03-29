import json
import os
import sys
from pathlib import Path

import pandas as pd

from categories import E_CATEGORIES, I_CATEGORIES


def create_data_frame(configs):
    files = configs['files']
    keep_columns = configs['keep_data_from']
    # https://dev.to/balapriya/building-a-dataframe-from-multiple-files-1590
    # The [keep_columns] after read_csv reorders the header to match keep_columns.
    df = pd.concat((pd.read_csv(f, parse_dates=[keep_columns[0]])[keep_columns] for f in files), ignore_index=True)

    # Rename columns to standard names.
    df.columns = ['Date', 'Description', 'Amount']
    # Switch order of columns.
    df = df[['Date', 'Amount', 'Description']]
    # Remove time from datetime objects.
    df['Date'] = pd.to_datetime(df['Date']).dt.date

    if option_enabled(configs, 'format', 'reverse_sign', 'true'):
        df['Amount'] = df['Amount'] * -1

    if 'exceptions' in configs:
        df = remove_exceptions(configs['exceptions'], df, 'Description')

    return df

def option_enabled(configs_dict, section, option, value):
    if section in configs_dict:
        if option in configs_dict[section]:
            if configs_dict[section][option].lower() == value:
                return True
    return False

def remove_exceptions(exceptions, df, description_column):
    with open(exceptions, 'r') as f:
        for line in f:
            # Print row containing exception without the header or index column.
            print('Removed ' + df[df[description_column].str.contains(line.strip())].to_string(index=False, header=False))
            # Remove row containing exception.
            df = df[~df[description_column].str.contains(line.strip())]
    # Print newline.
    print('')
    # Reset out of order index column and return.
    return df.reset_index(drop=True)

def separate_expenses_and_income(dataframes_list):
    df = pd.concat(dataframes_list, ignore_index=True)
    expenses, income = df[(mask:=df['Amount'] <= 0)].copy(), df[~mask].copy()
    expenses = expenses.sort_values(by='Date', ignore_index=True)
    income = income.sort_values(by='Date', ignore_index=True)
    return expenses, income

def categorize_data(df, finance_type):
    if finance_type == 'expenses':
        categories = E_CATEGORIES 
        to_from_category = 'To'
        rename_amount_column_to = 'Expense'
    elif finance_type == 'income':
        categories = I_CATEGORIES
        to_from_category = 'From'
        rename_amount_column_to = 'Income'
    else:
        print('Invalid finance type given')
        sys.exit(3)
    
    columns = df.columns.tolist()
    user_categories = []
    to_from_list = []
    updated_descriptions = []

    for index, row in df.iterrows():
        print(f'{columns} - {rename_amount_column_to} {index}')
        print(f'{row[columns[0]]}, ${row[columns[1]]}, "{row[columns[2]]}"')
        print(categories)
        category, to_from, user_description = get_user_input(categories, to_from_category)
        user_categories.append(category)
        to_from_list.append(to_from)
        updated_descriptions.append(user_description)
        os.system('clear')
    
    df = df.rename(columns={'Amount': rename_amount_column_to})
    df.insert(2, 'Category', user_categories, allow_duplicates=True)
    df.insert(3, to_from_category, to_from_list, allow_duplicates=True)
    df['Description'] = updated_descriptions

    return df

def get_user_input(categories, to_from_category):
    category = input('Select a category: ')
    while not good_category(category, categories):
        category = input('Invalid, select a category: ')

    to_from = input(f'{to_from_category}: ').strip()
    while not to_from:
        to_from = input(f'Entry can\'t be empty, {to_from_category}: ').strip()

    user_description = input('(Optional) Description: ')

    return categories[int(category)], to_from, user_description

def good_category(category, categories):
    return category.isdigit() and int(category) in categories

def write_final_df_to_file(df, path):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path_or_buf=filepath, index=False)

@staticmethod
def get_json_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)
