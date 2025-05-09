from together import Together
import PyPDF2
import tiktoken
from txt_to_blocks import count_tokens, split_by_tokens, extract_text_from_pdf
import json
import re
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# # === Настройки ===
# PDF_PATH = "/Users/timursaitbatalov/Downloads/978-5-7996-1198-9_2014.pdf"  # путь к вашему PDF
# TOKEN_LIMIT = 4000
# ENCODING_NAME = "cl100k_base"  # для GPT-4 и GPT-3.5-turbo

# # === Инициализация токенизатора ===
# encoding = tiktoken.get_encoding(ENCODING_NAME)

# full_text = extract_text_from_pdf(PDF_PATH)
# blocks = split_by_tokens(full_text, TOKEN_LIMIT)

# print(blocks[1])
api_key = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=api_key)


def fix_invalid_escapes(s: str) -> str:
    """
    Исправляет недопустимые escape-последовательности и управляющие символы в строке.
    
    Args:
        s: Исходная строка, возможно содержащая недопустимые символы
    
    Returns:
        Очищенная строка, пригодная для JSON
    """
    # Разрешённые escape-последовательности в JSON
    valid_escapes = {'"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'}
    
    # 1. Сначала заменяем недопустимые escape-последовательности
    def replacer(match):
        escape_seq = match.group(0)  # например \z
        next_char = escape_seq[1]
        if next_char not in valid_escapes:
            return next_char  # просто удаляем обратный слэш
        return escape_seq  # оставляем как есть
    
    s = re.sub(r'\\.', replacer, s)
    
    # 2. Затем удаляем оставшиеся управляющие символы (кроме разрешённых)
    # Разрешённые управляющие символы: \t, \n, \r
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', s)
    
    return s
def get_small_chapter(structure):
    prompt = f"""
Я тебе скину словарь, твоя задача — сократить главу, по которой будут учиться студенты.

Представь, что ты студент и не хочешь читать дословный пересказ книги, а хочешь понятное, структурированное объяснение. Именно таким должен быть `content` — не копия текста, а адаптированный учебный материал.

Может быть такое, что глав две, тогда тебе надо соединить в одну главу и скоратить информацию.

🔹 Формат вывода:
[
  {{
    "chapter_id": "id главы",
    "title": "название главы",
    "content": "здесь глава, по которой будут учиться студенты (title сюда писать не надо)",
    "status": "complete"
  }}
]
Важные правила:

В случае если глав отправленно две, тогда в chapter_id не надо указывать сразу две главы, как пример 3-4, надо указать первую, то есть 3.

Маркируй content, чтобы в дальнейшем я смог использовать его в формате markdown.

Ответ только JSON — никаких пояснений, комментариев и лишнего текста.

Все строки — в двойных кавычках ("), в том числе ключи и значения JSON.

Максимум 900 слов на весь ответ.

Вот словарь:
{structure}
"""
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def get_chapter(block, structure):
    prompt = f"""
Я тебе скину материал, твоя задача — создать главу, по которой будут учиться студенты.

Я тебе передаю блоки книги. Может быть такое, что в конце текст резко обрывается — в этом случае тебе нужно логически завершить текущую главу, описав только то, что есть, и начать следующую главу, указав в её статусе `"incomplete"`. В следующем запросе я передам продолжение.

Представь, что ты студент и не хочешь читать дословный пересказ книги, а хочешь понятное, структурированное объяснение. Именно таким должен быть `content` — не копия текста, а адаптированный учебный материал.

🔹 Формат вывода:
[
  {{
    "chapter_id": "id главы",
    "title": "название главы",
    "content": "здесь глава, по которой будут учиться студенты (title сюда писать не надо)",
    "status": "complete" или "incomplete"
  }},
  ...
]
Важные правила:

Маркируй content, чтобы в дальнейшем я смог использовать его в формате markdown.

Ответ только JSON — никаких пояснений, комментариев и лишнего текста.

Все строки — в двойных кавычках ("), в том числе ключи и значения JSON.

Максимум 900 слов на весь ответ.

Лучше сделать мало, но объёмных глав.

За один раз можешь сгенерировать 1 или 2 главы:

Если 1 глава — до 800 слов.

Если 2 главы — до 400 слов на каждую.

{structure}
Вот материал:
{block}"""
    
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_quiz_for_chapter(chapter):
    prompt = '''Твоя задача загенерировать вопросы в следующем формате:
{"questions": [{"question": "Текст вопроса","options": ["вариант1", "вариант2", "вариант3", "вариант4"],"correct_answer": "номер правильного вопроса (начинается с 1)","type": "single","explanation": "Объяснение"},...]}"""
Выведи все в одну строчку.
Вот материал, по которому ты должен все загенерировать: ''' + chapter
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content