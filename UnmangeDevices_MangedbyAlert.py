import requests
import time

# ==================== USER CONFIGURATION ====================
US_BASE_URL = "https://your-opsramp-url.com/"  # Replace with your OpsRamp base URL
OPS_RAMP_SECRET = 'YOUR_OPSRAMP_CLIENT_SECRET'  # Replace with your Client Secret
OPS_RAMP_KEY = 'YOUR_OPSRAMP_CLIENT_ID'         # Replace with your Client ID
# ============================================================

BaseUrls = {"default": US_BASE_URL}

# Generate a new access token
def token_generation():
    try:
        token_url = US_BASE_URL + "auth/oauth/token"
        auth_data = {
            'client_secret': OPS_RAMP_SECRET,
            'grant_type': 'client_credentials',
            'client_id': OPS_RAMP_KEY
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(token_url, data=auth_data, headers=headers, verify=True)

        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Failed to obtain token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print("Error during token generation:", str(e))
        return None

# Retry logic for expired/invalid tokens
def handle_retry(response, retry_count=3):
    attempts = 0
    while attempts < retry_count:
        if response.status_code in [401, 407]:
            print(f"Retrying due to status {response.status_code}...")
            token = token_generation()
            if token:
                return token
        attempts += 1
        time.sleep(2)
    return None

# Fetch clients under a partner
def fetch_clients(access_token, partner_id, base_url):
    clients = {}
    page = 1

    while True:
        try:
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
            url = f"{base_url}api/v2/tenants/{partner_id}/clients/search?pageNo={page}&pageSize=100"
            response = requests.get(url, headers=headers, verify=True)

            if response.status_code in [401, 407] or "invalid_token" in response.text.lower():
                access_token = handle_retry(response)
                if not access_token:
                    break
                continue

            elif response.status_code == 200:
                results = response.json().get('results', [])
                for client in results:
                    cid = client.get("uniqueId", "NA")
                    cname = client.get("name", "NA")
                    if cid != "NA" and cname != "NA":
                        clients[cname] = cid
                if page >= response.json().get('totalPages', 1):
                    break
                page += 1
            else:
                print(f"Failed to get clients: {response.status_code}")
                break
        except Exception as e:
            print("Error fetching clients:", str(e))
            break

    print(f"Total clients fetched: {len(clients)}")
    return clients

# Get NOC name for a given client
def get_noc_name(token, partner_id, client_id, client_name, base_url):
    try:
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        url = f"{base_url}api/v2/tenants/{partner_id}/clients/{client_id}"
        response = requests.get(url, headers=headers, verify=True)

        if response.status_code in [401, 407]:
            token = handle_retry(response)
            if not token:
                return "N/A"
            response = requests.get(url, headers=headers, verify=True)

        response.raise_for_status()
        return response.json().get('nocDetails', {}).get('name', 'N/A')
    except Exception as e:
        print(f"Error fetching NOC for {client_name}: {e}")
        return "N/A"

# Fetch and filter devices
def fetch_devices(token, client_id, client_name, partner_id, base_url):
    device_ids = []
    unmanaged_names = []
    found = False

    try:
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        url = f"{base_url}/api/v2/tenants/{client_id}/resources/minimal"
        response = requests.get(url, headers=headers, verify=True)

        if response.status_code in [401, 407]:
            token = handle_retry(response)
            if not token:
                return [], False, []
            response = requests.get(url, headers=headers, verify=True)

        response.raise_for_status()
        devices = response.json()

        if isinstance(devices, list):
            for device in devices:
                did = device.get("id")
                if did:
                    device_ids.append(did)
                    unmanaged, name = get_device_details(token, client_id, client_name, did, base_url)
                    if unmanaged:
                        found = True
                        unmanaged_names.append(name)
        else:
            print("Expected a list of devices.")

    except Exception as e:
        print(f"Error fetching devices for {client_name}: {e}")
    
    return device_ids, found, unmanaged_names

# Inspect individual device
def get_device_details(token, client_id, client_name, device_id, base_url):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f"{base_url}api/v2/tenants/{client_id}/resources/{device_id}"

    try:
        response = requests.get(url, headers=headers, verify=True)

        if response.status_code in [401, 407]:
            token = handle_retry(response)
            if not token:
                return False, None
            response = requests.get(url, headers=headers, verify=True)

        response.raise_for_status()
        data = response.json()
        name = data.get("generalInfo", {}).get("name", "No value available")
        tags = data.get("tags", [])

        for tag in tags:
            if tag.get("name") == "Managed By" and tag.get("value") == "Alert":
                unmanage_device(token, base_url, client_id, device_id)
                return True, name

        return False, name
    except Exception as e:
        print(f"Error fetching device details: {e}")
        return False, None

# Unmanage the device
def unmanage_device(token, base_url, client_id, device_id):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f"{base_url}api/v2/tenants/{client_id}/devices/{device_id}/unmanage"
    response = requests.post(url, headers=headers, verify=True)

    if response.status_code != 200:
        print("Error: Unable to unmanage device. Please retry.")

# Main logic
def main():
    token = token_generation()
    if not token:
        print("Token generation failed. Exiting.")
        return

    # Sample partner and clients (Replace with your actual IDs)
    partners = {
        "YOUR_PARTNER_ID": "Your Partner Name"
    }

    for partner_id, partner_name in partners.items():
        print(f"\nProcessing Partner: {partner_name}")

        clients = {
            "CLIENT_NAME_1": "CLIENT_ID_1",
            "CLIENT_NAME_2": "CLIENT_ID_2",
        }

        for client_name, client_id in clients.items():
            noc = get_noc_name(token, partner_id, client_id, client_name, US_BASE_URL)
            if noc in ["SRO1", "SRO2", "Vistara NOC"]:
                print(f"Fetching devices for client: {client_name}")
                _, found, unmanaged = fetch_devices(token, client_id, client_name, partner_id, US_BASE_URL)

                if not found:
                    print(f"No unmanaged-tagged devices for: {client_name}")
                else:
                    print(f"\nDevices unmanaged for '{client_name}':")
                    for name in unmanaged:
                        print(f"- {name}")

if __name__ == "__main__":
    main()
