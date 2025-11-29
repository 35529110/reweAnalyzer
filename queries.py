"""
Analytics and Query Module for REWE Receipt Data

Provides various statistical queries and reports for analyzing shopping patterns.
This module is completely standalone and only requires the database file.
"""

import sqlite3
from typing import List, Dict, Any
from contextlib import contextmanager


# Default database path
DEFAULT_DB_PATH = "rewe_receipts.db"


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager for database connections.
    Automatically commits and closes the connection.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_most_purchased_items(db_path: str = DEFAULT_DB_PATH, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the most frequently purchased items.

    Args:
        db_path: Path to SQLite database file
        limit: Number of top items to return

    Returns:
        List of dictionaries with item statistics
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                name,
                COUNT(*) as purchase_count,
                SUM(quantity) as total_quantity,
                SUM(total) as total_spent,
                ROUND(AVG(price_per_unit), 2) as avg_price_per_unit,
                ROUND(MIN(price_per_unit), 2) as min_price,
                ROUND(MAX(price_per_unit), 2) as max_price
            FROM items
            GROUP BY name
            ORDER BY purchase_count DESC, total_spent DESC
            LIMIT ?
        """, (limit,))

        columns = ['name', 'purchase_count', 'total_quantity', 'total_spent',
                   'avg_price_per_unit', 'min_price', 'max_price']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results


def get_spending_by_date(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Get total spending grouped by date.

    Args:
        db_path: Path to SQLite database file

    Returns:
        List of dictionaries with date and spending
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                date,
                COUNT(DISTINCT bon_nr) as receipt_count,
                SUM(total_amount) as total_spent,
                ROUND(AVG(total_amount), 2) as avg_receipt_amount
            FROM receipts
            GROUP BY date
            ORDER BY date DESC
        """)

        columns = ['date', 'receipt_count', 'total_spent', 'avg_receipt_amount']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results


def get_spending_by_city(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Get total spending grouped by city/store location.

    Args:
        db_path: Path to SQLite database file

    Returns:
        List of dictionaries with city and spending statistics
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                city,
                store_name,
                COUNT(*) as receipt_count,
                SUM(total_amount) as total_spent,
                ROUND(AVG(total_amount), 2) as avg_receipt_amount
            FROM receipts
            GROUP BY city, store_name
            ORDER BY total_spent DESC
        """)

        columns = ['city', 'store_name', 'receipt_count', 'total_spent', 'avg_receipt_amount']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results


def get_spending_by_month(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Get total spending grouped by month.

    Args:
        db_path: Path to SQLite database file

    Returns:
        List of dictionaries with month and spending statistics
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                substr(date, 4, 7) as month,
                COUNT(*) as receipt_count,
                SUM(total_amount) as total_spent,
                ROUND(AVG(total_amount), 2) as avg_receipt_amount
            FROM receipts
            GROUP BY month
            ORDER BY substr(date, 7, 4) || '-' || substr(date, 4, 2) DESC
        """)

        columns = ['month', 'receipt_count', 'total_spent', 'avg_receipt_amount']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results


def print_item_statistics(db_path: str = DEFAULT_DB_PATH, limit: int = 20):
    """
    Print a formatted report of most purchased items.

    Args:
        db_path: Path to SQLite database file
        limit: Number of top items to show
    """
    items = get_most_purchased_items(db_path, limit)

    print("\n" + "=" * 100)
    print(f"TOP {limit} MOST PURCHASED ITEMS")
    print("=" * 100)
    print(f"{'Item Name':<40} {'Times':<8} {'Qty':<8} {'Total €':<10} {'Avg €':<8} {'Min €':<8} {'Max €':<8}")
    print("-" * 100)

    for item in items:
        print(f"{item['name'][:40]:<40} "
              f"{item['purchase_count']:<8} "
              f"{item['total_quantity']:<8.1f} "
              f"{item['total_spent']:<10.2f} "
              f"{item['avg_price_per_unit']:<8.2f} "
              f"{item['min_price']:<8.2f} "
              f"{item['max_price']:<8.2f}")

    print("=" * 100)

    # Calculate totals
    total_purchases = sum(item['purchase_count'] for item in items)
    total_spent = sum(item['total_spent'] for item in items)
    print(f"\nTotal purchases (top {limit} items): {total_purchases}")
    print(f"Total spent (top {limit} items): {total_spent:.2f}€")
    print("=" * 100)


def print_spending_by_month(db_path: str = DEFAULT_DB_PATH):
    """
    Print a formatted report of spending by month.

    Args:
        db_path: Path to SQLite database file
    """
    months = get_spending_by_month(db_path)

    print("\n" + "=" * 70)
    print("SPENDING BY MONTH")
    print("=" * 70)
    print(f"{'Month':<15} {'Receipts':<12} {'Total Spent':<15} {'Avg/Receipt':<15}")
    print("-" * 70)

    for month in months:
        print(f"{month['month']:<15} "
              f"{month['receipt_count']:<12} "
              f"{month['total_spent']:<15.2f} "
              f"{month['avg_receipt_amount']:<15.2f}")

    print("=" * 70)

    # Calculate totals
    total_receipts = sum(m['receipt_count'] for m in months)
    total_spent = sum(m['total_spent'] for m in months)
    print(f"\nTotal receipts: {total_receipts}")
    print(f"Total spent: {total_spent:.2f}€")
    if total_receipts > 0:
        print(f"Overall average per receipt: {total_spent/total_receipts:.2f}€")
    print("=" * 70)


