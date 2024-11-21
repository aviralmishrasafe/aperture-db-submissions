import requests

def sync_sharepoint():
    url = "http://127.0.0.1:8000/sharepoint/sync"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            print("Sync successful!")
            print("Response:", response.json())
        else:
            print(f"Failed to sync. Status code: {response.status_code}")
            print("Response:", response.text)
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

# Call the function
sync_sharepoint()