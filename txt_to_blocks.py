import PyPDF2
import tiktoken

# === Настройки ===
PDF_PATH = "/Users/timursaitbatalov/Downloads/978-5-7996-1198-9_2014.pdf"  # путь к вашему PDF
TOKEN_LIMIT = 7500
ENCODING_NAME = "cl100k_base"  # для GPT-4 и GPT-3.5-turbo

# === Инициализация токенизатора ===
encoding = tiktoken.get_encoding(ENCODING_NAME)

def count_tokens(text):
    return len(encoding.encode(text))

def split_by_tokens(text, max_tokens):
    words = text.split()
    blocks = []
    current_block = []
    current_tokens = 0

    for word in words:
        token_count = count_tokens(word + " ")
        if current_tokens + token_count <= max_tokens:
            current_block.append(word)
            current_tokens += token_count
        else:
            blocks.append(" ".join(current_block))
            current_block = [word]
            current_tokens = token_count

    if current_block:
        blocks.append(" ".join(current_block))

    return blocks

# === Чтение PDF ===
def extract_text_from_pdf(path):
    reader = PyPDF2.PdfReader(path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    return full_text
