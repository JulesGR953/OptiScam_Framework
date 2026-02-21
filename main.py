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
            trocr_confidence_threshold=self.config.get('trocr_confidence_threshold', 0.8)
        )

        # Audio transcription with Whisper
        self.audio_transcriber = AudioTranscriber(
            model_size=self.config.get('whisper_model_size', 'tiny'),
            language=self.config.get('whisper_language', None),
            device=self.config.get('device', None)
        )

        # Qwen3-VL-2B for visual analysis
        self.vision_model = Qwen3VLModel(
            model_name=self.config.get('vision_model_name', 'Qwen/Qwen3-VL-2B-Instruct'),
            device=self.config.get('device', None)
        )

        print("All components initialized successfully!\n")

    def process_video(self, video_path, title=None, description=None, output_dir=None,
                      frame_interval=30, use_sharpness_filter=True):
        """
        Process a video through the complete analysis pipeline.
        Extracts frames, runs OCR and audio transcription, then classifies
        all frames together as scam/legitimate using the training prompt format.

        :param video_path: Path to video file
        :param title: Video title (used in the model prompt)
        :param description: Video description (used in the model prompt)
        :param output_dir: Directory for outputs (created if doesn't exist)
        :param frame_interval: Extract every N frames
        :param use_sharpness_filter: Use Laplacian Variance sharpness filtering
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
            'title': title,
            'description': description,
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
            transcription_file = os.path.join(output_dir, "transcription.txt")
            self.audio_transcriber.export_transcription(
                transcription, transcription_file, format='txt'
            )
            print(f"Audio transcribed successfully\n")
        else:
            results['audio_transcription'] = None
            print("No audio transcription available\n")

        # Step 4: Classify all frames together with title + description
        print("Step 4: Classifying video with Qwen3-VL-2B-Instruct...")
        print(f"  Frames: {len(frame_metadata)}  |  Title: {'yes' if title else 'none'}  |  Description: {'yes' if description else 'none'}\n")

        frame_paths = [f['path'] for f in frame_metadata]

        try:
            verdict = self.vision_model.classify_video(
                image_paths=frame_paths,
                title=title,
                description=description,
            )
            results['verdict'] = verdict
            is_scam = verdict.strip().lower().startswith('yes')
            results['is_scam'] = is_scam
            print(f"  Verdict: {'SCAM' if is_scam else 'NOT SCAM'}\n")
        except Exception as e:
            error_msg = f"Error during classification: {str(e)}"
            results['verdict'] = error_msg
            results['is_scam'] = None
            print(f"  Error: {error_msg}\n")

        # Step 5: Save results
        print("Step 5: Saving results...")
        report_path = os.path.join(output_dir, "analysis_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        summary_path = os.path.join(output_dir, "summary.txt")
        self._generate_summary(results, summary_path)

        print(f"\n{'='*60}")
        print(f"Analysis complete! Results saved to: {output_dir}")
        print(f"{'='*60}\n")

        return results

    def analyze_video_holistic(self, video_path, title=None, description=None, output_dir=None):
        """
        Holistic analysis — alias for process_video with a holistic output directory suffix.
        Kept for CLI backward compatibility.

        :param video_path: Path to video file
        :param title: Video title
        :param description: Video description
        :param output_dir: Directory for outputs (created if doesn't exist)
        :return: Analysis results
        """
        if output_dir is None:
            video_name = Path(video_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"output_{video_name}_{timestamp}_holistic"

        return self.process_video(
            video_path=video_path,
            title=title,
            description=description,
            output_dir=output_dir,
            frame_interval=60,
            use_sharpness_filter=True,
        )

    def _generate_summary(self, results, output_path):
        """Generate a human-readable summary report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("OptiScam Video Analysis Report\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Video: {results['video_path']}\n")
            f.write(f"Analysis Time: {results['timestamp']}\n")
            f.write(f"Frames Analyzed: {len(results.get('frames', []))}\n\n")

            # Metadata
            if results.get('title'):
                f.write(f"Title: {results['title']}\n")
            if results.get('description'):
                f.write(f"Description: {results['description']}\n")
            f.write("\n")

            # Verdict (most important)
            f.write("-" * 60 + "\n")
            f.write("SCAM VERDICT\n")
            f.write("-" * 60 + "\n")
            is_scam = results.get('is_scam')
            if is_scam is True:
                f.write("RESULT: YES — This video is likely a scam.\n\n")
            elif is_scam is False:
                f.write("RESULT: NO — This video does not appear to be a scam.\n\n")
            else:
                f.write("RESULT: UNKNOWN (error during classification)\n\n")
            f.write(results.get('verdict', 'No verdict available') + "\n\n")

            # Audio transcription
            f.write("-" * 60 + "\n")
            f.write("AUDIO TRANSCRIPTION\n")
            f.write("-" * 60 + "\n")
            if results.get('audio_transcription'):
                f.write(f"Language: {results['audio_transcription']['language']}\n\n")
                f.write(results['audio_transcription']['full_text'] + "\n\n")
            else:
                f.write("No audio transcription available.\n\n")

            # OCR text timeline
            f.write("-" * 60 + "\n")
            f.write("TEXT DETECTED IN FRAMES (Timeline)\n")
            f.write("-" * 60 + "\n")
            text_timeline = results.get('text_timeline', {})
            if text_timeline:
                for timestamp, texts in sorted(text_timeline.items()):
                    f.write(f"\n[{timestamp:.2f}s]\n")
                    for text_item in texts:
                        f.write(f"  - {text_item['text']} (conf: {text_item['confidence']:.2f})\n")
            else:
                f.write("No text detected.\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("End of Report\n")
            f.write("=" * 60 + "\n")

        print(f"Summary report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='OptiScam Video Analysis System')
    parser.add_argument('video_path', type=str, help='Path to video file')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for results')

    # Metadata (used in model prompt)
    parser.add_argument('--title', type=str, default=None,
                        help='Video title (passed to model prompt)')
    parser.add_argument('--description', type=str, default=None,
                        help='Video description (passed to model prompt)')

    # Analysis mode
    parser.add_argument('--holistic', action='store_true',
                        help='Use holistic mode (lower frame rate, same classification method)')

    # Frame extraction options
    parser.add_argument('--frame-interval', type=int, default=30,
                        help='Extract every N frames (default: 30)')
    parser.add_argument('--sharpness-threshold', type=float, default=100.0,
                        help='Laplacian variance threshold for sharpness (default: 100.0)')
    parser.add_argument('--no-sharpness-filter', action='store_true',
                        help='Disable sharpness filtering')

    # Common options
    parser.add_argument('--whisper-model', type=str, default='tiny',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper model size (default: tiny)')
    parser.add_argument('--device', type=str, default=None,
                        choices=['cuda', 'cpu'],
                        help='Device to run models on (default: auto-detect GPU)')

    args = parser.parse_args()

    config = {
        'sharpness_threshold': args.sharpness_threshold,
        'whisper_model_size': args.whisper_model,
        'device': args.device,
    }

    analyzer = OptiScamAnalyzer(config=config)

    if args.holistic:
        print("\nRunning HOLISTIC analysis mode\n")
        results = analyzer.analyze_video_holistic(
            video_path=args.video_path,
            title=args.title,
            description=args.description,
            output_dir=args.output_dir,
        )
    else:
        print("\nRunning FRAME-BY-FRAME analysis mode\n")
        results = analyzer.process_video(
            video_path=args.video_path,
            title=args.title,
            description=args.description,
            output_dir=args.output_dir,
            frame_interval=args.frame_interval,
            use_sharpness_filter=not args.no_sharpness_filter,
        )

    print("\nAnalysis complete!")
    print(f"Results saved to: {results['output_dir']}")


if __name__ == "__main__":
    main()
