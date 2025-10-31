# MeetingInsight Bot

Automated meeting bot using Puppeteer to join Google Meet/Zoom meetings and capture audio, participants, and captions.

## Features

- ✅ Auto-join Google Meet/Zoom meetings
- 👥 Capture participant list with exact display names
- 🎙️ Record audio stream
- 💬 Monitor live captions
- 📝 Export data for transcription pipeline
- 🤖 Headless or visible browser mode

## Prerequisites

### System Requirements

- Node.js 16+ and npm
- Chrome/Chromium browser
- ffmpeg (for audio capture)
- System audio routing (platform-specific)

### Install Dependencies

```bash
cd bot/
npm install
```

## System Audio Setup

### macOS

```bash
# Install BlackHole (virtual audio device)
brew install blackhole-2ch

# Configure Audio MIDI Setup:
# 1. Open "Audio MIDI Setup" app
# 2. Click "+" and create "Multi-Output Device"
# 3. Select both "BlackHole 2ch" and your speakers
# 4. Set as system output in System Preferences > Sound
```

### Linux (Ubuntu/Debian)

```bash
# PulseAudio is usually pre-installed
pulseaudio --version

# If not installed:
sudo apt-get install pulseaudio ffmpeg

# Configure default audio source
pactl list sources
```

### Windows

```bash
# Download and install Virtual Audio Cable
# https://vb-audio.com/Cable/

# Or use Voicemeeter:
# https://vb-audio.com/Voicemeeter/

# Set Virtual Audio Cable as default playback device
```

## Configuration

### Environment Variables

Create `.env` file in `bot/` directory:

```bash
# Meeting Configuration
MEET_URL=https://meet.google.com/xxx-yyyy-zzz
BOT_NAME="MeetingInsight Recording Bot"

# Browser Configuration
CHROME_PATH=/usr/bin/google-chrome  # Optional
HEADLESS=false  # true for headless mode

# Feature Flags
CAPTURE_AUDIO=true
CAPTURE_PARTICIPANTS=true
CAPTURE_CAPTIONS=true
```

## Usage

### Basic Usage

```bash
# Run with URL argument
node meet_bot.js "https://meet.google.com/abc-defg-hij"

# Or use environment variable
export MEET_URL="https://meet.google.com/abc-defg-hij"
node meet_bot.js

# Or use npm script
npm start
```

### Advanced Usage

```bash
# Headless mode (no browser window)
HEADLESS=true node meet_bot.js <meeting-url>

# Custom bot name
BOT_NAME="Company Recorder" node meet_bot.js <meeting-url>

# Custom Chrome path
CHROME_PATH=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome node meet_bot.js <meeting-url>
```

## Output Files

Bot generates files in `../data/bot_captures/`:

```
{meeting_id}_participants.json  - List of participant names
{meeting_id}_audio.mp3          - Audio recording
{meeting_id}_captions.json      - Live captions (line-delimited JSON)
```

Example `participants.json`:
```json
[
  "Alice Smith",
  "Bob Jones",
  "MeetingInsight Recording Bot"
]
```

Example `captions.json`:
```json
{"speaker":"Alice Smith","text":"Hello everyone","timestamp":"2025-01-30T14:30:15.123Z"}
{"speaker":"Bob Jones","text":"Hi Alice, how are you?","timestamp":"2025-01-30T14:30:18.456Z"}
```

## Important: Privacy & Consent

### Legal Requirements

⚠️ **CRITICAL:** Recording meetings without consent is illegal in many jurisdictions!

**Before using the bot:**

1. ✅ **Inform ALL participants** that the meeting will be recorded
2. ✅ **Obtain explicit consent** (verbal or written)
3. ✅ **Display clear indicators** (bot name shows "Recording")
4. ✅ **Provide opt-out mechanism** (allow participants to object)
5. ✅ **Comply with local laws** (research one-party vs two-party consent)

### Consent Best Practices

**Meeting Invite Notice:**
```
📹 RECORDING NOTICE

This meeting will be recorded and transcribed for documentation purposes.

Recording includes:
- Audio capture
- Speaker identification  
- AI transcription

The recording will be:
- Stored securely
- Accessible only to [specify who]
- Retained for [specify duration]
- Deleted upon request

By joining this meeting, you consent to being recorded.
To object, contact the host before the meeting.
```

**Verbal Announcement:**
```
"Before we begin, please note this meeting is being recorded and transcribed 
for documentation purposes. If anyone objects, please speak now."
```

### Compliance Checklist

- [ ] Meeting invite includes recording notice
- [ ] Verbal announcement at meeting start
- [ ] Bot name clearly indicates recording
- [ ] Consent documented in meeting notes
- [ ] Data retention policy defined
- [ ] Deletion process available
- [ ] Local laws researched and followed

## Troubleshooting

### Bot Can't Join Meeting

**Issue:** Bot fails to find join button

**Solutions:**
1. Google Meet UI has changed - update selectors in code
2. Run in non-headless mode to debug: `HEADLESS=false`
3. Check Chrome version compatibility
4. Ensure meeting link is valid

### No Audio Captured

**Issue:** Audio file is empty or not created

**Solutions:**
1. Verify ffmpeg installation: `ffmpeg -version`
2. Check system audio routing
3. Test audio device: 
   ```bash
   # macOS
   ffmpeg -f avfoundation -list_devices true -i ""
   
   # Linux
   pactl list sources
   
   # Windows
   ffmpeg -list_devices true -f dshow -i dummy
   ```
4. Ensure audio is playing through virtual device

### Participants Not Captured

**Issue:** `participants.json` is empty

**Solutions:**
1. Meeting host may have disabled participant list
2. Update DOM selectors (Google Meet UI changes frequently)
3. Check browser console for errors: run in non-headless mode
4. Wait longer before capturing (add delay)

### Captions Not Working

**Issue:** No captions in output file

**Solutions:**
1. Captions must be manually enabled in Google Meet settings
2. Meeting host may have disabled captions
3. Language not supported for auto-captions
4. Update caption DOM selectors

## Selector Maintenance

Google Meet frequently updates their UI. If bot stops working:

1. **Open Chrome DevTools** on Google Meet
2. **Inspect element** you want to interact with
3. **Find unique selector** (aria-label, data attributes, etc.)
4. **Update in meet_bot.js**

### Common Selectors to Check

```javascript
// Join button (check these)
'button[jsname="Qx7uuf"]'
'button:has-text("Join now")'
'span:has-text("Ask to join")'

// Participants panel
'button[aria-label*="Show everyone"]'
'[data-participant-id]'
'[data-self-name]'

// Captions
'[jsname="tgaKEf"]'
'.VbkSUe'
'[data-caption-text]'
```

## Rate Limiting & Detection

Google may detect and block bots. Best practices:

- ✅ Use reasonable delays between actions
- ✅ Don't run multiple bots simultaneously
- ✅ Rotate user agents
- ✅ Use authenticated Google account (via profile directory)
- ✅ Respect meeting host's wishes
- ✅ Don't abuse the system

## Development

### Debug Mode

```bash
# Run with console logging
DEBUG=* node meet_bot.js <url>

# Keep browser open after bot stops
# (comment out browser.close() in stop())
```

### Custom Modifications

```javascript
// Example: Add custom action after joining
async run() {
    await this.launch();
    await this.joinMeeting();
    
    // Your custom code here
    await this.customAction();
    
    await this.captureParticipants();
    // ...
}
```

## Support

For issues, questions, or contributions:

- 📧 Email: aditya.dev@projectmail.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: See main README.md

## License

MIT License - See LICENSE file in project root

---

**Remember:** Always obtain consent before recording meetings!
