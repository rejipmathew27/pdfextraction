import streamlit as st
from zipfile import ZipFile
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import base64
import os
#------- OCR ------------
import easyocr
import pdf2image
from PIL import Image

def images_to_txt(path, language):
    if path.name.endswith('.pdf'):
        images = pdf2image.convert_from_bytes(path.read())
    else:  # Assuming it's an image file
        image = Image.open(path)
        images = [image]
    
    reader = easyocr.Reader([language])
    all_text = []
    for img in images:
        result = reader.readtext(img)

        lines = []
        current_line = ""
        current_line_y = None
        for bbox, text, conf in result:
            (top_left, top_right, bottom_right, bottom_left) = bbox
            y = (top_left[1] + bottom_left[1]) / 2  # Average y-coordinate

            if current_line_y is None:
                current_line_y = y
            elif abs(y - current_line_y) > 10:  # New line detected (adjust threshold as needed)
                lines.append(current_line.strip())
                current_line = ""
                current_line_y = y

            current_line += text + " "

        lines.append(current_line.strip())  # Add the last line
        all_text.append("\n".join(lines))

    return all_text, len(all_text)


@st.cache_data  # Cache the results for faster processing
def convert_pdf_to_txt_pages(path):
    texts = []
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    size = 0
    c = 0
    file_pages = PDFPage.get_pages(path)
    nbPages = len(list(file_pages))
    for page in PDFPage.get_pages(path):
        interpreter.process_page(page)
        t = retstr.getvalue()
        if c == 0:
            texts.append(t)
        else:
            texts.append(t[size:])
        c = c+1
        size = len(t)
    device.close()
    retstr.close()
    return texts, nbPages

@st.cache_data  # Cache the results for faster processing
def convert_pdf_to_txt_file(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    file_pages = PDFPage.get_pages(path)
    nbPages = len(list(file_pages))
    for page in PDFPage.get_pages(path):
        interpreter.process_page(page)
        t = retstr.getvalue()

    device.close()
    retstr.close()
    return t, nbPages

def displayPDF(file):
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def displayImage(file):
    # Use use_container_width=True to retain width
    st.image(file, caption='Uploaded Image', use_container_width=True)


# --- Streamlit App ---

st.title("PDF/Image to Text Converter")

uploaded_file = st.file_uploader("Choose a PDF or JPG file", type=["pdf", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display the uploaded file
    if uploaded_file.name.endswith('.pdf'):
        displayPDF(uploaded_file)
    elif uploaded_file.name.lower().endswith(('.jpg', '.jpeg')):
        displayImage(uploaded_file)

    # Extract text from the file
    with st.spinner("Extracting text..."):
        # Option to choose between OCR or PDFMiner (for PDFs)
        if uploaded_file.name.endswith('.pdf'):
            option = st.radio("Choose extraction method:", ("PDFMiner", "OCR"))
        else:
            option = "OCR"  # For images, use OCR directly

        if option == "PDFMiner":
            # Extract text using PDFMiner
            full_text, nbPages = convert_pdf_to_txt_file(uploaded_file)

            # Create and download the text file
            st.download_button(
                label="Download Text",
                data=full_text,
                file_name="extracted_text.txt",
                mime="text/plain"
            )

        elif option == "OCR":
            # Extract text using OCR
            language = st.text_input("Enter language code (e.g., 'en' for English):", "en")
            all_text, nbPages = images_to_txt(uploaded_file, language)
            full_text = "\n".join(all_text)  # Combine all pages into a single string

            # Create and download the text file
            st.download_button(
                label="Download Text",
                data=full_text,
                file_name="extracted_text.txt",
                mime="text/plain"
            )
