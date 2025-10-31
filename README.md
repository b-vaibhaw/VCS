# 🎙️ MeetingInsight

**Free & Open-Source Meeting Transcription Platform**

A complete Fireflies.ai alternative with AI-powered transcription, speaker diarization, summarization, and action item extraction. 100% free, no API costs, runs on CPU.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

---

## ✨ Features

### 🎯 Core Transcription
- **Millisecond-precision timestamps** (HH:MM:SS.mmm format)
- **Exact speaker identification** from meeting platform metadata
- **CPU-optimized transcription** using faster-whisper
- **Speaker diarization** with pyannote.audio + fallback
- **95+ languages supported** via OpenAI Whisper

### 🤖 AI Analysis
- **AI-powered summarization** (BART/T5 models)
- **Automatic action item extraction** with assignee detection
- **Key points & decisions** identification
- **Open questions** tracking
- **Topic extraction** from discussions
- **Time-coded references** to important moments

### 🔗 Platform Integration
- **Google Meet notes** integration (auto-fetch from Docs)
- **Automated meeting bot** (Puppeteer for Google Meet/Zoom)
- **Calendar integration** (fetch participant lists)
- **Exact participant names** from platform metadata

### 💾 Storage & Sharing
- **Flexible storage**: Local / Google Drive / Temporary links
- **Professional PDF reports** with clickable audio links
- **Automatic email delivery** via SMTP
- **Searchable transcripts** with full-text search

### 🔒 Security & Access
- **Developer-controlled access** with approval system
- **Audit logging** for compliance
- **Encrypted token storage**
- **GDPR-compliant** data handling

---

## 🚀 Quick Start

### Prerequisites

```bash
# System Requirements
- Python 3.8+
- ffmpeg
- 4GB+ RAM (8GB+ recommended)
- CPU-only compatible (GPU optional)
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/meetinginsight.git
cd meetinginsight

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install PyTorch CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 5. Install ffmpeg
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org

# 6. Copy environment template
cp .env.example .env

# 7. Initialize database
python scripts/init_database.py

# 8. Run application
streamlit run app.py
```

**Access at:** http://localhost:8501

**Default credentials:**
- Username: `admin`
- Password: `admin123` (⚠️ Change immediately!)

---

## 📖 Usage

### 1. Upload Audio/Video

1. Login to application
2. Navigate to "Upload Recording" tab
3. Enter meeting title and participants
4. Upload audio/video file (MP3, WAV, MP4, WebM, etc.)
5. Click "Process Meeting"

### 2. Review Results

The system automatically:
- ✅ Transcribes audio with word-level timestamps
- ✅ Identifies speakers and assigns real names
- ✅ Generates AI summary and action items
- ✅ Creates professional PDF report
- ✅ Optionally emails participants

### 3. Export & Share

Download:
- 📄 PDF Report (complete meeting documentation)
- 📝 Transcript (JSON with millisecond timestamps)
- 📊 Summary (plain text)
- 🎵 Audio file

---

## 🔧 Configuration

### Storage Options

**Local Storage** (default)
- Files stored in `data/{meeting_id}/`
- Fast and free
- Suitable for single-machine deployments

**Google Drive**
- Automatic upload to your Drive
- Shareable links
- Requires OAuth setup (see checklist)

**Temporary Links (ngrok)**
- Public URLs for audio files
- Auto-expires after 2 hours
- Requires ngrok auth token

### Email Configuration

Edit `.env`:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**For Gmail:** Use App Password, not regular password!

1. Enable 2-Factor Authentication
2. Generate App Password
3. Use in `.env` file

---

## 🤖 Automated Bot

Join meetings automatically and capture:
- 🎙️ Audio stream
- 👥 Participant list with exact display names
- 💬 Live captions
- 📝 Meeting metadata

```bash
cd bot/
npm install

# Configure
export MEET_URL="https://meet.google.com/abc-defg-hij"
export BOT_NAME="MeetingInsight Bot"

# Run
node meet_bot.js
```

**⚠️ Important:** Always obtain consent before recording!

See [bot/README.md](bot/README.md) for detailed setup.

---

## 🏗️ Architecture

