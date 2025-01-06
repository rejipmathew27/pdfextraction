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
import pdf2image
import pytesseract
from pytesseract import Output, TesseractError
from PIL import Image


@st.cache_data  # Cache the results for faster processing
def images_to_txt(path, language):
    if path.name.endswith('.pdf'):
        images = pdf2image.convert_from_bytes(path.read())
    else:  # Assuming it's an image file
        image = Image.open(path)
        images = [image]
    all_text = []
    for i in images:
        pil_im = i
        text = pytesseract.image_to_string(pil_im, lang=language)
        all_text.append(text)
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

@st.cache_data  # Cache the results for faster processing
def save_pages(pages):
    # Create the directory if it doesn't exist
    if not os.path.exists("./file_pages"):
        os.makedirs("./file_pages")

    files = []
    for page in range(len(pages)):
        filename = "page_"+str(page)+".txt"
        with open("./file_pages/"+filename, 'w', encoding="utf-8") as file:
            file.write(pages[page])
            files.append(file.name)
    
    zipPath = './file_pages/pdf_to_txt.zip'
    zipObj = ZipFile(zipPath, 'w')
    for f in files:
        zipObj.write(f)
    zipObj.close()

    return zipPath

def displayPDF(file):
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def displayImage(file):
    st.image(file, caption='Uploaded Image', use_column_width=True)

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
            texts, nbPages = convert_pdf_to_txt_pages(uploaded_file) 
            # Or use convert_pdf_to_txt_file(uploaded_file) to get all text at once

            # Display or process the extracted text
            st.write(f"The file has {nbPages} pages")
            for i in range(len(texts)):
                st.write(f"Page {i+1}:")
                st.write(texts[i])

            # Example of saving the extracted text to a zip file
            zip_path = save_pages(texts)
            with open(zip_path, "rb") as fp:
                btn = st.download_button(
                    label="Download ZIP",
                    data=fp,
                    file_name="pdf_to_txt.zip",
                    mime="application/zip"
                )

        elif option == "OCR":
            # Extract text using OCR
            language = st.text_input("Enter language code (e.g., 'eng' for English):", "eng")
            all_text, nbPages = images_to_txt(uploaded_file, language)

            # Display or process the extracted text
            if uploaded_file.name.endswith('.pdf'):
                st.write(f"The pdf file has {nbPages} pages")
            else:
                st.write(f"The image file has {nbPages} pages")
            for i in range(len(all_text)):
                st.write(f"Page {i+1}:")
                st.write(all_text[i])
