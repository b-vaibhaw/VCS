/**
 * MeetingInsight Puppeteer Bot for Google Meet
 * 
 * Automatically joins meetings and captures:
 * - Audio stream
 * - Participant list with exact display names
 * - Live captions
 * - Meeting metadata
 * 
 * Usage:
 *   node meet_bot.js <meeting-url>
 * 
 * Environment Variables:
 *   MEET_URL - Meeting URL
 *   BOT_NAME - Display name for bot
 *   CHROME_PATH - Path to Chrome executable (optional)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Configuration
const CONFIG = {
    meetUrl: process.env.MEET_URL || '',
    botName: process.env.BOT_NAME || 'MeetingInsight Bot',
    captureAudio: true,
    captureParticipants: true,
    captureCaptions: true,
    outputDir: path.join(__dirname, '../data/bot_captures'),
    chromePath: process.env.CHROME_PATH || null,
    headless: process.env.HEADLESS === 'true',
};

// Ensure output directory exists
if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
}

/**
 * Google Meet Bot Class
 */
class GoogleMeetBot {
    constructor(meetUrl) {
        this.meetUrl = meetUrl;
        this.browser = null;
        this.page = null;
        this.participants = [];
        this.captions = [];
        this.audioProcess = null;
        this.meetingId = `meet_${Date.now()}`;
    }

    /**
     * Launch browser with required flags
     */
    async launch() {
        console.log('🚀 Launching browser...');
        
        const launchOptions = {
            headless: CONFIG.headless,
            executablePath: CONFIG.chromePath,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--autoplay-policy=no-user-gesture-required',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ],
        };

        this.browser = await puppeteer.launch(launchOptions);
        this.page = await this.browser.newPage();
        
        // Set viewport
        await this.page.setViewport({ width: 1920, height: 1080 });
        
        // Set user agent to avoid detection
        await this.page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );
        
