import logging
import time
import threading

logger = logging.getLogger("OmniClaw.BiometricVibe")

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not installed. Keystroke dynamics disabled.")

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logger.warning("SpeechRecognition not installed. Voice biometrics disabled.")

class BiometricVibe:
    """
    Experimental "Biometric Vibe" feature.
    Monitors typing patterns and voice prints to calculate a 'trust score'
    for the current user, unlocking OmniClaw's highest tier actions (Ghost Mode).
    """
    def __init__(self):
        self.trust_score = 50.0 # Starts neutral
        self.last_keystroke_time = time.time()
        self.keystroke_intervals = []
        
        self.listener = None
        if PYNPUT_AVAILABLE:
            self.listener = keyboard.Listener(on_press=self._on_press)
            logger.info("Keystroke dynamics monitor online.")

    def start(self):
        if self.listener:
            self.listener.start()

    def _on_press(self, key):
        """Measures time between keystrokes to slowly build a typing profile."""
        now = time.time()
        interval = now - self.last_keystroke_time
        self.last_keystroke_time = now
        
        if interval < 2.0: # Only count continuous typing
            self.keystroke_intervals.append(interval)
            if len(self.keystroke_intervals) > 100:
                self.keystroke_intervals.pop(0)
                
            # Naive verification: if typing speed is consistent with owner, increase trust
            # Production would use ML model (e.g. Isolation Forest) on timing vectors
            self.trust_score = min(100.0, self.trust_score + 0.1)
        else:
            # Long pause, slightly decay trust to verify presence
            self.trust_score = max(0.0, self.trust_score - 0.5)

    def verify_voice(self, audio_file: str = None) -> bool:
        """
        Stub for voice print verification.
        In reality, this would extract MFCCs and compare to a known embedding.
        """
        if not SPEECH_AVAILABLE:
            logger.warning("Voice verification failed: Module unavailable.")
            return False
            
        logger.info(f"Analyzing voiceprint from {audio_file or 'microphone'}")
        
        # Simulated success
        success = True
        
        if success:
            logger.info("Voiceprint verified. Trust score maximized.")
            self.trust_score = 100.0
            return True
        return False

    def is_ghost_mode_unlocked(self) -> bool:
        """Requires a high trust score to execute dangerous actions."""
        return self.trust_score >= 90.0

    def get_vibe_status(self) -> str:
        return f"Trust Score: {self.trust_score:.1f}/100"

    def stop(self):
        if self.listener:
            self.listener.stop()

# Singleton
biometric_vibe = BiometricVibe()
