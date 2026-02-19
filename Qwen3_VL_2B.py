import torch
try:
    from transformers import AutoImageTextToText as _VLModel
except ImportError:
    try:
        from transformers import AutoModelForVision2Seq as _VLModel
    except ImportError:
        from transformers import AutoModel as _VLModel
from transformers import AutoProcessor
from qwen_vl_utils import process_vision_info

class Qwen3VLModel:
    def __init__(self, model_name="unsloth/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit", device=None):
        """
        Initialize Qwen3-VL-2B-Instruct model for visual understanding.

        :param model_name: Model identifier from HuggingFace
        :param device: Device to run model on (cuda/cpu)
        """
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading {model_name} (4-bit) on {self.device}...")

        # Load 4-bit quantized model — device_map="auto" handles GPU placement
        self.model = _VLModel.from_pretrained(
            model_name,
            load_in_4bit=True,
            dtype=torch.float16,
            device_map="auto"
        )

        # Load processor
        self.processor = AutoProcessor.from_pretrained(model_name)

        print(f"Model loaded successfully on {self.device}")

    def analyze_image(self, image_path, prompt, max_new_tokens=512):
        """
        Analyze an image with a text prompt.

        :param image_path: Path to image file
        :param prompt: Text prompt for analysis
        :param max_new_tokens: Maximum tokens to generate
        :return: Model's response
        """
        # Prepare messages in the format Qwen expects
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path,
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Prepare for inference
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.device)

        # Generate response
        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        return output_text[0]

    def analyze_frames_for_scams(self, frame_metadata, custom_prompt=None):
        """
        Analyze frames specifically for scam detection.

        :param frame_metadata: List of frame metadata dicts
        :param custom_prompt: Custom analysis prompt (optional)
        :return: List of analysis results with timestamps
        """
        default_prompt = """Analyze this image for potential scam indicators:
1. Suspicious URLs or links
2. Fake urgency messages (limited time offers, account warnings)
3. Requests for personal information or payment
4. Impersonation of legitimate brands/services
5. Grammatical errors or unprofessional design
6. Too-good-to-be-true offers

Provide a brief analysis of any suspicious elements found."""

        prompt = custom_prompt if custom_prompt else default_prompt
        results = []

        for frame_info in frame_metadata:
            image_path = frame_info['path']
            timestamp = frame_info['timestamp']
            frame_id = frame_info.get('frame_id', 0)

            try:
                analysis = self.analyze_image(image_path, prompt)

                results.append({
                    'frame_id': frame_id,
                    'timestamp': timestamp,
                    'image_path': image_path,
                    'analysis': analysis,
                    'model': self.model_name
                })

                print(f"[Frame {frame_id} @ {timestamp:.2f}s] Analysis complete")

            except Exception as e:
                print(f"Error analyzing frame {frame_id}: {str(e)}")
                results.append({
                    'frame_id': frame_id,
                    'timestamp': timestamp,
                    'image_path': image_path,
                    'analysis': f"Error: {str(e)}",
                    'model': self.model_name
                })

        return results

    def analyze_video_holistic(self, video_path, title=None, description=None, transcription=None, ocr_text=None, max_new_tokens=1024):
        """
        Analyze an entire video holistically with title, description, and extracted content.

        :param video_path: Path to video file
        :param title: Video title
        :param description: Video description
        :param transcription: Full audio transcription
        :param ocr_text: All extracted OCR text from the video
        :param max_new_tokens: Maximum tokens to generate
        :return: Comprehensive scam analysis
        """
        # Build comprehensive context
        context_parts = []

        if title:
            context_parts.append(f"**Video Title:** {title}")

        if description:
            context_parts.append(f"**Video Description:** {description}")

        if transcription:
            context_parts.append(f"**Audio Transcription:** {transcription}")

        if ocr_text:
            context_parts.append(f"**Text Visible in Video:** {ocr_text}")

        context_str = "\n\n".join(context_parts)

        # Create comprehensive scam detection prompt
        prompt = f"""You are analyzing this video for potential scam indicators.

Here is the available context:

{context_str}

**Your Task:**
Analyze the entire video content along with the provided context (title, description, audio, and visual text) to detect if this is a scam. Consider:

1. **Mismatches & Deception:** Do the title, description, visual content, and audio align? Are there contradictions suggesting deception?

2. **Red Flags:** Look for:
   - Fake urgency ("limited time", "act now", "account suspended")
   - Requests for personal info, passwords, or payment
   - Too-good-to-be-true offers (free money, prizes, investment returns)
   - Impersonation of legitimate brands, companies, or officials
   - Suspicious URLs or contact information
   - Poor grammar, spelling, or unprofessional presentation

3. **Manipulation Tactics:** Does the video use fear, urgency, or greed to pressure viewers?

4. **Visual Analysis:** Look at the video content for:
   - Fake websites or login pages
   - Manipulated images or screenshots
   - Generic stock footage inconsistent with claims
   - Low-quality or stolen branding

**Provide:**
- **Scam Likelihood:** (Low/Medium/High/Very High)
- **Evidence:** Specific examples from the video, title, description, audio, or text
- **Scam Type:** (Phishing, Investment scam, Tech support scam, Fake giveaway, etc.)
- **Recommendation:** What viewers should know or do

Be thorough and specific in your analysis."""

        # Prepare messages with video input
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video",
                        "video": video_path,
                        "fps": 1.0,  # Sample 1 frame per second for comprehensive understanding
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Prepare for inference
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.device)

        # Generate response
        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        return output_text[0]

    def analyze_with_context(self, image_path, context_info, prompt_template=None):
        """
        Analyze an image with additional context (like OCR text or audio transcription).

        :param image_path: Path to image file
        :param context_info: Dictionary with context (transcription, ocr_text, etc.)
        :param prompt_template: Custom prompt template
        :return: Analysis result
        """
        if prompt_template is None:
            prompt_template = """Given the following context:
{context}

Analyze this image for scam indicators and explain how the visual content relates to the context provided."""

        # Build context string
        context_parts = []
        if 'transcription' in context_info:
            context_parts.append(f"Audio: {context_info['transcription']}")
        if 'ocr_text' in context_info:
            context_parts.append(f"Text in image: {context_info['ocr_text']}")
        if 'timestamp' in context_info:
            context_parts.append(f"Time: {context_info['timestamp']:.2f}s")

        context_str = "\n".join(context_parts)
        prompt = prompt_template.format(context=context_str)

        return self.analyze_image(image_path, prompt)

    def batch_analyze(self, image_paths, prompt, batch_size=4):
        """
        Analyze multiple images in batches.

        :param image_paths: List of image paths
        :param prompt: Prompt for analysis
        :param batch_size: Number of images to process at once
        :return: List of analysis results
        """
        results = []

        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]

            for img_path in batch:
                try:
                    result = self.analyze_image(img_path, prompt)
                    results.append({'image_path': img_path, 'analysis': result})
                except Exception as e:
                    results.append({'image_path': img_path, 'analysis': f"Error: {str(e)}"})

        return results
