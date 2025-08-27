#!/usr/bin/env python3
"""
Debug script to analyze the actual CSV files
"""

import pandas as pd
import sys
sys.path.append('.')

from app import process_online_csv, process_offline_csv

def analyze_csv_files():
    print("=== ANALYZING YOUR ACTUAL CSV FILES ===")
    print()

    # Analyze Online CSV
    print("1. ONLINE CSV ANALYSIS:")
    print("-" * 40)
    try:
        df_online = pd.read_csv('uploads/online.csv')
        print(f"Total rows: {len(df_online)}")
        print(f"Columns: {list(df_online.columns)}")
        print()
        print("Status values and counts:")
        print(df_online['Status'].value_counts())
        print()

        # Show filtering logic
        excluded_statuses = ['pending store acceptance', 'cancelled', 'pending payment']
        print(f"Filtering logic: EXCLUDE statuses: {excluded_statuses}")

        filtered_online = df_online[
            ~df_online['Status'].str.strip().str.lower().isin(excluded_statuses)
        ]
        print(f"Rows after filtering: {len(filtered_online)} out of {len(df_online)}")

        if len(filtered_online) > 0:
            print("Included statuses:")
            print(filtered_online['Status'].value_counts())
            print()
            print("Sample filtered data:")
            print(filtered_online[['Created Time', 'Status', 'Total']].head(3))

        print()

        # Test processing
        print("Testing online CSV processing...")
        online_result = process_online_csv('uploads/online.csv')
        print(f"Total online amount: ${online_result.sum():.2f}")

    except Exception as e:
        print(f"Error analyzing online CSV: {e}")
    
    print()
    print("2. OFFLINE CSV ANALYSIS:")
    print("-" * 40)
    try:
        df_offline = pd.read_csv('uploads/offline.csv')
        print(f"Total rows: {len(df_offline)}")
        print(f"Columns: {list(df_offline.columns)}")
        print()
        print("Transaction Type values and counts:")
        print(df_offline['Transaction Type'].value_counts())
        print()
        print("Is_Cancelled values and counts:")
        print(df_offline['Is_Cancelled'].value_counts())
        print()
        print("Sample data (first 3 rows):")
        print(df_offline[['Time', 'Transaction Type', 'Is_Cancelled', 'Total']].head(3))
        print()
        
        # Test processing
        print("Testing offline CSV processing...")
        offline_result = process_offline_csv('uploads/offline.csv')
        print(f"Total offline amount: ${offline_result.sum():.2f}")
        
    except Exception as e:
        print(f"Error analyzing offline CSV: {e}")

if __name__ == "__main__":
    analyze_csv_files()
