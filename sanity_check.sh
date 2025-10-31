#!/bin/bash

# MeetingInsight Sanity Check Script
# Verifies all dependencies and configurations

echo ""
echo "🔍 MeetingInsight Sanity Check"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    if python -c "import $1" &> /dev/null; then
        VERSION=$(python -c "import $1; print(getattr($1, '__version__', 'unknown'))" 2>/dev/null)
        echo -e "${GREEN}✓${NC} $1 ${BLUE}($VERSION)${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Header
echo -e "${BLUE}System Information:${NC}"
echo "  OS: $(uname -s)"
echo "  Architecture: $(uname -m)"
echo ""

# Check Python
echo -e "${BLUE}Checking Python...${NC}"
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
    
    # Check Python version
    PYTHON_MAJOR=$(python -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        echo -e "${GREEN}✓${NC} Python version is compatible (3.8+)"
    else
        echo -e "${RED}✗${NC} Python 3.8+ required, found $PYTHON_MAJOR.$PYTHON_MINOR"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${RED}✗${NC} Python not found"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Check ffmpeg
echo -e "${BLUE}Checking ffmpeg...${NC}"
if check_command ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1)
    echo "  Version: $FFMPEG_VERSION"
else
    echo -e "${YELLOW}  Install: ${NC}"
    echo "    macOS:   brew install ffmpeg"
    echo "    Ubuntu:  sudo apt-get install ffmpeg"
    echo "    Windows: Download from https://ffmpeg.org"
fi
echo ""

# Check Node.js (for bot)
echo -e "${BLUE}Checking Node.js (for bot)...${NC}"
if check_command node; then
    NODE_VERSION=$(node --version)
    echo "  Version: $NODE_VERSION"
    
    if check_command npm; then
        NPM_VERSION=$(npm --version)
        echo "  npm Version: $NPM_VERSION"
    fi
else
    echo -e "${YELLOW}  Optional: Only needed for bot automation${NC}"
fi
echo ""

# Check Python packages
echo -e "${BLUE}Checking Python packages...${NC}"
check_python_package streamlit
check_python_package torch
check_python_package transformers
check_python_package faster_whisper
check_python_package reportlab
check_python_package bcrypt
echo ""

# Check optional packages
echo -e "${BLUE}Checking optional packages...${NC}"
if check_python_package pyannote; then
    echo -e "${GREEN}  ✓${NC} Speaker diarization available"
else
    echo -e "${YELLOW}  ⚠ pyannote not found. Fallback diarization will be used.${NC}"
fi

if python -c "import google.auth" &> /dev/null; then
    echo -e "${GREEN}✓${NC} google-auth (Google API integration available)"
else
    echo -e "${YELLOW}⚠${NC} google-auth not found (Google integrations disabled)"
fi
echo ""

# Check directories
echo -e "${BLUE}Checking directory structure...${NC}"
DIRS=("data" "tokens" "logs" "modules" "bot" "scripts")
for DIR in "${DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        echo -e "${GREEN}✓${NC} $DIR/ exists"
    else
        echo -e "${YELLOW}⚠${NC} $DIR/ not found (creating...)"
        mkdir -p "$DIR"
        echo -e "${GREEN}  ✓${NC} Created $DIR/"
    fi
done
echo ""

# Check configuration files
echo -e "${BLUE}Checking configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Check critical vars
    if grep -q "SMTP_USER=" .env 2>/dev/null; then
        echo -e "${GREEN}  ✓${NC} SMTP configured"
    else
        echo -e "${YELLOW}  ⚠${NC} SMTP not configured (email disabled)"
    fi
    
    if grep -q "HF_TOKEN=" .env 2>/dev/null; then
        echo -e "${GREEN}  ✓${NC} HuggingFace token set"
    else
        echo -e "${YELLOW}  ⚠${NC} HuggingFace token not set (using fallback diarization)"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo -e "${YELLOW}  Copy .env.example to .env and configure${NC}"
fi
echo ""

# Check database
echo -e "${BLUE}Checking database...${NC}"
if [ -f "data/meetings.db" ]; then
    echo -e "${GREEN}✓${NC} Database exists"
    
    # Check database tables
    TABLES=$(sqlite3 data/meetings.db ".tables" 2>/dev/null)
    if echo "$TABLES" | grep -q "meetings"; then
        echo -e "${GREEN}  ✓${NC} Database tables initialized"
    else
        echo -e "${YELLOW}  ⚠${NC} Database tables missing"
        echo -e "${YELLOW}  Run: python scripts/init_database.py${NC}"
    fi
else
    echo -e "${YELLOW}⚠${NC} Database not initialized"
    echo -e "${YELLOW}  Run: python scripts/init_database.py${NC}"
fi
echo ""

# Check OAuth tokens
echo -e "${BLUE}Checking OAuth tokens...${NC}"
if [ -d "tokens" ] && [ "$(ls -A tokens/*.json 2>/dev/null)" ]; then
    TOKEN_COUNT=$(ls -1 tokens/*.json 2>/dev/null | wc -l)
    echo -e "${GREEN}✓${NC} OAuth tokens found ($TOKEN_COUNT files)"
else
    echo -e "${YELLOW}⚠${NC} OAuth tokens not configured (Google integrations disabled)"
    echo -e "${YELLOW}  Run: python scripts/generate_google_tokens.py${NC}"
fi
echo ""

# Test Whisper model
echo -e "${BLUE}Testing Whisper model...${NC}"
if python -c "from faster_whisper import WhisperModel; print('OK')" &> /dev/null; then
    echo -e "${GREEN}✓${NC} Whisper model accessible"
    echo -e "${YELLOW}  Note: Model will download on first use (~140MB)${NC}"
else
    echo -e "${RED}✗${NC} Whisper model test failed"
    echo -e "${YELLOW}  Check faster-whisper installation${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Summary
echo "======================================================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo -e "${BLUE}You're ready to run MeetingInsight:${NC}"
    echo -e "  ${GREEN}streamlit run app.py${NC}"
    echo ""
    echo "Additional setup (optional):"
    echo "  • Configure SMTP for email: Edit .env"
    echo "  • Set up Google OAuth: python scripts/generate_google_tokens.py"
    echo "  • Install bot dependencies: cd bot && npm install"
    echo ""
    echo "For complete setup guide, see: MANUAL_SETUP_CHECKLIST.md"
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before running the application."
    echo "See MANUAL_SETUP_CHECKLIST.md for detailed setup instructions."
    echo ""
    exit 1
fi
echo ""