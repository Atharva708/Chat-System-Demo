# Installing Tesseract OCR on Render

## Quick Fix - Method 1: Direct Build Command (EASIEST - Recommended)

In your Render dashboard:

1. Go to your **Web Service**
2. Go to **Settings**
3. Find **Build Command**
4. Replace it with this **single line** (NO sudo needed - Render runs as root):
```bash
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng && pip install -r requirements.txt
```

5. Find **Start Command** and set it to:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

6. Click **Save Changes**
7. Render will automatically redeploy

**This is the simplest and most reliable method!**

## Method 2: Using Build Script

If Method 1 doesn't work, try the build script:

1. In Render **Settings** → **Build Command**, set:
```bash
bash build.sh
```

2. Find **Start Command** and set it to:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Method 3: Using Dockerfile (Most Reliable)

If build commands don't work, switch to Docker:

1. In Render **Settings** → **Environment**, change to **Docker**
2. Render will automatically use the `Dockerfile` in your repo
3. The Dockerfile already includes Tesseract installation
4. No build command needed!

## Method 3: Using render.yaml

If you have a `render.yaml` file, it should automatically use the build script.

## Verify Installation

After deployment, check your Render logs. You should see:
```
📦 Installing Tesseract OCR...
✓ Verifying Tesseract installation...
tesseract 5.x.x
✓ Tesseract OCR version 5.x.x detected and working
```

## Troubleshooting

### If build command fails with "permission denied"
- Make sure `build.sh` is executable
- Or use the direct command from Method 2

### If Tesseract still not found after build
- Check Render logs for build errors
- Make sure the build command completed successfully
- Verify Tesseract is in PATH: `which tesseract`

### Alternative: Use Dockerfile

If build commands don't work, create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install Tesseract OCR
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 10000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

Then in Render:
- Set **Docker** as the environment
- Render will automatically use the Dockerfile

