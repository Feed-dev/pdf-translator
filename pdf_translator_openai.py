import fitz  # PyMuPDF
from googletrans import Translator
from fpdf import FPDF
import io
from PIL import Image
import os
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_pdf(input_path):
    try:
        doc = fitz.open(input_path)
        return doc
    except Exception as e:
        logging.error(f"Error opening PDF: {e}")
        raise


def extract_content(page):
    try:
        text = page.get_text("blocks")
        images = page.get_images(full=True)
        return text, images
    except Exception as e:
        logging.error(f"Error extracting content from page: {e}")
        raise


def translate_texts(texts, dest_lang='es'):
    try:
        translator = Translator()
        translations = translator.translate(texts, dest=dest_lang)
        return [translation.text for translation in translations]
    except Exception as e:
        logging.error(f"Error translating text: {e}")
        raise


def create_translated_pdf(original_doc, translated_content, output_path):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 10)

        for page_num, content in enumerate(translated_content):
            pdf.add_page()
            for block in content['text']:
                x, y, w, h, text = block
                pdf.set_xy(x, y)
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
        logging.info(f"Translated PDF created at {output_path}")
    except Exception as e:
        logging.error(f"Error creating translated PDF: {e}")
        raise


def translate_pdf(input_path, target_lang='es'):
    try:
        output_path = os.path.splitext(input_path)[0] + f"_{target_lang}.pdf"
        doc = process_pdf(input_path)
        translated_content = []

        logging.info("Starting translation process...")
        for page in tqdm(doc, desc="Translating pages"):
            text, images = extract_content(page)
            texts_to_translate = [block[4] for block in text]
            translated_texts = translate_texts(texts_to_translate, dest_lang=target_lang)
            translated_content.append({
                'text': [(*block[:4], translated) for block, translated in zip(text, translated_texts)],
                'images': [{'data': io.BytesIO(doc.extract_image(img[0])["image"]),
                            'x': img[1], 'y': img[2], 'w': img[3], 'h': img[4]}
                           for img in images]
            })

        create_translated_pdf(doc, translated_content, output_path)
        logging.info("Translation process completed successfully.")
    except Exception as e:
        logging.error(f"Error in translation process: {e}")
        raise


if __name__ == "__main__":
    input_pdf = r"F:\myCode\pdf_translator_eng_spa\dream-psychology.pdf"  # Using raw string literal
    target_language = 'es'  # You can change this to any language code supported by Google Translate
    translate_pdf(input_pdf, target_language)
