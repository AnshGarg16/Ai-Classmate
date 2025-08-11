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


gemini_key = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = gemini_key  # langchain_google_genai expects this
genai.api_key = gemini_key
genai.configure(api_key="AIzaSyCb17ba2EXd2fDTDVZW52CtMIlej7HDZIY")
# ========== CONFIGURE GEMINI API ==========
model = genai.GenerativeModel("gemini-2.0-flash-001")


# ================== CUSTOM STYLES ==================
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name='TitleStyle',
    fontName='Helvetica-Bold',
    fontSize=22,
    leading=26,
    spaceAfter=20,
    textColor=HexColor('#1a237e'),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name='HeadingStyle',
    fontName='Helvetica-Bold',
    fontSize=18,
    leading=22,
    spaceAfter=15,
    textColor=HexColor('#00695c'),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name='SubheadingStyle',
    fontName='Helvetica-Bold',
    fontSize=14,
    leading=20,
    spaceAfter=10,
    textColor=HexColor('#512da8'),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name='BodyStyle',
    fontName='Helvetica',
    fontSize=12,
    leading=18,
    leftIndent=20,
    spaceAfter=10,
    textColor=HexColor('#212121')
))

styles.add(ParagraphStyle(
    name='BulletStyle',
    fontName='Helvetica',
    fontSize=12,
    leading=18,
    leftIndent=35,
    bulletIndent=25,
    spaceAfter=8,
    textColor=HexColor('#212121')
))

styles.add(ParagraphStyle(
    name='ExampleStyle',
    fontName='Courier',
    fontSize=11,
    leading=16,
    backColor=HexColor('#f0f0f0'),
    leftIndent=25,
    rightIndent=10,
    spaceBefore=12,
    spaceAfter=14,
    textColor=HexColor('#424242')
))

styles.add(ParagraphStyle(
    name='BulletHigh',
    parent=styles['BulletStyle'],
    textColor=HexColor('#e74c3c')
))
styles.add(ParagraphStyle(
    name='BulletMedium',
    parent=styles['BulletStyle'],
    textColor=HexColor('#f39c12')
))
styles.add(ParagraphStyle(
    name='BulletLow',
    parent=styles['BulletStyle'],
    textColor=HexColor('#27ae60')
))





# ========== Functions ==========
def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        blocks = page.get_text("blocks")
        clean_blocks = [b[4] for b in blocks if b[6] == 0]
        pages.append("\n".join(clean_blocks))
    return pages

def elaborate_content_with_gemini(text):
    system_prompt = """Structure your response EXACTLY like this:
## MAIN TITLE
### [Subheading]
* Bullet points
<example>[example here]</example>
"""
    prompt = f"{system_prompt}\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if hasattr(response, "text") else text
    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return text




# ================== CONTENT PROCESSING ==================
def process_content_blocks(content):
    hierarchy = []
    current_level = 0
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('## '):
            hierarchy.append(('title', line[3:].strip()))
            current_level = 1
        elif line.startswith('### '):
            hierarchy.append(('subheading', line[4:].strip()))
            current_level = 2
        elif line.startswith('* '):
            text = line[2:].strip()
            if text.startswith('[HIGH]'):
                hierarchy.append(('bullet_high', text.replace('[HIGH]', '').strip()))
            elif text.startswith('[MEDIUM]'):
                hierarchy.append(('bullet_medium', text.replace('[MEDIUM]', '').strip()))
            elif text.startswith('[LOW]'):
                hierarchy.append(('bullet_low', text.replace('[LOW]', '').strip()))
            else:
                hierarchy.append(('bullet', text))
        elif '<example>' in line:
            example = line.replace('<example>', '').replace('</example>', '').strip()
            hierarchy.append(('example', example))
        else:
            if current_level == 1:
                hierarchy.append(('heading', line.strip()))
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
        if element_type == 'title':
            style = styles['TitleStyle']
        elif element_type == 'heading':
            style = styles['HeadingStyle']
        elif element_type == 'subheading':
            style = styles['SubheadingStyle']
        elif element_type == 'bullet':
            style = styles['BulletStyle']
            text = f"• {text}"
        elif element_type == 'bullet_high':
            style = styles['BulletHigh']
            text = f"• {text}"
        elif element_type == 'bullet_medium':
            style = styles['BulletMedium']
            text = f"• {text}"
        elif element_type == 'bullet_low':
            style = styles['BulletLow']
            text = f"• {text}"
        elif element_type == 'example':
            style = styles['ExampleStyle']
        else:
            style = styles['BodyStyle']

        para = Paragraph(text, style)
        available_width = c._pagesize[0] - 2 * margin
        w, h = para.wrap(available_width, c._pagesize[1])

        if y_position - h < margin:
            c.showPage()
            y_position = page_height - margin
            draw_page_border(c, margin)

        para.drawOn(c, margin, y_position - h)
        y_position -= h + style.spaceAfter

        if element_type in ['title', 'heading']:
            y_position -= 10

def create_enhanced_pdf(output_path, elaborated_contents):
    page_size = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=page_size)
    margin = 60
    
    for content in elaborated_contents:
        draw_structured_content(c, content, margin, page_size[1])
        c.showPage()
    
    c.save()

# ========== STREAMLIT UI ==========
from PIL import Image

# Set page config
st.set_page_config(page_title="Smart PDF Enhancer", page_icon="📚", layout="centered")

# --- HEADER ---
st.markdown(
    """
    <h1 style="text-align:center; color:#4a90e2;">
        📚 Smart PDF Learning Assistant
    </h1>
    <p style="text-align:center; font-size:18px; color:#555;">
        Transform your study materials into structured, colorful, and engaging PDFs
        with AI-powered summaries & highlights.
    </p>
    """,
    unsafe_allow_html=True
)

# --- UPLOAD CARD ---
with st.container():
    st.markdown(
        """
        <div style="padding:20px; border-radius:12px; border:2px dashed #4a90e2; background-color:#f9fbff;">
            <h3 style="color:#4a90e2;">📤 Upload your PDF</h3>
            <p style="color:#555; font-size:15px;">
                Upload your notes, textbooks, or research papers.<br>
                Our AI will format, summarize, and enhance them for better learning.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

uploaded_pdf = st.file_uploader("", type=["pdf"], label_visibility="collapsed")


if uploaded_pdf:
    if st.button("Generate Enhanced PDF"):
        with st.spinner("Processing PDF..."):
            original_contents = extract_text_from_pdf(uploaded_pdf.read())
            elaborated_contents = [elaborate_content_with_gemini(page) for page in original_contents]
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            create_enhanced_pdf(temp_output.name, elaborated_contents)
        
        with open(temp_output.name, "rb") as f:
            st.download_button("📥 Download Enhanced PDF", f, file_name="enhanced_document.pdf")


# ================== MAIN PIPELINE ==================
def process_pdf(input_path, output_path, gemini_model):
    original_contents = extract_text_from_pdf(input_path)  # <-- reuse your function
    elaborated_contents = []
    
    for page_text in original_contents:
        enhanced_content = elaborate_content_with_gemini(page_text, gemini_model)  # <-- reuse your function
        elaborated_contents.append(enhanced_content)
    
    create_enhanced_pdf(output_path, elaborated_contents)
    return output_path