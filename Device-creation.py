import requests
import json
import pandas as pd
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BaseUrl = "https://netenrich.opsramp.com/"
OpsRampSecret = 'c55PPRzMPg3BWp5tXZMwwT8Gzpq6GmUbBwWnAfdhJZjmVHfXB59ZMM5rZY3kA5wf'
OpsRampKey = 'cHrCgP3TWVtv3EwMzah3hfjH34eXUHM8'

def create_resource(data):
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
            auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
            api_endpoint = f'https://netenrich.opsramp.com/api/v2/tenants/{data["Client_ID"]}/resources'

            payload = {
                "hostName": data['hostName'],
                "resourceName": data['resourceName'],
                "resourceType": data['Type'],
                #"managementProfile": data['Mprofile'],
                "make": data['make'],
                "model": data['model'],
                #"serialNumber": data['serial'],
                "os": data['OS'],
        }
            response = requests.post(api_endpoint, headers=auth_header, json=payload, verify=True)

            if response.status_code == 200:
                print("Resource created successfully!")
            else:
                print(f"Failed to create resource. Status code: {response.status_code}")
                print("Error message:", response.text)
        else:
            print("Access token not found in the response.")
    else:
        print(f"Failed to obtain access token. Status code: {token_response.status_code}")
        print("Error message:", token_response.text)

# Read input data from Excel file
input_file = 'C:\\Users\\hari.boddu\\Downloads\\resource_creation.xlsx'  # Update with your file path
df = pd.read_excel(input_file)

# Get the 'Client_ID' from the user as input
client_id = df['Client_ID'].iloc[0]

# Assuming you want to create a resource for the first row in the DataFrame
for index, row in df.iterrows():
    create_resource(row)
    