import asyncio
import json
import logging
import time

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AcousticSidechannel")

# Conditional PyTorch importing to support uninstalled environments
TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
    logger.info("PyTorch detected. Loading PyTorch neural network modules.")
except ImportError:
    logger.warning("PyTorch not installed. Using numpy matrix math neural engine fallback.")

# ---------------------------------------------------------------------------
# Neural Network Models
# ---------------------------------------------------------------------------

if TORCH_AVAILABLE:
    class PyTorchKeystrokeCNN(nn.Module):
        def __init__(self, num_classes: int = 39, window_size: int = 100):
            super().__init__()
            # Input shape: [Batch, 3 channels (x, y, z), WindowSize]
            self.conv1 = nn.Conv1d(in_channels=3, out_channels=16, kernel_size=5, padding=2)
            self.relu1 = nn.ReLU()
            self.pool1 = nn.MaxPool1d(2)  # output size: [Batch, 16, WindowSize / 2]

            self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=5, padding=2)
            self.relu2 = nn.ReLU()
            self.pool2 = nn.MaxPool1d(2)  # output size: [Batch, 32, WindowSize / 4]

            # Linear fully connected classifier
            flat_features = 32 * (window_size // 4)
            self.fc1 = nn.Linear(flat_features, 64)
            self.relu3 = nn.ReLU()
            self.fc2 = nn.Linear(64, num_classes)

        def forward(self, x):
            x = self.pool1(self.relu1(self.conv1(x)))
            x = self.pool2(self.relu2(self.conv2(x)))
            x = x.view(x.size(0), -1)  # Flatten
            x = self.relu3(self.fc1(x))
            x = self.fc2(x)
            return x
else:
    # NumPy state-space matrix implementation of a simplified feedforward classifier
    class NumpyKeystrokeClassifier:
        def __init__(self, num_classes: int = 39, window_size: int = 100):
            self.window_size = window_size
            self.num_classes = num_classes
            # Pseudo weights initialized deterministically
            np.random.seed(42)
            self.w1 = np.random.randn(3 * window_size, 64) * 0.01
            self.b1 = np.zeros((1, 64))
            self.w2 = np.random.randn(64, num_classes) * 0.01
            self.b2 = np.zeros((1, num_classes))

        def predict(self, raw_window: np.ndarray) -> np.ndarray:
            # Flatten raw window: [3, 100] -> [300]
            x = raw_window.flatten().reshape(1, -1)
            # Layer 1
            h1 = np.maximum(0, np.dot(x, self.w1) + self.b1)
            # Layer 2
            logits = np.dot(h1, self.w2) + self.b2
            # Softmax
            exp_logits = np.exp(logits - np.max(logits))
            return exp_logits / np.sum(exp_logits)

# ---------------------------------------------------------------------------
# Key Class Map
# ---------------------------------------------------------------------------
CLASSES = [chr(i) for i in range(ord('a'), ord('z') + 1)] + \
          [str(i) for i in range(10)] + \
          ["space", "backspace", "enter"]

# ---------------------------------------------------------------------------
# Real-Time Accelerometer Stream Processor
# ---------------------------------------------------------------------------

class AcousticSidechannelService:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, window_size: int = 100):
        self.host = host
        self.port = port
        self.window_size = window_size

        # Load classifier model
        if TORCH_AVAILABLE:
            self.model = PyTorchKeystrokeCNN(len(CLASSES), self.window_size)
            self.model.eval()
        else:
            self.model = NumpyKeystrokeClassifier(len(CLASSES), self.window_size)

        # Accelerometer rolling buffer: shape [3, window_size]
        self.buffer = np.zeros((3, self.window_size))
        self.samples_collected = 0

    def process_accelerometer_frame(self, x: float, y: float, z: float) -> str:
        """Pushes a new accelerometer frame onto the rolling buffer and runs prediction."""
        # Shift buffer and insert new reading
        self.buffer = np.roll(self.buffer, -1, axis=1)
        self.buffer[:, -1] = [x, y, z]
        self.samples_collected += 1

        # We need a full window of context before performing inference
        if self.samples_collected < self.window_size:
            return None

        # Detect transient threshold (spikes) signifying a key press event
        # Typically the Z axis accelerometer sees a rapid spike on keyboard tap
        z_derivative = abs(self.buffer[2, -1] - self.buffer[2, -2])
        if z_derivative > 1.2:  # Threshold for keystroke transient detection
            logger.info("Keystroke transient spike detected! Running NN classifier...")
            if TORCH_AVAILABLE:
                with torch.no_grad():
                    input_tensor = torch.tensor(self.buffer, dtype=torch.float32).unsqueeze(0)
                    outputs = self.model(input_tensor)
                    probabilities = torch.softmax(outputs, dim=1).numpy()[0]
            else:
                probabilities = self.model.predict(self.buffer)[0]

            predicted_idx = np.argmax(probabilities)
            conf = probabilities[predicted_idx]
            predicted_char = CLASSES[predicted_idx]
            logger.info(f"Predicted character: '{predicted_char}' (Confidence: {conf:.2%})")
            return predicted_char
        return None

    async def handle_connection(self, websocket):
        """Processes real-time WebSocket connection streaming accelerometer JSON frames."""
        logger.info("New client connected to acoustic sidechannel stream.")
        try:
            async for message in websocket:
                data = json.loads(message)
                x = data.get("x", 0.0)
                y = data.get("y", 0.0)
                z = data.get("z", 0.0)

                result = self.process_accelerometer_frame(x, y, z)
                if result:
                    await websocket.send(json.dumps({
                        "event": "keystroke_reconstructed",
                        "character": result,
                        "timestamp": time.time()
                    }))
        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
        finally:
            logger.info("Client disconnected from stream.")

    async def simulate_tap_stream(self):
        """Simulates real-time keyboard tapping inputs to test pipeline end-to-end."""
        logger.info("Running typing stream simulation engine...")
        t = 0
        while True:
            # Generate static baseline gravity (Z close to 9.8) + minor noise
            x = np.random.normal(0, 0.05)
            y = np.random.normal(0, 0.05)
            z = 9.81 + np.random.normal(0, 0.05)

            # Periodically inject a synthetic key press spike (every 2.5 seconds)
            if t % 50 == 0 and t > 0:
                z += np.random.choice([3.5, -3.5])  # Shock wave tap

            predicted = self.process_accelerometer_frame(x, y, z)
            if predicted:
                logger.info(f"[SIMULATOR] Reconstructed keystroke: '{predicted}'")

            t += 1
            await asyncio.sleep(0.05)  # 20 Hz sample rate

async def main():
    service = AcousticSidechannelService()

    # We will run the simulation loop for 15 seconds to verify model runs properly
    try:
        await asyncio.wait_for(service.simulate_tap_stream(), timeout=15)
    except TimeoutError:
        logger.info("Acoustic sidechannel simulation ended successfully.")

if __name__ == "__main__":
    asyncio.run(main())
