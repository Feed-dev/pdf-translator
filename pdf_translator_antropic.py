import fitz
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
    images = page.get_images()
    return text, images


def translate_text(text, dest_lang='es'):
    translator = Translator()
    translated = translator.translate(text, dest=dest_lang)
    return translated.text


def create_translated_pdf(original_doc, translated_content):
    pdf = FPDF()
    for page_num, content in enumerate(translated_content):
        pdf.add_page()
        for block in content['text']:
            pdf.set_xy(block[0], block[1])
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(block[2] - block[0], 5, block[4])
        for img in content['images']:
            pdf.image(img['data'], x=img['x'], y=img['y'], w=img['w'], h=img['h'])
    return pdf


def translate_pdf(input_path, output_path):
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

    translated_pdf = create_translated_pdf(doc, translated_content)
    translated_pdf.output(output_path)
    print(f"Translated PDF saved as: {output_path}")


if __name__ == "__main__":
    # Set the input PDF path here
    input_pdf = r"F:\myCode\pdf_translator_eng_spa\dream-psychology.pdf"  # Use raw string literal

    if not os.path.exists(input_pdf):
        print(f"Error: The file '{input_pdf}' does not exist.")
        exit(1)

    input_dir = os.path.dirname(input_pdf)
    input_filename = os.path.basename(input_pdf)
    output_filename = f"translated_{input_filename}"
    output_pdf = os.path.join(input_dir, output_filename)

    translate_pdf(input_pdf, output_pdf)
