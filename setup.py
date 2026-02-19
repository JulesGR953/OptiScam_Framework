"""
Setup and verification script for OptiScam system.
Checks dependencies, downloads models, and verifies installation.
"""

import sys
import subprocess
import importlib
import os


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    print("\nChecking FFmpeg...")
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ {version_line}")
            return True
        else:
            print("❌ FFmpeg found but not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg not found")
        print("   Install FFmpeg:")
        print("   - Windows: choco install ffmpeg  OR  scoop install ffmpeg")
        print("   - Download: https://ffmpeg.org/download.html")
        return False


def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} not installed")
        return False


def check_dependencies():
    """Check all required Python packages."""
    print("\nChecking Python packages...")

    packages = [
        ('torch', 'torch'),
        ('torchvision', 'torchvision'),
        ('transformers', 'transformers'),
        ('opencv-python', 'cv2'),
        ('Pillow', 'PIL'),
        ('rapidocr-onnxruntime', 'rapidocr_onnxruntime'),
        ('openai-whisper', 'whisper'),
        ('numpy', 'numpy'),
    ]

    all_installed = True
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            all_installed = False

    return all_installed


def check_cuda():
    """Check if CUDA is available."""
    print("\nChecking CUDA availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available")
            print(f"  - Device: {torch.cuda.get_device_name(0)}")
            print(f"  - CUDA version: {torch.version.cuda}")
            return True
        else:
            print("⚠️  CUDA not available (CPU mode will be used)")
            return False
    except ImportError:
        print("❌ Cannot check CUDA (torch not installed)")
        return False


def download_models():
    """Test model downloads."""
    print("\nTesting model downloads...")
    print("This may take a while on first run...\n")

    try:
        # Test Whisper
        print("1. Testing Whisper model...")
        import whisper
        model = whisper.load_model("tiny")  # Use tiny for quick test
        print("✓ Whisper model loaded")
        del model

        # Test TrOCR
        print("\n2. Testing TrOCR model...")
        from transformers import TrOCRProcessor
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        print("✓ TrOCR model loaded")
        del processor

        # Note about Qwen
        print("\n3. Qwen2-VL-2B-Instruct (~4GB)")
        print("   This model will be downloaded on first use")
        print("   Set TRANSFORMERS_CACHE environment variable to customize location")

        return True

    except Exception as e:
        print(f"❌ Error downloading models: {str(e)}")
        return False


def setup_cache_dir():
    """Setup model cache directory."""
    print("\nSetting up cache directory...")

    cache_dir = os.path.join(os.path.dirname(__file__), 'models_cache')
    os.makedirs(cache_dir, exist_ok=True)

    print(f"✓ Cache directory: {cache_dir}")
    print("\nTo use this cache directory, set:")
    print(f"  os.environ['TRANSFORMERS_CACHE'] = r'{cache_dir}'")

    return cache_dir


def run_quick_test():
    """Run a quick system test."""
    print("\n" + "="*60)
    print("Running Quick System Test")
    print("="*60)

    try:
        from image_processing import ImageProcessing
        from text_extraction import TextExtractor
        from audio_transcription import AudioTranscriber

        print("\n1. Testing ImageProcessing...")
        img_proc = ImageProcessing()
        print("✓ ImageProcessing initialized")

        print("\n2. Testing TextExtractor...")
        text_ext = TextExtractor(use_trocr_fallback=False)
        print("✓ TextExtractor initialized")

        print("\n3. Testing AudioTranscriber...")
        transcriber = AudioTranscriber(model_size='tiny')
        print("✓ AudioTranscriber initialized")

        print("\n✓ All components working!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("Setup Complete! Next Steps:")
    print("="*60)
    print("""
1. Run basic analysis:
   python main.py path/to/your/video.mp4

2. Run with custom options:
   python main.py video.mp4 --frame-interval 30 --whisper-model base

3. See example usage:
   python example_usage.py

4. Read documentation:
   - README.md for full documentation
   - example_usage.py for code examples

5. Troubleshooting:
   - CUDA: Install PyTorch with CUDA support for GPU acceleration
   - FFmpeg: Required for audio extraction from videos
   - Memory: Use smaller models (--whisper-model tiny) if low on RAM
""")


def main():
    """Run complete setup and verification."""
    print("="*60)
    print("OptiScam Setup and Verification")
    print("="*60)

    checks = []

    # Python version
    checks.append(("Python Version", check_python_version()))

    # FFmpeg
    checks.append(("FFmpeg", check_ffmpeg()))

    # Dependencies
    checks.append(("Python Packages", check_dependencies()))

    # CUDA (optional)
    cuda_available = check_cuda()

    # Summary
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)

    for name, status in checks:
        status_str = "✓ PASS" if status else "❌ FAIL"
        print(f"{name:.<40} {status_str}")

    all_passed = all(status for _, status in checks)

    if not all_passed:
        print("\n⚠️  Some checks failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        return False

    # Setup cache
    setup_cache_dir()

    # Test models
    if input("\nDownload and test models? (y/n): ").lower().strip() == 'y':
        download_models()

    # Quick test
    if input("\nRun quick system test? (y/n): ").lower().strip() == 'y':
        if run_quick_test():
            print_next_steps()
            return True
        else:
            print("\n⚠️  System test failed. Check error messages above.")
            return False
    else:
        print_next_steps()
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
