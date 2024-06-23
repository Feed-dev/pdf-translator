import fitz
from googletrans import Translator
from fpdf import FPDF
import io
from PIL import Image
import os
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Custom PDF class to use DejaVuSans font
class UnicodePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)

    def header(self):
        pass

    def footer(self):
        pass


def process_pdf(input_path):
    try:
        doc = fitz.open(input_path)
        return doc
    except Exception as e:
        logger.error(f"Error opening PDF file: {e}")
        raise


def extract_content(page):
    try:
        text = page.get_text("blocks")
        images = page.get_images()
        return text, images
    except Exception as e:
        logger.error(f"Error extracting content from page: {e}")
        raise


def translate_text(text, dest_lang):
    translator = Translator()
    try:
        translated = translator.translate(text, dest=dest_lang)
        return translated.text
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text  # Return original text if translation fails


def create_translated_pdf(original_doc, translated_content):
    pdf = UnicodePDF()
    for page_num, content in enumerate(translated_content):
        pdf.add_page()
        for block in content['text']:
            pdf.set_xy(block[0], block[1])
            pdf.set_font("DejaVu", size=10)
            pdf.multi_cell(block[2] - block[0], 5, block[4])
        for img in content['images']:
            try:
                pdf.image(img['data'], x=img['x'], y=img['y'], w=img['w'], h=img['h'])
            except Exception as e:
                logger.warning(f"Error adding image to PDF: {e}")
    return pdf


def translate_pdf(input_path, output_path, target_lang):
    try:
        doc = process_pdf(input_path)
        translated_content = []

        with tqdm(total=len(doc), desc="Translating pages") as pbar:
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_page = {executor.submit(process_page, page, target_lang): page for page in doc}
                for future in as_completed(future_to_page):
                    translated_content.append(future.result())
                    pbar.update(1)

        translated_pdf = create_translated_pdf(doc, translated_content)
        translated_pdf.output(output_path)
        logger.info(f"Translated PDF saved as: {output_path}")
    except Exception as e:
        logger.error(f"Error in translate_pdf: {e}")
        raise


def process_page(page, target_lang):
    text, images = extract_content(page)
    translated_text = [translate_text(block[4], target_lang) for block in text]
    return {
        'text': [(*block[:4], translated) for block, translated in zip(text, translated_text)],
        'images': [{'data': io.BytesIO(page.parent.extract_image(img[0])["image"]),
                    'x': img[1], 'y': img[2], 'w': img[3], 'h': img[4]}
                   for img in images]
    }


if __name__ == "__main__":
    # Set the input PDF path here
    input_pdf = r"F:\myCode\pdf_translator_eng_spa\dream-psychology.pdf"  # Use raw string literal

    # Set the target language here (use ISO 639-1 two-letter language code)
    target_language = 'es'  # 'es' for Spanish, 'fr' for French, 'de' for German, etc.

    if not os.path.exists(input_pdf):
        logger.error(f"Error: The file '{input_pdf}' does not exist.")
        exit(1)

    input_dir = os.path.dirname(input_pdf)
    input_filename = os.path.basename(input_pdf)
    output_filename = f"translated_{input_filename}"
    output_pdf = os.path.join(input_dir, output_filename)

    try:
        translate_pdf(input_pdf, output_pdf, target_language)
    except Exception as e:
        logger.error(f"An error occurred during PDF translation: {e}")
        exit(1)
