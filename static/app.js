// Global state
const state = {
    imageId: null,
    originalWidth: 0,
    originalHeight: 0,
    displayWidth: 0,
    displayHeight: 0,
    bubbles: [],
    currentCorner: null,
    currentBubbleType: 'normal'
};

// DOM elements
const uploadBtn = document.getElementById('uploadBtn');
const imageUpload = document.getElementById('imageUpload');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const canvasContainer = document.getElementById('canvasContainer');
const instructions = document.getElementById('instructions');
const controls = document.getElementById('controls');
const status = document.getElementById('status');
const autoDetectBtn = document.getElementById('autoDetectBtn');
const translateBtn = document.getElementById('translateBtn');
const clearBtn = document.getElementById('clearBtn');
const resultSection = document.getElementById('resultSection');
const resultImage = document.getElementById('resultImage');
const downloadBtn = document.getElementById('downloadBtn');

// Event listeners
uploadBtn.addEventListener('click', () => imageUpload.click());
imageUpload.addEventListener('change', handleImageUpload);
canvas.addEventListener('click', handleCanvasClick);
autoDetectBtn.addEventListener('click', handleAutoDetect);
translateBtn.addEventListener('click', handleTranslate);
clearBtn.addEventListener('click', handleClearAll);
downloadBtn.addEventListener('click', handleDownload);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!state.imageId) return;

    switch(e.key.toLowerCase()) {
        case 'n':
            state.currentBubbleType = 'normal';
            showStatus('Bubble type: Normal');
            break;
        case 's':
            state.currentBubbleType = 'shout';
            showStatus('Bubble type: Shout');
            break;
        case 'w':
            state.currentBubbleType = 'whisper';
            showStatus('Bubble type: Whisper');
            break;
        case 'u':
            undoLastBubble();
            break;
    }
});

// Handle image upload
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    try {
        showStatus('Uploading image...', true);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        const data = await response.json();
        state.imageId = data.image_id;
        state.originalWidth = data.width;
        state.originalHeight = data.height;

        // Display image on canvas
        displayImageOnCanvas(file);

        // Show UI elements
        canvasContainer.style.display = 'block';
        instructions.style.display = 'block';
        controls.style.display = 'block';
        resultSection.style.display = 'none';

        showStatus('Image uploaded! Click two corners to select bubbles.');

    } catch (error) {
        showStatus(`Error: ${error.message}`, false, true);
    }
}

// Display image on canvas
function displayImageOnCanvas(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            // Calculate display size (max 800px width)
            const maxWidth = 800;
            let displayWidth = img.width;
            let displayHeight = img.height;

            if (displayWidth > maxWidth) {
                displayHeight = (maxWidth / displayWidth) * displayHeight;
                displayWidth = maxWidth;
            }

            state.displayWidth = displayWidth;
            state.displayHeight = displayHeight;

            canvas.width = displayWidth;
            canvas.height = displayHeight;

            ctx.drawImage(img, 0, 0, displayWidth, displayHeight);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// Handle canvas click
function handleCanvasClick(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (!state.currentCorner) {
        // First corner
        state.currentCorner = { x, y };
        drawCrosshair(x, y);
        showStatus('Click second corner...');
    } else {
        // Second corner - create bubble
        const bubble = {
            x: Math.min(state.currentCorner.x, x),
            y: Math.min(state.currentCorner.y, y),
            width: Math.abs(x - state.currentCorner.x),
            height: Math.abs(y - state.currentCorner.y),
            type: state.currentBubbleType,
            font_size: 16  // Default font size for manual bubbles
        };

        state.bubbles.push(bubble);
        state.currentCorner = null;

        redrawCanvas();
        showStatus(`Bubble added (${state.currentBubbleType}). Total: ${state.bubbles.length}`);
    }
}

// Draw crosshair at position
function drawCrosshair(x, y) {
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - 10, y);
    ctx.lineTo(x + 10, y);
    ctx.moveTo(x, y - 10);
    ctx.lineTo(x, y + 10);
    ctx.stroke();
}

// Redraw canvas with all bubbles
function redrawCanvas() {
    // Reload image
    const img = new Image();
    img.onload = () => {
        ctx.drawImage(img, 0, 0, state.displayWidth, state.displayHeight);

        // Draw all bubbles
        state.bubbles.forEach(bubble => {
            drawBubble(bubble);
        });
    };
    img.src = canvas.toDataURL();
}

// Draw bubble rectangle
function drawBubble(bubble) {
    const colors = {
        normal: '#48bb78',
        shout: '#f56565',
        whisper: '#667eea'
    };

    ctx.strokeStyle = colors[bubble.type] || colors.normal;
    ctx.lineWidth = 3;
    ctx.strokeRect(bubble.x, bubble.y, bubble.width, bubble.height);
}

// Undo last bubble
function undoLastBubble() {
    if (state.bubbles.length === 0) {
        showStatus('No bubbles to undo');
        return;
    }

    state.bubbles.pop();
    redrawCanvas();
    showStatus(`Bubble removed. Total: ${state.bubbles.length}`);
}

// Convert display coordinates to original image coordinates
function convertToOriginalCoords(bubble) {
    const scaleX = state.originalWidth / state.displayWidth;
    const scaleY = state.originalHeight / state.displayHeight;

    return {
        x: Math.round(bubble.x * scaleX),
        y: Math.round(bubble.y * scaleY),
        width: Math.round(bubble.width * scaleX),
        height: Math.round(bubble.height * scaleY),
        type: bubble.type,
        font_size: bubble.font_size || 16,
        korean_text: bubble.korean_text || ''  // Include Korean text!
    };
}

