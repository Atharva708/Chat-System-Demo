# Credentials.json Setup Guide

## File Structure

Place your `credentials.json` file in the root directory of the project. The file should contain your Google Service Account credentials.

## Option 1: Standard Service Account JSON

Your `credentials.json` should look like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## Option 2: With Sheet ID Included

You can optionally include the Google Sheet ID directly in the credentials file:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/...",
  "sheet_id": "your-google-sheet-id-here"
}
```

## Getting Your Google Sheet ID

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
3. Copy the `SHEET_ID_HERE` part - that's your Sheet ID

## Sharing the Sheet

**IMPORTANT:** You must share your Google Sheet with the service account email:

1. Open your Google Sheet
2. Click the "Share" button
3. Add the email address from `client_email` in your credentials.json
4. Give it "Editor" permissions
5. Click "Send"

## Environment Variable Alternative

If you prefer not to use a file, you can set environment variables instead:

- `GOOGLE_SHEET_ID`: Your Google Sheet ID
- `GOOGLE_SHEETS_CREDENTIALS_JSON`: The entire JSON content as a string

## All Fields Saved to Sheets

The system will save ALL extracted fields to Google Sheets, including:

- timestamp
- sentiment
- member_id
- first_name
- last_name
- dob
- address
- city
- state
- zip_code
- address_status
- member_status
- start_date
- end_date
- health_plan
- contract_type
- codes
- change_request
- raw_text
- user_identifier
- extracted_by
- extraction_timestamp

All fields are always included in the sheet, even if empty, ensuring consistent column structure.

