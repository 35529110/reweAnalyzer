# reweAnalyzer
Analysiert die Rewe e-bons. Die bekommen sie von meinem Email provider (Proton). Geht bestimmt auch mit anderen IMAP Servern. Ich versuche alles modular zu halten.

## What it does

- Connects to your email account via IMAP
- Lists all available folders
- Finds the REWE folder automatically
- Downloads all PDF receipts from REWE emails
- Saves them to the `receipts/` directory

## Setup

### 1. Install Proton Bridge (for ProtonMail users)

Download and install from: https://proton.me/mail/bridge

Start the bridge:
```bash
protonmail-bridge
```

Get your IMAP credentials from: Bridge app → Mailbox details → IMAP → Password

### 2. Configure credentials

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and fill in your IMAP credentials:

**For ProtonMail:**
```bash
IMAP_USERNAME=your@protonmail.com
IMAP_PASSWORD=your-bridge-password
IMAP_SERVER=127.0.0.1
IMAP_PORT=1143
```

**For Gmail:**
```bash
IMAP_USERNAME=your@gmail.com
IMAP_PASSWORD=your-app-password
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
```

### 3. Run the program

**Using the launch script (recommended):**
```bash
./run.sh
```

The script will:
- Check if `.env` exists
- Load credentials from `.env`
- Verify Proton Bridge is running (if using ProtonMail)
- Run the analyzer

**Or run directly:**
```bash
python main.py
```

**Or using environment variables:**
```bash
export IMAP_USERNAME="your@email.com"
export IMAP_PASSWORD="your-password"
export IMAP_SERVER="127.0.0.1"
export IMAP_PORT="1143"
python main.py
```

## Output

PDF receipts are saved to the `receipts/` directory with filenames like:
```
receipts/12345_Rechnung_REWE.pdf
receipts/12346_Beleg_2025-11-29.pdf
```

## Security Note

The `.env` file contains your personal credentials and is automatically ignored by git. Never commit this file to version control.

For detailed IMAP setup instructions for different providers, see [SETUP.md](SETUP.md).