```
meetinginsight/
├── app.py                      # Main Streamlit application
├── modules/
│   ├── auth.py                 # Authentication
│   ├── transcriber.py          # Faster-whisper
│   ├── diarizer.py             # Speaker diarization
│   ├── summarizer.py           # AI summarization
│   ├── pdf_email.py            # PDF & email
│   ├── storage.py              # Storage handlers
│   ├── platform_integrations.py# Google/Zoom/Teams APIs
│   └── utils.py                # Utilities
├── bot/
│   ├── meet_bot.js             # Google Meet bot
│   └── package.json            # Node dependencies
├── scripts/
│   ├── init_database.py        # DB initialization
│   ├── create_admin_user.py    # User management
│   └── generate_google_tokens.py# OAuth setup
├── data/                       # Meeting data
├── tokens/                     # OAuth tokens
└── logs/                       # Audit logs
```

---

## 📊 Performance

### Benchmarks (CPU-only, base model)

| Duration | Transcription | Diarization | Summary | Total |
|----------|--------------|-------------|---------|-------|
| 10 min   | ~2 min       | ~1 min      | ~10s    | ~3 min|
| 30 min   | ~6 min       | ~3 min      | ~15s    | ~9 min|
| 60 min   | ~12 min      | ~6 min      | ~20s    | ~18 min|

*On Intel i5 / 8GB RAM / Base Whisper model*

### Optimization Tips

- Use `tiny` or `base` Whisper model for faster processing
- Enable GPU if available: `device="cuda"`
- Increase CPU threads: `cpu_threads=8`
- Use `int8` quantization for lower memory

---

## 🔒 Privacy & Security

### Data Handling

- All processing happens locally (no cloud API calls)
- Audio files stored encrypted (optional)
- Automatic data retention policies
- GDPR deletion requests supported

### Consent Requirements

**CRITICAL:** Always obtain consent before recording!

- ✅ Inform all participants
- ✅ Display bot name clearly
- ✅ Provide opt-out mechanism
- ✅ Delete data upon request

See [PRIVACY.md](PRIVACY.md) for compliance guidelines.

---

## 🐛 Troubleshooting

### Common Issues

**"faster-whisper not found"**
```bash
pip install --force-reinstall faster-whisper
```

**"CUDA out of memory"**
```bash
# Use CPU instead
# In modules/transcriber.py: device="cpu"
```

**"Speaker diarization failed"**
```bash
# Verify HF token
echo $HF_TOKEN

# Accept license at:
# https://huggingface.co/pyannote/speaker-diarization
```

**"Email not sending"**
```bash
# Use Gmail App Password, not regular password
# Enable 2FA first, then generate app password
```

See [MANUAL_SETUP_CHECKLIST.md](MANUAL_SETUP_CHECKLIST.md) for full troubleshooting guide.

---

## 📚 Documentation

- **[MANUAL_SETUP_CHECKLIST.md](MANUAL_SETUP_CHECKLIST.md)** - Complete setup guide
- **[bot/README.md](bot/README.md)** - Bot documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **[PRIVACY.md](PRIVACY.md)** - Privacy & compliance
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🤝 Contributing

We welcome contributions!

### Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests
- 🌍 Add language support
- 🧪 Write tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file.

### Third-Party Licenses

- faster-whisper: MIT License
- pyannote.audio: MIT License
- Transformers (HuggingFace): Apache 2.0
- Streamlit: Apache 2.0
- Puppeteer: Apache 2.0

---

## 🙏 Acknowledgments

- OpenAI Whisper for transcription model
- Pyannote.audio for diarization
- Hugging Face for NLP models
- Streamlit for web framework

---

## 📞 Support

- 📧 Email: aditya.dev@projectmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/meetinginsight/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/meetinginsight/discussions)

---

## 🗺️ Roadmap

### v1.1 (Next Release)
- [ ] Real-time transcription during meetings
- [ ] Multi-speaker audio file support
- [ ] Custom vocabulary for technical terms
- [ ] Slack/Discord notifications
- [ ] Mobile-responsive UI improvements

### v1.2
- [ ] Advanced analytics dashboard
- [ ] Meeting insights & trends
- [ ] Team collaboration features
- [ ] Webhook integrations
- [ ] REST API for third-party apps

### v2.0
- [ ] Self-hosted cloud deployment
- [ ] Multi-tenancy support
- [ ] Enterprise SSO integration
- [ ] Advanced AI features (sentiment analysis)
- [ ] Real-time collaboration

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/meetinginsight&type=Date)](https://star-history.com/#yourusername/meetinginsight&Date)

---

**Made by Aditya and Team**

*Free Forever • Open Source • Privacy First*