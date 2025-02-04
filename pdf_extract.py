import os
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextContainer
from pathlib import Path
import fitz  # PyMuPDF
import pymupdf4llm


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a single PDF file.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        str: Extracted text from the PDF.
    """
    try:
        text = extract_text(pdf_path)
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""




def extract_images_from_pdf(pdf_path, images_output_path):
    """
    Extracts images from a single PDF file and saves them to the specified directory.

    Args:
        pdf_path (str): The file path to the PDF.
        images_output_path (str): The directory where extracted images will be saved.
    """
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        print(f"Opened PDF: {pdf_path}")

        # Iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)

            print(f"Found {len(image_list)} images on page {page_num + 1}")

            # Iterate through each image
            for img_index, img in enumerate(image_list, start=1):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"page{page_num + 1}_image{img_index}.{image_ext}"
                image_filepath = os.path.join(images_output_path, image_filename)

                # Save the image
                with open(image_filepath, "wb") as image_file:
                    image_file.write(image_bytes)

                print(f"Saved image: {image_filepath}")

        pdf_document.close()
    except Exception as e:
        print(f"Error extracting images from {pdf_path}: {e}")

def extract_text_with_positions(pdf_path):
    """
    Extracts text elements along with their bounding boxes from a PDF.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        dict: A dictionary where keys are page numbers and values are lists of tuples containing text and its bounding box.
    """
    pages_text = {}
    for page_layout in extract_pages(pdf_path):
        page_number = page_layout.pageid
        texts = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    text = text_line.get_text().strip()
                    if text:
                        bbox = text_line.bbox  # (x0, y0, x1, y1)
                        texts.append((text, bbox))
        pages_text[page_number] = texts
    return pages_text

def extract_drawings_from_pdf(pdf_path, drawings_output_path,table_dir="up"):
    """
    Extracts vector drawings (e.g., TikZ diagrams) from a PDF by rendering regions around figure captions.

    Args:
        pdf_path (str): The file path to the PDF.
        drawings_output_path (str): The directory where extracted drawings will be saved.
    """
    import fitz  # PyMuPDF

    # Ensure output directory exists
    os.makedirs(drawings_output_path, exist_ok=True)

    # Extract text with positions
    pages_text = extract_text_with_positions(pdf_path)

    # Open the PDF with PyMuPDF
    doc = fitz.open(pdf_path)

    for page_num, texts in pages_text.items():
        page = doc[page_num - 1]  # Pages are 0-indexed in PyMuPDF
        id =0
        id_tab=0
        for text, bbox in texts:
            if text.lower().startswith("figure") or text.lower().startswith("fig"):
                id+=1
                # Define the region around the caption to capture the drawing
                # Adjust the distance and size as needed
                x0, y0, x1, y1 = bbox
                # Define a margin to include objects below the caption
                margin = 75  # in points; adjust based on your PDF's layout

                # Get the page's dimensions
                page_width = page.rect.width
                page_height = page.rect.height

                # Define the rectangle for the figure
                figure_rect = fitz.Rect(
                    x0-10,  # left
                    max(0,page_height-y1-3*margin),
                    x1+10,  # right
                    min(page_height-y0+margin, page_height)  # bottom, limited by page height
                )
                # Render the figure region as an image
                pix = page.get_pixmap(clip=figure_rect,dpi=400)
                figure_filename = f"{drawings_output_path[-7:-4]}_page{page_num}_figure{id}.png"
                figure_filepath = os.path.join(drawings_output_path, figure_filename)
                #convert to png
                pix.save(figure_filepath)
                # print(f"Saved drawing: {figure_filepath}")
            if text.lower().startswith("table"):
                id_tab+=1
                # Define the region around the caption to capture the drawing
                # Adjust the distance and size as needed
                x0, y0, x1, y1 = bbox
                # Define a margin to include objects below the caption
                margin = 40  # in points; adjust based on your PDF's layout

                # Get the page's dimensions
                page_width = page.rect.width
                page_height = page.rect.height

                # Define the rectangle for the figure
                figure_rect = fitz.Rect(
                    0,#x0-margin,  # left
                    max(0,page_height-y1-margin) if table_dir=="down" else max(0,page_height-y1-5*margin),  # top
                    page_width,#x1+margin,  # right
                    min(page_height-y0+5*margin, page_height) if table_dir=="down" else min(page_height-y0+margin, page_height)  # bottom, limited by page height
                )
                # Render the figure region as an image
                pix = page.get_pixmap(clip=figure_rect,dpi=400)
                figure_filename = f"{drawings_output_path[-7:-4]}_page{page_num}_table{id_tab}.png"
                figure_filepath = os.path.join(drawings_output_path, figure_filename)
                pix.save(figure_filepath)
                # print(f"Saved drawing: {figure_filepath}"

    doc.close()



def extract_texts_from_folder(folder_path, output_folder=None):
    """
    Extracts text from all PDF files in the specified folder.

    Args:
        folder_path (str): The path to the folder containing PDF files.
        output_folder (str, optional): The folder where extracted text files will be saved.
                                       If None, texts will be printed to the console.
    """
    # Ensure the folder path exists
    if not os.path.isdir(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    # Create the output folder if specified and doesn't exist
    if output_folder:
        if output_folder:
            os.makedirs(output_folder, exist_ok=True)
            figures_folder = os.path.join(output_folder, "figures")
            os.makedirs(figures_folder, exist_ok=True)

    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            text_filename = Path(filename).stem + '.md'
            text_path = os.path.join(output_folder, text_filename)
            ref_path = os.path.join(output_folder, Path(filename).stem + '_ref.md')

            if os.path.exists(text_path) and os.path.exists(ref_path):
                print(f"Skipping {filename} as text and reference files already exist.")
                continue

            pdf_path = os.path.join(folder_path, filename)
            print(f"Processing: {pdf_path}")
            text = extract_text_from_pdf(pdf_path)

            text_split = text.split("References")
            if len(text_split)!=2:
                text_split = text.split("REFERENCES")
            if len(text_split)!=2:
                print("no ref")



            if output_folder:
                # Define the output text file path
                

                # Write the extracted text to the file
                try:
                    with open(text_path, 'w', encoding='utf-8') as text_file:
                        text_file.write(text_split[0])
                    with open(ref_path, 'w', encoding='utf-8') as text_file:
                        text_file.write(text_split[1])
                    # print(f"Extracted text saved to: {text_path}")
                except Exception as e:
                    print(f"Error writing text to {text_path}: {e}")
            else:
                # If no output folder specified, print the text
                print(f"\n--- Text from {filename} ---\n")
                print(text)
                print(f"--- End of {filename} ---\n")
            if output_folder:
                # # Create a subfolder for images of this PDF
                # pdf_images_folder = os.path.join(images_folder, Path(filename).stem)
                # os.makedirs(pdf_images_folder, exist_ok=True)
                # extract_images_from_pdf(pdf_path, pdf_images_folder)

                drawings_output_path = os.path.join(figures_folder, Path(filename).stem)
                os.makedirs(drawings_output_path, exist_ok=True)
                extract_drawings_from_pdf(pdf_path, drawings_output_path)

def format_arxiv_id(scrambled_text):
    #find the id of the pattern "arXiv" with pattern matching
    import re
    first_id = re.search(r"arXiv", scrambled_text)
    if first_id:
        first_id = first_id.start()
    else:
        return scrambled_text
    # Extract components using string slicing
    correct_text = scrambled_text[first_id:]
    arxiv_id = correct_text[5:19]  # Extract arXiv ID
    category = correct_text[19:25]  # Extract category
    date = correct_text[25:]  # Extract date part
    
    # Format components into standard format
    formatted_text = f"arXiv:{arxiv_id} [{category}] {date}"
    
    return formatted_text


def extract_single_pdf(pdf_path,figures_folder, output_folder,table_dir="up"):
    """
    Processes a single PDF file to extract text, images, and drawings.

    Args:
        pdf_path (str): The file path to the PDF.
        output_folder (str, optional): The folder where extracted content will be saved.
    """
    filename = os.path.basename(pdf_path)
    text_filename = Path(filename).stem + '.md'
    text_path = os.path.join(output_folder, text_filename)
    ref_path = os.path.join(output_folder, Path(filename).stem + '_ref.md')

    if os.path.exists(text_path) and os.path.exists(ref_path):
        print(f"Skipping extraction {filename} as text and reference files already exist.")
        return

    print(f"Processing: {pdf_path}")
    # text = extract_text_from_pdf(pdf_path)
    text = pymupdf4llm.to_markdown(pdf_path)

    text_split = text.split("References")
    if len(text_split)!=2:
        text_split = text.split("REFERENCES")
    if len(text_split)!=2:
        print("no ref")

    arxiv_header = ''.join(text_split[0][:100].split())[::-1]
    text_split[0] = format_arxiv_id(arxiv_header) + text_split[0][100:]



    if output_folder:
        try:
            with open(text_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text_split[0])
            with open(ref_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text_split[1])
        except Exception as e:
            print(f"Error writing text to {text_path}: {e}")
    else:
        print(f"\n--- Text from {filename} ---\n")
        print(text)
        print(f"--- End of {filename} ---\n")

    if output_folder:
        drawings_output_path = os.path.join(figures_folder, Path(filename).stem)
        os.makedirs(drawings_output_path, exist_ok=True)
        extract_drawings_from_pdf(pdf_path, drawings_output_path,table_dir=table_dir)



def main():
    """
    Main function to execute the script.
    """
    # Define the folder containing PDFs
    pdf_folder = "/home/pmarrec/vault/Knowledge/automation/PDF_inbox"

    # Define the output folder for extracted texts
    output_text_folder = "/home/pmarrec/vault/Knowledge/automation/pdf_raw"

    extract_texts_from_folder(pdf_folder, output_text_folder)
    # extract_text_and_figures_from_folder(pdf_folder, output_text_folder)

if __name__ == "__main__":
    main()


