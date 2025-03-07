import os

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
import argparse



def parse_md(pdf_file_name,local_md_dir,loc_image_dir="images"):

    name_without_suff = pdf_file_name.split(".")[0]
    local_image_dir = os.path.join(os.path.dirname(local_md_dir), loc_image_dir)

    image_dir = str(os.path.basename(local_image_dir))

    os.makedirs(local_image_dir, exist_ok=True)

    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
        local_md_dir
    )

    # read bytes
    reader1 = FileBasedDataReader("")
    pdf_bytes = reader1.read(pdf_file_name)  # read the pdf content

    # proc
    ## Create Dataset Instance
    ds = PymuDocDataset(pdf_bytes)

    ## inference
    if ds.classify() == SupportedPdfParseMethod.OCR:
        ds.apply(doc_analyze, ocr=True).pipe_ocr_mode(image_writer).dump_md(
        md_writer, f"{name_without_suff}.md", image_dir
    )

    else:
        ds.apply(doc_analyze, ocr=False).pipe_txt_mode(image_writer).dump_md(
        md_writer, f"{name_without_suff}.md", image_dir
    )
if __name__ == "__main__":
    # args
    # pdf_file_name = "abc.pdf"  # replace with the real pdf path
    # name_without_suff = pdf_file_name.split(".")[0]

    # # prepare env
    # local_image_dir, local_md_dir = "output/images", "output"
    # image_dir = str(os.path.basename(local_image_dir))
    parser = argparse.ArgumentParser(description="Convert PDF to markdown")
    
    parser.add_argument("pdf_file_name", type=str, help="the pdf file to convert")
    # parser.add_argument("name_without_suff", type=str, help="the name without the suffix")
    parser.add_argument("output_path", type=str, help="the local markdown directory")
    args = parser.parse_args()
    parse_md(args.pdf_file_name, args.local_md_dir)