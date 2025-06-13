# # import os
# # import datetime
# # import logging
# # import sounddevice as sd
# # from scipy.io.wavfile import write
# # import whisper

# # # ==== Configuration ====
# # MODEL_SIZE = "base"  # Change to "tiny", "small", "medium", or "large" if needed
# # RECORDINGS_DIR = "recordings"
# # DEFAULT_DURATION = 20  # seconds
# # SAMPLE_RATE = 44100

# # # ==== Logging Configuration ====
# # logging.basicConfig(
# #     level=logging.INFO,
# #     format='%(asctime)s - %(levelname)s - %(message)s',
# #     handlers=[
# #         logging.FileHandler("audio_transcription.log"),
# #         logging.StreamHandler()
# #     ]
# # )

# # # ==== Load Whisper model globally ====
# # try:
# #     logging.info(f"Loading Whisper model: {MODEL_SIZE}...")
# #     whisper_model = whisper.load_model(MODEL_SIZE)
# #     logging.info("Whisper model loaded successfully.")
# # except Exception as e:
# #     logging.critical(f"Error loading Whisper model: {e}")
# #     whisper_model = None

# # # ==== Audio Recording ====
# # def record_audio(duration=DEFAULT_DURATION, fs=SAMPLE_RATE, save_dir=RECORDINGS_DIR):
# #     """
# #     Records audio from the microphone for a given duration and saves it as a .wav file.
# #     Returns the path to the saved file.
# #     """
# #     try:
# #         os.makedirs(save_dir, exist_ok=True)
# #         timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# #         filename = os.path.join(save_dir, f"response_{timestamp}.wav")

# #         logging.info(f"Recording for {duration} seconds...")
# #         audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
# #         sd.wait()
# #         write(filename, fs, audio)
# #         logging.info(f"Saved audio to {filename}")
# #         return filename

# #     except Exception as e:
# #         logging.error(f"Error during audio recording: {e}")
# #         return None

# # # ==== Audio Transcription ====
# # def transcribe_audio(filename):
# #     """
# #     Transcribes a .wav audio file using the Whisper model.
# #     Returns a dictionary containing transcribed text and metadata.
# #     """
# #     try:
# #         if whisper_model is None:
# #             raise RuntimeError("Whisper model is not loaded.")

# #         if not os.path.exists(filename):
# #             raise FileNotFoundError(f"Audio file not found: {filename}")

# #         logging.info(f"Transcribing file: {filename}")
# #         result = whisper_model.transcribe(filename)
# #         text = result.get("text", "").strip()

# #         logging.info(f"Transcription complete: {text}")
# #         return {
# #             "text": text,
# #             "language": result.get("language", "unknown"),
# #             "segments": result.get("segments", []),
# #             "path": filename
# #         }

# #     except Exception as e:
# #         logging.error(f"Error during transcription: {e}")
# #         return {
# #             "text": "",
# #             "language": "unknown",
# #             "segments": [],
# #             "path": filename,
# #             "error": str(e)
# #         }

# import os
# import datetime
# import logging
# import threading
# import sounddevice as sd
# from scipy.io.wavfile import write
# import numpy as np
# from groq import Groq

# # ==== Configuration ====
# RECORDINGS_DIR = "recordings"
# SAMPLE_RATE = 44100
# GROQ_MODEL = "whisper-large-v3"  # Groq's Whisper model

# # ==== Logging Configuration ====
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("audio_transcription.log"),
#         logging.StreamHandler()
#     ]
# )

# # ==== Initialize Groq client ====
# try:
#     # Make sure to set your GROQ_API_KEY environment variable
#     groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
#     logging.info("Groq client initialized successfully.")
# except Exception as e:
#     logging.critical(f"Error initializing Groq client: {e}")
#     logging.critical("Make sure to set the GROQ_API_KEY environment variable")
#     groq_client = None

# # ==== Global variables for recording state ====
# recording_data = []
# is_recording = False
# recording_thread = None
# stream = None

# # ==== Start Recording Function ====
# def start_recording():
#     """
#     Starts recording audio from the microphone.
#     Returns True if recording started successfully, False otherwise.
#     """
#     global recording_data, is_recording, recording_thread, stream
    
#     try:
#         if is_recording:
#             logging.warning("Recording is already in progress.")
#             return False
        
#         # Reset recording data
#         recording_data = []
#         is_recording = True
        
#         logging.info("Starting audio recording...")
        
#         def audio_callback(indata, frames, time, status):
#             if status:
#                 logging.warning(f"Audio callback status: {status}")
#             if is_recording:
#                 recording_data.extend(indata.copy())
        
#         # Start the audio stream
#         stream = sd.InputStream(
#             samplerate=SAMPLE_RATE,
#             channels=1,
#             callback=audio_callback,
#             dtype=np.float32
#         )
#         stream.start()
        
#         logging.info("Recording started. Call stop_recording() to stop.")
#         return True
        
#     except Exception as e:
#         logging.error(f"Error starting recording: {e}")
#         is_recording = False
#         return False

