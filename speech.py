import streamlit as st
from gtts import gTTS
from dotenv import load_dotenv
import tempfile
import os
from PIL import Image
import google.generativeai as genai
import base64
import re
# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize session state variables
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False
if 'response' not in st.session_state:
    st.session_state.response = ""

def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, image[0], prompt])
    
    return response.text

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

def text_to_speech(text, lang):
    language = "en" if lang == "English" else "ta"
    tts = gTTS(text=text, lang=language, slow=False)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Image Demo")

st.header("Medicine Application")

# Input for text and file upload
input_text = ''
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])
image = ""
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", width=250)
# Language selection
language_options = ["English", "Tamil"]
selected_language = st.selectbox("Choose a language:", language_options, index=language_options.index("English"))

# Button to trigger processing
submit = st.button("Tell me about the image")

input_prompt = f"""
               You are an expert in finding the name of medicines or pills.You will be given images of medicine or pills .
               You will have to answer the name of the medicine, problems it cures. Reply in {selected_language}. If you find that the image is not clear or not a medicine, then provide a warning: "Recheck your medicine and upload."
               """

if submit:
    # Clear previous audio file if a new image or language change occurs
    if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
        os.remove(st.session_state.audio_file_path)
        st.session_state.audio_file_path = None

    if uploaded_file:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_prompt, image_data, input_text)
        if selected_language=='English':
            response = re.sub(r'[^a-zA-Z0-9\s]', '', response)
        st.subheader("The Response is")
        st.write(response)
        print(response)
        # Generate new audio file
        audio_file_path = text_to_speech(response, selected_language)
        st.session_state.audio_file_path = audio_file_path
        st.session_state.response = response
        st.session_state.is_playing = True

# Display audio player controls if audio file exists
if st.session_state.audio_file_path:
    # Generate the audio file's base64 encoding
    audio_base64 = None
    with open(st.session_state.audio_file_path, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode()

    if audio_base64:
        # Check if playback has not been initiated
        if not st.session_state.is_playing:
            st.session_state.is_playing = True
        else:
            st.session_state.is_playing = False

        audio_html = f"""
        <audio id="audio" controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

        # Optionally, provide a stop button to stop playback
        if st.button("Stop Playback"):
            st.session_state.audio_file_path = None
            st.session_state.is_playing = False
            if os.path.exists(st.session_state.audio_file_path):
                os.remove(st.session_state.audio_file_path)
            st.write("Playback stopped.")
