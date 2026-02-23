#!/usr/bin/env python3
"""
OmniClaw Voice Wake Module (macOS & Desktop)
Constantly listens for a hotword to activate the agent.
"""

import logging
import asyncio
import os
import threading
from typing import Callable, Optional

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

logger = logging.getLogger("OmniClaw.VoiceWake")

class VoiceWakeSystem:
    def __init__(self, hotword: str = "hey omni", api_key: Optional[str] = None):
        self.hotword = hotword.lower()
        self.api_key = api_key
        self.is_listening = False
        self.on_wake_callback: Optional[Callable[[str], None]] = None
        
        # Audio backend
        self._recognizer = None
        self._microphone = None
        self._stop_listening_fn = None
        
    async def initialize(self):
        """Initialize the audio engines (SpeechRecognition, PyAudio, etc.)"""
        if not SPEECH_AVAILABLE:
            logger.error("SpeechRecognition missing. Run `pip install SpeechRecognition PyAudio`.")
            return False
            
        try:
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            
            # Calibrate for ambient noise
            with self._microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                
            logger.info(f"Voice Wake System initialized. Hotword: '{self.hotword}'")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Voice Wake: {e}")
            return False

    def register_wake_callback(self, callback: Callable[[str], None]):
        """Pass a function to execute when the agent is woken up"""
        self.on_wake_callback = callback
        logger.info("Voice wake callback registered.")

    async def start_listening(self):
        """Start the background audio listening loop"""
        if self.is_listening or not self._recognizer:
            return
            
        self.is_listening = True
        logger.info(f"Voice Wake is now actively listening for: '{self.hotword}'")
        
        # listen_in_background returns a function that stops the background listener
        self._stop_listening_fn = self._recognizer.listen_in_background(
            self._microphone, 
            self._audio_callback
        )
        
    async def stop_listening(self):
        """Terminate the listening loop"""
        if self._stop_listening_fn:
            self._stop_listening_fn(wait_for_stop=False)
            self._stop_listening_fn = None
            
        self.is_listening = False
        logger.info("Voice Wake stopped listening.")

    def _audio_callback(self, recognizer, audio):
        """Callback executed in a background thread when audio is captured"""
        try:
            # Recognizer is passed in as the first argument
            text = recognizer.recognize_google(audio).lower()
            logger.debug(f"Captured: {text}")
            
            if self.hotword in text:
                command = text.split(self.hotword)[-1].strip()
                logger.info(f"Hotword detected! Command: {command}")
                
                if self.on_wake_callback:
                    # Execute callback in the main loop
                    asyncio.run_coroutine_threadsafe(
                        self._handle_callback(command), 
                        asyncio.get_event_loop()
                    )
        except sr.UnknownValueError:
            pass # Speech was unintelligible
        except sr.RequestError as e:
            logger.error(f"Speech Recognition service error: {e}")
        except Exception as e:
            logger.error(f"Error in audio processing: {e}")

    async def _handle_callback(self, command: str):
        if self.on_wake_callback:
            if asyncio.iscoroutinefunction(self.on_wake_callback):
                await self.on_wake_callback(command)
            else:
                self.on_wake_callback(command)

    async def speak(self, text: str):
        """TTS playback for conversational responses"""
        # Basic implementation using OS native TTS
        try:
            if os.name == 'posix': # Linux / macOS
                if os.uname().sysname == 'Darwin':
                    os.system(f'say "{text}"')
                else:
                    # Linux fallback (requires espeak or similar)
                    os.system(f'espeak "{text}" 2>/dev/null || echo "{text}"')
            elif os.name == 'nt': # Windows
                # Simple windows toast or similar? 
                # For now just use simple print if wsay etc aren't installed
                logger.info(f"OminClaw says: {text}")
            
            logger.info(f"Agent says: {text}")
        except Exception as e:
            logger.error(f"TTS Error: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    async def main():
        vw = VoiceWakeSystem(hotword="hey omni")
        if await vw.initialize():
            await vw.start_listening()
            print("Listening... say 'hey omni' and a command (or CTRL+C to stop)")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await vw.stop_listening()
        
    asyncio.run(main())