# # ==== Stop Recording Function ====
# def stop_recording():
#     """
#     Stops recording audio and saves it to a .wav file.
#     Returns the path to the saved file, or None if there was an error.
#     """
#     global recording_data, is_recording, stream
    
#     try:
#         if not is_recording:
#             logging.warning("No recording in progress.")
#             return None
        
#         # Stop recording
#         is_recording = False
        
#         if stream:
#             stream.stop()
#             stream.close()
#             stream = None
        
#         if not recording_data:
#             logging.warning("No audio data recorded.")
#             return None
        
#         # Create recordings directory if it doesn't exist
#         os.makedirs(RECORDINGS_DIR, exist_ok=True)
        
#         # Generate filename with timestamp
#         timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.wav")
        
#         # Convert list to numpy array and save
#         audio_array = np.array(recording_data, dtype=np.float32)
#         write(filename, SAMPLE_RATE, audio_array)
        
#         logging.info(f"Recording stopped. Saved audio to {filename}")
#         logging.info(f"Recording duration: {len(audio_array) / SAMPLE_RATE:.2f} seconds")
        
#         return filename
        
#     except Exception as e:
#         logging.error(f"Error stopping recording: {e}")
#         is_recording = False
#         return None

# # ==== Audio Transcription using Groq ====
# def transcribe_audio(filename):
#     """
#     Transcribes a .wav audio file using Groq's Whisper API.
#     Returns a dictionary containing transcribed text and metadata.
#     """
#     try:
#         if groq_client is None:
#             raise RuntimeError("Groq client is not initialized. Check your API key.")

#         if not os.path.exists(filename):
#             raise FileNotFoundError(f"Audio file not found: {filename}")

#         logging.info(f"Transcribing file: {filename} using Groq...")
        
#         # Open and send file to Groq
#         with open(filename, "rb") as file:
#             transcription = groq_client.audio.transcriptions.create(
#                 file=(os.path.basename(filename), file.read()),
#                 model=GROQ_MODEL,
#                 response_format="verbose_json",  # Get detailed response with timestamps
#                 temperature=0.0
#             )

#         text = transcription.text.strip()
#         logging.info(f"Transcription complete: {text}")
        
#         return {
#             "text": text,
#             "language": getattr(transcription, 'language', 'unknown'),
#             "segments": getattr(transcription, 'segments', []),
#             "duration": getattr(transcription, 'duration', None),
#             "path": filename,
#             "success": True
#         }

#     except Exception as e:
#         logging.error(f"Error during transcription: {e}")
#         return {
#             "text": "",
#             "language": "unknown",
#             "segments": [],
#             "duration": None,
#             "path": filename,
#             "success": False,
#             "error": str(e)
#         }

# # ==== Utility Functions ====
# def is_recording_active():
#     """
#     Returns True if recording is currently active, False otherwise.
#     """
#     return is_recording

# def get_recording_duration():
#     """
#     Returns the current recording duration in seconds.
#     """
#     if is_recording and recording_data:
#         return len(recording_data) / SAMPLE_RATE
#     return 0

# # ==== Complete Recording and Transcription Workflow ====
# def record_and_transcribe():
#     """
#     Complete workflow: starts recording, waits for user input to stop, then transcribes.
#     Returns transcription result.
#     """
#     try:
#         # Start recording
#         if not start_recording():
#             return {"success": False, "error": "Failed to start recording"}
        
#         # Wait for user to press Enter to stop
#         input("Recording... Press Enter to stop recording.")
        
#         # Stop recording and get filename
#         filename = stop_recording()
#         if not filename:
#             return {"success": False, "error": "Failed to stop recording"}
        
#         # Transcribe the audio
#         result = transcribe_audio(filename)
#         return result
        
#     except Exception as e:
#         logging.error(f"Error in record_and_transcribe workflow: {e}")
#         if is_recording:
#             stop_recording()
#         return {"success": False, "error": str(e)}

# # ==== Example Usage ====
# if __name__ == "__main__":
#     print("Audio Recording and Transcription with Groq")
#     print("=" * 50)
    
#     while True:
#         print("\nOptions:")
#         print("1. Start/Stop Recording Manually")
#         print("2. Quick Record and Transcribe")
#         print("3. Transcribe Existing File")
#         print("4. Exit")
        
#         choice = input("\nEnter your choice (1-4): ").strip()
        
#         if choice == "1":
#             if not is_recording_active():
#                 if start_recording():
#                     input("Recording... Press Enter to stop.")
#                     filename = stop_recording()
#                     if filename:
#                         print(f"Audio saved to: {filename}")
#             else:
#                 filename = stop_recording()
#                 if filename:
#                     print(f"Recording stopped. Audio saved to: {filename}")
        
#         elif choice == "2":
#             result = record_and_transcribe()
#             if result.get("success", True):
#                 print(f"\nTranscription: {result['text']}")
#                 print(f"Language: {result['language']}")
#             else:
#                 print(f"Error: {result.get('error', 'Unknown error')}")
        
#         elif choice == "3":
#             filename = input("Enter path to audio file: ").strip()
#             result = transcribe_audio(filename)
#             if result.get("success", True):
#                 print(f"\nTranscription: {result['text']}")
#                 print(f"Language: {result['language']}")
#             else:
#                 print(f"Error: {result.get('error', 'Unknown error')}")
        
