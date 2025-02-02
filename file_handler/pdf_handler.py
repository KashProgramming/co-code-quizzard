import fitz
import pytesseract
from PIL import Image
import io
import camelot
import pandas as pd

def extract_pdf_content(pdf_file):
    """
    Will be used to extract text, images and tables from a pdf document
    Will also be used to extract text, images and tables from a scanned PDF using OCR
    """

    pdf_content = {
        "text": [],
        "images": [],
        "tables": []
    }

    document = fitz.open(pdf_file)

    for page_num, page in enumerate(document):
        page_text = page.get_text() # extracting text from the pdf
        if page_text.strip():  # If text exists, PDF is processed as text-based
            try: # extracting tables as pdfs and appending to the list in dictionary
                tables = camelot.read_pdf(pdf_file,pages=str(page_num+1),flavor="lattice")
                for table in tables:
                    df = pd.DataFrame(table.df.values)
                    df.columns = df.iloc[0]  # setting the first row as column headers
                    df = df.drop(0).reset_index(drop=True)
                    pdf_content["tables"].append(df)
            except Exception as e:
                print(f"No tables found on page {page_num+1}: {e}")
            pdf_content["text"].append(page_text)

            for img_index, img in enumerate(page.get_images(full=True)): # extracting images from 
                xref = img[0]
                base_image = document.extract_image(xref)
                img_bytes = base_image["image"]
                img_extension = base_image["ext"]  # to get image format to preserve transparency if needed
                # Load the image with Pillow
                image = Image.open(io.BytesIO(img_bytes))
                # Preserve transparency if the image has an alpha channel
                if image.mode in ("RGBA", "LA"):
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")
                # Save the image in its original format
                img_filename = f"{pdf_file}_page{page_num+1}_img{img_index+1}.{img_extension}"
                image.save(img_filename, format=img_extension.upper())
                pdf_content["images"].append(img_filename)
        else:
            # If no text, process as scanned PDF using OCR
            pix = page.get_pixmap()  # Render page to an image
            img = Image.open(io.BytesIO(pix.tobytes()))
            ocr_text = pytesseract.image_to_string(img)
            pdf_content["text"].append(ocr_text)
    document.close()
    return pdf_content