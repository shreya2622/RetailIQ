import snowflake.connector
import pandas as pd
import os

conn = snowflake.connector.connect(
    user='SHREYAP',
    password='GunniShinu@1997',
    account='pvbpypn-cl36404',
    warehouse='RETAILIQ_WH',
    database='RETAILIQ',
    schema='RAW'
)

cursor = conn.cursor()

FILE_TABLE_MAP = {
    'olist_orders_dataset.csv':           'ORDERS',
    'olist_order_items_dataset.csv':      'ORDER_ITEMS',
    'olist_order_payments_dataset.csv':   'ORDER_PAYMENTS',
    'olist_order_reviews_dataset.csv':    'ORDER_REVIEWS',
    'olist_customers_dataset.csv':        'CUSTOMERS',
    'olist_products_dataset.csv':         'PRODUCTS',
    'olist_sellers_dataset.csv':          'SELLERS',
}

RAW_DIR = 'data/raw'

for filename, table in FILE_TABLE_MAP.items():
    filepath = os.path.join(RAW_DIR, filename)
    df = pd.read_csv(filepath)
    print(f"Loading {filename} ({len(df):,} rows) → {table}")

    temp_path = f'/tmp/{filename}'
    df.to_csv(temp_path, index=False)

    cursor.execute(f"PUT file://{temp_path} @%{table}")
    cursor.execute(f"""
        COPY INTO {table}
        FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                       SKIP_HEADER = 1 NULL_IF = ('NULL', 'null', ''))
        PURGE = TRUE
    """)
    print(f"  ✓ {table} loaded")

cursor.close()
conn.close()
print("\nAll tables loaded successfully.")