"""Flask backend API for Gemator manhwa translator."""

from flask import Flask, request, jsonify, send_file, send_from_directory
from PIL import Image
import os
import uuid
import io
from translator import TranslationEngine
from compositor import TextCompositor
from bubble_detector import BubbleDetector

app = Flask(__name__, static_folder='static')

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize engines
translator = TranslationEngine()
compositor = TextCompositor()
detector = None  # Lazy load (heavy model)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Handle image upload.

    Returns:
        JSON: {image_id: str, width: int, height: int}
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file format. Use PNG or JPEG'}), 400

    try:
        # Generate unique ID
        image_id = str(uuid.uuid4())
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{image_id}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save file
        file.save(filepath)

        # Get image dimensions
        with Image.open(filepath) as img:
            width, height = img.size

        return jsonify({
            'image_id': image_id,
            'width': width,
            'height': height
        })

    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/auto-detect', methods=['POST'])
def auto_detect_bubbles():
    """
    Automatically detect speech bubbles using OCR.

    Expects JSON: {image_id: str}
    Returns: {bubbles: [{x, y, width, height, type}]}
    """
    global detector

    try:
        data = request.get_json()
        if not data or 'image_id' not in data:
            return jsonify({'error': 'Missing image_id'}), 400

        image_id = data['image_id']

        # Find uploaded image
        image_path = None
        for ext in ALLOWED_EXTENSIONS:
            path = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_id}.{ext}")
            if os.path.exists(path):
                image_path = path
                break

        if not image_path:
            return jsonify({'error': 'Image not found'}), 404

        # Lazy load detector (it's heavy!)
        if detector is None:
            print("Loading bubble detector (this may take a moment)...")
            detector = BubbleDetector()

        # Detect bubbles
        bubbles = detector.detect_bubbles(image_path)

        # Merge overlapping bubbles
        bubbles = detector.merge_overlapping_bubbles(bubbles)

        # Return bubbles WITH Korean text for translation
        clean_bubbles = [
            {
                'x': b['x'],
                'y': b['y'],
                'width': b['width'],
                'height': b['height'],
                'type': b['type'],
                'font_size': b.get('font_size', 16),
                'korean_text': b.get('text', '')  # Include OCR-detected Korean text!
            }
            for b in bubbles
        ]

        return jsonify({
            'bubbles': clean_bubbles,
            'count': len(clean_bubbles)
        })

    except Exception as e:
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500


@app.route('/api/translate', methods=['POST'])
def translate_image():
    """
    Process translation request.

    Expects JSON:
    {
        image_id: str,
        bubbles: [{x, y, width, height, type}]
    }

    Returns:
        Binary image file (PNG)
    """
    # Store debug info to send to browser console
    debug_info = {
        'ocr_detections': [],
        'gemini_prompt': '',
        'gemini_response': '',
        'translations': []
    }

    try:
        data = request.get_json()

        if not data or 'image_id' not in data or 'bubbles' not in data:
            return jsonify({'error': 'Missing image_id or bubbles'}), 400

        image_id = data['image_id']
        bubbles = data['bubbles']

        # Find uploaded image
        image_path = None
        for ext in ALLOWED_EXTENSIONS:
            path = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_id}.{ext}")
            if os.path.exists(path):
                image_path = path
                break

        if not image_path:
            return jsonify({'error': 'Image not found'}), 404

        # Load image
        image = Image.open(image_path).convert('RGB')
        print(f"✓ Loaded image: {image_path}", flush=True)
        print(f"✓ Processing {len(bubbles)} bubbles", flush=True)

        # Sort bubbles by y-coordinate (top to bottom)
        # This ensures bottom bubbles are drawn last (on top)
        sorted_bubbles = sorted(bubbles, key=lambda b: b['y'])

        # PASS 1: Draw ALL solid white blocks first (hide all Korean text)
        print("Pass 1: Drawing white blocks to hide Korean text...", flush=True)
        for bubble in sorted_bubbles:
            compositor.draw_white_block(image, bubble)

        # Batch translation: process 10 bubbles at a time
        batch_size = 10
        all_translations = []
        all_debug_info = []

        for i in range(0, len(sorted_bubbles), batch_size):
            batch = sorted_bubbles[i:i + batch_size]

            # Crop all bubbles and get Korean text in this batch
            crops = [
                image.crop((b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height']))
                for b in batch
            ]
            korean_texts = [b.get('korean_text', '') for b in batch]

            # Translate entire batch in one API call
            print(f"Translating batch {i//batch_size + 1}: {len(crops)} bubbles", flush=True)
            translations, debug = translator.translate_bubbles_batch(crops, korean_texts, image)
            all_translations.extend(translations)
            all_debug_info.append(debug)
            print(f"  → Got {len(translations)} translations", flush=True)

        # PASS 2: Draw ALL English text with glass backgrounds (overlaps are readable)
        print("Pass 2: Drawing English text with glass backgrounds...", flush=True)
        for bubble, translated_text in zip(sorted_bubbles, all_translations):
            image = compositor.draw_text_with_glass(image, bubble, translated_text)

        # Clean up original upload
        try:
            os.remove(image_path)
        except Exception:
            pass

        # Convert image to base64 for JSON response
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        import base64
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        # Return JSON with image and debug info
        return jsonify({
            'image': f'data:image/png;base64,{img_base64}',
            'debug': {
                'bubble_count': len(bubbles),
                'translations': all_translations,
                'batches': all_debug_info,
                'message': 'Translation complete - check console for details'
            }
        })

    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
