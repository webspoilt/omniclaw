import asyncio
import logging

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SDRIntelligence")

class SDRIntelligenceService:
    def __init__(self, sample_rate: float = 2.048e6, center_freq: float = 433.92e6, gain: str = 'auto'):
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain
        self.sdr = None
        self.simulator_mode = False

        # Attempt to import rtlsdr
        try:
            from rtlsdr import RtlSdr
            logger.info("RtlSdr library imported successfully. Initializing hardware...")
            self.sdr = RtlSdr()
            self.sdr.sample_rate = self.sample_rate
            self.sdr.center_freq = self.center_freq
            self.sdr.gain = self.gain
            logger.info(f"RTL-SDR hardware initialized at {self.center_freq / 1e6:.3f} MHz")
        except Exception as e:
            logger.warning(f"Could not initialize RTL-SDR hardware ({e}). Switching to simulator mode.")
            self.simulator_mode = True

        # Pre-configured baseline device fingerprints for verification (Center Freq Offset, Spectral Entropy, Flatness)
        self.fingerprint_baselines = {
            "authorized_transmitter_1": {"offset_hz": 1500.0, "entropy": 5.2, "flatness": 0.12},
            "authorized_transmitter_2": {"offset_hz": -800.0, "entropy": 4.8, "flatness": 0.08}
        }

    def generate_synthetic_samples(self, num_samples: int = 1024) -> np.ndarray:
        """Generates synthetic complex I/Q samples (sine wave + noise) for testing."""
        t = np.arange(num_samples) / self.sample_rate

        # Simulate a small frequency offset (e.g. 1200 Hz carrier offset from center frequency)
        freq_offset = 1200.0
        carrier = np.exp(2j * np.pi * freq_offset * t)

        # Add thermal noise (Gaussian complex noise)
        noise_std = 0.5
        noise = (np.random.normal(0, noise_std, num_samples) +
                 1j * np.random.normal(0, noise_std, num_samples))

        # Combine
        samples = carrier + noise
        return samples

    def capture_samples(self, num_samples: int = 1024) -> np.ndarray:
        """Captures raw I/Q samples from the hardware or the simulator."""
        if self.simulator_mode or not self.sdr:
            return self.generate_synthetic_samples(num_samples)
        try:
            return self.sdr.read_samples(num_samples)
        except Exception as e:
            logger.error(f"Hardware read error: {e}. Falling back to simulation.")
            return self.generate_synthetic_samples(num_samples)

    def extract_features(self, samples: np.ndarray) -> dict:
        """Performs FFT on raw I/Q samples and extracts spectral fingerprint features."""
        # 1. Compute FFT and Power Spectral Density
        fft_res = np.fft.fft(samples)
        psd = np.abs(fft_res) ** 2
        psd_norm = psd / np.sum(psd)

        # 2. Estimate Center Frequency Offset (Peak Frequency index)
        freqs = np.fft.fftfreq(len(samples), 1 / self.sample_rate)
        peak_idx = np.argmax(psd)
        freq_offset = freqs[peak_idx]

        # 3. Compute Spectral Entropy (information content / complexity)
        spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-12))

        # 4. Compute Spectral Flatness (Wiener entropy: geometric mean / arithmetic mean)
        # Avoid zero elements
        psd_safe = psd + 1e-12
        geo_mean = np.exp(np.mean(np.log(psd_safe)))
        arith_mean = np.mean(psd_safe)
        spectral_flatness = geo_mean / arith_mean

        return {
            "offset_hz": float(freq_offset),
            "entropy": float(spectral_entropy),
            "flatness": float(spectral_flatness),
            "peak_power": float(np.max(psd))
        }

    def verify_fingerprint(self, features: dict) -> tuple:
        """Verifies if the extracted RF fingerprint matches authorized transmitters."""
        tolerance = {"offset_hz": 500.0, "entropy": 0.5, "flatness": 0.05}

        for name, baseline in self.fingerprint_baselines.items():
            offset_diff = abs(features["offset_hz"] - baseline["offset_hz"])
            entropy_diff = abs(features["entropy"] - baseline["entropy"])
            flatness_diff = abs(features["flatness"] - baseline["flatness"])

            if (offset_diff <= tolerance["offset_hz"] and
                entropy_diff <= tolerance["entropy"] and
                flatness_diff <= tolerance["flatness"]):
                return True, name

        return False, "Unknown/Unauthenticated Transmitter"

    async def run_loop(self):
        """Asynchronous execution loop for the SIGINT pipeline."""
        logger.info("SDR Intelligence Service: Main loop active.")
        try:
            while True:
                # Capture and process I/Q samples
                samples = self.capture_samples(2048)
                features = self.extract_features(samples)

                # Verify fingerprint
                auth, match_name = self.verify_fingerprint(features)

                # Log outcome
                log_msg = (f"Capture - Freq Offset: {features['offset_hz']:.1f}Hz, "
                           f"Entropy: {features['entropy']:.3f}, Flatness: {features['flatness']:.4f} | "
                           f"Status: {'AUTHORIZED ('+match_name+')' if auth else 'ANOMALY DETECTED ('+match_name+')'}")

                if auth:
                    logger.info(log_msg)
                else:
                    logger.warning(log_msg)

                # Periodic scanning interval
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Main loop task cancelled.")
        finally:
            if self.sdr:
                try:
                    self.sdr.close()
                    logger.info("RTL-SDR interface closed safely.")
                except Exception as e:
                    logger.error(f"Error closing SDR: {e}")

async def main():
    service = SDRIntelligenceService()
    # Configure loop to run for a short duration or indefinitely
    try:
        await asyncio.wait_for(service.run_loop(), timeout=15)
    except TimeoutError:
        logger.info("Verification timeout reached. Service shutting down.")

if __name__ == "__main__":
    asyncio.run(main())
