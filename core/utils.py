import sqlite3
import logging

def clean_transfer_database(db_path: str):
    """
    Keep only the first 50 BUY/SELL transfers that:
    - Have valid decimals
    - Do NOT have UNKNOWN symbols
    Everything else will be deleted from the raw_transfers table.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Find rowids of first 50 transfers with valid decimals and real symbol
    cursor.execute("""
        SELECT rowid FROM raw_transfers
        WHERE action IN ('BUY', 'SELL')
          AND decimals IS NOT NULL
          AND token_symbol IS NOT NULL
          AND token_symbol NOT LIKE 'UNKNOWN_%'
        ORDER BY timestamp ASC
        LIMIT 50
    """)
    keep_ids = [str(row[0]) for row in cursor.fetchall()]

    if not keep_ids:
        logging.warning("No valid transfers found with real symbols and decimals. Keeping database untouched.")
        conn.close()
        return

    # Step 2: Delete everything not in keep list
    ids_str = ",".join(keep_ids)
    cursor.execute(f"""
        DELETE FROM raw_transfers
        WHERE rowid NOT IN ({ids_str})
    """)
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    logging.info(f"🧹 Cleaned database: kept {len(keep_ids)} transfers, deleted {deleted} others.")
