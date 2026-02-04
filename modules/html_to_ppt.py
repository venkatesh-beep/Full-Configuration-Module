from html.parser import HTMLParser
import io

import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        if data:
            self._parts.append(data)

    def get_text(self):
        return " ".join(part.strip() for part in self._parts if part.strip())


def html_to_text(html):
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text() or " "


def build_pptx(slide_html_list):
    presentation = Presentation()
    blank_layout = presentation.slide_layouts[6]

    for html in slide_html_list:
        slide = presentation.slides.add_slide(blank_layout)
        left = top = Inches(0.7)
        width = Inches(12.0)
        height = Inches(6.0)
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        paragraph = text_frame.paragraphs[0]
        paragraph.text = html_to_text(html)
        paragraph.font.size = Pt(20)

    buffer = io.BytesIO()
    presentation.save(buffer)
    buffer.seek(0)
    return buffer


def html_to_ppt_ui():
    st.subheader("HTML to PPT")
    st.caption("Paste HTML for each slide, then generate an editable PowerPoint file.")

    if "html_slide_count" not in st.session_state:
        st.session_state.html_slide_count = 4

    if "html_slide_inputs" not in st.session_state:
        st.session_state.html_slide_inputs = [""] * st.session_state.html_slide_count

    if st.button("➕ Add Slide"):
        st.session_state.html_slide_count += 1
        st.session_state.html_slide_inputs.append("")

    slide_html_list = []
    for index in range(st.session_state.html_slide_count):
        value = st.text_area(
            f"Slide {index + 1} HTML",
            value=st.session_state.html_slide_inputs[index],
            height=160,
            key=f"html_slide_{index}",
        )
        slide_html_list.append(value)
    st.session_state.html_slide_inputs = slide_html_list

    if st.button("Generate PPT"):
        if not any(html.strip() for html in slide_html_list):
            st.warning("Please enter HTML for at least one slide.")
            return

        pptx_buffer = build_pptx(slide_html_list)
        st.success("Your PPT is ready to download.")
        st.download_button(
            "Download PPT",
            data=pptx_buffer,
            file_name="html_slides.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
