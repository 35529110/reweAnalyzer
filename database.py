"""
Database Helper Module for REWE Receipt Analyzer

Provides functions for connecting to and interacting with the SQLite database.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from receipt import Receipt, Item


# Default database path
DEFAULT_DB_PATH = "rewe_receipts.db"


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager for database connections.
    Automatically commits and closes the connection.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM receipts")
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign keys
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


class ReceiptDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def insert_receipt(self, receipt: Receipt) -> tuple[bool, str]:
        """
        Insert a receipt and its items into the database.

        Args:
            receipt: Receipt object to insert

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if receipt already exists
            self.cursor.execute("""
                SELECT id FROM receipts
                WHERE date = ? AND time = ? AND bon_nr = ?
            """, (receipt.date, receipt.time, receipt.bon_nr))

            existing = self.cursor.fetchone()
            if existing:
                return (False, f"Receipt already exists (Date: {receipt.date}, Time: {receipt.time}, Bon: {receipt.bon_nr})")

            # Insert receipt
            self.cursor.execute("""
                INSERT INTO receipts (
                    store_name, address, city, uid_nr, total_amount,
                    change, payment_methode, taxes, date, time, bon_nr, amount_given
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receipt.store_name,
                receipt.address,
                receipt.city,
                receipt.uid_nr,
                receipt.total_amount,
                receipt.change,
                receipt.payment_methode,
                receipt.taxes,
                receipt.date,
                receipt.time,
                receipt.bon_nr,
                receipt.amount_given
            ))

            receipt_id = self.cursor.lastrowid

            # Insert items
            for item in receipt.items:
                self.cursor.execute("""
                    INSERT INTO items (
                        receipt_id, name, price_per_unit, quantity, total, date, time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    receipt_id,
                    item.name,
                    item.price_per_unit,
                    item.quantity,
                    item.total,
                    receipt.date,
                    receipt.time
                ))

            self.conn.commit()
            return (True, f"Successfully inserted receipt with {len(receipt.items)} items (ID: {receipt_id})")

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return (False, f"Database integrity error: {str(e)}")
        except Exception as e:
            self.conn.rollback()
            return (False, f"Error inserting receipt: {str(e)}")

    def insert_receipts_batch(self, receipts: List[Receipt]) -> dict:
        """
        Insert multiple receipts into the database.

        Args:
            receipts: List of Receipt objects to insert

        Returns:
            dict: Statistics about the insertion (success_count, duplicate_count, error_count, messages)
        """
        stats = {
            'success_count': 0,
            'duplicate_count': 0,
            'error_count': 0,
            'messages': []
        }

        for i, receipt in enumerate(receipts, 1):
            success, message = self.insert_receipt(receipt)

            if success:
                stats['success_count'] += 1
                stats['messages'].append(f"[{i}/{len(receipts)}] ✓ {message}")
            elif "already exists" in message:
                stats['duplicate_count'] += 1
                stats['messages'].append(f"[{i}/{len(receipts)}] ⊗ Skipped duplicate: {receipt.date} {receipt.time} Bon:{receipt.bon_nr}")
            else:
                stats['error_count'] += 1
                stats['messages'].append(f"[{i}/{len(receipts)}] ✗ {message}")

        return stats

    def get_receipt_by_id(self, receipt_id: int) -> Receipt:
        """
        Retrieve a receipt by its ID.

        Args:
            receipt_id: Database ID of the receipt

        Returns:
            Receipt object or None if not found
        """
        self.cursor.execute("""
            SELECT store_name, address, city, uid_nr, total_amount,
                   change, payment_methode, taxes, date, time, bon_nr, amount_given
            FROM receipts WHERE id = ?
        """, (receipt_id,))

        row = self.cursor.fetchone()
        if not row:
            return None

        # Get items for this receipt
        self.cursor.execute("""
            SELECT name, price_per_unit, quantity, total
            FROM items WHERE receipt_id = ?
        """, (receipt_id,))

        items = [Item(name=item[0], price_per_unit=item[1], quantity=item[2], total=item[3])
                 for item in self.cursor.fetchall()]

        return Receipt(
            store_name=row[0],
            address=row[1],
            city=row[2],
            uid_nr=row[3],
            total_amount=row[4],
            change=row[5],
            payment_methode=row[6],
            taxes=row[7],
            date=row[8],
            time=row[9],
            bon_nr=row[10],
            amount_given=row[11],
            items=items
        )

    def get_all_receipts(self) -> List[Receipt]:
        """
        Retrieve all receipts from the database.

        Returns:
            List of Receipt objects
        """
        self.cursor.execute("SELECT id FROM receipts ORDER BY date DESC, time DESC")
        receipt_ids = [row[0] for row in self.cursor.fetchall()]

        return [self.get_receipt_by_id(rid) for rid in receipt_ids]


def save_receipts_to_database(receipts: List[Receipt], db_path: str = DEFAULT_DB_PATH) -> dict:
    """
    Save a list of receipts to the database.

    Args:
        receipts: List of Receipt objects to save
        db_path: Path to SQLite database file

    Returns:
        dict: Statistics about the save operation
    """
    with ReceiptDatabase(db_path) as db:
        stats = db.insert_receipts_batch(receipts)

    # Print summary
    print("\n" + "=" * 60)
    print("DATABASE UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Total receipts processed: {len(receipts)}")
    print(f"Successfully inserted:    {stats['success_count']}")
    print(f"Duplicates skipped:       {stats['duplicate_count']}")
    print(f"Errors:                   {stats['error_count']}")
    print("=" * 60)

    if stats['messages']:
        print("\nDetailed Results:")
        for msg in stats['messages']:
            print(msg)
        print("=" * 60)

    return stats
