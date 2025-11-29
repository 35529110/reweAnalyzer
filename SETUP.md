# Email Setup Guide

This guide explains how to set up IMAP access for different email providers.

## What You Need

The code uses **IMAP** (Internet Message Access Protocol) to **receive** emails. You need to configure these 4 variables:

1. `IMAP_USERNAME` - Your email address
2. `IMAP_PASSWORD` - Your email password or app-specific password
3. `IMAP_SERVER` - The IMAP server address
4. `IMAP_PORT` - The IMAP server port (usually 993 for SSL, or custom for bridges)

---

## ProtonMail Setup

### Step 1: Download and Install Proton Bridge

ProtonMail requires **Proton Bridge** because emails are end-to-end encrypted.

**Download:**
- Linux: https://proton.me/mail/bridge#download
- Install via `.deb` or `.rpm` package, or use the official repository

**Installation (Debian/Ubuntu):**
```bash
# Download the .deb package from the link above, then:
sudo dpkg -i proton-bridge_*.deb
```

**Installation (Fedora/RHEL):**
```bash
# Download the .rpm package from the link above, then:
sudo dnf install proton-bridge-*.rpm
```

### Step 2: Start Proton Bridge

```bash
protonmail-bridge
```

or (recommended) the gui application.
IMAP Credentials can be retrieved even while the mailbox is syncing. 

### Step 3: Configure Proton Bridge

1. Log in with your ProtonMail credentials in the Bridge app
2. Go to Mailbox details
3. Note IMAP Credentials. We dont need SMTP, as we dont send emails. We just read them

### Step 4: Set Environment Variables

```bash
export IMAP_USERNAME="your@protonmail.com"
export IMAP_PASSWORD="the-bridge-password-from-step-3"
export IMAP_SERVER="127.0.0.1"
export IMAP_PORT="1143"
```

### Step 5: Run the Script

```bash
python main.py
```

**Important:** Proton Bridge must be running whenever you use the script!

---

## Gmail Setup

### Step 1: Enable IMAP in Gmail

1. Go to Gmail Settings → See all settings → Forwarding and POP/IMAP
2. Enable IMAP
3. Save changes

### Step 2: Create an App Password

Gmail requires an **App Password** (not your regular password) for security.

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (required for App Passwords)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and your device
5. Click "Generate"
6. Copy the 16-character password (no spaces)

### Step 3: Set Environment Variables

```bash
export IMAP_USERNAME="your@gmail.com"
export IMAP_PASSWORD="your-16-char-app-password"
export IMAP_SERVER="imap.gmail.com"
export IMAP_PORT="993"
```

### Step 4: Run the Script

```bash
python main.py
```

---

## Other Email Providers

### Outlook/Hotmail

```bash
export IMAP_USERNAME="your@outlook.com"
export IMAP_PASSWORD="your-password"
export IMAP_SERVER="outlook.office365.com"
export IMAP_PORT="993"
```

### Yahoo Mail

```bash
export IMAP_USERNAME="your@yahoo.com"
export IMAP_PASSWORD="your-app-password"  # Generate at account.yahoo.com/account/security
export IMAP_SERVER="imap.mail.yahoo.com"
export IMAP_PORT="993"
```

### Custom/Corporate Email

Check with your email provider for IMAP settings. Common patterns:

```bash
export IMAP_USERNAME="your@example.com"
export IMAP_PASSWORD="your-password"
export IMAP_SERVER="imap.example.com"  # or mail.example.com
export IMAP_PORT="993"  # Standard SSL port
```

---

## Alternative: Command-Line Arguments

Instead of environment variables, you can pass credentials as arguments:

```bash
python main.py \
  --imap-username "your@email.com" \
  --imap-password "your-password" \
  --imap-server "imap.gmail.com" \
  --imap-port 993
```

**Warning:** This is less secure as passwords may be visible in command history!

---

## Troubleshooting

### Connection Errors

- **ProtonMail:** Make sure Proton Bridge is running
- **Gmail:** Make sure you're using an App Password, not your regular password
- **Firewall:** Ensure port 993 (or 1143 for Proton) is not blocked

### Login Errors

- Double-check username and password
- For ProtonMail: Use the Bridge password, not your ProtonMail password
- For Gmail: Must use App Password, not regular password

### No Emails Found

- Check that REWE emails are in your INBOX (not spam/trash)
- The search looks for emails with "rewe" in the FROM field

---

## Security Best Practices

1. **Use environment variables** instead of command-line arguments
2. **Never commit credentials** to version control
3. Add `.env` files to `.gitignore`
4. Use **app-specific passwords** when available
5. Revoke app passwords when no longer needed
