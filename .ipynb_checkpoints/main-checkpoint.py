from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional
import json
import base64
from datetime import datetime
import aiohttp
import asyncio
import pandas as pd
import os
from extractor import extract_attributes, ConversationData, asdict
from openpyxl import Workbook, load_workbook

app = FastAPI()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.messages: List[Dict] = []  # Store messages per session
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send chat history to new connection
        if self.messages:
            await websocket.send_json({
                "type": "history",
                "messages": self.messages
            })
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        # Add message to history
        self.messages.append(message)
        # Keep only last 100 messages to prevent memory issues
        if len(self.messages) > 100:
            self.messages.pop(0)
        
        # Broadcast to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass  # Skip failed connections

manager = ConnectionManager()

# API Configuration
OCR_API_URL = "https://ocr-deploy-lbdg.onrender.com"  # OCR API for images

# Save Excel files to Desktop
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
EXCEL_OUTPUT_DIR = os.path.join(DESKTOP_PATH, "Chat_Extracted_Data")

# Create output directory if it doesn't exist
os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)

async def extract_text_from_image(image_base64: str) -> Optional[str]:
    """
    Sends image to OCR API and returns extracted text.
    Returns None if OCR fails.
    """
    try:
        # Convert base64 to bytes
        if ',' in image_base64:
            # Remove data URL prefix (e.g., "data:image/png;base64,")
            header, image_base64 = image_base64.split(',', 1)
            # Try to detect image type from header
            if 'image/jpeg' in header or 'image/jpg' in header:
                content_type = 'image/jpeg'
                filename = 'image.jpg'
            elif 'image/png' in header:
                content_type = 'image/png'
                filename = 'image.png'
            else:
                content_type = 'image/png'  # Default
                filename = 'image.png'
        else:
            content_type = 'image/png'
            filename = 'image.png'
        
        image_data = base64.b64decode(image_base64)
        print(f"📤 Sending image to OCR API ({len(image_data)} bytes, {content_type})...")
        
        async with aiohttp.ClientSession() as session:
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('file', 
                         image_data,
                         filename=filename,
                         content_type=content_type)
            
            # Make OCR API call
            async with session.post(OCR_API_URL, data=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    content_type_header = response.headers.get('content-type', '').lower()
                    if 'application/json' in content_type_header:
                        result = await response.json()
                        ocr_text = result.get('text') or result.get('extracted_text') or result.get('ocr_text') or ''
                        if ocr_text:
                            print(f"✓ OCR returned {len(ocr_text)} characters")
                        else:
                            print("⚠ OCR returned empty text")
                        return ocr_text if ocr_text else None
                    else:
                        ocr_text = await response.text()
                        if ocr_text:
                            print(f"✓ OCR returned {len(ocr_text)} characters (plain text)")
                        return ocr_text if ocr_text else None
                else:
                    error_text = await response.text()
                    print(f"✗ OCR API Error: {response.status} - {error_text[:200]}")
                    return None
    except asyncio.TimeoutError:
        print("✗ OCR API timeout (60s)")
        return None
    except Exception as e:
        print(f"✗ Error calling OCR API: {str(e)}")
        return None

async def process_text_locally(text: str) -> Dict:
    """
    Processes text using local extractor and returns extracted data.
    """
    try:
        # Use local extractor
        extracted_data = extract_attributes(text)
        # Convert to dictionary
        result_dict = asdict(extracted_data)
        # Remove None values for cleaner output
        result_dict = {k: v for k, v in result_dict.items() if v is not None}
        return {
            "status": "success",
            "extracted_data": result_dict
        }
    except Exception as e:
        print(f"Error in local extraction: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def save_to_excel(extracted_data: Dict, timestamp: str) -> str:
    """
    Saves extracted data to an Excel file.
    Uses the same format as the original extractor (appends to daily file).
    Returns the file path.
    """
    try:
        # Get today's date for filename
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"extracted_data_{today}.xlsx"
        filepath = os.path.join(EXCEL_OUTPUT_DIR, filename)
        
        # Get field names from ConversationData
        field_names = list(extracted_data.keys())
        row_values = [extracted_data.get(field, '') for field in field_names]
        
        # Create or append to Excel file
        if not os.path.exists(filepath):
            wb = Workbook()
            ws = wb.active
            ws.title = "Extraction Data"
            ws.append(field_names)  # Header row
            ws.append(row_values)    # Data row
            wb.save(filepath)
        else:
            wb = load_workbook(filepath)
            ws = wb.active
            ws.append(row_values)  # Append data row
            wb.save(filepath)
        
        return filepath
        
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")
        # Fallback: save as JSON if Excel fails
        filename = f"extracted_data_{timestamp.replace(':', '-').replace(' ', '_')}.json"
        filepath = os.path.join(EXCEL_OUTPUT_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        return filepath

@app.get("/test")
async def test():
    return {"status": "Server is running!"}

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #f3f4f6;
            height: 100vh;
            overflow: hidden;
        }
        /* Custom scrollbar */
        .custom-scrollbar::-webkit-scrollbar {
            width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        /* Teams purple color */
        .teams-purple {
            background-color: #4B53BC !important;
        }
        .teams-purple-dark {
            background-color: #3d44a0 !important;
        }
        .teams-purple-light {
            background-color: #6b73d4 !important;
        }
        .teams-purple-text {
            color: #4B53BC !important;
        }
        .teams-purple-border {
            border-color: #4B53BC !important;
        }
        .teams-purple-ring:focus {
            outline: 2px solid #4B53BC;
            outline-offset: 2px;
        }
    </style>
</head>
<body class="bg-gray-100 h-screen overflow-hidden">
    <div class="flex h-screen">
        <!-- Left Sidebar -->
        <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div class="p-4 border-b border-gray-200">
                <h2 class="text-xl font-semibold text-gray-800">Recent Chats</h2>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar">
                <div class="p-2">
                    <div class="chat-item p-3 rounded-lg hover:bg-gray-100 cursor-pointer mb-2 active-chat" data-chat="Team Alpha">
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-full teams-purple flex items-center justify-center text-white font-semibold mr-3">
                                TA
                            </div>
                            <div class="flex-1">
                                <div class="font-semibold text-gray-800">Team Alpha</div>
                                <div class="text-sm text-gray-500">Active now</div>
                            </div>
                        </div>
                    </div>
                    <div class="chat-item p-3 rounded-lg hover:bg-gray-100 cursor-pointer mb-2" data-chat="General">
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold mr-3">
                                G
                            </div>
                            <div class="flex-1">
                                <div class="font-semibold text-gray-800">General</div>
                                <div class="text-sm text-gray-500">Active now</div>
                            </div>
                        </div>
                    </div>
                    <div class="chat-item p-3 rounded-lg hover:bg-gray-100 cursor-pointer mb-2" data-chat="Project Beta">
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white font-semibold mr-3">
                                PB
                            </div>
                            <div class="flex-1">
                                <div class="font-semibold text-gray-800">Project Beta</div>
                                <div class="text-sm text-gray-500">Active now</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Chat Area -->
        <div class="flex-1 flex flex-col bg-white">
            <!-- Chat Header -->
            <div class="teams-purple text-white p-4 flex items-center justify-between border-b teams-purple-dark">
                <div class="flex items-center">
                    <div class="w-10 h-10 rounded-full teams-purple-dark flex items-center justify-center text-white font-semibold mr-3">
                        TA
                    </div>
                    <div>
                        <div class="font-semibold text-lg" id="chat-title">Team Alpha</div>
                        <div class="text-sm opacity-80">Online</div>
                    </div>
                </div>
                <div class="flex items-center space-x-2 text-sm">
                    <div class="flex items-center space-x-1">
                        <span id="ocr-status-indicator" class="w-2 h-2 rounded-full bg-gray-400" title="OCR API"></span>
                        <span class="opacity-80">OCR</span>
                    </div>
                    <div class="flex items-center space-x-1">
                        <span id="extractor-status-indicator" class="w-2 h-2 rounded-full bg-green-400" title="Local Extractor"></span>
                        <span class="opacity-80">Extractor</span>
                    </div>
                </div>
            </div>

            <!-- Messages Area -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-4 bg-gray-50" id="messages-container">
                <div id="messages" class="space-y-4">
                    <!-- Messages will be inserted here -->
                </div>
            </div>

            <!-- Input Area -->
            <div class="border-t border-gray-200 p-4 bg-white">
                <div class="flex items-end space-x-2">
                    <label class="cursor-pointer p-2 hover:bg-gray-100 rounded-lg transition">
                        <input type="file" id="image-input" accept="image/*" class="hidden">
                        <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
                        </svg>
                    </label>
                    <div class="flex-1">
                        <textarea 
                            id="message-input" 
                            placeholder="Type a message..." 
                            class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 teams-purple-ring focus:border-transparent resize-none"
                            rows="1"
                            onkeydown="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }"
                        ></textarea>
                    </div>
                    <button 
                        id="send-button"
                        onclick="sendMessage()" 
                        class="teams-purple text-white px-6 py-3 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
                        style="background-color: #4B53BC;"
                        onmouseover="this.style.backgroundColor='#3d44a0'"
                        onmouseout="this.style.backgroundColor='#4B53BC'"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Dynamically detect WebSocket protocol based on current page protocol
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        const messagesContainer = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const imageInput = document.getElementById('image-input');
        const messagesScrollContainer = document.getElementById('messages-container');
        let currentChat = 'Team Alpha';

        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Handle image selection
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const base64Image = event.target.result;
                    sendImageMessage(base64Image, file.name);
                };
                reader.readAsDataURL(file);
                // Reset input
                e.target.value = '';
            }
        });

        // Check API status on page load
        async function checkAPIStatus() {
            try {
                // Check OCR API
                const ocrResponse = await fetch('https://ocr-deploy-lbdg.onrender.com', { 
                    method: 'HEAD',
                    mode: 'no-cors',
                    cache: 'no-cache'
                });
                document.getElementById('ocr-status-indicator').className = 'w-2 h-2 rounded-full bg-green-400';
            } catch (e) {
                document.getElementById('ocr-status-indicator').className = 'w-2 h-2 rounded-full bg-red-400';
            }
            // Extractor is always local (green)
            document.getElementById('extractor-status-indicator').className = 'w-2 h-2 rounded-full bg-green-400';
        }
        
        // Check API status on load
        checkAPIStatus();
        // Re-check every 30 seconds
        setInterval(checkAPIStatus, 30000);

        // WebSocket event handlers
        ws.onopen = function() {
            console.log('WebSocket connected');
            sendButton.disabled = false;
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'history') {
                // Load chat history
                messagesContainer.innerHTML = '';
                data.messages.forEach(msg => {
                    addMessageToUI(msg);
                });
                scrollToBottom();
            } else if (data.type === 'message' || data.type === 'image') {
                addMessageToUI(data);
                scrollToBottom();
            } else if (data.type === 'notification') {
                // Only show final notifications (not status updates)
                addNotificationToUI(data);
                scrollToBottom();
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        ws.onclose = function() {
            console.log('WebSocket disconnected');
            sendButton.disabled = true;
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            }, 3000);
        };

        function addMessageToUI(data) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'flex items-start space-x-3';
            
            const avatar = document.createElement('div');
            avatar.className = 'w-8 h-8 rounded-full teams-purple flex items-center justify-center text-white font-semibold flex-shrink-0';
            avatar.textContent = data.sender ? data.sender.substring(0, 2).toUpperCase() : 'U';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'flex-1';
            
            const senderName = document.createElement('div');
            senderName.className = 'text-sm font-semibold text-gray-800 mb-1';
            senderName.textContent = data.sender || 'Anonymous';
            
            if (data.type === 'image' && data.image) {
                const img = document.createElement('img');
                img.src = data.image;
                img.className = 'max-w-md rounded-lg shadow-md cursor-pointer';
                img.onclick = function() {
                    window.open(this.src, '_blank');
                };
                contentDiv.appendChild(senderName);
                contentDiv.appendChild(img);
                if (data.text) {
                    const textP = document.createElement('p');
                    textP.className = 'text-gray-700 mt-2';
                    textP.textContent = data.text;
                    contentDiv.appendChild(textP);
                }
            } else {
                const textP = document.createElement('p');
                textP.className = 'text-gray-700';
                textP.textContent = data.text || '';
                contentDiv.appendChild(senderName);
                contentDiv.appendChild(textP);
            }
            
            const timeSpan = document.createElement('span');
            timeSpan.className = 'text-xs text-gray-500 ml-2';
            timeSpan.textContent = data.timestamp || '';
            
            senderName.appendChild(timeSpan);
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
            messagesContainer.appendChild(messageDiv);
        }

        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text && !imageInput.files[0]) return;
            
            if (text) {
                const message = {
                    type: 'message',
                    text: text,
                    sender: 'You',
                    timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                };
                
                ws.send(JSON.stringify(message));
                messageInput.value = '';
                messageInput.style.height = 'auto';
            }
        }

        function sendImageMessage(base64Image, filename) {
            const message = {
                type: 'image',
                image: base64Image,
                text: filename,
                sender: 'You',
                timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
            };
            
            ws.send(JSON.stringify(message));
        }

        function addNotificationToUI(data) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'flex items-center justify-center my-2';
            
            const notificationContent = document.createElement('div');
            
            // Determine color based on status (only success/error now)
            const status = data.status || 'success';
            let bgColor, borderColor, textColor;
            
            if (status === 'success') {
                bgColor = 'bg-green-100';
                borderColor = 'border-green-400';
                textColor = 'text-green-700';
            } else {
                bgColor = 'bg-red-100';
                borderColor = 'border-red-400';
                textColor = 'text-red-700';
            }
            
            notificationContent.className = `${bgColor} border ${borderColor} ${textColor} px-4 py-2 rounded-lg text-sm`;
            notificationContent.textContent = data.text || 'Completed';
            
            notificationDiv.appendChild(notificationContent);
            messagesContainer.appendChild(notificationDiv);
        }

        function scrollToBottom() {
            messagesScrollContainer.scrollTop = messagesScrollContainer.scrollHeight;
        }

        // Chat selection (for future enhancement)
        document.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', function() {
                document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('active-chat'));
                this.classList.add('active-chat');
                this.style.backgroundColor = '#f3f4f6';
                currentChat = this.dataset.chat;
                document.getElementById('chat-title').textContent = currentChat;
            });
        });
    </script>
