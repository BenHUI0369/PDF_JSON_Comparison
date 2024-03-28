from waitress import serve
# once app.py complete, import app
# from app import app
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Read the configuration values from environment variables
host = os.getenv('HOST', '0.0.0.0')
port = int(os.getenv('PORT', 8099))
url_scheme = os.getenv('URL_SCHEME', 'https')

if __name__ == '__main__':
    serve(app, host=host, port=port, url_scheme=url_scheme)