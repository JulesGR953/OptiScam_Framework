import cv2
import numpy as np
from PIL import Image, ImageEnhance


class PreProcessing:
    """
    Additional preprocessing utilities for video frames before analysis.
    Complements the CLAHE processing in ImageProcessing class.
    """

    @staticmethod
    def denoise_image(image, method='bilateral', **kwargs):
        """
        Apply denoising to reduce noise while preserving edges.

        :param image: Input image (numpy array)
        :param method: Denoising method ('bilateral', 'nlmeans', 'gaussian')
        :param kwargs: Additional parameters for the denoising method
        :return: Denoised image
        """
        if method == 'bilateral':
            d = kwargs.get('d', 9)
            sigma_color = kwargs.get('sigma_color', 75)
            sigma_space = kwargs.get('sigma_space', 75)
            return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

        elif method == 'nlmeans':
            h = kwargs.get('h', 10)
            template_window_size = kwargs.get('template_window_size', 7)
            search_window_size = kwargs.get('search_window_size', 21)

            if len(image.shape) == 3:
                return cv2.fastNlMeansDenoisingColored(
                    image, None, h, h, template_window_size, search_window_size
                )
            else:
                return cv2.fastNlMeansDenoising(
                    image, None, h, template_window_size, search_window_size
                )

        elif method == 'gaussian':
            kernel_size = kwargs.get('kernel_size', (5, 5))
            sigma_x = kwargs.get('sigma_x', 0)
            return cv2.GaussianBlur(image, kernel_size, sigma_x)

        return image

    @staticmethod
    def adjust_brightness_contrast(image, brightness=0, contrast=0):
        """
        Adjust brightness and contrast of an image.

        :param image: Input image (numpy array)
        :param brightness: Brightness adjustment (-100 to 100)
        :param contrast: Contrast adjustment (-100 to 100)
        :return: Adjusted image
        """
        # Convert to PIL for easier manipulation
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Adjust brightness
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(pil_image)
            factor = 1 + (brightness / 100.0)
            pil_image = enhancer.enhance(factor)

        # Adjust contrast
        if contrast != 0:
            enhancer = ImageEnhance.Contrast(pil_image)
            factor = 1 + (contrast / 100.0)
            pil_image = enhancer.enhance(factor)

        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
        """
        Apply unsharp masking to enhance edges and details.

        :param image: Input image
        :param kernel_size: Gaussian kernel size
        :param sigma: Gaussian sigma
        :param amount: Strength of sharpening
        :param threshold: Minimum difference threshold
        :return: Sharpened image
        """
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
        sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
        sharpened = sharpened.round().astype(np.uint8)

        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)

        return sharpened

    @staticmethod
    def auto_white_balance(image):
        """
        Perform automatic white balance correction.

        :param image: Input image (BGR)
        :return: White-balanced image
        """
        result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])

        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)

        result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
        return result

    @staticmethod
    def enhance_for_ocr(image):
        """
        Apply preprocessing specifically optimized for OCR.

        :param image: Input image
        :return: OCR-enhanced image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Binarization using Otsu's method
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return processed

    @staticmethod
    def detect_and_correct_skew(image):
        """
        Detect and correct skew in text-containing images.

        :param image: Input image
        :return: Deskewed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Hough line detection
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return image

        # Calculate average angle
        angles = []
        for _, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            angles.append(angle)

        median_angle = np.median(angles)

        # Rotate image if skew is detected
        if abs(median_angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return rotated

        return image

    @staticmethod
    def resize_for_model(image, target_size=(224, 224), maintain_aspect=True):
        """
        Resize image for model input while optionally maintaining aspect ratio.

        :param image: Input image
        :param target_size: Target size (width, height)
        :param maintain_aspect: Whether to maintain aspect ratio
        :return: Resized image
        """
        if maintain_aspect:
            h, w = image.shape[:2]
            target_w, target_h = target_size

            # Calculate scaling factor
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)

            # Resize
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Create padded image
            padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

            return padded
        else:
            return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)

    @staticmethod
    def apply_preprocessing_pipeline(image, for_ocr=False, for_model=False):
        """
        Apply a complete preprocessing pipeline.

        :param image: Input image
        :param for_ocr: Optimize for OCR
        :param for_model: Optimize for vision model
        :return: Preprocessed image
        """
        processed = image.copy()

        if for_ocr:
            # OCR-specific pipeline
            processed = PreProcessing.denoise_image(processed, method='nlmeans')
            processed = PreProcessing.detect_and_correct_skew(processed)
            processed = PreProcessing.enhance_for_ocr(processed)

        elif for_model:
            # Vision model pipeline
            processed = PreProcessing.denoise_image(processed, method='bilateral')
            processed = PreProcessing.auto_white_balance(processed)
            processed = PreProcessing.unsharp_mask(processed, amount=0.5)

        return processed
