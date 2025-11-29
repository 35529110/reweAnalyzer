# Database Setup Guide

## Overview

The REWE Receipt Analyzer uses SQLite to store parsed receipt data. The database schema is based on your PostgreSQL design but adapted for SQLite.

## Database Structure

### Tables

1. **receipts** - Main receipt information (Bon details, totals, payment, etc.)
2. **receipt_items** - Individual items on each receipt
3. **tax_summary** - Tax breakdown per receipt
4. **markets** - REWE market/store information
5. **products** - Product catalog for normalization

## Quick Start

### 1. Initialize the Database

Run the initialization script to create the database and all tables:

```bash
python init_db.py
```

This will:
- Create `rewe_receipts.db` in the project root
- Execute `database_schema.sql` to create all tables and indexes
- Show a summary of created tables

**Output:**
```
Connecting to database: rewe_receipts.db
Reading schema from database_schema.sql...
Creating tables and indexes...

Database initialized successfully!
Created 5 tables:
  - receipts
  - receipt_items
  - tax_summary
  - markets
  - products
```

### 2. Using the Database in Code

Import the database helper module:

```python
from database import (
    get_db_connection,
    insert_receipt,
    insert_receipt_items,
    get_all_receipts,
    search_receipts_by_date
)

# Get all receipts
receipts = get_all_receipts()
for receipt in receipts:
    print(f"{receipt['kaufdatum']}: {receipt['summe_brutto']} EUR")

# Search by date
receipts = search_receipts_by_date('2025-11-01', '2025-11-30')

# Direct SQL queries
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM receipts WHERE summe_brutto > 50")
    expensive = cursor.fetchall()
```

## Database Files

- `database_schema.sql` - SQL schema definition
- `init_db.py` - Initialization script
- `database.py` - Helper functions for database operations
- `rewe_receipts.db` - The SQLite database file (git-ignored)

## Schema Details

### receipts Table

Main table storing receipt header information:

```sql
receipt_id INTEGER PRIMARY KEY
bon_nummer VARCHAR(20) - Receipt number
markt_nummer VARCHAR(10) - Market/store number
kaufdatum DATE - Purchase date
kaufzeit TIME - Purchase time
summe_brutto DECIMAL(10,2) - Total amount
zahlungsart VARCHAR(50) - Payment method
bonus_eingesetzt DECIMAL(10,2) - Bonus points used
pdf_dateiname VARCHAR(255) - Source PDF filename
```

### receipt_items Table

Individual line items on each receipt:

```sql
item_id INTEGER PRIMARY KEY
receipt_id INTEGER - Foreign key to receipts
artikel_name VARCHAR(200) - Product name
gesamt_preis DECIMAL(10,2) - Item total price
menge INTEGER - Quantity
ist_pfand BOOLEAN - Is deposit (Pfand)?
ist_leergut BOOLEAN - Is return (Leergut)?
```

### Indexes

The following indexes are created for query performance:

- `idx_receipts_kaufdatum` - Search by date
- `idx_receipts_markt` - Search by market
- `idx_items_artikel` - Search items by name
- `idx_items_receipt` - Get items for a receipt

## Example Queries

### Total spending per month

```sql
SELECT
    strftime('%Y-%m', kaufdatum) AS month,
    SUM(summe_brutto) AS total
FROM receipts
GROUP BY month
ORDER BY month DESC;
```

### Most purchased items

```sql
SELECT
    artikel_name,
    COUNT(*) AS times_purchased,
    SUM(gesamt_preis) AS total_spent
FROM receipt_items
GROUP BY artikel_name
ORDER BY times_purchased DESC
LIMIT 10;
```

### Average basket value

```sql
SELECT
    AVG(summe_brutto) AS avg_basket,
    COUNT(*) AS num_receipts
FROM receipts;
```

### Spending by market

```sql
SELECT
    r.markt_nummer,
    m.markt_name,
    COUNT(*) AS num_visits,
    SUM(r.summe_brutto) AS total_spent
FROM receipts r
LEFT JOIN markets m ON r.markt_nummer = m.markt_nummer
GROUP BY r.markt_nummer
ORDER BY total_spent DESC;
```

## Maintenance Commands

### View database structure

```bash
sqlite3 rewe_receipts.db ".schema"
```

### Count records

```bash
sqlite3 rewe_receipts.db "SELECT COUNT(*) FROM receipts;"
```

### Export to CSV

```bash
sqlite3 rewe_receipts.db <<EOF
.headers on
.mode csv
.output receipts_export.csv
SELECT * FROM receipts;
EOF
```

### Backup database

```bash
cp rewe_receipts.db rewe_receipts_backup_$(date +%Y%m%d).db
```

### Reset database

```bash
rm rewe_receipts.db
python init_db.py
```

## Integration with Main Script

The database is designed to store AI-parsed receipt data. After the AI analyzes a receipt, you can:

1. Parse the AI response (JSON)
2. Extract receipt header fields
3. Insert into `receipts` table
4. Extract items
5. Insert into `receipt_items` table

Example integration point in `main.py`:

```python
from database import insert_receipt, insert_receipt_items

# After AI analysis
ai_analysis = analyze_receipt_with_ai(extracted_text)

if ai_analysis:
    # Insert receipt
    receipt_id = insert_receipt({
        'bon_nummer': ai_analysis['bon_nummer'],
        'markt_nummer': ai_analysis['markt_nummer'],
        'kaufdatum': ai_analysis['kaufdatum'],
        # ... other fields
    })

    # Insert items
    if receipt_id:
        insert_receipt_items(receipt_id, ai_analysis['items'])
```

## SQLite vs PostgreSQL

This schema is adapted from your PostgreSQL design with these changes:

- `SERIAL` ’ `INTEGER PRIMARY KEY AUTOINCREMENT`
- `BOOLEAN` ’ `INTEGER` (0/1 in SQLite)
- Full-text search indexes removed (can be added with FTS5 extension)
- `CURRENT_TIMESTAMP` works the same

## Troubleshooting

### Database locked

If you get "database is locked" errors, make sure:
- No other process is accessing the database
- Use the context manager `with get_db_connection()` to ensure proper closing

### Foreign key violations

Foreign keys are disabled by default in SQLite. The helper functions automatically enable them with:
```python
conn.execute("PRAGMA foreign_keys = ON;")
```

### Viewing query results in terminal

```bash
sqlite3 rewe_receipts.db
sqlite> .mode column
sqlite> .headers on
sqlite> SELECT * FROM receipts LIMIT 5;
```
