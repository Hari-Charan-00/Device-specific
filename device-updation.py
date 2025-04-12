import requests
import json
import pandas as pd
import urllib3

# Disable SSL warnings (only do this in non-production environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =================== CONFIGURATION (Replace with actual values) ===================
BaseUrl = "https://your-opsramp-url.com/"  # Replace with your OpsRamp base URL
OpsRampSecret = 'YOUR_OPSRAMP_CLIENT_SECRET'  # Replace with your OpsRamp client secret
OpsRampKey = 'YOUR_OPSRAMP_CLIENT_ID'        # Replace with your OpsRamp client ID
input_file = 'C:\\path\\to\\your\\resource_updation.xlsx'  # Update to your Excel file path
# ===================================================================================

def update_resource(data):
    token_url = BaseUrl + "auth/oauth/token"
    auth_data = {
        'client_secret': OpsRampSecret,
        'grant_type': 'client_credentials',
        'client_id': OpsRampKey
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    token_response = requests.post(token_url, data=auth_data, headers=headers, verify=True)

    if token_response.status_code == 200:
        access_token = token_response.json().get('access_token')
        if access_token:
            auth_header = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            api_endpoint = f'https://your-opsramp-url.com/api/v2/tenants/{data["Client_ID"]}/resources/{data["uuid"]}'  # Ensure URL is correct

            payload = {
                "aliasName": "Test2"  # Modify this payload as needed
            }

            response = requests.post(api_endpoint, headers=auth_header, json=payload, verify=True)

            if response.status_code == 200:
                print("Resource updated successfully!")
            else:
                print(f"Failed to update resource. Status code: {response.status_code}")
                print("Error message:", response.text)
        else:
            print("Access token not found in the response.")
    else:
        print(f"Failed to obtain access token. Status code: {token_response.status_code}")
        print("Error message:", token_response.text)

# Load Excel file with resource data
df = pd.read_excel(input_file)

# Loop through each row and update the corresponding resource
for index, row in df.iterrows():
    update_resource(row)
