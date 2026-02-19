"""
Quick test script for holistic video analysis.
Run this to verify your setup is working correctly.
"""

import sys
from pathlib import Path
from main import OptiScamAnalyzer


def test_holistic_analysis():
    """
    Test the holistic analysis pipeline.
    """
    print("="*70)
    print(" OptiScam Holistic Analysis - Test Script")
    print("="*70)
    print()

    # Get video path from user
    video_path = input("Enter path to test video (or press Enter for example): ").strip()

    if not video_path:
        print("\n⚠️  No video provided. Using example configuration.")
        print("   To test with a real video, run: python test_holistic.py")
        print("   Or edit this file to add your video path.")
        return

    if not Path(video_path).exists():
        print(f"\n❌ Error: Video file not found: {video_path}")
        print("   Please check the path and try again.")
        return

    # Get optional metadata
    print("\n" + "-"*70)
    print("Optional: Provide video metadata (or press Enter to skip)")
    print("-"*70)

    title = input("Video Title: ").strip() or None
    description = input("Video Description: ").strip() or None

    print("\n" + "="*70)
    print(" Starting Analysis...")
    print("="*70)
    print()

    # Initialize analyzer
    try:
        print("Loading models (this may take a minute on first run)...")
        analyzer = OptiScamAnalyzer()
        print("✓ Models loaded successfully!")
        print()
    except Exception as e:
        print(f"❌ Error loading models: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Ensure you have enough GPU/CPU memory")
        print("3. Check that model files can be downloaded from HuggingFace")
        return

    # Run holistic analysis
    try:
        print("-"*70)
        print(" Running Holistic Analysis")
        print("-"*70)
        print(f"Video: {video_path}")
        if title:
            print(f"Title: {title}")
        if description:
            print(f"Description: {description[:100]}..." if len(description) > 100 else f"Description: {description}")
        print()

        results = analyzer.analyze_video_holistic(
            video_path=video_path,
            title=title,
            description=description
        )

        # Display results
        print("\n" + "="*70)
        print(" SCAM ANALYSIS RESULT")
        print("="*70)
        print()
        print(results['scam_analysis'])
        print()

        # Additional info
        print("="*70)
        print(" Analysis Summary")
        print("="*70)

        if results.get('audio_transcription'):
            transcript = results['audio_transcription']['full_text']
            print(f"\n📢 Audio Transcript ({results['audio_transcription']['language']}):")
            print(f"   {transcript[:200]}..." if len(transcript) > 200 else f"   {transcript}")

        if results.get('ocr_text'):
            print(f"\n📝 Text Detected in Video:")
            print(f"   {results['ocr_text'][:200]}..." if len(results['ocr_text']) > 200 else f"   {results['ocr_text']}")

        print(f"\n💾 Full report saved to: {results['output_dir']}")
        print("   • holistic_analysis_report.json (detailed JSON)")
        print("   • scam_analysis_summary.txt (human-readable)")

        print("\n" + "="*70)
        print(" ✓ Test Complete!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Make sure the video file is valid and not corrupted")
        print("2. Check that you have enough disk space for temporary files")
        print("3. Verify GPU/CPU has enough memory (try smaller Whisper model)")
        return


def test_with_example_metadata():
    """
    Test with example scam video metadata (no actual video needed).
    """
    print("="*70)
    print(" Testing with Example Scam Metadata")
    print("="*70)
    print()

    # Example scam scenarios
    examples = [
        {
            'name': 'Phishing Scam',
            'title': 'URGENT: Your Account Has Been Suspended',
            'description': 'Click this link to verify your account within 24 hours or it will be permanently deleted!'
        },
        {
            'name': 'Investment Scam',
            'title': 'Make $10,000 Per Day - Guaranteed Returns!',
            'description': 'Join my exclusive trading course. Limited spots! 500% ROI guaranteed!'
        },
        {
            'name': 'Fake Giveaway',
            'title': 'FREE iPhone 15 Pro Max Giveaway!',
            'description': 'Click here to claim your free iPhone! Only 10 left! Hurry!'
        }
    ]

    print("Example scam scenarios loaded:")
    for i, ex in enumerate(examples, 1):
        print(f"{i}. {ex['name']}")

    print("\nNote: This demonstrates the prompt structure.")
    print("To run actual analysis, you need a video file.\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Video path provided as argument
        video_path = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else None
        description = sys.argv[3] if len(sys.argv) > 3 else None

        analyzer = OptiScamAnalyzer()
        results = analyzer.analyze_video_holistic(
            video_path=video_path,
            title=title,
            description=description
        )

        print(results['scam_analysis'])
    else:
        # Interactive mode
        test_holistic_analysis()
