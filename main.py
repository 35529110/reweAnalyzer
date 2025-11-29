import os
import argparse

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
  SMTP_USERNAME    Email account username
  SMTP_TOKEN       Email account password/token
  SMTP_SERVER      SMTP server address (e.g., imap.gmail.com)
  SMTP_PORT        SMTP server port (e.g., 993)

Example:
  export SMTP_USERNAME="your@email.com"
  export SMTP_TOKEN="your-app-password"
  export SMTP_SERVER="imap.gmail.com"
  export SMTP_PORT="993"
  python main.py
        '''
    )

    parser.add_argument('--smtp-username',
                        help='Email username (or set SMTP_USERNAME env var)')
    parser.add_argument('--smtp-token',
                        help='Email password/token (or set SMTP_TOKEN env var)')
    parser.add_argument('--smtp-server',
                        help='SMTP server address (or set SMTP_SERVER env var)')
    parser.add_argument('--smtp-port',
                        help='SMTP server port (or set SMTP_PORT env var)')

    args = parser.parse_args()

    # Priority: command-line args > environment variables
    config = {
        'username': args.smtp_username or os.getenv('SMTP_USERNAME'),
        'token': args.smtp_token or os.getenv('SMTP_TOKEN'),
        'server': args.smtp_server or os.getenv('SMTP_SERVER'),
        'port': args.smtp_port or os.getenv('SMTP_PORT'),
    }

    # Validate that all required credentials are provided
    missing = [key for key, value in config.items() if not value]
    if missing:
        parser.error(f"Missing required credentials: {', '.join(missing)}\n"
                     f"Set them via environment variables or command-line arguments.")

    return config

if __name__ == "__main__":
    config = get_config()

    SMTP_USERNAME = config['username']
    SMTP_TOKEN = config['token']
    SMTP_SERVER = config['server']
    SMTP_PORT = config['port']

    print(f"Configuration loaded successfully")
    print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"Username: {SMTP_USERNAME}")
    # TODO: Connect to email server and scan directories