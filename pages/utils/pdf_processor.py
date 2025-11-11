import fitz  # PyMuPDF
import streamlit as st
import io

def extract_text_from_pdf(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> str:
    """
    Extracts text from an in-memory PDF file uploaded via Streamlit.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        A single string containing all text from the PDF, or None on failure.
    
    References: 
    """
    try:
        # Read bytes from the Streamlit UploadedFile object
        bytes_data = uploaded_file.getvalue()
        
        # Open the PDF directly from the byte stream
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        full_text = ""
        # Iterate through each page to extract text [39]
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Load the page
            full_text += page.get_text()     # Extract text from the page
        
        doc.close()
        
        if not full_text:
            st.warning("The PDF appears to be empty or contains no extractable text.")
            return None
            
        return full_text
        
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None