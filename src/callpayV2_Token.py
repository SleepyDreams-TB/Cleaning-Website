import time
import hashlib

from dotenv import load_dotenv
import os
load_dotenv()

# === Global configuration ===
SALT = os.getenv("SALT")
ORG_ID = os.getenv("ORG_ID")    

def generate_callpay_token():
    """
    Generates the Callpay auth token, current timestamp, and returns
    them along with org_id as a dictionary.
    """
    current_timestamp = str(int(time.time()))  # current Unix timestamp

    # Concatenate as "salt_orgid_timestamp"
    input_string = f"{SALT}_{ORG_ID}_{current_timestamp}"

    # SHA256 hash
    hash_object = hashlib.sha256(input_string.encode())
    token = hash_object.hexdigest()

    return {
        "Token": token,
        "org_id": ORG_ID,
        "timestamp": current_timestamp
    }

# Example usage
if __name__ == "__main__":
    creds = generate_callpay_token()
    print("Generated Callpay credentials:", creds)
