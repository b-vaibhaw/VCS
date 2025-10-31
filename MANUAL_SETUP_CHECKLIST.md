# MeetingInsight Manual Setup Checklist

Complete step-by-step guide to fully configure MeetingInsight with all features.

---

## Table of Contents

1. [Python Environment Setup](#1-python-environment-setup)
2. [Install Dependencies](#2-install-dependencies)
3. [Download Whisper Model](#3-download-whisper-model)
4. [Hugging Face Token](#4-hugging-face-token)
5. [Google OAuth Setup](#5-google-oauth-setup)
6. [SMTP Email Configuration](#6-smtp-email-configuration)
7. [Initialize Database](#7-initialize-database)
8. [Test Installation](#8-test-installation)
9. [Optional: ngrok Setup](#9-optional-ngrok-setup)
10. [Optional: Puppeteer Bot](#10-optional-puppeteer-bot)
11. [Run Application](#11-run-application)
12. [Production Deployment](#12-production-deployment)
13. [Security Checklist](#13-security-checklist)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Python Environment Setup

### On Jetson Nano / ARM Devices

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.8+
sudo apt-get install python3.8 python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch CPU-only
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install ffmpeg
sudo apt-get install ffmpeg -y

# Verify
ffmpeg -version
python --version
```

### On Standard Linux/macOS/Windows

```bash
# Create virtual environment
python -m venv venv

# Activate
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install PyTorch CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install ffmpeg
# macOS:
brew install ffmpeg
# Linux:
sudo apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html
```

---

## 2. Install Dependencies

```bash
# Install all Python dependencies
pip install -r requirements.txt

# Verify critical packages
python -c "import streamlit; print('Streamlit OK')"
python -c "import faster_whisper; print('Whisper OK')"
python -c "import torch; print('PyTorch OK')"
```

**If faster-whisper fails on ARM:**
```bash
# Build from source
pip install git+https://github.com/guillaumekln/faster-whisper.git
```

---

## 3. Download Whisper Model

```bash
# Models auto-download on first use
# Pre-download to verify:
python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu')"
```

**Model sizes:**
- `tiny`: 39M params, fastest, lowest accuracy
- `base`: 74M params, **recommended for CPU**
- `small`: 244M params, better accuracy
- `medium`: 769M params, high accuracy (slow on CPU)
- `large-v2`: 1550M params, best accuracy (very slow on CPU)

**Storage locations:**
- Linux: `~/.cache/huggingface/hub/`
- macOS: `~/Library/Caches/huggingface/hub/`
- Windows: `%USERPROFILE%\.cache\huggingface\hub\`

---

## 4. Hugging Face Token

Required for pyannote speaker diarization.

### Steps:

1. **Create account** at https://huggingface.co

2. **Go to Settings → Access Tokens**

3. **Create new token** (Read access sufficient)

4. **Accept model license:**
   - Visit: https://huggingface.co/pyannote/speaker-diarization
   - Click "Agree and access repository"

5. **Add to `.env`:**
```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

6. **Test:**
```bash
python -c "import os; from pyannote.audio import Pipeline; print('pyannote OK')"
```

---

## 5. Google OAuth Setup

### 5.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **"Select a Project"** → **"New Project"**
3. Project name: **"MeetingInsight"**
4. Click **"Create"**

### 5.2 Enable APIs

1. Go to **"APIs & Services"** → **"Library"**
2. Enable these APIs:
   - **Google Drive API**
   - **Google Docs API**
   - **Google Calendar API**

### 5.3 Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. If prompted, configure **OAuth consent screen**:
   - User Type: **External**
   - App name: **"MeetingInsight"**
   - User support email: your email
   - Developer contact: **aditya.dev@projectmail.com**
4. Application type: **"Desktop app"**
5. Name: **"MeetingInsight Desktop"**
6. Click **"Create"**
7. Download JSON as **`credentials.json`**
8. Place in project root directory

### 5.4 Configure OAuth Scopes

1. Go to **OAuth consent screen**
2. Click **"Edit App"**
3. Add scopes:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/documents.readonly`
   - `https://www.googleapis.com/auth/calendar.events.readonly`
4. Add test users (your email)
5. Click **"Save and Continue"**

### 5.5 Generate Tokens

```bash
# Run OAuth flow
python scripts/generate_google_tokens.py

# This will:
# 1. Open browser for Google login
# 2. Request permissions
# 3. Save tokens to tokens/ directory
```

**Output:**
```
tokens/
├── google_tokens.json
├── google_drive_token.json
├── google_docs_token.json
└── google_calendar_token.json
```

---

## 6. SMTP Email Configuration

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication:**
   - Go to: https://myaccount.google.com/security
   - Enable **2-Step Verification**

2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: **Mail**
   - Select device: **Other (Custom name)**
   - Name: **"MeetingInsight"**
   - Click **"Generate"**
   - Copy 16-character password

3. **Add to `.env`:**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-character app password
```

4. **Test:**
```bash
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('SMTP OK')
server.quit()
"
```

### Other SMTP Providers

**Outlook/Hotmail:**
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

**Yahoo:**
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password  # Generate at account.yahoo.com
```

**Custom SMTP:**
```bash
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
```

---

## 7. Initialize Database

```bash
# Create database with default admin account
python scripts/init_database.py

# Output:
# ✅ Database initialized successfully!
# Default Admin Account:
#   Username: admin
#   Password: admin123
```

**Important:** Change default password immediately after first login!

### Create Additional Users

```bash
# Interactive user creation
python scripts/create_admin_user.py

# Follow prompts to create new user
```

---

## 8. Test Installation

```bash
# Run sanity check
chmod +x sanity_check.sh
./sanity_check.sh

# Expected output:
# ✓ All critical checks passed!
```

### Test Workflow

```bash
# Run integration test (if you have test audio)
python tests/test_workflow.py
```

**Create test audio:**
```bash
# Record 10 seconds of test audio
ffmpeg -f avfoundation -i ":0" -t 10 samples/test_meeting.mp3  # macOS
ffmpeg -f pulse -i default -t 10 samples/test_meeting.mp3      # Linux
```

---

## 9. Optional: ngrok Setup

For temporary public links to audio files.

```bash
# 1. Sign up at https://ngrok.com

# 2. Install ngrok
# macOS:
brew install ngrok/ngrok/ngrok
# Linux:
snap install ngrok
# Windows: Download from https://ngrok.com/download

# 3. Get auth token from https://dashboard.ngrok.com/get-started/your-authtoken

# 4. Set auth token
ngrok authtoken YOUR_AUTH_TOKEN

# 5. Add to .env
echo "NGROK_AUTH_TOKEN=YOUR_AUTH_TOKEN" >> .env

# 6. Test
ngrok http 8501
# Should open tunnel to localhost:8501
```

---

## 10. Optional: Puppeteer Bot

For automated meeting capture.

```bash
# 1. Install Node.js 16+
# macOS:
brew install node
# Linux:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
# Windows: Download from https://nodejs.org

# 2. Install bot dependencies
cd bot/
npm install

# 3. Configure bot
cp .env.example .env
# Edit .env with meeting URL and bot name

# 4. Test bot
node meet_bot.js "https://meet.google.com/test-test-test"
```

**System Audio Setup:**

See [bot/README.md](bot/README.md) for platform-specific audio routing setup.

---

## 11. Run Application

```bash
# From project root
streamlit run app.py

# Access at: http://localhost:8501
```

### First Login

1. Username: `admin`
2. Password: `admin123`
3. **Change password immediately:**
   - Go to Settings
   - Update password
   - Save

### Upload First Meeting

1. Go to **"Upload Recording"** tab
2. Enter meeting title: "Test Meeting"
3. Enter participants: "Alice, Bob"
4. Upload test audio file
5. Click **"Process Meeting"**
6. Wait for processing (~2-5 min/hour)
7. Download PDF report

---

## 12. Production Deployment

### Docker Deployment

```bash
# Build image
docker-compose build

# Run container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Systemd Service (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/meetinginsight.service
```

Add:
```ini
[Unit]
Description=MeetingInsight Transcription Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/meetinginsight
Environment="PATH=/path/to/meetinginsight/venv/bin"
ExecStart=/path/to/meetinginsight/venv/bin/streamlit run app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable meetinginsight
sudo systemctl start meetinginsight
sudo systemctl status meetinginsight
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name meetinginsight.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable HTTPS with Let's Encrypt:
```bash
sudo certbot --nginx -d meetinginsight.yourdomain.com
```

---

## 13. Security Checklist

- [ ] Change default admin password
- [ ] Use strong passwords (12+ characters)
- [ ] Enable HTTPS in production
- [ ] Restrict file permissions on tokens/ directory
- [ ] Use SMTP app passwords (not main password)
- [ ] Rotate OAuth tokens periodically (every 6 months)
- [ ] Enable database backups
- [ ] Review audit logs regularly
- [ ] Set up firewall rules
- [ ] Keep dependencies updated
- [ ] Document user access approvals
- [ ] Implement data retention policies

---

## 14. Troubleshooting

### Issue: faster-whisper not found

```bash
pip uninstall faster-whisper
pip install --no-cache-dir faster-whisper

# If still fails (ARM devices):
pip install git+https://github.com/guillaumekln/faster-whisper.git
```

### Issue: pyannote fails

```bash
# Check HF token
echo $HF_TOKEN

# Accept model license
# Visit: https://huggingface.co/pyannote/speaker-diarization

# Reinstall
pip uninstall pyannote.audio
pip install pyannote.audio
```

### Issue: Google OAuth fails

```bash
# Delete old tokens
rm tokens/*.json

# Re-run OAuth flow
python scripts/generate_google_tokens.py

# If credentials.json missing:
# Download from Google Cloud Console → Credentials
```

### Issue: Email not sending

```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('Connection OK')
server.quit()
"

# Verify credentials
# Use App Password for Gmail (not regular password)
```

### Issue: Bot can't join meeting

```bash
# Update Puppeteer
cd bot/
npm update puppeteer

# Run in non-headless mode for debugging
HEADLESS=false node meet_bot.js <url>

# Check Chrome version
google-chrome --version
chromium --version
```

### Issue: Permission denied

```bash
# Fix permissions
chmod +x sanity_check.sh
chmod 600 .env
chmod 700 tokens/
chmod 755 data/
```

### Issue: Port 8501 already in use

```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8502
```

---

## Support

For additional help:

- 📧 Email: aditya.dev@projectmail.com
- 🐛 GitHub Issues: Report bugs
- 💬 GitHub Discussions: Ask questions
- 📖 Documentation: See README.md

---

## Next Steps

1. ✅ Complete this checklist
2. ✅ Test with sample meeting
3. ✅ Configure email notifications
4. ✅ Set up Google OAuth (optional)
5. ✅ Install bot (optional)
6. ✅ Review privacy policy
7. ✅ Obtain user consent
8. ✅ Start transcribing meetings!

---

**Checklist Complete!** 🎉

You're ready to use MeetingInsight. For questions, contact: 1h22ai002@hkbk.edu.in