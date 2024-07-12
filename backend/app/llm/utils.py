import PyPDF2
import re
from io import BytesIO


def extract_text_from_pdf_bytes(pdf_data: bytes):
    resume_text = ""
    # Create a file-like object from the bytes
    file = BytesIO(pdf_data)
    pdf_reader = PyPDF2.PdfReader(file)
    num_pages = len(pdf_reader.pages)

    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        text = page.extract_text().split("\n")  # type: ignore

        # Remove Unicode characters from each line
        cleaned_text = [re.sub(r"[^\x00-\x7F]+", "", line) for line in text]

        # Join the lines into a single string
        cleaned_text_string = "\n".join(cleaned_text)
        resume_text += cleaned_text_string

    return resume_text


def get_columns(model, column_names):
    return [getattr(model, attr) for attr in column_names]
