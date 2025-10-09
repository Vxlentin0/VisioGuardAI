# VisioGuardAI

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - HOST: The host to run the server on (default: 0.0.0.0)
   - PORT: The port to run the server on (default: 8000)
   - SSL_KEYFILE: Path to your SSL key file
   - SSL_CERTFILE: Path to your SSL certificate file

## Running the application
1. Ensure all environment variables are set
2. Run `python app/main.py`

Note: For development without SSL, you can omit the SSL_KEYFILE and SSL_CERTFILE variables.