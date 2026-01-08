# Local OCR Setup Guide

The system now uses **local Tesseract OCR** instead of an external API. This means:
- ✅ No external API dependencies
- ✅ Works offline
- ✅ Faster processing (no network calls)
- ✅ More control over OCR quality

## Installation

### macOS
```bash
brew install tesseract
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR\`
3. The code will auto-detect it

### Docker/Render
Add to your Dockerfile or build command:
```dockerfile
RUN apt-get update && apt-get install -y tesseract-ocr
```

## Python Dependencies

Install Python packages:
```bash
pip install -r requirements.txt
```

This will install:
- `pytesseract` - Python wrapper for Tesseract
- `Pillow` - Image processing
- `pypdfium2` - PDF processing (if needed)
- `python-docx` - DOCX processing (if needed)

## Configuration

The system automatically detects Tesseract:
1. Checks `TESSERACT_CMD` environment variable
2. On Windows: Checks default install path
3. Otherwise: Uses system PATH

### Custom Tesseract Path

If Tesseract is installed in a non-standard location, set:
```bash
export TESSERACT_CMD="/path/to/tesseract"
```

Or in Render, add environment variable:
- Key: `TESSERACT_CMD`
- Value: `/path/to/tesseract`

## How It Works

1. **Image Upload**: User uploads an image
2. **Base64 Decode**: Image is decoded from base64
3. **Image Preprocessing**:
   - Convert to grayscale
   - Resize if too small (improves accuracy)
   - Auto-contrast enhancement
   - Sharpen filter
4. **OCR**: Tesseract extracts text
5. **Extraction**: Text is processed by local extractor
6. **Save**: Data saved to Google Sheets or Excel

## Testing

After installation, test with:
```python
import pytesseract
from PIL import Image

# Test OCR
image = Image.open("test_image.png")
text = pytesseract.image_to_string(image)
print(text)
```

## Troubleshooting

### "TesseractNotFoundError"
- Install Tesseract (see above)
- Check if it's in PATH: `tesseract --version`
- Set `TESSERACT_CMD` environment variable

### Poor OCR Results
- Ensure image quality is good
- Try higher resolution images
- Check if image is clear and readable

### Slow Processing
- Large images take longer
- Consider resizing very large images before upload
- Processing happens server-side, so network speed doesn't affect OCR

## Benefits Over API

- ✅ **No API costs** - Free to use
- ✅ **No rate limits** - Process as many images as needed
- ✅ **Privacy** - Images never leave your server
- ✅ **Reliability** - No external service dependencies
- ✅ **Speed** - No network latency

