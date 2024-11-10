import os
import sqlite3
from typing import List, Tuple

# Database path setup
db_directory = 'database'

if not os.path.exists(db_directory):
    os.makedirs(db_directory)

db_name = os.path.join(db_directory, 'translation.db')


# Connect to the database
def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_name)
    return conn


# Create tables
def create_tables() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk TEXT NOT NULL,
        status INTEGER CHECK(status IN (0, 1)) DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS translated_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        translated_chunk TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()


# Insert chunks into the database
def insert_chunks(chunks: List[str]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    for chunk in chunks:
        cursor.execute('INSERT INTO chunks (chunk) VALUES (?)', (chunk,))

    conn.commit()
    conn.close()


# Update chunk status to 'translated'
def update_chunk_status(chunk_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE chunks SET status=1 WHERE id=?', (chunk_id,))
    conn.commit()
    conn.close()


# Retrieve untranslated chunks
def get_untranslated_chunks() -> List[Tuple[int, str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, chunk FROM chunks WHERE status=0')
    rows = cursor.fetchall()
    conn.close()
    return rows


# Save translated chunks to the database
def save_translated_chunk(translated_chunk: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO translated_chunks (translated_chunk) VALUES (?)', (translated_chunk,))
    conn.commit()
    conn.close()


# Save all translated chunks to a file
def save_translation_to_file(file_name: str, target_lang: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT translated_chunk FROM translated_chunks')
    all_translations = [row[0] for row in cursor.fetchall()]
    conn.close()

    file_path = f"./output/{file_name.replace('.txt', f'-{target_lang}.txt')}"
    # Write to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(all_translations))

    print(f'Translation saved to {file_path}.')


# Clean database tables
def clear_tables() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chunks')
    cursor.execute('DELETE FROM translated_chunks')
    conn.commit()
    conn.close()
