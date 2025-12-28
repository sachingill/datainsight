#!/usr/bin/env python3
"""
Setup script to create and populate the ecommerce database from CSV files.
Based on the Language to Dashboard.ipynb notebook.
"""

import csv
import sqlite3
from datetime import datetime
from src.constants import DATABASE

def setup_database():
    """Create tables and load data from CSV files."""
    
    # Connect to database
    mydb = sqlite3.connect(DATABASE)
    mycursor = mydb.cursor()
    
    print("Creating database tables...")
    
    # Create all tables
    mycursor.execute("CREATE TABLE IF NOT EXISTS distribution_centers(id INT, name VARCHAR(255), latitude FLOAT, longitude FLOAT)")
    mycursor.execute("CREATE TABLE IF NOT EXISTS events(id INT, user_id INT, sequence_number INT, session_id VARCHAR(255), created_at TIMESTAMP, ip_address VARCHAR(255), city VARCHAR(255), state VARCHAR(255), postal_code VARCHAR(255), browser VARCHAR(255), traffic_source VARCHAR(255), uri VARCHAR(255), event_type VARCHAR(255))")
    mycursor.execute("CREATE TABLE IF NOT EXISTS inventory_items(id INT, product_id INT, created_at TIMESTAMP, sold_at TIMESTAMP, cost FLOAT, product_category VARCHAR(255), product_name VARCHAR(255), product_brand VARCHAR(255), product_retail_price FLOAT, product_department VARCHAR(255), product_sku VARCHAR(255), product_distribution_center_id INT)")
    mycursor.execute("CREATE TABLE IF NOT EXISTS order_items(id INT, order_id INT, user_id INT, product_id INT, inventory_item_id INT, status VARCHAR(255), created_at TIMESTAMP, shipped_at TIMESTAMP, delivered_at TIMESTAMP, returned_at TIMESTAMP, sale_price FLOAT)")
    mycursor.execute("CREATE TABLE IF NOT EXISTS orders(order_id INT, user_id INT, status VARCHAR(255), gender VARCHAR(255), created_at TIMESTAMP, returned_at TIMESTAMP, shipped_at TIMESTAMP, delivered_at TIMESTAMP, num_of_item INT)")
    mycursor.execute("CREATE TABLE IF NOT EXISTS products(id INT, cost FLOAT, category VARCHAR(255), name VARCHAR(255), brand VARCHAR(255), retail_price FLOAT, department VARCHAR(255), sku VARCHAR(255), distribution_center_id INT)")
    mycursor.execute("CREATE TABLE IF NOT EXISTS users(id INT, first_name VARCHAR(255), last_name VARCHAR(255), email VARCHAR(255), age INT, gender VARCHAR(255), state VARCHAR(255), street_address VARCHAR(255), postal_code VARCHAR(255), city VARCHAR(255), country VARCHAR(255), latitude FLOAT, longitude FLOAT, traffic_source VARCHAR(255), created_at TIMESTAMP)")
    mydb.commit()
    print("✓ Tables created successfully")
    
    # Function to detect timestamp columns
    def detect_timestamp_columns(cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        timestamp_indices = [i for i, column in enumerate(columns) if column[2].startswith('TIMESTAMP')]
        return timestamp_indices
    
    # Load data from CSV files
    table_names = ["distribution_centers", "events", "inventory_items", "order_items", "orders", "products", "users"]
    
    print("\nLoading data from CSV files...")
    
    for table_name in table_names:
        timestamp_indices = detect_timestamp_columns(mycursor, table_name)
        
        csv_path = f"data/{table_name}.csv"
        try:
            with open(csv_path, 'r', encoding='utf-8') as csv_file:
                csv_data = csv.reader(csv_file)
                next(csv_data)  # Skip headers
                counter = 0
                print(f"  Loading {table_name}...", end=" ", flush=True)
                
                for row in csv_data:
                    counter += 1
                    if counter % 10000 == 0:
                        print(f"({counter} rows)", end=" ", flush=True)
                    
                    row = [None if cell == "" else cell for cell in row]
                    
                    # Correct datetime values if necessary
                    for col_index in timestamp_indices:
                        if row[col_index] is not None and row[col_index] != '':
                            try:
                                clean_val = row[col_index].replace(" UTC", "")
                                datetime.strptime(clean_val, "%Y-%m-%d %H:%M:%S")
                                row[col_index] = clean_val
                            except ValueError:
                                row[col_index] = None
                        else:
                            row[col_index] = None
                    
                    postfix = ','.join(["?"] * len(row))
                    query = f"INSERT INTO {table_name} VALUES ({postfix})"
                    try:
                        mycursor.execute(query, row)
                    except sqlite3.Error as err:
                        print(f"\n    Error: {err}")
                        print(f"    Failed row: {row[:5]}...")  # Show first 5 columns
                
                mydb.commit()
                print(f"✓ Completed ({counter} rows)")
        except FileNotFoundError:
            print(f"✗ CSV file not found: {csv_path}")
        except Exception as e:
            print(f"✗ Error loading {table_name}: {e}")
    
    mydb.close()
    print("\n✓ Database setup complete!")

if __name__ == "__main__":
    setup_database()

