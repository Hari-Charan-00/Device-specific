import requests
import time

US_BASE_URL = "https://netenrich.opsramp.com/"
OPS_RAMP_SECRET = 'c55PPRzMPg3BWp5tXZMwwT8Gzpq6GmUbBwWnAfdhJZjmVHfXB59ZMM5rZY3kA5wf'
OPS_RAMP_KEY = 'cHrCgP3TWVtv3EwMzah3hfjH34eXUHM8'

BaseUrls = {"default": US_BASE_URL}  # add the base url dictionary.

# Function to generate a new access token
def token_generation():
    try:
        token_url = US_BASE_URL + "auth/oauth/token"
        auth_data = {
            'client_secret': OPS_RAMP_SECRET,
            'grant_type': 'client_credentials',
            'client_id': OPS_RAMP_KEY
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        token_response = requests.post(token_url, data=auth_data, headers=headers, verify=True)

        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            if access_token:
                return access_token
            else:
                print("Error: No access token returned in the response.")
                return None
        else:
            print(f"Failed to obtain access token: {token_response.status_code} - {token_response.text}")
            return None
    except Exception as e:
        print("Error during token generation:", str(e))
        return None

# Retry Logic function
def handle_retry(response, retry_count=3):
    """Handles retry logic for 401 and 407 status codes."""
    retry_attempts = 0
    while retry_attempts < retry_count:
        if response.status_code in [401, 407]:
            print(f"Retrying due to status code {response.status_code}...")
            access_token = token_generation()  # Renew token
            if access_token:
                return access_token
        retry_attempts += 1
        time.sleep(2)  # Wait 2 seconds before retrying
    return None  # Return None if retries fail

def fetch_clients(access_token, partner_id, base_url):
    clients = {}  # A dictionary to store client_name as key and client_id as value.
    page = 1

    while True:
        try:
            # Prepare the authorization header
            auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
            client_ids_url = base_url + f"api/v2/tenants/{partner_id}/clients/search?pageNo={page}&pageSize=100"

            # Send the request
            response = requests.get(client_ids_url, headers=auth_header, verify=True)

            # Token renewal logic
            if response.status_code in [401, 407] or "invalid_token" in response.text.lower():
                print("Token invalid or expired. Generating a new token...")
                access_token = handle_retry(response)
                if not access_token:
                    print("Unable to generate new token.")
                    break
                continue

            # If successful response
            elif response.status_code == 200:
                clients_data = response.json()
                results = clients_data.get('results', [])

                for client in results:  # Loop through each client in the 'results' list
                    clientid = client.get("uniqueId", "NA")  # Get 'uniqueId' from each client
                    client_name = client.get("name", "NA")

                    # Skip clients with invalid data (NA values)
                    if clientid == "NA" or client_name == "NA":
                        continue

                    # Store the valid client name and client ID in the dictionary
                    clients[client_name] = clientid

                # Check if there are more pages to fetch
                total_pages = clients_data.get('totalPages', 1)
                if page >= total_pages:
                    break  # Exit when all pages have been processed
                page += 1
            else:
                print(f"Failed to get clients with status code: {response.status_code}")
                break
        except Exception as e:
            print("Error fetching clients:", str(e))
            break

    print(f"Total clients fetched: {len(clients)}")
    return clients


# Function to get NOC Name for a given client
def get_noc_name(access_token, partner_id, client_id, client_name, base_url):
    try:
        auth_header = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        noc_details_url = base_url + f"api/v2/tenants/{partner_id}/clients/{client_id}"
        response = requests.get(noc_details_url, headers=auth_header, verify=True)

        # Handle retry logic
        if response.status_code in [401, 407]:
            access_token = handle_retry(response)
            if not access_token:
                return "N/A"
            response = requests.get(noc_details_url, headers=auth_header, verify=True)

        response.raise_for_status()
        noc_data = response.json()
        noc_details = noc_data.get('nocDetails', {})
        return noc_details.get('name', 'N/A')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NOC details for client {client_name}: {e}")
        return "N/A"
    except Exception as e:
        print(f"Unexpected error fetching NOC details for client {client_name}: {e}")
        return "N/A"

def fetch_devices(access_token, client_id, client_name, partner_id, base_url):
    device_ids = []
    unmanaged_device_names = []  # To store names of unmanaged devices
    device_found = False

    try:
        auth_header = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
        devices_url = f"{base_url}/api/v2/tenants/{client_id}/resources/minimal"
        response = requests.get(devices_url, headers=auth_header, verify=True)

        # Handle retry logic (as before)
        if response.status_code in [401, 407]:
            access_token = handle_retry(response)
            if not access_token:
                return [], False, []
            response = requests.get(devices_url, headers=auth_header, verify=True)

        response.raise_for_status()
        devices_data = response.json()

        if isinstance(devices_data, list):
            for device in devices_data:
                device_id = device.get("id")
                if device_id:
                    device_ids.append(device_id)
                    # Check device details and unmanage if the tag exists
                    unmanaged, device_name = get_device_details(access_token, client_id, client_name, device_id, base_url)
                    if unmanaged:
                        device_found = True
                        unmanaged_device_names.append(device_name)
        else:
            print("Error: Expected a list of devices.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching devices for {client_name}: {e}")
    except Exception as e:
        print("Error fetching device IDs:", str(e))

    return device_ids, device_found, unmanaged_device_names

def get_device_details(access_token, client_id, client_name, device_id, base_url):
    auth_header = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    device_url = base_url + f"api/v2/tenants/{client_id}/resources/{device_id}"
    response = requests.get(device_url, headers=auth_header, verify=True)

    try:
        # Handle retry logic (as before)
        if response.status_code in [401, 407]:
            access_token = handle_retry(response)
            if not access_token:
                return False, None
            response = requests.get(device_url, headers=auth_header, verify=True)

        response.raise_for_status()
        if response.status_code == 200:
            device_data = response.json()
            gnrlinfo = device_data.get("generalInfo")
            device_name = gnrlinfo.get('name', 'No value available') if gnrlinfo else 'No value available'
            tags = device_data.get('tags', [])

            if isinstance(tags, list):
                for tag in tags:
                    tagname = tag.get('name')
                    tagvalue = tag.get('value')
                    if tagname == "Managed By" and tagvalue == "Alert":
                        unmanage_device(access_token, base_url, client_id, device_id)
                        return True, device_name
            return False, device_name
        else:
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching device details for device ID {device_id}: {e}")
        return False, None
    except Exception as e:
        print(f"Unexpected error fetching device details for device ID {device_id}: {e}")
        return False, None

def unmanage_device(access_token, base_url, client_id, device_id):
    
    auth_header = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    device_url = base_url + f"api/v2/tenants/{client_id}/devices/{device_id}/unmanage"
    response = requests.post(device_url, headers=auth_header, verify=True)
    
    if response.status_code == 200:
        pass
    else:
        print ("Error, Unable to unmanage, please retry")
    
def main():
    access_token = token_generation()
    if not access_token:
        print("Failed to generate access token. Exiting.")
        return

    partners = {
                "b5c94cda-23bb-b843-6be3-3f929e37e191": "Tri-Valley"  # Example partner
                }
    
    for partner_id, partner_name in partners.items():
        print(f"\nProcessing Partner: {partner_name}")
        
        clients = {
                   "NXCloudGW_Client2" : "ba9c811a-c993-4e3a-a004-76ded2d931c9",
                   "NXCloudGW_Client1" : "7d3157b2-16bb-478c-8cc5-1561a5051260",
                   }
    
        for client_name, client_id in clients.items():
            noc_name = get_noc_name(access_token, partner_id, client_id, client_name, US_BASE_URL)
            if noc_name in ["SRO1", "SRO2", "Vistara NOC"]:
                print(f"Fetching devices for client: {client_name}")
    
                devices, device_found, unmanaged_device_names = fetch_devices(access_token, client_id, client_name, partner_id, US_BASE_URL)
    
                if not device_found:
                    print(f"No devices found with the 'Managed By: Alert' tag for client: {client_name}")
                else:
                    print(f"Please be advised that for client '{client_name}', the devices identified with the 'Managed By: Alert' tag have been automatically unmanaged. The devices are as follows")
                    for name in unmanaged_device_names:
                        print(f"- {name}")

if __name__ == "__main__":
    main()
