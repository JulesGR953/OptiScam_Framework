import whisper
import os
import json
import torch
from pathlib import Path

class AudioTranscriber:
    def __init__(self, model_size="base", device=None, language=None):
        """
        Initialize Whisper audio transcription.

        :param model_size: Whisper model size (tiny, base, small, medium, large)
        :param device: Device to run on (cuda/cpu)
        :param language: Language code (e.g., 'en', 'es') or None for auto-detect
        """
        self.model_size = model_size
        self.language = language
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading Whisper {model_size} model on {self.device}...")
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"Whisper model loaded successfully on {self.device}")

    def extract_audio_from_video(self, video_path, output_audio_path=None):
        """
        Extract audio from video file using ffmpeg.

        :param video_path: Path to video file
        :param output_audio_path: Path for extracted audio (optional)
        :return: Path to extracted audio file
        """
        if output_audio_path is None:
            video_name = Path(video_path).stem
            output_audio_path = f"{video_name}_audio.mp3"

        import subprocess

        # Use ffmpeg to extract audio
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-q:a', '2',  # Good quality
            '-y',  # Overwrite output file
            output_audio_path
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"Audio extracted to: {output_audio_path}")
            return output_audio_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            return None

    def transcribe_audio(self, audio_path, word_timestamps=True):
        """
        Transcribe audio file with Whisper.

        :param audio_path: Path to audio file
        :param word_timestamps: Include word-level timestamps
        :return: Transcription result with timestamps
        """
        print(f"Transcribing audio: {audio_path}")

        result = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=word_timestamps,
            verbose=False
        )

        return result

    def transcribe_video(self, video_path, extract_audio=True, temp_audio_path=None,
                         cleanup_audio=True):
        """
        Transcribe audio from video file.

        :param video_path: Path to video file
        :param extract_audio: Whether to extract audio first
        :param temp_audio_path: Path for temporary audio file
        :param cleanup_audio: Delete temporary audio file after transcription
        :return: Transcription result with timestamps
        """
        if extract_audio:
            audio_path = self.extract_audio_from_video(video_path, temp_audio_path)
            if audio_path is None:
                return None
        else:
            audio_path = video_path

        result = self.transcribe_audio(audio_path)

        # Cleanup temporary audio file
        if extract_audio and cleanup_audio and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up temporary audio file: {audio_path}")

        return result

    def get_transcription_timeline(self, transcription_result):
        """
        Extract timeline of transcribed text with timestamps.

        :param transcription_result: Result from transcribe_audio/transcribe_video
        :return: List of segments with text and timestamps
        """
        if not transcription_result or 'segments' not in transcription_result:
            return []

        timeline = []

        for segment in transcription_result['segments']:
            timeline.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'words': segment.get('words', [])
            })

        return timeline

    def get_text_at_timestamp(self, transcription_result, timestamp):
        """
        Get transcribed text at a specific timestamp.

        :param transcription_result: Result from transcribe_audio/transcribe_video
        :param timestamp: Time in seconds
        :return: Text active at that timestamp
        """
        timeline = self.get_transcription_timeline(transcription_result)

        for segment in timeline:
            if segment['start'] <= timestamp <= segment['end']:
                return segment['text']

        return None

    def export_transcription(self, transcription_result, output_path, format='txt'):
        """
        Export transcription to file.

        :param transcription_result: Result from transcribe_audio/transcribe_video
        :param output_path: Path for output file
        :param format: Output format (txt, json, srt)
        """
        timeline = self.get_transcription_timeline(transcription_result)

        if format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for segment in timeline:
                    f.write(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}\n")

        elif format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(timeline, f, indent=2, ensure_ascii=False)

        elif format == 'srt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(timeline, 1):
                    start_time = self._seconds_to_srt_time(segment['start'])
                    end_time = self._seconds_to_srt_time(segment['end'])
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text']}\n\n")

        print(f"Transcription exported to: {output_path}")

    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def get_full_text(self, transcription_result):
        """
        Get the complete transcribed text.

        :param transcription_result: Result from transcribe_audio/transcribe_video
        :return: Full transcription as single string
        """
        if not transcription_result:
            return ""

        return transcription_result.get('text', '')
