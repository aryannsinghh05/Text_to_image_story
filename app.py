import os
import streamlit as st
import re
import requests
from fpdf import FPDF
import io
from transformers import pipeline

story_generator = pipeline("text2text-generation", model="google/flan-t5-small")

def generate_story(prompt, num_parts, genre):
    story_prompt = f"""
    Based on the following short prompt, expand it into a detailed {genre} story.
    The story should be divided into {num_parts} distinct parts.
    After each part, include the text 'IMAGE_PROMPT:' followed by a short, descriptive sentence 
    for an image that represents that part of the story.

    User prompt: '{prompt}'
    """

    result = story_generator(story_prompt, max_length=800)
    return result[0]["generated_text"]

def generate_image(prompt):
    api_key = os.getenv("STABILITY_API_KEY")
    url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"

    headers = {
        "Content-Type": "application/json",
        "Accept": "image/png",
        "Authorization": f"Bearer {api_key}"
    }

    body = {
        "text_prompts": [{"text": prompt, "weight": 1}],
        "cfg_scale": 7,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30,
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"Error generating image: {response.text}")
        return None

def generate_pdf_report(story_sections, image_contents):
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font("DejaVu", size=12)

    for i in range(len(story_sections)):
        story_part_text = story_sections[i].strip()
        pdf.multi_cell(0, 10, story_part_text)

        if i < len(image_contents) and image_contents[i]:
            image_buffer = io.BytesIO(image_contents[i])
            pdf.image(image_buffer, x=10, w=150)
        pdf.ln(10)

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return pdf_output

# Streamlit UI
st.set_page_config(layout="wide")
st.title("AI-Powered Illustrated Story Generator 📖✨")

st.subheader("Create a captivating story with beautiful illustrations in a few simple steps!")
genre = st.selectbox("1. Select a Genre", ("Fantasy", "Sci-Fi", "Mystery", "Comedy"))
num_parts = st.number_input("2. How many parts should the story have?", min_value=2, max_value=10, value=3)
user_idea = st.text_area("3. Enter your story idea or a short prompt:", placeholder="A lone warrior with a magical sword...")
generate_button = st.button("Generate My Story & Illustrations")

if generate_button and user_idea:
    with st.spinner("Generating story..."):
        full_story = generate_story(user_idea, num_parts, genre)

    st.subheader("Your Story")
    st.markdown(full_story)

    st.info("Generating images and preparing for download...")

    parts = re.split(r'IMAGE_PROMPT:', full_story)
    story_sections = parts[0::2]
    image_prompts = parts[1::2]

    image_contents = []
    st.subheader("Illustrations")

    if image_prompts:
        for i in range(len(image_prompts)):
            image_prompt_text = image_prompts[i].strip()
            with st.spinner(f"Generating image {i+1} for: '{image_prompt_text}'"):
                image_content = generate_image(image_prompt_text)
                if image_content:
                    image_contents.append(image_content)
                    st.image(image_content, caption=story_sections[i].strip() if i < len(story_sections) else "")

    st.subheader("Download Options")
    if image_contents:
        pdf_data = generate_pdf_report(story_sections, image_contents)
        st.download_button(
            label="Download Story as PDF 📥",
            data=pdf_data,
            file_name=f"{genre.lower()}_story.pdf",
            mime="application/pdf"
        )

    st.success("Your story is ready!")
