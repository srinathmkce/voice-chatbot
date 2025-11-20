"""
Streamlit frontend for voice-enabled chatbot.
Records audio and sends to backend after 5-second pause.
"""
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import requests
import time
import base64

# Page configuration
st.set_page_config(
    page_title="Conv-AI Voice Chatbot",
    page_icon="🎤",
    layout="centered"
)

# Backend API URL
BACKEND_URL = st.sidebar.text_input(
    "Backend URL",
    value="http://localhost:8000",
    help="URL of the FastAPI backend"
)

# Initialize session state
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_chunks" not in st.session_state:
    st.session_state.audio_chunks = []
if "last_audio_time" not in st.session_state:
    st.session_state.last_audio_time = None
if "transcriptions" not in st.session_state:
    st.session_state.transcriptions = []


def send_audio_to_backend(audio_bytes: bytes):
    """Send audio bytes to FastAPI backend for transcription."""
    try:
        files = {"audio_file": ("audio.wav", audio_bytes, "audio/wav")}
        response = requests.post(
            f"{BACKEND_URL}/transcribe",
            files=files,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None


def main():
    st.title("🎤 Conv-AI Voice Chatbot")
    st.markdown("### Click the microphone button to start recording")
    st.markdown("**Your speech will be transcribed after 5 seconds of silence.**")
    
    # Display connection status
    try:
        health_response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success(f"✅ Connected to backend (Model: {health_data.get('model', 'unknown')})")
        else:
            st.warning("⚠️ Backend responded with an error")
    except:
        st.error(f"❌ Cannot connect to backend at {BACKEND_URL}")
        st.info("Make sure the FastAPI backend is running: `python backend.py`")
    
    st.divider()
    
    # Audio recorder component
    # pause_threshold: stops recording after silence of specified seconds
    audio_bytes = audio_recorder(
        text="",
        icon_size="3x",
        recording_color="#e74c3c",
        neutral_color="#34495e",
        pause_threshold=5.0,  # 5 seconds pause detection - stops after 5s of silence
    )
    
    # Handle recorded audio
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        # Show processing indicator
        with st.spinner("🔄 Transcribing audio..."):
            result = send_audio_to_backend(audio_bytes)
            
            if result:
                transcript = result.get("text", "")
                language = result.get("language", "unknown")
                agent_result = result.get("agent_result", {})
                
                if transcript:
                    # Store transcription with agent result
                    st.session_state.transcriptions.append({
                        "text": transcript,
                        "language": language,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "agent_result": agent_result
                    })
                    
                    st.success("✅ Transcription successful!")
                    st.markdown(f"**Language detected:** {language}")
                    st.markdown(f"**Transcribed text:**")
                    st.info(transcript)
                    
                    # Display agent result
                    if agent_result:
                        result_type = agent_result.get("type", "unknown")
                        intent = agent_result.get("intent", "unknown")
                        
                        st.divider()
                        st.markdown("### 🤖 Agent Result")
                        
                        # Get response text and audio
                        response_text = result.get("response_text", "")
                        audio_base64 = result.get("audio_response")
                        
                        # Display response text
                        if response_text:
                            st.markdown("### 🔊 Voice Response")
                            st.info(f"**{response_text}**")
                            
                            # Play audio if available
                            if audio_base64:
                                try:
                                    # Decode base64 audio
                                    audio_bytes = base64.b64decode(audio_base64)
                                    st.audio(audio_bytes, format="audio/mpeg", autoplay=True)
                                    st.success("✅ Voice response generated and playing!")
                                except Exception as e:
                                    st.warning(f"Could not play audio: {str(e)}")
                        
                        if result_type == "command":
                            command = agent_result.get("command", "")
                            st.success(f"🎯 **Command Detected:** {command.upper()}")
                            st.info(f"Intent: {intent}")
                        elif result_type == "add_product":
                            st.info("📦 **Product Addition Request**")
                            st.info(f"Intent: {intent}")
                            product_info = agent_result.get("product_info", {})
                            if product_info:
                                st.markdown("**Extracted Product Information:**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if product_info.get("brand_name"):
                                        st.write(f"Brand: {product_info['brand_name']}")
                                    if product_info.get("product_name"):
                                        st.write(f"Product: {product_info['product_name']}")
                                with col2:
                                    if product_info.get("sales_value"):
                                        st.write(f"Sales Value: ${product_info['sales_value']}")
                                    if product_info.get("quantity"):
                                        st.write(f"Quantity: {product_info['quantity']}")
                            message = agent_result.get("message", "")
                            if message:
                                st.warning(message)
                        elif result_type == "error":
                            st.error(f"❌ {agent_result.get('message', 'An error occurred')}")
                        else:
                            st.info(f"Intent: {intent}")
                            if agent_result.get("message"):
                                st.write(agent_result["message"])
                else:
                    st.warning("No text detected in audio")
            else:
                st.error("Failed to transcribe audio")
    
    # Display transcription history
    if st.session_state.transcriptions:
        st.divider()
        st.markdown("### 📝 Transcription History")
        
        for i, trans in enumerate(reversed(st.session_state.transcriptions), 1):
            agent_result = trans.get("agent_result", {})
            result_type = agent_result.get("type", "")
            title_suffix = ""
            if result_type == "command":
                command = agent_result.get("command", "")
                title_suffix = f" - Command: {command.upper()}"
            elif result_type == "add_product":
                title_suffix = " - Add Product"
            
            with st.expander(f"🎤 {trans['timestamp']} - {trans['language']}{title_suffix}"):
                st.write(f"**Text:** {trans['text']}")
                if agent_result:
                    st.write(f"**Intent:** {agent_result.get('intent', 'unknown')}")
                    if result_type == "command":
                        st.write(f"**Command:** {agent_result.get('command', 'N/A')}")
                    elif result_type == "add_product":
                        product_info = agent_result.get("product_info", {})
                        if product_info:
                            st.write("**Product Info:**")
                            st.json(product_info)
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.transcriptions = []
            st.rerun()


if __name__ == "__main__":
    main()

