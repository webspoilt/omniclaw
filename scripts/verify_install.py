#!/usr/bin/env python3
import sys
import platform

print("=== OmniClaw Pre-Flight System Verification ===")
print(f"System: {platform.system()} {platform.release()}")
print(f"Python Version: {platform.python_version()}")

def check_python_version():
    """Verify strictly >= 3.9"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ FAILED: Python version must be 3.9 or higher.")
        sys.exit(1)
    print("✅ Python Version Check Passed")

def check_dependencies():
    """Verify critical external modules"""
    critical_deps = {
        "telegram": "python-telegram-bot",
        "discord": "discord.py",
        "slack_sdk": "slack-sdk",
        "speech_recognition": "SpeechRecognition",
        "pyaudio": "PyAudio",
        "numpy": "numpy",
        "openai": "openai",
        "anthropic": "anthropic"
    }
    
    missing = []
    
    for module_name, pip_name in critical_deps.items():
        try:
            __import__(module_name)
            print(f"  ✅ {module_name} (from {pip_name}) installed")
        except ImportError:
            print(f"  ❌ MISSING: {module_name}")
            missing.append(pip_name)
            
    if missing:
        print("\n❌ FAILED: Missing dependencies detected.")
        print("Please run: pip install " + " ".join(missing))
        sys.exit(1)
    print("\n✅ All core dependencies successfully installed.")

if __name__ == "__main__":
    check_python_version()
    print("\nVerifying external modules...")
    check_dependencies()
    print("\n🎉 Verification Complete! System is ready to deploy OmniClaw.")
    sys.exit(0)
