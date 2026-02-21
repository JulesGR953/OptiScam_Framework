import torch
from transformers import AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info

try:
    from transformers import Qwen3VLForConditionalGeneration as _VLModel
except ImportError:
    try:
        from transformers import Qwen2VLForConditionalGeneration as _VLModel
    except ImportError:
        from transformers import AutoModelForVision2Seq as _VLModel


class Qwen3VLModel:
    def __init__(self, model_name="Qwen/Qwen3-VL-2B-Instruct", device=None):
        """
        Initialize Qwen3-VL-2B-Instruct model for visual understanding.

        :param model_name: Model identifier from HuggingFace
        :param device: Device to run model on (cuda/cpu)
        """
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"Loading {model_name} on {self.device}...")

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=False,
            bnb_4bit_quant_type="nf4",
        )

        self.model = _VLModel.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
        )

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
        messages = [{"role": "user", "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": prompt},
        ]}]

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
        ).to(self.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

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

        prompt = f"""You are analyzing this video for potential scam indicators.

Here is the available context:

{context_str}

**Your Task:**
BE PRAGMATIC DO NOT BE FOOLED BY SEMANTIC MISDIRECTION. Analyze the video content along with the provided context to detect if this is a scam. Consider:
1. Mismatches & Deception: Do the title, description, visual content, and audio align? Are there contradictions suggesting deception?
2. Red Flags: Look for fake urgency, requests for personal info, too-good-to-be-true offers, impersonation, suspicious URLs, poor grammar, etc.
3. Manipulation Tactics: Does the video use fear, urgency, or greed to pressure viewers?
4. Visual Analysis: Look for fake websites, manipulated images, generic stock footage, low-quality branding, etc.
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

        messages = [{"role": "user", "content": [
            {"type": "video", "video": video_path, "fps": 1.0},
            {"type": "text", "text": prompt},
        ]}]

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
        ).to(self.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

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

    def classify_video(self, image_paths, title=None, description=None,
                       max_frames=6, max_new_tokens=512):
        """
        Classify a video as scam or legitimate using multiple frames.
        Matches the training format: all frames + title/description → Yes/No + reasoning.

        :param image_paths: List of frame image paths
        :param title: Video title
        :param description: Video description
        :param max_frames: Maximum number of frames to pass (prevents OOM)
        :param max_new_tokens: Maximum tokens to generate
        :return: Tuple of ("Yes. <reasoning>" or "No. <reasoning>", confidence_pct float or None)
                 confidence_pct is the model's probability for the Yes/No verdict (0–100).
        """
        # Subsample evenly across the full frame list so we get representative coverage
        if len(image_paths) > max_frames:
            step = len(image_paths) / max_frames
            frames = [image_paths[int(i * step)] for i in range(max_frames)]
        else:
            frames = image_paths

        content = []
        for img_path in frames:
            # Cap resolution to limit visual tokens per image and prevent OOM
            content.append({
                "type": "image",
                "image": img_path,
                "min_pixels": 224 * 224,
                "max_pixels": 448 * 448,
            })

        prompt_parts = []
        if title:
            prompt_parts.append(f"Title: {title}")
        if description:
            prompt_parts.append(f"Description: {description}")
        prompt_parts.append("")
        prompt_parts.append(
            "DEFINITION OF SCAM: A scam is strictly defined as a policy-violating deceptive "
            "pattern in accordance with the official Community Guidelines of the target platforms. "
            "Specifically: YouTube's 'Spam, Deceptive Practices & Scams Policies' and TikTok's "
            "prohibitions on deceptive practices, financial frauds, and impersonation. "
            "Observable scam behaviors include but are not limited to: promoting get-rich-quick "
            "or guaranteed-return investment schemes, misleading or disguised external links, "
            "visual or audio impersonation of legitimate brands/officials/platforms, fake "
            "giveaways or prize claims, phishing for personal or financial information, "
            "artificial urgency tactics (e.g. 'limited time', 'act now', 'account suspended'), "
            "and coordinated inauthentic behavior designed to deceive viewers.\n"
            "DO NOT flag content solely for being promotional, opinionated, or low-quality "
            "unless it also exhibits the deceptive patterns above.\n\n"
            "Given the above definition, is this video a scam? "
            "Check the video frames, title, and description for deceptive patterns. "
            "Answer Yes/No followed by your reasoning in 4-5 sentences."
        )
        content.append({"type": "text", "text": "\n".join(prompt_parts)})

        messages = [{"role": "user", "content": content}]

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
        ).to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            return_dict_in_generate=True,
            output_scores=True,
        )

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, outputs.sequences)
        ]
        verdict_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # --- Logit-based confidence ---
        # outputs.scores[0] holds logits over the full vocabulary for the FIRST generated token.
        # We compare the logit for "Yes" vs "No" to get a calibrated probability.
        confidence_pct = None
        try:
            first_token_logits = outputs.scores[0][0].float()  # (vocab_size,)
            yes_ids = self.processor.tokenizer.encode("Yes", add_special_tokens=False)
            no_ids  = self.processor.tokenizer.encode("No",  add_special_tokens=False)
            if yes_ids and no_ids:
                yes_logit = first_token_logits[yes_ids[0]]
                no_logit  = first_token_logits[no_ids[0]]
                probs = torch.softmax(torch.stack([yes_logit, no_logit]), dim=0)
                is_yes = verdict_text.strip().lower().startswith("yes")
                # confidence = probability of whichever answer was actually given
                confidence_pct = (probs[0] if is_yes else probs[1]).item() * 100
        except Exception:
            confidence_pct = None

        return verdict_text, confidence_pct

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
