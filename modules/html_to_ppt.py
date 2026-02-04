from html.parser import HTMLParser
import io
import tempfile

import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from playwright.sync_api import sync_playwright


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


def render_html_to_png(html, width=1280, height=720):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html, wait_until="networkidle")
        png_bytes = page.screenshot(full_page=True)
        browser.close()
    return png_bytes


def build_pptx(slide_html_list, include_text_layer):
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    blank_layout = presentation.slide_layouts[6]

    with tempfile.TemporaryDirectory() as tmp_dir:
        for index, html in enumerate(slide_html_list):
            slide = presentation.slides.add_slide(blank_layout)
            png_bytes = render_html_to_png(html)
            tmp_path = f"{tmp_dir}/slide_{index + 1}.png"
            with open(tmp_path, "wb") as tmp_file:
                tmp_file.write(png_bytes)
            slide.shapes.add_picture(
                tmp_path,
                left=Inches(0),
                top=Inches(0),
                width=presentation.slide_width,
                height=presentation.slide_height,
            )

            if include_text_layer:
                textbox = slide.shapes.add_textbox(
                    left=Inches(0.5),
                    top=Inches(6.5),
                    width=Inches(12.5),
                    height=Inches(0.8),
                )
                text_frame = textbox.text_frame
                text_frame.word_wrap = True
                paragraph = text_frame.paragraphs[0]
                paragraph.text = html_to_text(html)
                paragraph.font.size = Pt(12)

    buffer = io.BytesIO()
    presentation.save(buffer)
    buffer.seek(0)
    return buffer


def html_to_ppt_ui():
    st.subheader("HTML to PPT")
    st.caption(
        "Paste HTML for each slide, then generate a PPTX rendered from the HTML layout."
    )
    st.info("Requires Playwright with Chromium installed for HTML rendering.")

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

    include_text_layer = st.checkbox(
        "Add editable text layer (from HTML text)",
        value=True,
    )

    if st.button("Generate PPT"):
        if not any(html.strip() for html in slide_html_list):
            st.warning("Please enter HTML for at least one slide.")
            return

        pptx_buffer = build_pptx(slide_html_list, include_text_layer)
        st.success("Your PPT is ready to download.")
        st.download_button(
            "Download PPT",
            data=pptx_buffer,
            file_name="html_slides.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