</body>
</html>
    """
    return html_content

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_data['timestamp'] = message_data.get('timestamp', datetime.now().strftime('%H:%M'))
            
            # Process message through API if it's a new message (not history)
            if message_data.get('type') in ['message', 'image']:
                # Extract text and image
                text = message_data.get('text', '')
                image_base64 = message_data.get('image', None)
                
                # For image messages, don't send filename as text (only send the image)
                # For regular messages, send the text
                text_to_send = text if message_data.get('type') == 'message' else None
                
                # Only process if there's actual content (not empty)
                if text_to_send or image_base64:
                    # Call API asynchronously (don't block message broadcast)
                    asyncio.create_task(process_and_save_message(text_to_send, image_base64, message_data['timestamp']))
            
            # Broadcast message to all clients
            await manager.broadcast(message_data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def process_and_save_message(text: str, image_base64: Optional[str], timestamp: str):
    """
    Processes a message using local extractor (and OCR if image) and saves the result to Excel.
    Flow: Image → OCR API → Extract text → Local Extractor → Excel
    Runs silently in background - only shows final success/error notification.
    """
    try:
        final_text = None
        ocr_status = "skipped"
        
        # Step 1: If image is provided, call OCR API first
        if image_base64:
            print("📷 Image detected, calling OCR API...")
            ocr_text = await extract_text_from_image(image_base64)
            if ocr_text and ocr_text.strip():
                final_text = ocr_text.strip()
                ocr_status = "success"
                print(f"✓ OCR successful, extracted {len(final_text)} characters")
            else:
                ocr_status = "failed"
                print("✗ OCR failed or returned empty text")
        
        # Step 2: If we have text (from message or OCR), use it
        # If image OCR failed but we have original text, use that as fallback
        if not final_text and text:
            final_text = text.strip()
            print(f"Using provided text ({len(final_text)} characters)")
        
        # Step 3: Process text using local extractor
        if not final_text or not final_text.strip():
            error_notification = {
                "type": "notification",
                "text": "✗ No text to process. OCR failed and no text provided.",
                "status": "error",
                "timestamp": datetime.now().strftime('%H:%M')
            }
            await manager.broadcast(error_notification)
            print("✗ No text available for processing")
            return
        
        print(f"🔍 Processing text with local extractor ({len(final_text)} characters)...")
        # Use local extractor on the OCR text or provided text
        result = await process_text_locally(final_text)
        
        if result.get('status') == 'success':
            extracted_data = result.get('extracted_data', {})
            
            # Create a filesystem-safe timestamp
            safe_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save to Excel
            filepath = save_to_excel(extracted_data, safe_timestamp)
            
            # Log success to console
            print(f"✓ Successfully processed message and saved to: {filepath}")
            if ocr_status == "success":
                print(f"  (Processed via: Image → OCR API → Local Extractor)")
            else:
                print(f"  (Processed via: Text → Local Extractor)")
            
            # Only show final success notification to sender
            success_msg = f"✓ Data extracted and saved to Desktop: {os.path.basename(filepath)}"
            if ocr_status == "success":
                success_msg += " (from image)"
            
            notification = {
                "type": "notification",
                "text": success_msg,
                "status": "success",
                "timestamp": datetime.now().strftime('%H:%M'),
                "filepath": filepath
            }
            await manager.broadcast(notification)
        else:
            error_msg = result.get('message', 'Unknown error')
            print(f"✗ Extraction failed: {error_msg}")
            
            error_notification = {
                "type": "notification",
                "text": f"✗ Extraction failed: {error_msg}",
                "status": "error",
                "timestamp": datetime.now().strftime('%H:%M')
            }
            await manager.broadcast(error_notification)
            
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error processing message: {error_msg}")
        
        error_notification = {
            "type": "notification",
            "text": f"✗ Error: {error_msg}",
            "status": "error",
            "timestamp": datetime.now().strftime('%H:%M')
        }
        await manager.broadcast(error_notification)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)

