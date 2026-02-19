import cv2
import os

class ImageProcessing:
    def __init__(self, clip_limit=2.0, tile_grid_size=(8, 8), sharpness_threshold=100.0):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.sharpness_threshold = sharpness_threshold
        self._clahe = cv2.createCLAHE(clipLimit=self.clip_limit,
                                      tileGridSize=self.tile_grid_size)

    def calculate_sharpness(self, image):
        """Calculates Laplacian Variance to measure image sharpness."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        return variance

    def apply_clahe(self, image):
        """Applies CLAHE to grayscale or color images."""
        if len(image.shape) == 2:
            return self._clahe.apply(image)

        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_enhanced = self._clahe.apply(l)
        enhanced_lab = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def sample_frames_by_sharpness(self, video_path, interval=10, output_dir="sampled_frames",
                                    use_sharpness_filter=True):
        """
        Samples frames from a video using sharpness-based filtering and applies CLAHE.

        :param video_path: Path to the video file.
        :param interval: Extract every 'n' frames for evaluation.
        :param output_dir: Folder to save the processed frames.
        :param use_sharpness_filter: If True, only save frames above sharpness threshold.
        :return: List of dictionaries with frame info (path, timestamp, sharpness)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        saved_count = 0
        frame_metadata = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Only process every 'n-th' frame
            if frame_count % interval == 0:
                sharpness = self.calculate_sharpness(frame)
                timestamp = frame_count / fps if fps > 0 else 0

                # Apply sharpness filter if enabled
                if use_sharpness_filter and sharpness < self.sharpness_threshold:
                    frame_count += 1
                    continue

                processed_frame = self.apply_clahe(frame)

                filename = f"frame_{saved_count:04d}.jpg"
                save_path = os.path.join(output_dir, filename)
                cv2.imwrite(save_path, processed_frame)

                frame_metadata.append({
                    'frame_id': saved_count,
                    'original_frame_number': frame_count,
                    'path': save_path,
                    'timestamp': timestamp,
                    'sharpness': sharpness
                })

                saved_count += 1

            frame_count += 1

        cap.release()
        print(f"Done! Extracted {saved_count} sharp frames to '{output_dir}'.")
        return frame_metadata

    def sample_frames(self, video_path, interval=10, output_dir="sampled_frames"):
        """
        Legacy method: Samples frames from a video and applies CLAHE before saving.

        :param video_path: Path to the video file.
        :param interval: Extract every 'n' frames.
        :param output_dir: Folder to save the processed frames.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Only process every 'n-th' frame
            if frame_count % interval == 0:
                processed_frame = self.apply_clahe(frame)

                filename = f"frame_{saved_count:04d}.jpg"
                save_path = os.path.join(output_dir, filename)
                cv2.imwrite(save_path, processed_frame)
                saved_count += 1

            frame_count += 1

        cap.release()
        print(f"Done! Extracted {saved_count} frames to '{output_dir}'.")