def print_spending_by_city(db_path: str = DEFAULT_DB_PATH):
    """
    Print a formatted report of spending by city/store.

    Args:
        db_path: Path to SQLite database file
    """
    cities = get_spending_by_city(db_path)

    print("\n" + "=" * 90)
    print("SPENDING BY CITY/STORE")
    print("=" * 90)
    print(f"{'City':<20} {'Store':<30} {'Receipts':<12} {'Total €':<12} {'Avg €':<12}")
    print("-" * 90)

    for city in cities:
        print(f"{city['city'][:20]:<20} "
              f"{city['store_name'][:30]:<30} "
              f"{city['receipt_count']:<12} "
              f"{city['total_spent']:<12.2f} "
              f"{city['avg_receipt_amount']:<12.2f}")

    print("=" * 90)


def get_top_receipts(db_path: str = DEFAULT_DB_PATH, limit: int = 10, order_by: str = 'total') -> List[Dict[str, Any]]:
    """
    Get top receipts by total amount.

    Args:
        db_path: Path to SQLite database file
        limit: Number of receipts to return
        order_by: Sort by 'total' or 'items' (item count)

    Returns:
        List of dictionaries with receipt information
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        order_clause = "total_amount DESC" if order_by == 'total' else "item_count DESC"

        cursor.execute(f"""
            SELECT
                r.date,
                r.time,
                r.bon_nr,
                r.store_name,
                r.city,
                r.total_amount,
                r.payment_methode,
                COUNT(i.id) as item_count
            FROM receipts r
            LEFT JOIN items i ON r.id = i.receipt_id
            GROUP BY r.id
            ORDER BY {order_clause}
            LIMIT ?
        """, (limit,))

        columns = ['date', 'time', 'bon_nr', 'store_name', 'city',
                   'total_amount', 'payment_methode', 'item_count']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results


def print_most_expensive_receipt(db_path: str = DEFAULT_DB_PATH):
    """
    Print details of the most expensive receipt.

    Args:
        db_path: Path to SQLite database file
    """
    receipts = get_top_receipts(db_path, limit=1, order_by='total')

    if not receipts:
        print("\nNo receipts found in database.")
        return

    receipt = receipts[0]

    print("\n" + "=" * 80)
    print("MOST EXPENSIVE RECEIPT")
    print("=" * 80)
    print(f"Date:         {receipt['date']} {receipt['time']}")
    print(f"Bon Nr:       {receipt['bon_nr']}")
    print(f"Store:        {receipt['store_name']}")
    print(f"City:         {receipt['city']}")
    print(f"Payment:      {receipt['payment_methode']}")
    print(f"Total:        {receipt['total_amount']:.2f}€")
    print(f"Items:        {receipt['item_count']}")
    print("-" * 80)

    # Get items for this receipt
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, quantity, price_per_unit, total
            FROM items
            WHERE date = ? AND time = ? AND receipt_id IN (
                SELECT id FROM receipts WHERE bon_nr = ?
            )
            ORDER BY total DESC
        """, (receipt['date'], receipt['time'], receipt['bon_nr']))

        print("ITEMS:")
        print(f"{'Name':<45} {'Qty':<8} {'Price/Unit':<12} {'Total':<10}")
        print("-" * 80)

        for row in cursor.fetchall():
            name, qty, price_per_unit, total = row
            print(f"{name[:45]:<45} {qty:<8.1f} {price_per_unit:<12.2f} {total:<10.2f}")

    print("=" * 80)


def print_top_receipts(db_path: str = DEFAULT_DB_PATH, limit: int = 10):
    """
    Print a formatted table of top receipts by amount.

    Args:
        db_path: Path to SQLite database file
        limit: Number of top receipts to show
    """
    receipts = get_top_receipts(db_path, limit, order_by='total')

    print("\n" + "=" * 90)
    print(f"TOP {limit} MOST EXPENSIVE RECEIPTS")
    print("=" * 90)
    print(f"{'Date':<12} {'Time':<8} {'Bon':<8} {'Store':<25} {'Items':<8} {'Total €':<10}")
    print("-" * 90)

    for receipt in receipts:
        print(f"{receipt['date']:<12} "
              f"{receipt['time']:<8} "
              f"{receipt['bon_nr']:<8} "
              f"{receipt['store_name'][:25]:<25} "
              f"{receipt['item_count']:<8} "
              f"{receipt['total_amount']:<10.2f}")

    print("=" * 90)


def print_all_statistics(db_path: str = DEFAULT_DB_PATH, top_items: int = 20):
    """
    Print all available statistics reports.

    Args:
        db_path: Path to SQLite database file
        top_items: Number of top items to show
    """
    print_most_expensive_receipt(db_path)
    print_top_receipts(db_path, limit=10)
    print_item_statistics(db_path, top_items)
    print_spending_by_month(db_path)
    print_spending_by_city(db_path)


if __name__ == "__main__":
    # Run all statistics when script is executed directly
    print_all_statistics()