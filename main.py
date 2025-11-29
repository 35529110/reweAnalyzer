import os
import argparse
import json
import imaplib
import email
from email.header import decode_header

def get_config():
    """
    Get configuration from environment variables or command-line arguments.
    Environment variables are the recommended method for security reasons.
    """
    parser = argparse.ArgumentParser(
        description='REWE Receipt Analyzer - Extract data from REWE digital receipts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Environment Variables (Recommended):
  IMAP_USERNAME    Email account username
  IMAP_PASSWORD    Email account password/token
  IMAP_SERVER      IMAP server address (e.g., imap.gmail.com)
  IMAP_PORT        IMAP server port (default: 993 for SSL)

Examples:

ProtonMail (requires Proton Bridge installed and running):
  export IMAP_USERNAME="your@protonmail.com"
  export IMAP_PASSWORD="bridge-password-from-proton-bridge"
  export IMAP_SERVER="127.0.0.1"
  export IMAP_PORT="1143"
  python main.py

Gmail (requires App Password):
  export IMAP_USERNAME="your@gmail.com"
  export IMAP_PASSWORD="your-app-password"
  export IMAP_SERVER="imap.gmail.com"
  export IMAP_PORT="993"
  python main.py
        '''
    )

    parser.add_argument('--imap-username',
                        help='Email username (or set IMAP_USERNAME env var)')
    parser.add_argument('--imap-password',
                        help='Email password/token (or set IMAP_PASSWORD env var)')
    parser.add_argument('--imap-server',
                        help='IMAP server address (or set IMAP_SERVER env var)')
    parser.add_argument('--imap-port',
                        type=int,
                        help='IMAP server port (default: 993, or set IMAP_PORT env var)')

    args = parser.parse_args()

    # Priority: command-line args > environment variables
    config = {
        'username': args.imap_username or os.getenv('IMAP_USERNAME'),
        'password': args.imap_password or os.getenv('IMAP_PASSWORD'),
        'server': args.imap_server or os.getenv('IMAP_SERVER'),
        'port': args.imap_port if args.imap_port is not None else int(os.getenv('IMAP_PORT', 993)),
    }

    # Validate that all required credentials are provided
    missing = [key for key, value in config.items() if not value]
    if missing:
        parser.error(f"Missing required credentials: {', '.join(missing)}\n"
                     f"Set them via environment variables or command-line arguments.")

    return config

def list_folders(imap):
    """
    List all available IMAP folders.
    """
    print("\nListing all folders...")
    _, folders = imap.list()
    folder_list = []

    for folder in folders:
        # Decode folder name
        folder_str = folder.decode()
        # Extract folder name (format: '(\\HasNoChildren) "/" "FolderName"')
        parts = folder_str.split('"')
        if len(parts) >= 3:
            folder_name = parts[-2]
            folder_list.append(folder_name)
            print(f"  - {folder_name}")

    return folder_list

def download_pdf_attachments(imap, folder_name="REWE", output_dir="receipts"):
    """
    Download PDF attachments from emails in a specific folder.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Select the folder
    print(f"\nSelecting folder: {folder_name}")
    status, messages = imap.select(folder_name)

    if status != 'OK':
        print(f"Error: Could not select folder '{folder_name}'")
        return []

    total_messages = int(messages[0].decode())
    print(f"Total messages in {folder_name}: {total_messages}")

    # Search for all emails in the folder
    _, message_ids = imap.search(None, 'ALL')
    email_ids = message_ids[0].split()

    print(f"Processing {len(email_ids)} emails...")

    downloaded_files = []

    for i, email_id in enumerate(email_ids, 1):
        print(f"\nProcessing email {i}/{len(email_ids)} (ID: {email_id.decode()})...")

        # Fetch the email
        _, msg_data = imap.fetch(email_id, '(RFC822)')

        # Parse the email
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Get email subject
        subject = email_message.get('Subject', 'No Subject')
        if subject:
            subject, encoding = decode_header(subject)[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')

        print(f"  Subject: {subject}")

        # Get email date
        date = email_message.get('Date', 'unknown')

        # Look for attachments
        for part in email_message.walk():
            # Check if this part is an attachment
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()

            if filename:
                # Decode filename if needed
                filename_decoded, encoding = decode_header(filename)[0]
                if isinstance(filename_decoded, bytes):
                    filename_decoded = filename_decoded.decode(encoding if encoding else 'utf-8')

                # Check if it's a PDF
                if filename_decoded.lower().endswith('.pdf'):
                    print(f"  Found PDF: {filename_decoded}")

                    # Generate unique filename (include email ID to avoid duplicates)
                    safe_filename = f"{email_id.decode()}_{filename_decoded}"
                    filepath = os.path.join(output_dir, safe_filename)

                    # Download the attachment
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))

                    downloaded_files.append({
                        'filename': safe_filename,
                        'path': filepath,
                        'subject': subject,
                        'date': date,
                        'email_id': email_id.decode()
                    })

                    print(f"  Downloaded: {filepath}")

    return downloaded_files

def analyze_emails(username, password, server, port):
    """
    Connect to IMAP server, list folders, and download PDFs from REWE folder.
    """
    try:
        # Connect to IMAP server
        print(f"Connecting to {server}:{port}...")

        # Use SSL by default (port 993), non-SSL for port 143 or custom ports like Proton Bridge
        if port == 993:
            imap = imaplib.IMAP4_SSL(server, port)
        else:
            imap = imaplib.IMAP4(server, port)

        # Login
        print(f"Logging in as {username}...")
        imap.login(username, password)
        print("Login successful!")

        # List all folders
        folders = list_folders(imap)

        # Check if REWE folder exists
        rewe_folder = None
        for folder in folders:
            if 'rewe' in folder.lower():
                rewe_folder = folder
                break

        if not rewe_folder:
            print("\nWarning: No folder with 'REWE' in the name found.")
            print("Available folders listed above. Please check your email folders.")
            imap.logout()
            return json.dumps({
                "status": "warning",
                "message": "REWE folder not found",
                "folders": folders
            })

        # Download PDF attachments from REWE folder
        print(f"\nFound REWE folder: {rewe_folder}")
        downloaded = download_pdf_attachments(imap, folder_name=rewe_folder)

        print(f"\n{'='*60}")
        print(f"Summary: Downloaded {len(downloaded)} PDF receipts")
        print(f"{'='*60}")

        for item in downloaded:
            print(f"  - {item['filename']}")

        # Logout
        imap.logout()

        return json.dumps({
            "status": "success",
            "folders": folders,
            "rewe_folder": rewe_folder,
            "downloaded_count": len(downloaded),
            "downloaded_files": downloaded
        }, indent=2)

    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    config = get_config()

    IMAP_USERNAME = config['username']
    IMAP_PASSWORD = config['password']
    IMAP_SERVER = config['server']
    IMAP_PORT = config['port']

    result = analyze_emails(
        username=IMAP_USERNAME,
        password=IMAP_PASSWORD,
        server=IMAP_SERVER,
        port=IMAP_PORT
    )