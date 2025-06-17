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
