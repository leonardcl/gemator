<div align="center">

# 🎨 Gemator

### AI-Powered Korean Manhwa Translator

*Transform Korean manhwa into English with the power of AI*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gemini AI](https://img.shields.io/badge/Powered%20by-Gemini%20AI-purple.svg)](https://ai.google.dev/)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#-tech-stack) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### 🤖 **Intelligent OCR Detection**
- Automatic speech bubble detection using EasyOCR
- Korean text recognition with confidence scoring
- Smart bubble merging to combine overlapping regions

### 🌐 **AI-Powered Translation**
- Google Gemini 2.5 Flash for natural translations
- Batch processing (10 bubbles per API call for efficiency)
- Context-aware translation using full page + bubble crops
- Bubble type classification (normal, shout, whisper)

### 🎨 **Advanced Text Rendering**
- Two-pass rendering system: white blocks → glass text overlays
- Intelligent text wrapping for long translations
- Font size normalization for consistent appearance
- Auto-shrinking fonts to fit bubble dimensions
- Semi-transparent glass backgrounds for overlapping text

### 💻 **Modern Web Interface**
- Interactive HTML5 Canvas for manual bubble selection
- Real-time progress bar with stage-by-stage updates
- Browser console debugging with colored output
- Responsive design with gradient UI
- Download translated images

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Modern web browser

### Quick Start

```bash
# Clone the repository
git clone https://github.com/leonardcl/gemator.git
cd gemator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the application
python app.py
```

Visit `http://localhost:5001` in your browser!

---

## 📖 Usage

### Method 1: Auto-Detect (Recommended)
1. **Upload** a Korean manhwa image
2. Click **"🔍 Auto-Detect Bubbles"**
3. Wait for OCR to find all text regions
4. Click **"Translate"** to process
5. **Download** your translated image!

### Method 2: Manual Selection
1. **Upload** an image
2. **Click two corners** to draw rectangles around bubbles
3. Press `N` (normal), `S` (shout), or `W` (whisper) to change bubble type
4. Press `U` to undo last bubble
5. Click **"Translate"** when ready

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `N` | Normal bubble type |
| `S` | Shout bubble type (emphasized) |
| `W` | Whisper/thought bubble type |
| `U` | Undo last bubble |

---

## 🛠️ Tech Stack

### Backend
- **Flask 3.0.0** - Web framework
- **Google Generative AI** - Gemini 2.5 Flash for translation
- **EasyOCR** - Korean text detection
- **Pillow & OpenCV** - Image processing

### Frontend
- **Vanilla JavaScript** - No frameworks, pure performance
- **HTML5 Canvas** - Interactive bubble selection
- **CSS3** - Modern gradient UI with animations

---

## 📂 Project Structure

```
gemator/
├── app.py                 # Flask application & API endpoints
├── bubble_detector.py     # EasyOCR integration for auto-detection
├── translator.py          # Gemini API translation engine
├── compositor.py          # Text rendering & image composition
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── static/
│   ├── index.html        # Web interface
│   ├── app.js            # Frontend logic
│   └── style.css         # Modern gradient styling
├── uploads/              # Temporary image storage
└── README.md             # You are here!
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
FLASK_ENV=development
MAX_UPLOAD_SIZE=10485760  # 10MB
```

### API Rate Limits

**Gemini Free Tier:**
- 15 requests per minute
- 1,500 requests per day
- Batch translation helps stay within limits!

---

## 🔧 How It Works

### Translation Pipeline

```
1. 📤 Image Upload
   └─> Store in uploads/ with UUID

2. 🔍 OCR Detection (Auto-Detect)
   ├─> EasyOCR scans for Korean text
   ├─> Extract bounding boxes
   ├─> Estimate font sizes from OCR height
   └─> Normalize font sizes for consistency

3. 🌐 Batch Translation
   ├─> Group bubbles (max 10 per batch)
   ├─> Send to Gemini: full page + Korean texts + bubble crops
   ├─> Parse [1], [2], [3] format translations
   └─> Strict prompt for 1:1 translation accuracy

4. 🎨 Two-Pass Rendering
   ├─> Pass 1: Draw ALL white blocks (hide Korean)
   └─> Pass 2: Draw ALL text with glass backgrounds

5. 📥 Download Result
   └─> Return base64 encoded translated image
```

---

## 🐛 Troubleshooting

### OCR Issues
**Problem:** "Loading OCR model takes too long"
**Solution:** First load downloads ~100MB Korean model. Subsequent loads are faster. Be patient!

**Problem:** "Text not detected"
**Solution:** Ensure image has clear Korean text. Try adjusting image brightness/contrast.

### Translation Issues
**Problem:** "Translation failed"
**Solution:** Check API key validity. Verify you haven't hit rate limits (15 req/min).

**Problem:** "Weird translations"
**Solution:** Gemini needs context. Auto-detect sends Korean text + images for better accuracy.

### Rendering Issues
**Problem:** "Text cut off or overflowing"
**Solution:** Text wrapping is enabled. If still issues, bubble might be too small for translation.

**Problem:** "Font too small/large"
**Solution:** Font sizes are normalized. Manual bubbles default to 16pt, auto-detect estimates from OCR.

---

## 🎯 Roadmap

- [x] Auto-detect bubbles with OCR
- [x] Batch translation
- [x] Text wrapping
- [x] Progress bar
- [ ] Reading order detection (right-to-left panels)
- [ ] Multi-page batch processing
- [ ] Translation quality rating
- [ ] Cloud deployment (Railway/Fly.io)
- [ ] Support for other languages (Japanese, Chinese)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.dev/) for powerful translation
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for Korean text detection
- [Flask](https://flask.palletsprojects.com/) for the web framework
- Korean manhwa creators for inspiring this project

---

## 📬 Contact

**Leonard** - [@leonardcl](https://github.com/leonardcl)
**Marcell** - [@mjwsolver](https://github.com/mjwSolver)
**Matthew** - [@SpacePeant](https://github.com/SpacePeant)

Project Link: [https://github.com/leonardcl/gemator](https://github.com/leonardcl/gemator)

---

<div align="center">

Made with ❤️ and AI

⭐ Star this repo if you found it helpful!

</div>
