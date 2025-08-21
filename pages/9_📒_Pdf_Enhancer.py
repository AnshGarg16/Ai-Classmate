import re # <--- THIS IMPORT IS CRUCIAL
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor
import google.generativeai as genai
import streamlit as st
import os
import tempfile

# ========== CONFIGURE GEMINI API (SECURE METHOD) ==========
# IMPORTANT: Your hardcoded API key was removed for security.
# This code now safely gets the key from Streamlit Secrets or an environment variable.
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    st.error("GEMINI_API_KEY is not set. Please add it to your Streamlit secrets or environment variables.")
    st.stop()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel("gemini-1.5-flash") # Updated to the latest model


# ================== CUSTOM STYLES ==================
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='TitleStyle', fontName='Helvetica-Bold', fontSize=22, leading=26, spaceAfter=20, textColor=HexColor('#1a237e'), alignment=TA_LEFT
))
styles.add(ParagraphStyle(
    name='HeadingStyle', fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=15, textColor=HexColor('#00695c'), alignment=TA_LEFT
))
styles.add(ParagraphStyle(
    name='SubheadingStyle', fontName='Helvetica-Bold', fontSize=14, leading=20, spaceAfter=10, textColor=HexColor('#512da8'), alignment=TA_LEFT
))
styles.add(ParagraphStyle(
    name='BodyStyle', fontName='Helvetica', fontSize=12, leading=18, leftIndent=20, spaceAfter=10, textColor=HexColor('#212121')
))
styles.add(ParagraphStyle(
    name='BulletStyle', fontName='Helvetica', fontSize=12, leading=18, leftIndent=35, bulletIndent=25, spaceAfter=8, textColor=HexColor('#212121')
))
styles.add(ParagraphStyle(
    name='ExampleStyle', fontName='Courier', fontSize=11, leading=16, backColor=HexColor('#f0f0f0'), leftIndent=25, rightIndent=10, spaceBefore=12, spaceAfter=14, textColor=HexColor('#424242')
))
styles.add(ParagraphStyle(
    name='BulletHigh', parent=styles['BulletStyle'], textColor=HexColor('#e74c3c')
))
styles.add(ParagraphStyle(
    name='BulletMedium', parent=styles['BulletStyle'], textColor=HexColor('#f39c12')
))
styles.add(ParagraphStyle(
    name='BulletLow', parent=styles['BulletStyle'], textColor=HexColor('#27ae60')
))


# ========== FUNCTIONS ==========
def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        blocks = page.get_text("blocks")
        clean_blocks = [b[4] for b in blocks if b[6] == 0]
        pages.append("\n".join(clean_blocks))
    return pages

def elaborate_content_with_gemini(text):
    system_prompt = """
    Structure your response using the following format. Be creative and enhance the provided text for better learning. Use bolding with ** on key terms within bullet points.
    ## MAIN TITLE
    ### An Insightful Subheading
    * **Key Term 1:** Explanation of the key term.
    * **Key Term 2:** Explanation of another key term.
    <example>A relevant, easy-to-understand example.</example>
    """
    prompt = f"{system_prompt}\n\nEnhance this text:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return text

# ================== CONTENT PROCESSING (CORRECTED) ==================
def process_content_blocks(content):
    """
    Parses content and correctly converts markdown bolding to ReportLab bolding.
    """
    hierarchy = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('## '):
            hierarchy.append(('title', line[3:].strip()))
        elif line.startswith('### '):
            hierarchy.append(('subheading', line[4:].strip()))
        elif line.startswith('* '):
            # --- THIS IS THE FIX ---
            raw_text = line[2:].strip()
            style_type = 'bullet'
            text_content = raw_text

            # Check for special bullet types
            if raw_text.startswith('[HIGH]'):
                style_type = 'bullet_high'
                text_content = raw_text.replace('[HIGH]', '').strip()
            elif raw_text.startswith('[MEDIUM]'):
                style_type = 'bullet_medium'
                text_content = raw_text.replace('[MEDIUM]', '').strip()
            elif raw_text.startswith('[LOW]'):
                style_type = 'bullet_low'
                text_content = raw_text.replace('[LOW]', '').strip()

            # Find markdown bolding (**text**) and convert it to ReportLab's bold tag (<b>text</b>)
            processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text_content)
            hierarchy.append((style_type, processed_text))
            # --- END OF FIX ---
        elif '<example>' in line:
            example = line.replace('<example>', '').replace('</example>', '').strip()
            hierarchy.append(('example', example))
        else:
            hierarchy.append(('body', line.strip()))
            
    return hierarchy

