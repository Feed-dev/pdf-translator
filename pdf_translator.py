import fitz  # PyMuPDF
from PIL import Image
import io
import os
import tempfile
from googletrans import Translator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Set your input path here (use raw string for Windows paths)
INPUT_PDF_PATH = r"your/path/here.pdf"


def get_output_path(input_path):
    """Generate output path based on input path"""
    dir_name = os.path.dirname(input_path)
    file_name = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(dir_name, f"{file_name}_spanish.pdf")


def get_pdf_title(doc):
    """Extract the title from PDF metadata or generate from filename"""
    metadata = doc.metadata
    if metadata and metadata.get('title'):
        return metadata['title']
    return os.path.splitext(os.path.basename(INPUT_PDF_PATH))[0].replace('_', ' ').title()


def safe_translate(translator, text, src='en', dest='es'):
    """Safely translate text, handling potential errors"""
    try:
        if not text.strip():
            return ""
        return translator.translate(text, src=src, dest=dest).text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


def translate_pdf(input_path):
    # Initialize translator
    translator = Translator()

    # Open the input PDF
    doc = fitz.open(input_path)

    # Get and translate the PDF title
    original_title = get_pdf_title(doc)
    translated_title = safe_translate(translator, original_title)

    # Generate output path
    output_path = get_output_path(input_path)

    # Create a new PDF document
    pdf = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title page
    story.append(Paragraph(translated_title, styles['Title']))
    story.append(PageBreak())

    # Create a temporary directory to store images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Translate text
            translated_text = safe_translate(translator, text)

            # Add translated text to story
            for paragraph in translated_text.split('\n'):
                if paragraph.strip():
                    story.append(Paragraph(paragraph, styles['Normal']))

            # Extract images
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Open image with PIL
                img = Image.open(io.BytesIO(image_bytes))

                # Save image to a temporary file
                img_path = os.path.join(temp_dir, f"temp_img_{page_num}_{img_index}.png")
                img.save(img_path)

                # Add image to story
                img = RLImage(img_path, width=6 * inch, height=4 * inch, kind='proportional')
                story.append(img)

            story.append(PageBreak())

        # Build the PDF
        pdf.build(story)

    print(f"Translation complete. Output saved to {output_path}")
    print(f"Original title: {original_title}")
    print(f"Translated title: {translated_title}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_PDF_PATH):
        print(f"Error: Input file '{INPUT_PDF_PATH}' does not exist.")
    else:
        translate_pdf(INPUT_PDF_PATH)