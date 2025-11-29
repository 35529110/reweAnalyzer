# reweAnalyzer
Analysiert die Rewe e-bons. Die bekommen sie von meinem Email provider (Proton). Geht bestimmt auch mit anderen imap/pop servern. Ich versuche alles modular zu halten.

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your email credentials:
   - `SMTP_USERNAME`: Your email address
   - `SMTP_TOKEN`: Your email password or app-specific password
   - `SMTP_SERVER`: Your IMAP server (e.g., `imap.gmail.com`)
   - `SMTP_PORT`: IMAP port (usually `993`)

3. Run the program:
   ```bash
   python main.py
   ```

   Or press F5 in VSCode to run/debug with your configured credentials.

## Security Note

The `.env` file contains your personal credentials and is automatically ignored by git. Never commit this file to version control.