def draw_page_border(c, margin):
    width, height = c._pagesize
    c.setLineWidth(0.5)
    c.setStrokeColor(HexColor("#d0d3d4"))
    c.rect(margin / 2, margin / 2, width - margin, height - margin)

def draw_structured_content(c, content, margin, page_height):
    parsed_content = process_content_blocks(content)
    y_position = page_height - margin
    draw_page_border(c, margin)

    for element_type, text in parsed_content:
        if element_type == 'title': style = styles['TitleStyle']
        elif element_type == 'heading': style = styles['HeadingStyle']
        elif element_type == 'subheading': style = styles['SubheadingStyle']
        elif element_type == 'bullet':
            style = styles['BulletStyle']
            text = f"• {text}" # The text already contains <b> tags if needed
        elif element_type == 'bullet_high':
            style = styles['BulletHigh']
            text = f"• {text}"
        elif element_type == 'bullet_medium':
            style = styles['BulletMedium']
            text = f"• {text}"
        elif element_type == 'bullet_low':
            style = styles['BulletLow']
            text = f"• {text}"
        elif element_type == 'example': style = styles['ExampleStyle']
        else: style = styles['BodyStyle']

        para = Paragraph(text, style)
        available_width = c._pagesize[0] - 2 * margin
        w, h = para.wrap(available_width, c._pagesize[1])

        if y_position - h < margin:
            c.showPage()
            y_position = page_height - margin
            draw_page_border(c, margin)
        para.drawOn(c, margin, y_position - h)
        y_position -= h + style.spaceAfter

def create_enhanced_pdf(output_path, elaborated_contents):
    page_size = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=page_size)
    margin = 60
    
    for content in elaborated_contents:
        draw_structured_content(c, content, margin, page_size[1])
        c.showPage()
    
    c.save()

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Smart PDF Enhancer", page_icon="📚", layout="centered")
st.markdown("""
<h1 style="text-align:center; color:#4a90e2;">📚 Smart PDF Learning Assistant</h1>
<p style="text-align:center; font-size:18px; color:#555;">
    Transform your study materials into structured, colorful, and engaging PDFs with AI-powered summaries & highlights.
</p>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    <div style="padding:20px; border-radius:12px; border:2px dashed #4a90e2; background-color:#f9fbff;">
        <h3 style="color:#4a90e2;">📤 Upload your PDF</h3>
        <p style="color:#555; font-size:15px;">
            Upload your notes, textbooks, or research papers.<br>
            Our AI will format, summarize, and enhance them for better learning.
        </p>
    </div>
    """, unsafe_allow_html=True)

uploaded_pdf = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

if uploaded_pdf:
    if st.button("Generate Enhanced PDF", type="primary"):
        with st.spinner("Enhancing your document... This can take a moment."):
            original_contents = extract_text_from_pdf(uploaded_pdf.read())
            elaborated_contents = [elaborate_content_with_gemini(page) for page in original_contents]
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
                create_enhanced_pdf(temp_output.name, elaborated_contents)
        
        st.success("✅ Enhanced PDF created successfully!")
        with open(temp_output.name, "rb") as f:
            st.download_button("📥 Download Enhanced PDF", f, file_name="enhanced_document.pdf")