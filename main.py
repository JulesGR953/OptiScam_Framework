import os
import json
from datetime import datetime
from pathlib import Path
import argparse

from image_processing import ImageProcessing
from text_extraction import TextExtractor
from audio_transcription import AudioTranscriber
from Qwen3_VL_2B import Qwen3VLModel


class OptiScamAnalyzer:
    def __init__(self, config=None):
        """
        Initialize the OptiScam video analysis system.

        :param config: Configuration dictionary for all components
        """
        self.config = config or {}

        # Initialize components
        print("Initializing OptiScam Analyzer...")

        # Image processing with CLAHE and sharpness filtering
        self.image_processor = ImageProcessing(
            clip_limit=self.config.get('clahe_clip_limit', 2.0),
            tile_grid_size=self.config.get('clahe_tile_grid_size', (8, 8)),
            sharpness_threshold=self.config.get('sharpness_threshold', 100.0)
        )

        # Text extraction with RapidOCR + TrOCR
        self.text_extractor = TextExtractor(
            use_trocr_fallback=self.config.get('use_trocr_fallback', True),
            trocr_confidence_threshold=self.config.get('trocr_confidence_threshold', 0.5)
        )

        # Audio transcription with Whisper
        self.audio_transcriber = AudioTranscriber(
            model_size=self.config.get('whisper_model_size', 'tiny'),
            language=self.config.get('whisper_language', None),
            device=self.config.get('device', None)
        )

        # Qwen3-VL-2B for visual analysis
        self.vision_model = Qwen3VLModel(
            model_name=self.config.get('vision_model_name', 'unsloth/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit'),
            device=self.config.get('device', None)
        )

        print("All components initialized successfully!\n")

    def process_video(self, video_path, output_dir=None, frame_interval=30,
                      use_sharpness_filter=True, analyze_frames=True):
        """
        Process a video through the complete analysis pipeline.

        :param video_path: Path to video file
        :param output_dir: Directory for outputs (created if doesn't exist)
        :param frame_interval: Extract every N frames
        :param use_sharpness_filter: Use Laplacian Variance sharpness filtering
        :param analyze_frames: Run Qwen3-VL analysis on frames
        :return: Complete analysis results
        """
        print(f"\n{'='*60}")
        print(f"Processing video: {video_path}")
        print(f"{'='*60}\n")

        # Setup output directory
        if output_dir is None:
            video_name = Path(video_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"output_{video_name}_{timestamp}"

        os.makedirs(output_dir, exist_ok=True)
        frames_dir = os.path.join(output_dir, "frames")

        results = {
            'video_path': video_path,
            'output_dir': output_dir,
            'timestamp': datetime.now().isoformat(),
            'config': self.config
        }

        # Step 1: Extract and process frames with sharpness filtering
        print("Step 1: Extracting frames with CLAHE and sharpness filtering...")
        frame_metadata = self.image_processor.sample_frames_by_sharpness(
            video_path=video_path,
            interval=frame_interval,
            output_dir=frames_dir,
            use_sharpness_filter=use_sharpness_filter
        )
        results['frames'] = frame_metadata
        print(f"Extracted {len(frame_metadata)} frames\n")

        # Step 2: Extract text from frames using RapidOCR + TrOCR
        print("Step 2: Extracting text from frames (RapidOCR + TrOCR)...")
        text_detections = self.text_extractor.extract_text_from_frames(frame_metadata)
        results['text_detections'] = text_detections

        # Organize text by timestamp
        text_timeline = self.text_extractor.get_text_timeline(text_detections)
        results['text_timeline'] = text_timeline
        print(f"Detected text in {len(text_timeline)} timestamps\n")

        # Step 3: Transcribe audio with Whisper
        print("Step 3: Transcribing audio with Whisper...")
        transcription = self.audio_transcriber.transcribe_video(
            video_path=video_path,
            extract_audio=True,
            temp_audio_path=os.path.join(output_dir, "temp_audio.mp3")
        )

        if transcription:
            audio_timeline = self.audio_transcriber.get_transcription_timeline(transcription)
            results['audio_transcription'] = {
                'full_text': transcription['text'],
                'timeline': audio_timeline,
                'language': transcription.get('language', 'unknown')
            }

            # Export transcription
            transcription_file = os.path.join(output_dir, "transcription.txt")
            self.audio_transcriber.export_transcription(
                transcription, transcription_file, format='txt'
            )
            print(f"Audio transcribed successfully\n")
        else:
            results['audio_transcription'] = None
            print("No audio transcription available\n")

        # Step 4: Analyze frames with Qwen3-VL-2B (optional)
        if analyze_frames and len(frame_metadata) > 0:
            print("Step 4: Analyzing frames with Qwen3-VL-2B-Instruct...")

            # Create context-aware analyses
            visual_analyses = []

            for frame_info in frame_metadata:
                timestamp = frame_info['timestamp']
                image_path = frame_info['path']

                # Gather context for this frame
                context = {'timestamp': timestamp}

                # Add OCR text from this timestamp
                if timestamp in text_timeline:
                    ocr_texts = [item['text'] for item in text_timeline[timestamp]]
                    context['ocr_text'] = " | ".join(ocr_texts)

                # Add audio transcription around this timestamp
                if transcription:
                    audio_text = self.audio_transcriber.get_text_at_timestamp(
                        transcription, timestamp
                    )
                    if audio_text:
                        context['transcription'] = audio_text

                # Analyze with context
                analysis = self.vision_model.analyze_with_context(image_path, context)

                visual_analyses.append({
                    'frame_id': frame_info['frame_id'],
                    'timestamp': timestamp,
                    'image_path': image_path,
                    'analysis': analysis,
                    'context': context
                })

            results['visual_analyses'] = visual_analyses
            print(f"Completed {len(visual_analyses)} frame analyses\n")
        else:
            results['visual_analyses'] = []

        # Step 5: Generate comprehensive report
        print("Step 5: Generating comprehensive report...")
        report_path = os.path.join(output_dir, "analysis_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Generate human-readable summary
        summary_path = os.path.join(output_dir, "summary.txt")
        self._generate_summary(results, summary_path)

        print(f"\n{'='*60}")
        print(f"Analysis complete! Results saved to: {output_dir}")
        print(f"{'='*60}\n")

        return results

    def analyze_video_holistic(self, video_path, title=None, description=None, output_dir=None):
        """
        Perform holistic video analysis with title and description context.
        The model analyzes the entire video along with metadata for scam detection.

        :param video_path: Path to video file
        :param title: Video title
        :param description: Video description
        :param output_dir: Directory for outputs (created if doesn't exist)
        :return: Comprehensive analysis results
        """
        print(f"\n{'='*60}")
        print(f"Holistic Video Analysis")
        print(f"{'='*60}\n")
        print(f"Video: {video_path}")
        if title:
            print(f"Title: {title}")
        if description:
            print(f"Description: {description[:100]}..." if len(description) > 100 else f"Description: {description}")
        print()

        # Setup output directory
        if output_dir is None:
            video_name = Path(video_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"output_{video_name}_{timestamp}_holistic"

        os.makedirs(output_dir, exist_ok=True)

        results = {
            'video_path': video_path,
            'title': title,
            'description': description,
            'output_dir': output_dir,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'holistic',
            'config': self.config
        }

        # Step 1: Extract audio transcription
        print("Step 1: Transcribing audio with Whisper...")
        transcription = self.audio_transcriber.transcribe_video(
            video_path=video_path,
            extract_audio=True,
            temp_audio_path=os.path.join(output_dir, "temp_audio.mp3")
        )

        full_transcription = None
        if transcription:
            full_transcription = transcription['text']
            results['audio_transcription'] = {
                'full_text': full_transcription,
                'language': transcription.get('language', 'unknown')
            }
            print(f"Audio transcribed successfully (Language: {transcription.get('language', 'unknown')})\n")
        else:
            results['audio_transcription'] = None
            print("No audio transcription available\n")

        # Step 2: Extract OCR text from sampled frames (for context only)
        print("Step 2: Extracting text from video frames...")
        frames_dir = os.path.join(output_dir, "frames")
        frame_metadata = self.image_processor.sample_frames_by_sharpness(
            video_path=video_path,
            interval=60,  # Sample less frequently for holistic analysis
            output_dir=frames_dir,
            use_sharpness_filter=True
        )

        text_detections = self.text_extractor.extract_text_from_frames(frame_metadata)

        # Combine all OCR text
        all_ocr_text = []
        for detection in text_detections:
            text = detection.get('text_trocr', detection.get('text', ''))
            if text and text not in all_ocr_text:  # Avoid duplicates
                all_ocr_text.append(text)

        combined_ocr = " | ".join(all_ocr_text) if all_ocr_text else None
        results['ocr_text'] = combined_ocr
        print(f"Extracted text from {len(frame_metadata)} frames\n")

        # Step 3: Holistic video analysis with Qwen3-VL
        print("Step 3: Performing holistic scam analysis with Qwen3-VL-2B...")
        print("(This analyzes the entire video with title, description, audio, and visual text)\n")

        try:
            scam_analysis = self.vision_model.analyze_video_holistic(
                video_path=video_path,
                title=title,
                description=description,
                transcription=full_transcription,
                ocr_text=combined_ocr
            )

            results['scam_analysis'] = scam_analysis
            print("Holistic analysis complete!\n")

        except Exception as e:
            error_msg = f"Error during holistic analysis: {str(e)}"
            results['scam_analysis'] = error_msg
            print(f"⚠️  {error_msg}\n")

        # Step 4: Save results
        print("Step 4: Saving results...")

        # Save JSON report
        report_path = os.path.join(output_dir, "holistic_analysis_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save human-readable summary
        summary_path = os.path.join(output_dir, "scam_analysis_summary.txt")
        self._generate_holistic_summary(results, summary_path)

        print(f"\n{'='*60}")
        print(f"Analysis complete! Results saved to: {output_dir}")
        print(f"{'='*60}\n")

        return results

    def _generate_holistic_summary(self, results, output_path):
        """Generate a human-readable summary for holistic analysis."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("OptiScam Holistic Video Analysis Report\n")
            f.write("="*60 + "\n\n")

            f.write(f"Video: {results['video_path']}\n")
            f.write(f"Analysis Time: {results['timestamp']}\n")
            f.write(f"Analysis Type: Holistic (Entire Video Context)\n\n")

            # Video metadata
            f.write("-"*60 + "\n")
            f.write("VIDEO METADATA\n")
            f.write("-"*60 + "\n")
            if results.get('title'):
                f.write(f"Title: {results['title']}\n\n")
            if results.get('description'):
                f.write(f"Description:\n{results['description']}\n\n")

            # Audio transcription
            f.write("-"*60 + "\n")
            f.write("AUDIO TRANSCRIPTION\n")
            f.write("-"*60 + "\n")
            if results.get('audio_transcription'):
                f.write(f"Language: {results['audio_transcription']['language']}\n\n")
                f.write("Full Transcript:\n")
                f.write(results['audio_transcription']['full_text'] + "\n\n")
            else:
                f.write("No audio transcription available.\n\n")

            # OCR text
            f.write("-"*60 + "\n")
            f.write("TEXT DETECTED IN VIDEO\n")
            f.write("-"*60 + "\n")
            if results.get('ocr_text'):
                f.write(f"{results['ocr_text']}\n\n")
            else:
                f.write("No text detected.\n\n")

            # Scam analysis
            f.write("-"*60 + "\n")
            f.write("COMPREHENSIVE SCAM ANALYSIS\n")
            f.write("-"*60 + "\n")
            f.write(results.get('scam_analysis', 'No analysis available') + "\n\n")

            f.write("="*60 + "\n")
            f.write("End of Report\n")
            f.write("="*60 + "\n")

        print(f"Summary report saved to: {output_path}")

    def _generate_summary(self, results, output_path):
        """Generate a human-readable summary report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("OptiScam Video Analysis Report\n")
            f.write("="*60 + "\n\n")

            f.write(f"Video: {results['video_path']}\n")
            f.write(f"Analysis Time: {results['timestamp']}\n")
            f.write(f"Frames Analyzed: {len(results.get('frames', []))}\n\n")

            # Audio transcription summary
            f.write("-"*60 + "\n")
            f.write("AUDIO TRANSCRIPTION\n")
            f.write("-"*60 + "\n")
            if results.get('audio_transcription'):
                f.write(f"Language: {results['audio_transcription']['language']}\n\n")
                f.write("Transcript:\n")
                f.write(results['audio_transcription']['full_text'] + "\n\n")
            else:
                f.write("No audio transcription available.\n\n")

            # Text detection summary
            f.write("-"*60 + "\n")
            f.write("TEXT DETECTED IN FRAMES (Timeline)\n")
            f.write("-"*60 + "\n")
            text_timeline = results.get('text_timeline', {})
            for timestamp, texts in sorted(text_timeline.items()):
                f.write(f"\n[{timestamp:.2f}s]\n")
                for text_item in texts:
                    f.write(f"  - {text_item['text']} (confidence: {text_item['confidence']:.2f})\n")

            # Visual analysis summary
            f.write("\n" + "-"*60 + "\n")
            f.write("VISUAL ANALYSIS (Qwen3-VL-2B)\n")
            f.write("-"*60 + "\n")
            for analysis in results.get('visual_analyses', []):
                f.write(f"\n[Frame {analysis['frame_id']} @ {analysis['timestamp']:.2f}s]\n")
                f.write(f"Analysis: {analysis['analysis']}\n")

                if analysis.get('context'):
                    context = analysis['context']
                    if 'ocr_text' in context:
                        f.write(f"OCR Text: {context['ocr_text']}\n")
                    if 'transcription' in context:
                        f.write(f"Audio: {context['transcription']}\n")

            f.write("\n" + "="*60 + "\n")
            f.write("End of Report\n")
            f.write("="*60 + "\n")

        print(f"Summary report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='OptiScam Video Analysis System')
    parser.add_argument('video_path', type=str, help='Path to video file')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for results')

    # Analysis mode
    parser.add_argument('--holistic', action='store_true',
                        help='Use holistic analysis mode (analyzes entire video with metadata)')
    parser.add_argument('--title', type=str, default=None,
                        help='Video title (for holistic analysis)')
    parser.add_argument('--description', type=str, default=None,
                        help='Video description (for holistic analysis)')

    # Frame-by-frame mode options
    parser.add_argument('--frame-interval', type=int, default=30,
                        help='Extract every N frames (default: 30) [frame-by-frame mode]')
    parser.add_argument('--sharpness-threshold', type=float, default=100.0,
                        help='Laplacian variance threshold for sharpness (default: 100.0)')
    parser.add_argument('--no-sharpness-filter', action='store_true',
                        help='Disable sharpness filtering')
    parser.add_argument('--no-frame-analysis', action='store_true',
                        help='Skip Qwen3-VL frame analysis [frame-by-frame mode]')

    # Common options
    parser.add_argument('--whisper-model', type=str, default='tiny',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: base)')
    parser.add_argument('--device', type=str, default=None,
                        choices=['cuda', 'cpu'],
                        help='Device to run models on (default: auto-detect GPU)')

    args = parser.parse_args()

    # Build configuration
    config = {
        'sharpness_threshold': args.sharpness_threshold,
        'whisper_model_size': args.whisper_model,
        'device': args.device,
    }

    # Initialize analyzer
    analyzer = OptiScamAnalyzer(config=config)

    # Choose analysis mode
    if args.holistic:
        # Holistic analysis mode
        print("\n🎯 Running HOLISTIC analysis mode")
        print("   (Analyzes entire video with title and description)\n")

        results = analyzer.analyze_video_holistic(
            video_path=args.video_path,
            title=args.title,
            description=args.description,
            output_dir=args.output_dir
        )
    else:
        # Frame-by-frame analysis mode (original)
        print("\n🎯 Running FRAME-BY-FRAME analysis mode")
        print("   (Analyzes individual frames separately)\n")

        results = analyzer.process_video(
            video_path=args.video_path,
            output_dir=args.output_dir,
            frame_interval=args.frame_interval,
            use_sharpness_filter=not args.no_sharpness_filter,
            analyze_frames=not args.no_frame_analysis
        )

    print("\nAnalysis complete!")
    print(f"Results saved to: {results['output_dir']}")


if __name__ == "__main__":
    main()
