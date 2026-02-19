"""
Example usage of the OptiScam video analysis system.
This demonstrates different ways to use the system programmatically.
"""

from main import OptiScamAnalyzer
from image_processing import ImageProcessing
from text_extraction import TextExtractor
from audio_transcription import AudioTranscriber
from Qwen3_VL_2B import Qwen3VLModel
import json


def example_1_basic_analysis():
    """Example 1: Basic video analysis with default settings."""
    print("="*60)
    print("Example 1: Basic Video Analysis")
    print("="*60)

    analyzer = OptiScamAnalyzer()
    results = analyzer.process_video(
        video_path='path/to/your/video.mp4',
        frame_interval=30
    )

    print(f"\nAnalysis complete!")
    print(f"- Frames analyzed: {len(results['frames'])}")
    print(f"- Text timestamps: {len(results['text_timeline'])}")
    print(f"- Output directory: {results['output_dir']}")


def example_2_custom_config():
    """Example 2: Custom configuration for specific use case."""
    print("\n" + "="*60)
    print("Example 2: Custom Configuration")
    print("="*60)

    # Configure for high-quality analysis
    config = {
        'sharpness_threshold': 150.0,      # Higher threshold = only very sharp frames
        'whisper_model_size': 'medium',    # Better transcription quality
        'use_trocr_fallback': True,        # Enable TrOCR for difficult text
        'trocr_confidence_threshold': 0.6  # Higher bar for RapidOCR
    }

    analyzer = OptiScamAnalyzer(config=config)
    results = analyzer.process_video(
        video_path='path/to/your/video.mp4',
        frame_interval=15,  # More frames
        use_sharpness_filter=True,
        analyze_frames=True
    )

    print(f"\nHigh-quality analysis complete!")
    print(f"Results saved to: {results['output_dir']}")


def example_3_quick_ocr_only():
    """Example 3: Quick OCR-only analysis (no frame analysis)."""
    print("\n" + "="*60)
    print("Example 3: Quick OCR-Only Analysis")
    print("="*60)

    config = {
        'whisper_model_size': 'tiny',  # Fast transcription
        'sharpness_threshold': 80.0     # Lower threshold = more frames
    }

    analyzer = OptiScamAnalyzer(config=config)
    results = analyzer.process_video(
        video_path='path/to/your/video.mp4',
        frame_interval=60,           # Fewer frames
        analyze_frames=False         # Skip vision model analysis
    )

    # Access OCR results
    print(f"\nOCR Results:")
    for timestamp, texts in results['text_timeline'].items():
        print(f"\n[{timestamp:.2f}s]")
        for text_item in texts:
            print(f"  - {text_item['text']}")


def example_4_individual_components():
    """Example 4: Using individual components separately."""
    print("\n" + "="*60)
    print("Example 4: Individual Components")
    print("="*60)

    # 1. Frame extraction with sharpness filtering
    img_processor = ImageProcessing(sharpness_threshold=100.0)
    frame_metadata = img_processor.sample_frames_by_sharpness(
        video_path='path/to/your/video.mp4',
        interval=30,
        output_dir='frames_output',
        use_sharpness_filter=True
    )
    print(f"Extracted {len(frame_metadata)} frames")

    # 2. Text extraction
    text_extractor = TextExtractor(use_trocr_fallback=True)
    text_detections = text_extractor.extract_text_from_frames(frame_metadata)
    text_timeline = text_extractor.get_text_timeline(text_detections)
    print(f"Found text in {len(text_timeline)} timestamps")

    # 3. Audio transcription
    transcriber = AudioTranscriber(model_size='base')
    transcription = transcriber.transcribe_video('path/to/your/video.mp4')
    print(f"Transcription: {transcription['text'][:100]}...")

    # 4. Visual analysis
    vision_model = Qwen3VLModel()
    analyses = vision_model.analyze_frames_for_scams(frame_metadata[:5])  # First 5 frames
    print(f"Analyzed {len(analyses)} frames")


