# Google Sheets Setup Guide

Since Render doesn't allow local file saving, you need to set up Google Sheets integration to save extracted data.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

## Step 2: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Give it a name (e.g., "chat-system-sheets")
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

## Step 3: Create Service Account Key

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Download the JSON file

## Step 4: Create Google Sheet

1. Create a new Google Sheet
2. Note the Sheet ID from the URL:
   - URL format: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Copy the `SHEET_ID_HERE` part

## Step 5: Share Sheet with Service Account

1. Open your Google Sheet
2. Click "Share" button
3. Add the service account email (found in the JSON file as `client_email`)
4. Give it "Editor" permissions
5. Click "Send"

## Step 6: Set Environment Variables in Render

In your Render dashboard, add these environment variables:

1. **GOOGLE_SHEET_ID**: Your Google Sheet ID (from Step 4)
2. **GOOGLE_SHEETS_CREDENTIALS_JSON**: The entire contents of the JSON file (from Step 3)
   - Copy the entire JSON file content
   - Paste it as a single-line value (or use Render's multi-line support)

## Alternative: Use Local File Saving

If you're running locally (not on Render), the system will automatically fall back to saving Excel files to your Desktop in the `Chat_Extracted_Data` folder.

## Testing

After deployment, check your Google Sheet - it should automatically create worksheets named "Extracted Data YYYY-MM-DD" and append data there.

