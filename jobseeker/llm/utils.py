import PyPDF2
import re

def extract_text(pdf_path: str):
    resume_text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)

        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text().split("\n")

            # Remove Unicode characters from each line
            cleaned_text = [re.sub(r'[^\x00-\x7F]+', '', line) for line in text]

            # Join the lines into a single string
            cleaned_text_string = '\n'.join(cleaned_text)
            resume_text += cleaned_text_string
        
        return resume_text