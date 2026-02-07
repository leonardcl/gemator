"""Automatic speech bubble detection using OCR."""

import easyocr
import cv2
import numpy as np
from PIL import Image
import ssl
import certifi

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context


class BubbleDetector:
    """Detects speech bubbles in manhwa images using OCR."""

    def __init__(self):
        """Initialize EasyOCR reader for Korean text detection."""
        print("Initializing Korean OCR detector...")
        self.reader = easyocr.Reader(['ko'], gpu=False)
        print("✓ OCR detector ready")

    def detect_bubbles(self, image_path, min_width=50, min_height=30, padding=10):
        """
        Detect speech bubbles in manhwa image.

        Args:
            image_path: Path to manhwa image
            min_width: Minimum bubble width in pixels
            min_height: Minimum bubble height in pixels
            padding: Extra padding around detected text (pixels)

        Returns:
            list: Detected bubbles as dicts with x, y, width, height, type
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Detect text regions
        results = self.reader.readtext(img)

        bubbles = []
        for (bbox, text, confidence) in results:
            # Skip low-confidence detections
            if confidence < 0.3:
                continue

            # Extract bounding box coordinates
            # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]

            x = int(min(x_coords)) - padding
            y = int(min(y_coords)) - padding
            width = int(max(x_coords) - min(x_coords)) + (2 * padding)
            height = int(max(y_coords) - min(y_coords)) + (2 * padding)

            # Filter out tiny detections
            if width < min_width or height < min_height:
                continue

            # Ensure coordinates are within image bounds
            x = max(0, x)
            y = max(0, y)
            width = min(width, img.shape[1] - x)
            height = min(height, img.shape[0] - y)

            # Classify bubble type based on text characteristics
            bubble_type = self._classify_bubble_type(text, confidence)

            # Estimate original text size from OCR bounding box
            text_height = int(max(y_coords) - min(y_coords))
            # Scale font size MUCH LARGER (English needs more space than compact Korean)
            # Use 3x multiplier, but MINIMUM 40pt for small bubbles (readability first!)
            estimated_font_size = max(40, int(text_height * 3.0))
            print(f"  OCR detected Korean: '{text}' (confidence={confidence:.2f})", flush=True)
            print(f"    → height={text_height}px, font_size={estimated_font_size}pt", flush=True)

            bubbles.append({
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'type': bubble_type,
                'text': text,
                'confidence': confidence,
                'font_size': estimated_font_size
            })

        # Calculate average font size for consistency
        if bubbles:
            font_sizes = [b['font_size'] for b in bubbles]
            avg_font_size = sum(font_sizes) / len(font_sizes)
            median_font_size = sorted(font_sizes)[len(font_sizes) // 2]

            # Use median as base (more robust than average)
            target_font_size = max(40, int(median_font_size))

            print(f"\nFont size normalization:", flush=True)
            print(f"  Range: {min(font_sizes)}pt - {max(font_sizes)}pt", flush=True)
            print(f"  Median: {median_font_size}pt → Target: {target_font_size}pt", flush=True)

            # Normalize all font sizes to be closer to target
            # Allow some variation (±20%) but keep them similar
            for bubble in bubbles:
                original_size = bubble['font_size']
                # Blend: 70% target + 30% original (keeps some variation)
                normalized_size = int(0.7 * target_font_size + 0.3 * original_size)
                bubble['font_size'] = max(40, normalized_size)
                print(f"  {original_size}pt → {bubble['font_size']}pt", flush=True)

        print(f"\nDetected {len(bubbles)} text regions")
        return bubbles

    def _classify_bubble_type(self, text, confidence):
        """
        Classify bubble type based on text characteristics.

        Args:
            text: Detected Korean text
            confidence: OCR confidence score

        Returns:
            str: 'normal', 'shout', or 'whisper'
        """
        # Heuristics for bubble type classification
        # These can be adjusted based on manhwa conventions

        # Check for exclamation marks or all caps (shouting)
        if '!' in text or '！' in text:
            return 'shout'

        # Check for ellipsis or parentheses (whisper/thought)
        if '...' in text or '…' in text or '(' in text or ')' in text:
            return 'whisper'

        # Default to normal dialogue
        return 'normal'

    def merge_overlapping_bubbles(self, bubbles, overlap_threshold=0.5):
        """
        Merge overlapping bubble detections.

        Args:
            bubbles: List of detected bubbles
            overlap_threshold: IoU threshold for merging (0-1)

        Returns:
            list: Merged bubbles
        """
        if len(bubbles) <= 1:
            return bubbles

        merged = []
        used = set()

        for i, bubble1 in enumerate(bubbles):
            if i in used:
                continue

            # Start with current bubble
            merged_bubble = bubble1.copy()

            # Check for overlaps with other bubbles
            for j, bubble2 in enumerate(bubbles[i+1:], start=i+1):
                if j in used:
                    continue

                # Calculate IoU (Intersection over Union)
                iou = self._calculate_iou(bubble1, bubble2)

                if iou > overlap_threshold:
                    # Merge bubbles
                    merged_bubble = self._merge_two_bubbles(merged_bubble, bubble2)
                    used.add(j)

            merged.append(merged_bubble)
            used.add(i)

        return merged

    def _calculate_iou(self, bubble1, bubble2):
        """Calculate Intersection over Union of two bubbles."""
        x1 = max(bubble1['x'], bubble2['x'])
        y1 = max(bubble1['y'], bubble2['y'])
        x2 = min(bubble1['x'] + bubble1['width'], bubble2['x'] + bubble2['width'])
        y2 = min(bubble1['y'] + bubble1['height'], bubble2['y'] + bubble2['height'])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area1 = bubble1['width'] * bubble1['height']
        area2 = bubble2['width'] * bubble2['height']
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def _merge_two_bubbles(self, bubble1, bubble2):
        """Merge two bubbles into one larger bubble."""
        x = min(bubble1['x'], bubble2['x'])
        y = min(bubble1['y'], bubble2['y'])
        x_max = max(bubble1['x'] + bubble1['width'], bubble2['x'] + bubble2['width'])
        y_max = max(bubble1['y'] + bubble1['height'], bubble2['y'] + bubble2['height'])

        return {
            'x': x,
            'y': y,
            'width': x_max - x,
            'height': y_max - y,
            'type': bubble1['type'],  # Keep first bubble's type
            'confidence': max(bubble1.get('confidence', 0), bubble2.get('confidence', 0))
        }
