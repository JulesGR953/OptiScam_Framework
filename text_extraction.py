import cv2
from rapidocr_onnxruntime import RapidOCR
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

class TextExtractor:
    def __init__(self, use_trocr_fallback=True, trocr_confidence_threshold=0.8):
        """
        Initialize text extraction with RapidOCR and optional TrOCR fallback.

        :param use_trocr_fallback: Use TrOCR for low-confidence detections
        :param trocr_confidence_threshold: RapidOCR confidence below which TrOCR takes over (default 0.8 = 80%)
        """
        self.use_trocr_fallback = use_trocr_fallback
        self.trocr_confidence_threshold = trocr_confidence_threshold

        # Initialize RapidOCR
        self.rapid_ocr = RapidOCR()

        # Initialize TrOCR if fallback is enabled
        if use_trocr_fallback:
            self.trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-small-printed')
            self.trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-small-printed')
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.trocr_model.to(self.device)

    def extract_with_rapidocr(self, image_path):
        """
        Extract text using RapidOCR.

        :param image_path: Path to image file
        :return: List of tuples (bbox, text, confidence)
        """
        result, _ = self.rapid_ocr(image_path)

        if result is None or len(result) == 0:
            return []

        detections = []
        for detection in result:
            if detection:
                bbox = detection[0]  # Bounding box coordinates
                text = detection[1]  # Detected text
                confidence = float(detection[2])  # Confidence score
                detections.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence,
                    'method': 'rapidocr'
                })

        return detections

    def extract_with_trocr(self, image_path, bbox=None):
        """
        Extract text using TrOCR (more accurate but slower).

        :param image_path: Path to image file
        :param bbox: Optional bounding box to crop image before OCR
        :return: Extracted text
        """
        if not self.use_trocr_fallback:
            return None

        image = Image.open(image_path).convert("RGB")

        # Crop to bounding box if provided
        if bbox:
            # bbox format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            left, top = min(x_coords), min(y_coords)
            right, bottom = max(x_coords), max(y_coords)
            image = image.crop((left, top, right, bottom))

        pixel_values = self.trocr_processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self.device)

        generated_ids = self.trocr_model.generate(pixel_values)
        generated_text = self.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return generated_text

    def extract_text(self, image_path):
        """
        Extract text using RapidOCR with optional TrOCR fallback for low-confidence detections.

        :param image_path: Path to image file
        :return: List of text detections with metadata
        """
        detections = self.extract_with_rapidocr(image_path)

        # Use TrOCR fallback for low-confidence detections
        if self.use_trocr_fallback:
            for detection in detections:
                if detection['confidence'] < self.trocr_confidence_threshold:
                    trocr_text = self.extract_with_trocr(image_path, detection['bbox'])
                    if trocr_text:
                        detection['text_trocr'] = trocr_text
                        detection['method'] = 'rapidocr+trocr'

        return detections

    def extract_text_from_frames(self, frame_metadata):
        """
        Extract text from multiple frames with timestamp tracking.

        :param frame_metadata: List of frame metadata dicts with 'path' and 'timestamp'
        :return: List of text detections with timestamps
        """
        all_text_detections = []

        for frame_info in frame_metadata:
            image_path = frame_info['path']
            timestamp = frame_info['timestamp']
            frame_id = frame_info.get('frame_id', 0)

            detections = self.extract_text(image_path)

            # Add timestamp and frame info to each detection
            for detection in detections:
                detection['timestamp'] = timestamp
                detection['frame_id'] = frame_id
                detection['source_image'] = image_path
                all_text_detections.append(detection)

        return all_text_detections

    def get_text_timeline(self, text_detections):
        """
        Organize text detections by timestamp for timeline view.

        :param text_detections: List of text detection dicts
        :return: Dictionary mapping timestamps to text content
        """
        timeline = {}

        for detection in text_detections:
            timestamp = detection['timestamp']
            text = detection.get('text_trocr', detection['text'])

            if timestamp not in timeline:
                timeline[timestamp] = []

            timeline[timestamp].append({
                'text': text,
                'confidence': detection['confidence'],
                'method': detection['method'],
                'bbox': detection['bbox']
            })

        return dict(sorted(timeline.items()))
