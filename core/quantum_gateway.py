import os
import logging
import json

logger = logging.getLogger("OmniClaw.QuantumGateway")

QISKIT_AVAILABLE = None # Will be determined lazily

class QuantumGateway:
    """
    Gateway to execute Quantum Assembly (OpenQASM 3) on IBM Quantum hardware or simulators.
    Requires IBM_QUANTUM_TOKEN to be set in the environment or .env file.
    """
    def __init__(self):
        self.service = None
        self.backend = None
        self.initialized = False

    def _lazy_init(self):
        global QISKIT_AVAILABLE
        if self.initialized:
            return

        try:
            import qiskit
            import qiskit_ibm_runtime
            QISKIT_AVAILABLE = True
        except ImportError:
            QISKIT_AVAILABLE = False
            logger.warning("Qiskit not installed. QuantumGateway going into simulation mode.")
            self.initialized = True
            return

        token = os.getenv("IBM_QUANTUM_TOKEN")
        if not token:
            logger.warning("IBM_QUANTUM_TOKEN not found. QuantumGateway will not be able to execute circuits.")
            self.initialized = True
            return
            
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            self.service = QiskitRuntimeService(channel="ibm_quantum", token=token)
            # Use simulator by default to save quantum compute credits
            self.backend = self.service.backend("ibm_brisbane") # Use actual hardware if needed, else fake/sim
            logger.info("QuantumGateway initialized successfully via IBM Quantum.")
        except Exception as e:
            logger.error(f"Failed to initialize QiskitRuntimeService: {e}")
        finally:
            self.initialized = True

    def execute_qasm(self, qasm_string: str) -> dict:
        """
        Executes an OpenQASM 3 script and returns the result probabilities/counts.
        """
        self._lazy_init()
        
        if not QISKIT_AVAILABLE or not self.service:
            return {"error": "Quantum backend unavailable. Please check Qiskit installation and API tokens.", "qasm_received": qasm_string}

        try:
            from qiskit import QuantumCircuit
            from qiskit_ibm_runtime import Session, SamplerV2
            
            # Build circuit from QASM
            circuit = QuantumCircuit.from_qasm_str(qasm_string)
            
            # Use Sampler to get quasi-probabilities
            with Session(service=self.service, backend=self.backend) as session:
                sampler = SamplerV2(session=session)
                job = sampler.run([circuit])
                result = job.result()
                
                # Format output
                pub_result = result[0]
                counts = pub_result.data.meas.get_counts()
                
            return {"status": "success", "counts": counts}
        except Exception as e:
            logger.error(f"Quantum execution failed: {e}")
            return {"status": "error", "message": str(e)}

# Singleton
quantum_gateway = QuantumGateway()
