import re
import fitz
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
import time
from collections import OrderedDict

# ========== CONFIGURE GEMINI API ==========
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    st.error("GEMINI_API_KEY is not set. Please add it to your .streamlit/secrets.toml file.")
    st.stop()
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel("gemini-1.5-flash")


# ================== CUSTOM STYLES ==================
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=24, leading=30, spaceAfter=25, textColor=HexColor('#1a237e')))
styles.add(ParagraphStyle(name='HeadingStyle', fontName='Helvetica-Bold', fontSize=18, leading=24, spaceAfter=15, textColor=HexColor('#00695c')))
styles.add(ParagraphStyle(name='SubheadingStyle', fontName='Helvetica-Bold', fontSize=14, leading=20, spaceAfter=10, textColor=HexColor('#512da8')))
styles.add(ParagraphStyle(name='BodyStyle', fontName='Helvetica', fontSize=12, leading=18, spaceAfter=10, textColor=HexColor('#212121')))
styles.add(ParagraphStyle(name='BulletStyle', parent=styles['BodyStyle'], leftIndent=20, bulletIndent=10, spaceAfter=8))
styles.add(ParagraphStyle(name='ExampleStyle', fontName='Courier', fontSize=11, leading=16, backColor=HexColor('#f0f0f0'), leftIndent=15, rightIndent=15, spaceBefore=10, spaceAfter=12, textColor=HexColor('#424242'), borderPadding=8, borderRadius=5))


# ========== HELPER FUNCTIONS ==========

def process_content_blocks(content):
    hierarchy = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('## '):
            hierarchy.append(('title', line[3:].strip()))
        elif line.startswith('### '):
            clean_text = line[4:].strip().strip('*')
            hierarchy.append(('subheading', clean_text))
        elif line.startswith('* '):
            text = line[2:].strip()
            processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            hierarchy.append(('bullet', processed_text))
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

# ========== CORE PDF GENERATION LOGIC (REBUILT) ==========

def generate_document_outline(topic, length):
    prompt = f"Generate a detailed document outline for the topic '{topic}'. The final document should be approximately {length} pages. Use `##` for main headings and `###` for subheadings. Every main heading must have at least two subheadings."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini Error while creating outline: {e}")
        return None

def generate_content_for_section(topic, main_heading, subheadings, total_sections):
    """
    Generates content for an entire section at once for better context and length control.
    """
    subheading_list_str = "\n".join(subheadings)
    # Heuristic to control length: request less text per section if there are many sections.
    length_guidance = "concise and roughly one page long."
    if total_sections > 4:
        length_guidance = "very concise, about half a page long."

    prompt = f"""
    You are an expert author writing a document on '{topic}'.
    Your task is to write the complete content for the section titled '{main_heading}'.

    This section MUST be structured with the following subheadings:
    {subheading_list_str}

    **CRITICAL INSTRUCTIONS:**
    1.  **Generate Full Content:** Write the complete text for this entire section, including the main heading (`##...`) and each subheading (`###...`).
    2.  **Content For Each Subheading:** Under each subheading, provide a short introductory paragraph, 2-3 bullet points (`* `), and an `<example>`.
    3.  **STRICT Length Control:** The entire output for this whole section must be {length_guidance}
    4.  **Clean Formatting:** Do not use markdown bolding (`**...**`). The code will handle it.

    Now, generate the complete text for the '{main_heading}' section.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.warning(f"Could not generate content for '{main_heading}': {e}")
        return f"## {main_heading}\nContent could not be generated for this section."

def create_generated_pdf(output_path, full_content):
    page_size = landscape(A4)
    c = canvas.Canvas(output_path, pagesize=page_size)
    margin = 60
    draw_structured_content(c, full_content, margin, page_size[1])
    c.save()

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="PDF Generator", page_icon="💡", layout="centered")
st.markdown("""
<h1 style="text-align:center; color:#4a90e2;">💡 AI PDF Generator</h1>
<p style="text-align:center; font-size:18px; color:#555;">Enter a topic and desired length, and let AI create a structured, easy-to-read document for you.</p>
""", unsafe_allow_html=True)
st.markdown("---")

topic = st.text_input("Enter the topic you want to learn about:", placeholder="e.g., 'The Renaissance'")
length = st.number_input("Desired number of pages:", min_value=1, max_value=20, value=3)

if st.button("✨ Generate PDF from Topic", type="primary"):
    if not topic:
        st.warning("Please enter a topic to generate the PDF.")
    else:
        full_document_content = []
        with st.spinner("Step 1/3: Designing a smart document outline..."):
            outline = generate_document_outline(topic, length)
        
        if outline:
            st.success("✅ Outline designed successfully!")
            
            # Group outline into sections
            sections = OrderedDict()
            current_heading = None
            for line in outline.split('\n'):
                line = line.strip()
                if line.startswith("## "):
                    current_heading = line
                    sections[current_heading] = []
                elif line.startswith("### ") and current_heading:
                    sections[current_heading].append(line)

            total_sections = len(sections)
            progress_bar = st.progress(0, text="Step 2/3: Generating content section by section...")
            
            # Generate content for each section
            for i, (main_heading, subheadings) in enumerate(sections.items()):
                clean_heading = main_heading.replace('##', '').strip()
                progress_text = f"Step 2/3: Writing section '{clean_heading}' ({i+1}/{total_sections})..."
                progress_bar.progress((i + 1) / total_sections, text=progress_text)
                
                if not subheadings:
                    continue

                section_content = generate_content_for_section(topic, main_heading, subheadings, total_sections)
                full_document_content.append(section_content)
                time.sleep(0.05) 

            with st.spinner("Step 3/3: Assembling and finalizing your PDF..."):
                final_content_string = "\n\n".join(full_document_content)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
                    create_generated_pdf(temp_output.name, final_content_string)
                    st.success("✅ Your new PDF is ready!")
                    with open(temp_output.name, "rb") as f:
                        safe_topic_name = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
                        st.download_button("📥 Download Generated PDF", f, file_name=f"{safe_topic_name.replace(' ', '_').lower()}_document.pdf")
            progress_bar.empty()