import json
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from database.operations import create_tables, insert_chunks, get_untranslated_chunks, save_translated_chunk, save_translation_to_file, update_chunk_status, clear_tables
from typing import List, Tuple

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

# Access config values
file_name = config['file_name']
src_lang = config['src_lang']
target_lang = config['target_lang']

# Model setup
model_name = 'facebook/m2m100_418M'
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

tokenizer.src_lang = src_lang
target_lang = target_lang

# Create tables
create_tables()

# Helper function to split text into manageable chunks
def split_text(text: str, max_length: int = 512) -> List[str]:
    sentences = text.split('. ')
    chunks = []
    chunk = ''

    for sentence in sentences:
        if len(chunk) + len(sentence) <= max_length:
            chunk += f'{sentence}. '
        else:
            chunks.append(chunk.strip())
            chunk = f'{sentence}. '

    if chunk:
        chunks.append(chunk.strip())

    return chunks

# Insert text chunks into the database
def insert_book_chunks() -> None:
    with open(f'./resources/{file_name}', 'r', encoding='utf-8') as file:
        book_text = file.read()

    chunks = split_text(book_text)
    insert_chunks(chunks)

# Translate chunks and save results to the database
def translate_and_store_chunks() -> bool:
    untranslated_chunks = get_untranslated_chunks()

    for row in untranslated_chunks:
        chunk_id, chunk_text = row

        try:
            # Translate the chunk
            inputs = tokenizer(chunk_text, return_tensors='pt', padding=True)
            generated_tokens = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id[target_lang])
            translated_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)

            # Save translated text to the translated_chunks table
            save_translated_chunk(translated_text)

            # Update status of original chunk
            update_chunk_status(chunk_id)

        except Exception as e:
            print(f'Error translating chunk with ID {chunk_id}: {e}')
            return False

    return True

# Write all translated chunks to a file and clean tables if successful
def save_translation() -> None:
    save_translation_to_file(file_name=file_name, target_lang=target_lang)
    clear_tables()

# Main function
def main() -> None:
    # Step 1: Insert book text chunks into the database
    insert_book_chunks()

    # Step 2: Translate and store chunks in the database
    success = translate_and_store_chunks()

    # Step 3: Save translation to file and clear tables if successful
    if success:
        save_translation()
    else:
        print('Translation failed; check error messages for failed chunk IDs.')

# Run the main function
if __name__ == '__main__':
    main()
