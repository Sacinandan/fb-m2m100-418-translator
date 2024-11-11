import json
from typing import List
from tqdm import tqdm
from colorama import Fore, Style

from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from database.operations import create_tables, insert_chunks, get_untranslated_chunks, save_translated_chunk, save_translation_to_file, update_chunk_status, clear_tables


with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)


file_name = config['file_name']
src_lang = config['src_lang']
target_lang = config['target_lang']

max_length = 512
model_name = 'facebook/m2m100_418M'
model = M2M100ForConditionalGeneration.from_pretrained(model_name)
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
tokenizer.src_lang = src_lang
target_lang = target_lang
tokenizer.model_max_length = max_length


def split_text(text: str) -> List[str]:
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


def insert_book_chunks() -> None:
    with open(f'./resources/{file_name}', 'r', encoding='utf-8') as file:
        book_text = file.read()

    chunks = split_text(book_text)
    insert_chunks(chunks)


def translate_and_store_chunks() -> bool:
    untranslated_chunks = get_untranslated_chunks()
    progress_bar = tqdm(iterable=untranslated_chunks, desc='Translating', colour = 'green')

    for row in progress_bar:
        chunk_id, chunk_text = row

        try:
            inputs = tokenizer(chunk_text, return_tensors='pt', padding=True, truncation=True, max_length=max_length)
            generated_tokens = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id[target_lang])
            translated_text = tokenizer.decode(generated_tokens[0], skip_special_tokens=True)

            save_translated_chunk(translated_text)

            update_chunk_status(int(chunk_id))

        except Exception as e:
            print(f'Error translating chunk with ID {chunk_id}: {e}')
            return False

    print(f'{Fore.GREEN}\u2713\ufe0e{Style.RESET_ALL} Done')

    return True


def save_translation() -> None:
    save_translation_to_file(file_name=file_name, target_lang=target_lang)
    clear_tables()


def main() -> None:
    create_tables()

    if len(get_untranslated_chunks()) == 0:
        insert_book_chunks()

    success = translate_and_store_chunks()
    if success:
        save_translation()
    else:
        print('Translation failed; check error messages for failed chunk IDs.')


if __name__ == '__main__':
    main()
