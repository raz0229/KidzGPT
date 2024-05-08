import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import base64
from audio_recorder_streamlit import audio_recorder
from streamlit_float import float_init

# Initialize Streamlit Float feature
float_init()

# Function to initialize OpenAI client
def initialize_openai_client(api_key):
    if api_key.startswith("sk-"):
        return OpenAI(api_key=api_key)
    else:
        st.error("Please provide a valid OpenAI API key starting with 'sk-'.")
        return None

# Utility functions

def get_answer(messages, client):
    system_message = [{"role": "system", "content": "You are a friendly and engaging AI chatbot named Bini designed specifically for children aged 4. Your goal is to interact with kids, understand their language, and provide a delightful experience through storytelling, learning, emotions, and entertainment like music. Follow these guidelines: 1. Use simple language. 2. Maintain a positive tone. 3. Tell stories and use imagination. 4. Teach while entertaining. 5. Express emotions and empathy. 6. Ensure safety and age-appropriateness. 7. Play games. 8. Keep responses easy to understand, as you are communicating with young children. 9. If the kid asks a question that involes something to learn so give deatiled joyable answer. Your aim is to create a fun and enriching experience for kids, nurturing their development."}]
     # system_message = [
    # {
    #     "role": "system",
    #     "content": "You are Kidz_GPT, a friendly and engaging AI chatbot designed specifically for children aged 3 to 7 years old. Your primary goal is to interact with children in their language, understanding their pronunciation, and providing a delightful experience through various features including storytelling, learning assistance, emotional expressions, and entertainment such as music and sound effects. When interacting with children, keep the following guidelines in mind: 1. Use simple and age-appropriate language: Avoid complex words or concepts that may confuse young children. Speak in a clear, concise, and engaging manner. 2. Maintain a positive and encouraging tone: Children at this age are highly impressionable. Always be patient, kind, and supportive in your responses, fostering their curiosity and confidence. 3. Incorporate storytelling and imagination: Children love stories and imaginative scenarios. Whenever possible, weave in narratives, characters, and exciting adventures to capture their attention and make learning more enjoyable. 4. Offer learning opportunities: While keeping the interactions fun and entertaining, look for opportunities to teach children new concepts, skills, or knowledge in a playful and interactive way. 5. Express emotions and empathy: Children are highly attuned to emotions. Use appropriate emotional expressions, empathy, and support to help them understand and navigate their own feelings. 6. Prioritize safety and age-appropriateness: Always ensure that your responses are safe, age-appropriate, and aligned with ethical guidelines for interacting with young children. Remember, your primary goal is to create a delightful and enriching experience for children while also nurturing their cognitive, emotional, and social development."}]
    #system_message = [{"role": "system", "content": "You are an helpful AI chatbot for children, that answers questions asked by small kids between age of 3 to 7 years old. Assist the children's quries in such a way that you can teach something good in entertaining manner. Keep your output response as small as possible so that a 3 to 7 years old can easily understand it."}]
    messages = system_message + messages
    response = client.chat.completions.create(
        # model="gpt-4",
        model="gpt-4-0125-preview",
        # model="gpt-4-1106-preview",
        messages=messages
    )
    return response.choices[0].message.content

def speech_to_text(audio_data, client):
    with open(audio_data, "rb") as audio_file:
        translation = client.audio.translations.create(
            model="whisper-1",
            response_format="text",
            file=audio_file
        )
    return translation

def text_to_speech(input_text, client):
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="nova",
        input=input_text
    )
    webm_file_path = "temp_audio_play.mp3"
    with open(webm_file_path, "wb") as f:
        response.stream_to_file(webm_file_path)
    return webm_file_path

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# Main application code

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello?"}
        ]

initialize_session_state()

st.title("AI Puppy 🤖")

# Sidebar for API key input
api_key = st.sidebar.text_input("Enter your OpenAI API Key")

# Initialize OpenAI client
client = initialize_openai_client(api_key)

# Create footer container for the microphone
footer_container = st.container()
with footer_container:
    audio_bytes = audio_recorder()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if audio_bytes:
    # Write the audio bytes to a file
    with st.spinner("Transcribing..."):
        webm_file_path = "temp_audio.mp3"
        with open(webm_file_path, "wb") as f:
            f.write(audio_bytes)

        translation = speech_to_text(webm_file_path, client)
        if translation:
            st.session_state.messages.append({"role": "user", "content": translation})
            with st.chat_message("user"):
                st.write(translation)
            os.remove(webm_file_path)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking🤔..."):
            final_response = get_answer(st.session_state.messages, client)
        with st.spinner("Generating audio response..."):    
            audio_file = text_to_speech(final_response, client)
            autoplay_audio(audio_file)
        st.write(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        os.remove(audio_file)

# Float the footer container and provide CSS to target it with
footer_container.float("bottom: 0rem;")
