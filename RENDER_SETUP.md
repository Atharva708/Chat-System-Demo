# Render Setup Guide - Google Sheets Configuration

Since `credentials.json` is in `.gitignore` (for security), you need to use **Environment Variables** on Render.

## Step 1: Get Your Credentials

You already have `credentials.json` locally. You need to:

1. **Get the Sheet ID**: `1wsIj3UJFlyDUaD0af-XbguRcP20La8uc0C3JP3imTgQ`

2. **Get the Service Account JSON**: Open your `credentials.json` file and copy the entire contents.

## Step 2: Set Environment Variables in Render

1. Go to your Render Dashboard: https://dashboard.render.com
2. Select your web service
3. Go to **Environment** tab
4. Click **Add Environment Variable**

### Add These Two Variables:

#### Variable 1: `GOOGLE_SHEET_ID`
- **Key**: `GOOGLE_SHEET_ID`
- **Value**: `1wsIj3UJFlyDUaD0af-XbguRcP20La8uc0C3JP3imTgQ`
- Click **Save Changes**

#### Variable 2: `GOOGLE_SHEETS_CREDENTIALS_JSON`
- **Key**: `GOOGLE_SHEETS_CREDENTIALS_JSON`
- **Value**: Paste the **entire contents** of your `credentials.json` file
  - This should be a JSON object starting with `{` and ending with `}`
  - Include all fields: `type`, `project_id`, `private_key`, `client_email`, etc.
  - Make sure it's valid JSON (no extra commas, proper quotes)
- Click **Save Changes**

## Step 3: Verify the Sheet is Shared

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1wsIj3UJFlyDUaD0af-XbguRcP20La8uc0C3JP3imTgQ/edit
2. Click **Share** button
3. Find the `client_email` from your credentials.json (looks like: `something@project-id.iam.gserviceaccount.com`)
4. Add that email with **Editor** permissions
5. Click **Send**

## Step 4: Install Tesseract OCR (Required for Image Processing)

### Option A: Using Build Command (Recommended)

1. Go to your Render service **Settings**
2. Find **Build Command** field
3. Set it to (NO sudo - Render runs as root):
```bash
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng && pip install -r requirements.txt
```

4. Find **Start Command** and set it to:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Option B: Using Build Script

1. The `build.sh` script is already in your repo
2. In Render **Settings**, set **Build Command** to:
```bash
chmod +x build.sh && ./build.sh
```

### Option C: Using Dockerfile

1. The `Dockerfile` is already in your repo
2. In Render **Settings**, change **Environment** to **Docker**
3. Render will automatically use the Dockerfile

## Step 5: Redeploy

After setting environment variables and build command:
1. Render will automatically redeploy, OR
2. Go to **Manual Deploy** > **Deploy latest commit**

## Step 6: Test

1. Check server logs - you should see:
   ```
   🌐 Running on Render - using environment variables for credentials
   📝 Initializing from environment variables...
   ✓ Google Sheets client authorized from environment variables
   ✓ Successfully connected to Google Sheet: [Your Sheet Name]
   ✓ Google Sheets fully initialized and ready!
   ```

2. Visit: `https://your-render-url/test-sheets`
   - Should return success message

3. Send a test message in the chat
   - Data should appear in your Google Sheet

## Troubleshooting

### Error: "Missing environment variables on Render"
- Make sure both `GOOGLE_SHEET_ID` and `GOOGLE_SHEETS_CREDENTIALS_JSON` are set
- Check for typos in variable names
- Make sure values are saved (click Save Changes)

### Error: "Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON"
- Make sure you copied the entire JSON from credentials.json
- Check for extra characters or line breaks
- Validate JSON format

### Error: "Cannot access Google Sheet"
- Verify the sheet is shared with the service account email
- Check that the email in `client_email` matches what you shared
- Ensure Editor permissions (not Viewer)

### Still Not Working?
1. Check Render logs for detailed error messages
2. Visit `/test-sheets` endpoint to see specific errors
3. Verify environment variables are set correctly in Render dashboard

