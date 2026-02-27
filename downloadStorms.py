import requests

# Configuration
AUTH_URL = "https://fist-noki.iri.columbia.edu/token"
DATA_URL = "https://fist-noki.iri.columbia.edu/download_csv"
# Updated the output filename as requested
OUTPUT_FILE = "NokiEvacuateOutput.csv"

# Credentials
payload = {
    "username": "noki_admin",
    "password": "NokiCol@1754_DESDR"
}

# Parameters for the data download
params = {
    "deployment_name": "Scored storms"
}

def download_noki_data():
    try:
        # 1. Generate the Token
        print("Authenticating...")
        auth_response = requests.post(AUTH_URL, json=payload)
        auth_response.raise_for_status()
        
        # Extract the token
        token = auth_response.json().get('token')
        
        if not token:
            print("Error: Could not find 'token' in response.")
            return

        # 2. Download the CSV
        print(f"Downloading data to {OUTPUT_FILE}...")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        with requests.get(DATA_URL, headers=headers, params=params, stream=True) as r:
            r.raise_for_status()
            with open(OUTPUT_FILE, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        print("Download complete.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    download_noki_data()