        console.log(`📍 Navigating to: ${this.meetUrl}`);
        await this.page.goto(this.meetUrl, { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        console.log('✅ Browser launched successfully');
    }

    /**
     * Join Google Meet meeting
     */
    async joinMeeting() {
        console.log('🎯 Joining meeting...');
        
        try {
            // Wait for join page to load
            await this.page.waitForSelector('input[aria-label*="name" i], input[placeholder*="name" i]', { 
                timeout: 10000 
            });
            
            console.log('📝 Setting bot name...');
            
            // Set bot name
            const nameInput = await this.page.$('input[aria-label*="name" i], input[placeholder*="name" i]');
            if (nameInput) {
                await nameInput.click({ clickCount: 3 });
                await nameInput.type(CONFIG.botName, { delay: 50 });
                console.log(`✅ Bot name set to: ${CONFIG.botName}`);
            }
            
            // Disable camera and microphone
            console.log('🎥 Disabling camera and microphone...');
            
            // Try multiple selectors for camera button
            const cameraSelectors = [
                'div[data-is-muted="false"][aria-label*="camera" i]',
                'button[aria-label*="turn off camera" i]',
                'div[jsname][aria-label*="camera" i]'
            ];
            
            for (const selector of cameraSelectors) {
                try {
                    const cameraBtn = await this.page.$(selector);
                    if (cameraBtn) {
                        await cameraBtn.click();
                        console.log('✅ Camera disabled');
                        break;
                    }
                } catch (e) {
                    // Try next selector
                }
            }
            
            // Try multiple selectors for microphone button
            const micSelectors = [
                'div[data-is-muted="false"][aria-label*="microphone" i]',
                'button[aria-label*="turn off microphone" i]',
                'div[jsname][aria-label*="microphone" i]'
            ];
            
            for (const selector of micSelectors) {
                try {
                    const micBtn = await this.page.$(selector);
                    if (micBtn) {
                        await micBtn.click();
                        console.log('✅ Microphone disabled');
                        break;
                    }
                } catch (e) {
                    // Try next selector
                }
            }
            
            // Click join button
            console.log('🚪 Clicking join button...');
            
            await this.page.waitForTimeout(2000);
            
            const joinSelectors = [
                'button[jsname="Qx7uuf"]', // Google Meet specific
                'button:has-text("Join now")',
                'button:has-text("Ask to join")',
                'span:has-text("Join now")',
                'span:has-text("Ask to join")'
            ];
            
            let joined = false;
            for (const selector of joinSelectors) {
                try {
                    await this.page.click(selector);
                    joined = true;
                    console.log('✅ Join button clicked');
                    break;
                } catch (e) {
                    // Try next selector
                }
            }
            
            if (!joined) {
                console.warn('⚠️  Could not find join button, trying alternative method...');
                // Press Enter key as fallback
                await this.page.keyboard.press('Enter');
            }
            
            // Wait for meeting to start
            await this.page.waitForTimeout(5000);
            
            console.log('✅ Successfully joined meeting!');
            
        } catch (error) {
            console.error('❌ Error joining meeting:', error.message);
            throw error;
        }
    }

    /**
     * Enable captions for live transcription
     */
    async enableCaptions() {
        if (!CONFIG.captureCaptions) return;
        
        console.log('💬 Enabling captions...');
        
        try {
            // Click more options button (three dots)
            const moreOptionsSelectors = [
                'button[aria-label*="More options" i]',
                'button[aria-label*="More actions" i]',
                'div[aria-label*="More options" i]'
            ];
            
            let optionsClicked = false;
            for (const selector of moreOptionsSelectors) {
                try {
                    await this.page.click(selector);
                    optionsClicked = true;
                    console.log('✅ Opened more options menu');
                    break;
                } catch (e) {
                    // Try next selector
                }
            }
            
            if (!optionsClicked) {
                console.warn('⚠️  Could not open more options menu');
                return;
            }
            
            await this.page.waitForTimeout(1000);
            
            // Click captions button
            const captionSelectors = [
                'div[aria-label*="captions" i]:not([aria-label*="off" i])',
                'span:has-text("Turn on captions")',
                'div[role="menuitem"]:has-text("Captions")'
            ];
            
            for (const selector of captionSelectors) {
                try {
                    await this.page.click(selector);
                    console.log('✅ Captions enabled');
                    return;
                } catch (e) {
                    // Try next selector
                }
            }
            
            console.warn('⚠️  Could not enable captions');
            
        } catch (error) {
            console.error('❌ Error enabling captions:', error.message);
        }
    }

    /**
     * Capture participant list
     */
    async captureParticipants() {
        if (!CONFIG.captureParticipants) return;
        
        console.log('👥 Capturing participant list...');
        
        try {
            // Open participants panel
            const peopleSelectors = [
                'button[aria-label*="Show everyone" i]',
                'button[aria-label*="People" i]',
                'i[data-icon-name="people"]'
            ];
            
            let panelOpened = false;
            for (const selector of peopleSelectors) {
                try {
                    await this.page.click(selector);
                    panelOpened = true;
                    console.log('✅ Opened participants panel');
                    break;
                } catch (e) {
                    // Try next selector
                }
            }
            
            if (!panelOpened) {
                console.warn('⚠️  Could not open participants panel');
                return;
            }
            
            await this.page.waitForTimeout(2000);
            
            // Scrape participant names
            // NOTE: Selectors may change - update as needed
            const participantSelectors = [
                '[data-participant-id]',
                '[data-self-name]',
                '[data-requested-participant-name]',
                'div[role="listitem"]',
                'span[data-self-name]'
            ];
            
            this.participants = [];
            
            for (const selector of participantSelectors) {
                const elements = await this.page.$(selector);
                
                for (const element of elements) {
                    try {
                        const name = await this.page.evaluate(el => {
                            // Try multiple ways to extract name
                            return el.getAttribute('data-self-name') ||
                                   el.getAttribute('data-requested-participant-name') ||
                                   el.textContent ||
                                   el.innerText;
                        }, element);
                        
                        if (name && name.trim()) {
                            const cleanName = name.trim();
                            if (!this.participants.includes(cleanName)) {
                                this.participants.push(cleanName);
                            }
                        }
                    } catch (e) {
                        // Skip this element
                    }
                }
                
                if (this.participants.length > 0) {
                    break; // Found participants with this selector
                }
            }
            
            console.log(`✅ Captured ${this.participants.length} participants:`, this.participants);
            
            // Save to file
            const outputPath = path.join(CONFIG.outputDir, `${this.meetingId}_participants.json`);
            fs.writeFileSync(outputPath, JSON.stringify(this.participants, null, 2));
            console.log(`💾 Saved participants to: ${outputPath}`);
            
        } catch (error) {
            console.error('❌ Error capturing participants:', error.message);
        }
    }

    /**
     * Capture audio stream using ffmpeg
     */
    async captureAudioStream() {
        if (!CONFIG.captureAudio) return;
        
        console.log('🎙️  Starting audio capture...');
        
        const audioFile = path.join(CONFIG.outputDir, `${this.meetingId}_audio.mp3`);
        
        // Platform-specific ffmpeg commands
        let ffmpegCommand;
        
        if (process.platform === 'darwin') {
            // macOS - requires BlackHole or Soundflower
            ffmpegCommand = `ffmpeg -f avfoundation -i ":BlackHole 2ch" -acodec libmp3lame -ar 16000 -ac 1 "${audioFile}"`;
        } else if (process.platform === 'linux') {
            // Linux - uses PulseAudio
            ffmpegCommand = `ffmpeg -f pulse -i default -acodec libmp3lame -ar 16000 -ac 1 "${audioFile}"`;
        } else if (process.platform === 'win32') {
            // Windows - requires Virtual Audio Cable
            ffmpegCommand = `ffmpeg -f dshow -i audio="Virtual Audio Cable" -acodec libmp3lame -ar 16000 -ac 1 "${audioFile}"`;
        } else {
            console.warn('⚠️  Audio capture not supported on this platform');
            return;
        }
        
        console.log('🎵 Recording audio to:', audioFile);
        console.log('Command:', ffmpegCommand);
        
        this.audioProcess = exec(ffmpegCommand, (error, stdout, stderr) => {
            if (error && !error.killed) {
                console.error('❌ Audio capture error:', error.message);
            }
        });
        
        console.log('✅ Audio recording started');
    }

    /**
     * Monitor live captions
     */
    async captureLiveCaptions() {
        if (!CONFIG.captureCaptions) return;
        
        console.log('📝 Monitoring captions...');
        
        const captionsFile = path.join(CONFIG.outputDir, `${this.meetingId}_captions.json`);
        
        // Inject script to monitor DOM for caption elements
        await this.page.evaluateOnNewDocument(() => {
            const capturedCaptions = [];
            
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            // Look for caption text
                            // NOTE: Selectors may change - update as needed
                            const captionSelectors = [
                                '[jsname="tgaKEf"]', // Google Meet caption container
                                '.VbkSUe', // Caption text
                                '[data-caption-text]'
                            ];
                            
                            for (const selector of captionSelectors) {
                                const captionEl = node.matches && node.matches(selector) ? 
                                                  node : 
                                                  node.querySelector && node.querySelector(selector);
                                
                                if (captionEl) {
                                    const speakerEl = captionEl.querySelector('[data-speaker-name]');
                                    const textEl = captionEl.querySelector('[data-caption-text]') || captionEl;
                                    
                                    const speaker = speakerEl ? speakerEl.textContent : 'Unknown';
                                    const text = textEl.textContent || '';
                                    
                                    if (text.trim()) {
                                        const caption = {
                                            speaker: speaker.trim(),
                                            text: text.trim(),
                                            timestamp: new Date().toISOString()
                                        };
                                        
                                        capturedCaptions.push(caption);
                                        
                                        // Send to console (will be captured by page.on('console'))
                                        console.log('CAPTION:', JSON.stringify(caption));
                                    }
                                    break;
                                }
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
        
        // Listen for caption logs
        this.page.on('console', async (msg) => {
            const text = msg.text();
            if (text.startsWith('CAPTION:')) {
                const caption = JSON.parse(text.replace('CAPTION:', ''));
                this.captions.push(caption);
                
                // Append to file
                fs.appendFileSync(
                    captionsFile, 
                    JSON.stringify(caption) + '\n'
                );
                
                console.log(`💬 [${caption.speaker}]: ${caption.text}`);
            }
        });
        
        console.log('✅ Caption monitoring started');
    }

    /**
     * Main bot execution
     */
    async run() {
        try {
            await this.launch();
            await this.joinMeeting();
            await this.enableCaptions();
            await this.captureParticipants();
            
            if (CONFIG.captureAudio) {
                await this.captureAudioStream();
            }
            
            if (CONFIG.captureCaptions) {
                await this.captureLiveCaptions();
            }
            
            console.log('\n✅ Bot is running. Press Ctrl+C to stop.\n');
            
            // Keep bot alive until interrupted
            process.on('SIGINT', async () => {
                console.log('\n⏹️  Stopping bot...');
                await this.stop();
                process.exit(0);
            });
            
            // Keep process alive
            await new Promise(() => {});
            
        } catch (error) {
            console.error('❌ Bot error:', error);
            await this.stop();
            process.exit(1);
        }
    }

    /**
     * Stop bot and cleanup
     */
    async stop() {
        console.log('🛑 Stopping bot...');
        
        // Stop audio recording
        if (this.audioProcess) {
            this.audioProcess.kill('SIGINT');
            console.log('✅ Audio recording stopped');
        }
        
        // Leave meeting
        if (this.page) {
            try {
                const leaveSelectors = [
                    'button[aria-label*="Leave call" i]',
                    'button[aria-label*="Exit" i]',
                    'span:has-text("Leave call")'
                ];
                
                for (const selector of leaveSelectors) {
                    try {
                        await this.page.click(selector);
                        console.log('✅ Left meeting');
                        break;
                    } catch (e) {
                        // Try next selector
                    }
                }
            } catch (error) {
                console.log('⚠️  Could not leave meeting gracefully');
            }
        }
        
        // Close browser
        if (this.browser) {
            await this.browser.close();
            console.log('✅ Browser closed');
        }
        
        // Summary
        console.log('\n📊 Bot Summary:');
        console.log(`   Meeting ID: ${this.meetingId}`);
        console.log(`   Participants: ${this.participants.length}`);
        console.log(`   Captions: ${this.captions.length}`);
        console.log(`   Output: ${CONFIG.outputDir}`);
        console.log('\n✅ Bot stopped successfully\n');
    }
}

// Main execution
if (require.main === module) {
    const meetUrl = process.argv[2] || CONFIG.meetUrl;
    
    if (!meetUrl) {
        console.error('❌ Error: Meeting URL required');
        console.log('\nUsage:');
        console.log('  node meet_bot.js <meeting-url>');
        console.log('\nOr set MEET_URL environment variable:');
        console.log('  export MEET_URL="https://meet.google.com/abc-defg-hij"');
        console.log('  node meet_bot.js');
        process.exit(1);
    }
    
    console.log('\n🎙️  MeetingInsight Bot v1.0.0');
    console.log('================================\n');
    
    const bot = new GoogleMeetBot(meetUrl);
    bot.run();
}

module.exports = GoogleMeetBot;