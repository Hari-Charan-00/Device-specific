import requests
import json
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BaseUrl = "https://netenrich.opsramp.com/"
OpsRampSecret = 'ZqbbkUPdVCTp95M3Gvc7tYVhh8fDuRCzfc7M8TEKaCHsXugUPaDV2NKZ7RDXqxyM'
OpsRampKey = 'jhNBET5pzS5pH9CcTEyVnHnNrTmnM2U9'



def delete_unmanaged_devices(data,count):
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
        auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
        api_endpoint = f'https://netenrich.opsramp.com/api/v2/tenants/{data["clientId"]}/resources/{data["resourceId"]}'

        try:
            response = requests.delete(api_endpoint, headers=auth_header)
            response.raise_for_status()
            
            if response.status_code == 200:
                print(f"\n{count}.Device deleted successfully, ID: {data['resourceId']}")
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

# Assuming 'clientId' and 'resourceId' are column names in your Excel file
input_file = 'C:\\Users\\hari.boddu\\Downloads\\Unmanaged_Deletions.xlsx'
df = pd.read_excel(input_file)

count =1
for index, row in df.iterrows():
    delete_unmanaged_devices(row,count)
    count+=1