def example_5_context_aware_analysis():
    """Example 5: Context-aware analysis with custom prompts."""
    print("\n" + "="*60)
    print("Example 5: Context-Aware Analysis")
    print("="*60)

    # First, get OCR and audio data
    analyzer = OptiScamAnalyzer()
    results = analyzer.process_video(
        video_path='path/to/your/video.mp4',
        frame_interval=30,
        analyze_frames=False  # We'll do custom analysis
    )

    # Now do custom context-aware analysis
    vision_model = Qwen3VLModel()

    custom_prompt = """
    Analyze this frame for scam indicators:
    1. Check if visual content matches the spoken/written claims
    2. Look for manipulated images or deepfakes
    3. Identify pressure tactics or urgency language
    4. Flag suspicious URLs or contact information
    5. Note any impersonation of known brands/people

    Given context: {context}

    Provide specific evidence for any red flags found.
    """

    for frame_info in results['frames'][:3]:  # First 3 frames
        timestamp = frame_info['timestamp']

        # Build context
        context = {
            'timestamp': timestamp,
            'ocr_text': '',
            'transcription': ''
        }

        # Add OCR text
        if timestamp in results['text_timeline']:
            texts = [item['text'] for item in results['text_timeline'][timestamp]]
            context['ocr_text'] = ' '.join(texts)

        # Add audio transcription
        if results.get('audio_transcription'):
            audio_text = analyzer.audio_transcriber.get_text_at_timestamp(
                results['audio_transcription'], timestamp
            )
            if audio_text:
                context['transcription'] = audio_text

        # Analyze with context
        analysis = vision_model.analyze_with_context(
            frame_info['path'],
            context,
            custom_prompt
        )

        print(f"\n[Frame @ {timestamp:.2f}s]")
        print(f"Analysis: {analysis[:200]}...")


def example_6_batch_processing():
    """Example 6: Batch process multiple videos."""
    print("\n" + "="*60)
    print("Example 6: Batch Processing")
    print("="*60)

    video_files = [
        'path/to/video1.mp4',
        'path/to/video2.mp4',
        'path/to/video3.mp4'
    ]

    analyzer = OptiScamAnalyzer()

    for video_path in video_files:
        print(f"\nProcessing: {video_path}")
        try:
            results = analyzer.process_video(
                video_path=video_path,
                frame_interval=60,  # Quick analysis
                analyze_frames=False
            )
            print(f"✓ Complete: {results['output_dir']}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")


def example_7_export_results():
    """Example 7: Export and process results."""
    print("\n" + "="*60)
    print("Example 7: Export Results")
    print("="*60)

    analyzer = OptiScamAnalyzer()
    results = analyzer.process_video(
        video_path='path/to/your/video.mp4',
        frame_interval=30
    )

    # Results are already saved to JSON and TXT
    # Load and process them
    with open(f"{results['output_dir']}/analysis_report.json", 'r') as f:
        data = json.load(f)

    # Extract all detected text
    all_text = []
    for timestamp, texts in data['text_timeline'].items():
        for text_item in texts:
            all_text.append({
                'time': float(timestamp),
                'text': text_item['text'],
                'confidence': text_item['confidence']
            })

    # Sort by confidence
    sorted_by_confidence = sorted(all_text, key=lambda x: x['confidence'], reverse=True)

    print("\nTop 5 highest confidence text detections:")
    for item in sorted_by_confidence[:5]:
        print(f"  {item['text']} (confidence: {item['confidence']:.2f})")

    # Count suspicious keywords
    suspicious_keywords = ['urgent', 'limited time', 'act now', 'verify', 'suspended']
    full_transcription = data['audio_transcription']['full_text'].lower()

    found_keywords = [kw for kw in suspicious_keywords if kw in full_transcription]
    if found_keywords:
        print(f"\n⚠️  Suspicious keywords found: {', '.join(found_keywords)}")


def main():
    """Run all examples (comment out those you don't want to run)."""
    print("OptiScam Video Analysis - Example Usage\n")

    # Uncomment the examples you want to run:

    # example_1_basic_analysis()
    # example_2_custom_config()
    # example_3_quick_ocr_only()
    # example_4_individual_components()
    # example_5_context_aware_analysis()
    # example_6_batch_processing()
    # example_7_export_results()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == "__main__":
    main()
