import requests
import pandas as pd
import urllib3
from collections import Counter

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========================= USER CONFIGURATION =========================
BASE_URL = "https://your-opsramp-url.com/"  # Replace with your OpsRamp base URL
OPS_RAMP_SECRET = 'YOUR_OPSRAMP_CLIENT_SECRET'  # Replace with your Client Secret
OPS_RAMP_KEY = 'YOUR_OPSRAMP_CLIENT_ID'         # Replace with your Client ID
EXCEL_FILE_PATH = "C:\\path\\to\\your\\Duplicates_check.xlsx"  # Update with your Excel file path
# ======================================================================

def read_data(file_path):
    df = pd.read_excel(file_path)
    tenant_id = df['TENANT_ID'][0]  
    return tenant_id

def get_access_token():
    token_url = BASE_URL + "auth/oauth/token"
    auth_data = {
        'client_secret': OPS_RAMP_SECRET,
        'grant_type': 'client_credentials',
        'client_id': OPS_RAMP_KEY
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(token_url, data=auth_data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error generating token: {e}")
        return None

def get_device_details(access_token, tenant_id):
    url = f"{BASE_URL}api/v2/tenants/{tenant_id}/resources/minimal"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching device details: {e}")
        return None

def device_details(device_data, file_path):
    servers = []
    others = []

    if isinstance(device_data, list):
        for resource in device_data:
            resource_name = resource.get('name', '')
            resource_ip = resource.get('ipAddress', '')
            resource_type = resource.get('resourceType', '')

            if resource_type == "Server":
                if resource_name and resource_ip:
                    servers.append((resource_name, resource_ip))
            else:
                if resource_ip:
                    others.append(resource_ip)
        
        server_counts = Counter(servers)
        server_duplicates = [f"{name} ({ip})" for (name, ip), count in server_counts.items() if count > 1]
        
        other_counts = Counter(others)
        other_duplicates = [ip for ip, count in other_counts.items() if count > 1]
        
        print("Duplicate Servers:")
        for dup in server_duplicates:
            print(dup)
        
        print("\nDuplicate Others:")
        for dup in other_duplicates:
            print(dup)
        
        df = pd.read_excel(file_path)

        if 'Duplicate_Servers' not in df.columns:
            df['Duplicate_Servers'] = ''
        if 'Duplicate_Others' not in df.columns:
            df['Duplicate_Others'] = ''
        
        df.loc[df.index[:len(server_duplicates)], 'Duplicate_Servers'] = server_duplicates
        df.loc[df.index[:len(other_duplicates)], 'Duplicate_Others'] = other_duplicates

        df.to_excel(file_path, index=False)
        
        print("Duplicates saved to Excel file.")
    else:
        print("No device data available or incorrect format.")

def main():
    tenant_id = read_data(EXCEL_FILE_PATH)
    access_token = get_access_token()
    
    if access_token:
        device_data = get_device_details(access_token, tenant_id)
        if device_data:
            device_details(device_data, EXCEL_FILE_PATH)
        else:
            print("Failed to retrieve device data.")
    else:
        print("Failed to retrieve access token.")

if __name__ == "__main__":
    main()