#         elif choice == "4":
#             if is_recording_active():
#                 stop_recording()
#             print("Goodbye!")
#             break
        
#         else:
#             print("Invalid choice. Please try again.")



import os
import datetime
import logging
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import threading
import numpy as np
import time
from typing import Optional, Dict

class VoiceRecorder:
    """Handles voice recording and transcription functionality"""
    
    def __init__(self, model_size: str = "base", sample_rate: int = 44100):
        """
        Initialize the VoiceRecorder.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            sample_rate: Audio sample rate in Hz
        """
        self.model_size = model_size
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_data = []
        self.recording_thread = None
        self.model = self._load_whisper_model()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _load_whisper_model(self):
        """Load the Whisper speech recognition model"""
        try:
            logging.info(f"Loading Whisper model: {self.model_size}")
            return whisper.load_model(self.model_size)
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            raise
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback function for audio stream"""
        if status:
            logging.warning(f"Audio stream status: {status}")
        if self.is_recording:
            self.audio_data.append(indata.copy())
    
    def start_recording(self):
        """
        Start recording audio from the microphone.
        
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logging.warning("Recording already in progress")
            return False
            
        self.is_recording = True
        self.audio_data = []
        
        def record_callback():
            """Background thread for recording"""
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    callback=self._audio_callback,
                    dtype='float32'
                ):
                    while self.is_recording:
                        time.sleep(0.1)
            except Exception as e:
                logging.error(f"Recording error: {e}")
                self.is_recording = False
        
        self.recording_thread = threading.Thread(target=record_callback)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logging.info("Recording started")
        return True
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """
        Stop recording and return audio data.
        
        Returns:
            Optional[np.ndarray]: Recorded audio data as numpy array, or None if failed
        """
        if not self.is_recording:
            logging.warning("No active recording to stop")
            return None
            
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=1)
        
        if not self.audio_data:
            logging.warning("No audio data recorded")
            return None
        
        try:
            audio_array = np.concatenate(self.audio_data, axis=0)
            logging.info(f"Recording stopped. Captured {len(audio_array)/self.sample_rate:.2f} seconds")
            return audio_array
        except Exception as e:
            logging.error(f"Error processing audio data: {e}")
            return None
    
    def save_recording(self, audio_data: np.ndarray, directory: str = "recordings") -> Optional[str]:
        """
        Save recorded audio to a WAV file.
        
        Args:
            audio_data: Audio data as numpy array
            directory: Directory to save recordings
            
        Returns:
            Optional[str]: Path to saved file, or None if failed
        """
        try:
            os.makedirs(directory, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(directory, f"recording_{timestamp}.wav")
            write(filename, self.sample_rate, audio_data)
            logging.info(f"Audio saved to {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error saving audio: {e}")
            return None
    
    def transcribe(self, audio_data: np.ndarray) -> Dict:
        """
        Transcribe audio data using Whisper.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Dict: Transcription result containing:
                - text: Transcribed text
                - language: Detected language
                - segments: Detailed segments
                - error: Optional error message
        """
        try:
            if not isinstance(audio_data, np.ndarray):
                raise ValueError("Audio data must be numpy array")
                
            # Save temporary file for Whisper
            temp_file = "temp_recording.wav"
            write(temp_file, self.sample_rate, audio_data)
            
            result = self.model.transcribe(temp_file)
            os.remove(temp_file)
            
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "error": None
            }
        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            return {
                "text": "",
                "language": "unknown",
                "segments": [],
                "error": str(e)
            }
    
    def record_and_transcribe(self, max_duration: float = 60.0) -> Dict:
        """
        Record audio for specified duration and transcribe it.
        
        Args:
            max_duration: Maximum recording duration in seconds
            
        Returns:
            Dict: Transcription result (same format as transcribe())
        """
        logging.info(f"Starting recording (max {max_duration} seconds)")
        self.start_recording()
        
        start_time = time.time()
        while self.is_recording and (time.time() - start_time) < max_duration:
            time.sleep(0.1)
        
        audio_data = self.stop_recording()
        if audio_data is None:
            return {
                "text": "",
                "language": "unknown",
                "segments": [],
                "error": "No audio recorded"
            }
        
        return self.transcribe(audio_data)


# Example usage
if __name__ == "__main__":
    recorder = VoiceRecorder(model_size="base")
    
    print("Starting recording...")
    recorder.start_recording()
    input("Press Enter to stop recording...")
    
    audio_data = recorder.stop_recording()
    if audio_data is not None:
        print(f"Recorded {len(audio_data)/recorder.sample_rate:.2f} seconds of audio")
        
        # Save recording
        saved_path = recorder.save_recording(audio_data)
        if saved_path:
            print(f"Saved recording to {saved_path}")
        
        # Transcribe
        result = recorder.transcribe(audio_data)
        print("\nTranscription Result:")
        print(f"Text: {result['text']}")
        print(f"Language: {result['language']}")
        if result['error']:
            print(f"Error: {result['error']}")