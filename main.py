import streamlit as st
from gtts import gTTS
from dotenv import load_dotenv
import tempfile
import os
from PIL import Image
import google.generativeai as genai
import base64
import re
import cv2
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# Load environment variables
load_dotenv()
genai.configure(api_key='AIzaSyC-OEPHOBSsiwTaEgMMSSqLiDnYgZJHyG8' )

# Initialize session state variables
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False
if 'response' not in st.session_state:
    st.session_state.response = ""
if 'captured_image' not in st.session_state:
    st.session_state.captured_image = None

# Function to get response from Gemini model
def get_gemini_response(input_text, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_text, image[0], prompt])
    return response.text

# Function to process uploaded image
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function for text-to-speech conversion
def text_to_speech(text, lang):
    language = "en" if lang == "English" else "ta"
    tts = gTTS(text=text, lang=language, slow=False)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name


st.set_page_config(page_title="Gemini Image Demo")

st.header("Medicine Application")
st.markdown(
    """
    <style>
    .stCameraInput {
        width: 500px; /* Adjust the width */
        height: 350px; /* Adjust the height */
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Dropdown for choosing input method
input_method = st.selectbox("Choose Input Method", ["Upload Image", "Scan Image"])

uploaded_file = None
if input_method == "Upload Image":
    # File uploader for image upload
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])
    image = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image.", width=300)

elif input_method == "Scan Image":
    uploaded_file = st.camera_input("Take a picture")

    if uploaded_file:
        st.image(uploaded_file)
    else:
        st.error("No image captured. Please ensure your webcam is working.")

# Language selection in main content
language_options = ["English", "Tamil"]
selected_language = st.selectbox("Choose a language:", language_options, index=language_options.index("English"))

# Button to trigger processing
submit = st.button("Tell me about the image")

input_prompt = f"""
               You are an expert in finding the name of medicines or pills. You will be given images of medicine or pills.
               You will have to answer the name of the medicine, and the problems it cures. Reply in {selected_language}. 
               If you find that the image is not clear or not a medicine, then provide a warning: "Recheck your medicine and upload."
               """

# If submit button is clicked
if submit:
    # Clear previous audio file if a new image or language change occurs
    if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
        os.remove(st.session_state.audio_file_path)
        st.session_state.audio_file_path = None

    if input_method == "Upload Image" and uploaded_file:
        # Setup image data
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_prompt, image_data, '')

    elif input_method == "Scan Image" and uploaded_file:
        # Convert captured image to bytes for processing
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_prompt, image_data, '')

    else:
        st.error("No image provided. Please upload or scan an image.")
        response = None

    if response:
        # Clean response for English by removing special characters
        if selected_language == 'English':
            response = re.sub(r'[^a-zA-Z0-9.\s]', '', response)

        # Display response
        st.subheader("The Response is")
        st.write(response)
        print(response)

        # Generate audio file for response
        audio_file_path = text_to_speech(response, selected_language)
        st.session_state.audio_file_path = audio_file_path
        st.session_state.response = response
        st.session_state.is_playing = True

# Display audio player if audio file is available
if st.session_state.audio_file_path:
    # Generate the audio file's base64 encoding
    with open(st.session_state.audio_file_path, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()

    if audio_base64:
        # Display audio player
        audio_html = f"""
        <audio id="audio" controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

        # Stop playback button
        if st.button("Stop Playback"):
            if os.path.exists(st.session_state.audio_file_path):
                os.remove(st.session_state.audio_file_path)
            st.session_state.audio_file_path = None
            st.session_state.is_playing = False
            st.write("Playback stopped.")