// Handle translate
async function handleTranslate() {
    if (state.bubbles.length === 0) {
        showStatus('Please select at least one bubble', false, true);
        return;
    }

    try {
        showStatus('Translating...', true);
        showProgress('Preparing translation...', 10);
        translateBtn.disabled = true;

        // Convert bubbles to original coordinates
        const originalBubbles = state.bubbles.map(convertToOriginalCoords);

        showProgress(`Translating ${originalBubbles.length} bubbles...`, 30);

        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_id: state.imageId,
                bubbles: originalBubbles
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Translation failed');
        }

        showProgress('Processing translation...', 70);

        // Get JSON response with image and debug info
        const data = await response.json();

        // Log debug info to browser console
        console.clear();
        console.log('%c='.repeat(80), 'color: purple; font-weight: bold');
        console.log('%cGEMATOR TRANSLATION DEBUG INFO', 'color: purple; font-size: 16px; font-weight: bold');
        console.log('%c='.repeat(80), 'color: purple; font-weight: bold');

        console.log('\n%cBUBBLE COUNT:', 'color: blue; font-weight: bold', data.debug.bubble_count);
        console.log('\n%cTRANSLATIONS:', 'color: green; font-weight: bold');
        data.debug.translations.forEach((trans, i) => {
            console.log(`  [${i+1}] →`, trans);
        });

        console.log('\n%cGEMINI BATCHES:', 'color: orange; font-weight: bold');
        data.debug.batches.forEach((batch, i) => {
            console.log(`\n--- Batch ${i+1} ---`);
            console.log('Prompt:', batch.prompt);
            console.log('Response:', batch.response);
            console.log('Translations:', batch.translations);
        });

        console.log('\n%c='.repeat(80), 'color: purple; font-weight: bold');

        showProgress('Rendering result...', 90);

        // Display result image
        resultImage.src = data.image;
        resultSection.style.display = 'block';

        showProgress('Complete!', 100);
        setTimeout(hideProgress, 800);
        showStatus('✓ Translation complete! Check browser console for details.');

    } catch (error) {
        hideProgress();
        showStatus(`Error: ${error.message}`, false, true);
    } finally {
        translateBtn.disabled = false;
    }
}

// Handle clear all
function handleClearAll() {
    state.bubbles = [];
    state.currentCorner = null;
    redrawCanvas();
    showStatus('All bubbles cleared');
}

// Handle download
function handleDownload() {
    const link = document.createElement('a');
    link.href = resultImage.src;
    link.download = 'translated_manhwa.png';
    link.click();
}

// Handle auto-detect bubbles
async function handleAutoDetect() {
    if (!state.imageId) {
        showStatus('Please upload an image first', false, true);
        return;
    }

    // Track timeouts so we can clear them
    let progressTimeouts = [];

    try {
        showStatus('Starting OCR detection...', true);
        showProgress('Loading OCR model...', 10);
        autoDetectBtn.disabled = true;

        // Simulate progress updates (since we can't get real-time updates from backend)
        progressTimeouts.push(setTimeout(() => showProgress('Scanning image for Korean text...', 30), 1000));
        progressTimeouts.push(setTimeout(() => showProgress('Detecting text regions...', 50), 3000));

        const response = await fetch('/api/auto-detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_id: state.imageId
            })
        });

        // Clear simulated progress timeouts since we got real response
        progressTimeouts.forEach(timeout => clearTimeout(timeout));

        showProgress('Processing results...', 90);

        const data = await response.json();

        if (!response.ok) {
            hideProgress();
            throw new Error(data.error || 'Detection failed');
        }

        // Clear existing bubbles
        state.bubbles = [];

        // Convert detected bubbles from original coords to display coords
        const scaleX = state.displayWidth / state.originalWidth;
        const scaleY = state.displayHeight / state.originalHeight;

        data.bubbles.forEach(bubble => {
            state.bubbles.push({
                x: Math.round(bubble.x * scaleX),
                y: Math.round(bubble.y * scaleY),
                width: Math.round(bubble.width * scaleX),
                height: Math.round(bubble.height * scaleY),
                type: bubble.type,
                font_size: bubble.font_size || 16,
                korean_text: bubble.korean_text || ''  // Store OCR-detected Korean text
            });
        });

        // Redraw canvas with detected bubbles
        redrawCanvas();

        showProgress('Complete!', 100);
        setTimeout(hideProgress, 800);
        showStatus(`✓ Detected ${data.count} speech bubbles! Click "Translate" to process.`);

    } catch (error) {
        // Clear simulated progress timeouts on error too
        progressTimeouts.forEach(timeout => clearTimeout(timeout));
        hideProgress();
        showStatus(`Error: ${error.message}`, false, true);
    } finally {
        autoDetectBtn.disabled = false;
    }
}

// Show status message
function showStatus(message, loading = false, isError = false) {
    status.textContent = message;
    status.className = 'status';

    if (loading) {
        status.classList.add('loading');
    }

    if (isError) {
        status.classList.add('error');
    }
}

// Progress bar functions
function showProgress(message, percent) {
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    progressContainer.style.display = 'block';
    progressFill.style.width = percent + '%';
    progressText.textContent = message;
}

function hideProgress() {
    const progressContainer = document.getElementById('progressContainer');
    progressContainer.style.display = 'none';
}
