"""
FastAPI backend for receiving audio and transcribing using Whisper.
"""
import os
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import logging
from agent import process_user_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Conv-AI Backend")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model (tiny or small, runs on CPU)
# Using 'tiny' for faster CPU processing, change to 'small' for better accuracy
MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
logger.info(f"Loading Whisper model: {MODEL_SIZE}")
model = whisper.load_model(MODEL_SIZE)
logger.info("Whisper model loaded successfully")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Conv-AI Backend is running", "model": MODEL_SIZE}


@app.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Receive audio file and transcribe it using Whisper.
    
    Args:
        audio_file: Audio file in any format supported by Whisper (mp3, wav, m4a, etc.)
        
    Returns:
        JSON with transcribed text and additional metadata
    """
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    temp_file_path = None
    try:
        # Read audio content first
        content = await audio_file.read()
        logger.info(f"Received audio file: {audio_file.filename}, size: {len(content)} bytes")
        
        # Create temporary file to save uploaded audio
        # Use delete=False and manually manage the file
        file_ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
        temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}").name
        
        # Write content to file and ensure it's closed
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(content)
        # File is now closed, safe to use with Whisper
        
        # Transcribe audio using Whisper
        logger.info("Starting transcription...")
        result = model.transcribe(temp_file_path)
        
        transcript = result["text"].strip()
        logger.info(f"Transcription completed: {transcript[:50]}...")
        
        # Process transcribed text through the agent
        logger.info("Processing transcription through agent...")
        agent_result = process_user_input(transcript)
        logger.info(f"Agent processing completed: {agent_result.get('type', 'unknown')}")
        
        return {
            "text": transcript,
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", []),
            "agent_result": agent_result
        }
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Clean up temporary file with retry logic for Windows
        if temp_file_path and os.path.exists(temp_file_path):
            max_retries = 5
            retry_delay = 0.1  # 100ms
            
            for attempt in range(max_retries):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Temporary file deleted: {temp_file_path}")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"File locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Failed to delete temporary file after {max_retries} attempts: {temp_file_path}")
                        # On Windows, we can try to mark for deletion on next reboot
                        try:
                            import platform
                            if platform.system() == 'Windows':
                                # Try to mark file for deletion on next reboot
                                os.chmod(temp_file_path, 0o777)  # Make it writable
                                logger.warning(f"File will be cleaned up on next system restart: {temp_file_path}")
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"Unexpected error deleting temporary file: {e}")
                    break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

