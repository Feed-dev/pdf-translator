import fitz  # PyMuPDF
from googletrans import Translator
from fpdf import FPDF
import io
from PIL import Image
import os


def process_pdf(input_path):
    doc = fitz.open(input_path)
    return doc


def extract_content(page):
    text = page.get_text("blocks")
    images = page.get_images(full=True)
    return text, images


def translate_text(text, dest_lang='es'):
    translator = Translator()
    translated = translator.translate(text, dest=dest_lang)
    return translated.text


def create_translated_pdf(original_doc, translated_content, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for page_num, content in enumerate(translated_content):
        pdf.add_page()
        for block in content['text']:
            x, y, w, h, text = block
            pdf.set_xy(x, y)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(w - x, 5, text)

        for img in content['images']:
            img_data = img['data']
            img_x = img['x']
            img_y = img['y']
            img_w = img['w']
            img_h = img['h']
            img_data.seek(0)  # Reset the file pointer to the beginning of the BytesIO object
            pdf.image(img_data, x=img_x, y=img_y, w=img_w, h=img_h)

    pdf.output(output_path)


def translate_pdf(input_path):
    output_path = os.path.splitext(input_path)[0] + "_spanish.pdf"
    doc = process_pdf(input_path)
    translated_content = []

    for page in doc:
        text, images = extract_content(page)
        translated_text = [translate_text(block[4]) for block in text]
        translated_content.append({
            'text': [(*block[:4], translated) for block, translated in zip(text, translated_text)],
            'images': [{'data': io.BytesIO(doc.extract_image(img[0])["image"]),
                        'x': img[1], 'y': img[2], 'w': img[3], 'h': img[4]}
                       for img in images]
        })

    create_translated_pdf(doc, translated_content, output_path)


if __name__ == "__main__":
    input_pdf = r"F:\myCode\pdf_translator_eng_spa\dream-psychology.pdf"  # Using raw string literal
    translate_pdf(input_pdf)
