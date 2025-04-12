import requests
import json
import pandas as pd
import urllib3

# Suppress SSL warnings for non-verified requests (use only in development!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================== CONFIGURATION ==========================
BaseUrl = "https://your-opsramp-url.com/"  # Replace with your OpsRamp URL
OpsRampSecret = 'YOUR_OPSRAMP_CLIENT_SECRET'  # Replace with your Client Secret
OpsRampKey = 'YOUR_OPSRAMP_CLIENT_ID'         # Replace with your Client ID
input_file = 'C:\\path\\to\\your\\Unmanaged_Deletions.xlsx'  # Update with your Excel file path
# ===================================================================

def delete_unmanaged_devices(data, count):
    token_url = BaseUrl + "auth/oauth/token"
    auth_data = {
        'client_secret': OpsRampSecret,
        'grant_type': 'client_credentials',
        'client_id': OpsRampKey
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    token_response = requests.post(token_url, data=auth_data, headers=headers, verify=False)

    if token_response.status_code == 200:
        access_token = token_response.json().get('access_token')
        auth_header = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        api_endpoint = f'{BaseUrl}api/v2/tenants/{data["clientId"]}/resources/{data["resourceId"]}'

        try:
            response = requests.delete(api_endpoint, headers=auth_header)
            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"\n{count}. Device deleted successfully, ID: {data['resourceId']}")
            else:
                try:
                    error_response = response.json()
                    if "HTTPError: 500" in error_response:
                        print("Resource already deleted")
                    else:
                        print("\nDeletion Unsuccessful, Error message:", error_response)
                except json.JSONDecodeError:
                    print("\nDeletion Unsuccessful, Error message:", response.text)

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")

    else:
        print("\nFailed to obtain access token. Error message:", token_response.text)

# Read the Excel file
df = pd.read_excel(input_file)

# Loop through each device and delete
for count, (_, row) in enumerate(df.iterrows(), start=1):
    delete_unmanaged_devices(row, count)
