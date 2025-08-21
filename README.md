# Pykada: A Python Client for the Verkada API
## Introduction to Pykada
Navigating the Verkada Public API directly can present certain complexities. Pykada was developed to serve as a dedicated Python library aimed at simplifying these interactions. The core objective is to provide developers with a Pythonic and intuitive interface, abstracting the lower-level details of direct API calls. This library is designed to enhance developer efficiency when integrating Verkada's physical security solutions into custom applications and workflows.

## About Verkada
Verkada is recognized as a leader in cloud-based physical security. Their mission is centered on protecting people and places while prioritizing privacy. They achieve this through a unified system accessible via their cloud platform, Verkada Command.

Verkada offers a comprehensive suite of integrated product lines:

* Video Security
* Access Control
* Environmental sensors
* Alarms
* Workplace (Guest and Mailroom)
* Intercoms
* Gateways (Cell and WiFi)

Pykada is designed to interface with the APIs governing these systems, enabling programmatic access and management of data within the Verkada ecosystem.

## Important Disclaimer:

Please be aware that Pykada is not an official Verkada product. It is not affiliated with, endorsed by, or supported by Verkada Inc. This library is maintained independently.

For the most accurate and current information regarding the Verkada API, developers should always refer to the official Verkada API documentation at apidocs.verkada.com. Any support requests or issues related to the Verkada platform itself should be directed to Verkada Support.

## Key Features of Pykada
Pykada offers several features designed to streamline the use of the Verkada API:

**Simplified Authentication:** Manages the intricacies of API token generation and management, including the automatic refreshing of short-lived tokens.

**Object-Oriented Interface:** Provides Python objects representing Verkada entities (e.g., Cameras, Doors, Alerts), offering a more intuitive approach compared to handling raw JSON responses.

**Camera Management Capabilities:** Retrieve lists and detailed information for Verkada cameras.

**Alert Analytics:** Access camera alerts, including motion, crowd, person of interest, online/offline status, and tamper events.

**Ingest Analytics** Fetch camera analytics such as occupancy trends and License Plate Recognition (LPR) data.

**Access Control Integration:** List Verkada access control doors and retrieve their details.

**Control Doors:** Programmatically unlock doors (requires specific configuration within Verkada Command).

**Clear Error Handling:** Translates API error responses into descriptive Python exceptions for easier debugging.

The primary value of Pykada lies in the abstraction and ease of use it provides. For example, the automatic handling of short-lived API token refreshing allows developers to concentrate on application logic rather than authentication management.

## Requirements
Python Version: Python 3.8 or higher is required.

External Dependencies: Pykada relies on libraries such as requests for making HTTP API calls. These dependencies are typically installed automatically when Pykada is installed via pip.

**Verkada Account & API Access:**

A valid Verkada organization account is mandatory.

API access must be enabled for the organization within Verkada Command.

An API Key must be generated from the Verkada Command platform; this key serves as the primary credential for API interaction. 

That API key can be handled in Pykada one of two ways. 

1. The client-based API is recommended for handling requests. Each Verkada product line ahs an associated API client, eg. `CamerasClient` or `AccessControlClient`. Simple create a client as an object and provide the API key as a parameter to the constructor. Then simply make calls to the Verkada API through that client, eg.

```
from pykada.cameras import CamerasClient

client = CamerasClient(api_key="YOUR_API_KEY_HERE")
print(client.get_camera_data())
```

If an API key isn't provided, the Client will default to using a key in a .env file in the project root directory, described below. If the client cannot find a valid API key in a `.env` file, then it will raise an exception.

2. The functional API can be called without any client instantiation by placing the API key in a `.env` file in the root directory of the project. The file should contain a line in the format:
```
VERKADA_API_KEY="YOUR_API_KEY_HERE"
```

By calling a request function directly, it will create an associated client using the key in that .env file and make the request directly, eg.

```
from pykada.cameras import get_camera_data

print(client.get_camera_data())
```

The functional API relies on a properly formatted API key in a `.env` file, making it more difficult to troubleshoot. It is recommended only for simple use cases where you are making only a single call.

## Token and Request Manager

If all the function wrappers obfuscate the request process (or just suck the fun out of API development), you can also take advantage of Pykada's `RequestManager`. `RequestManager` takes care of token management in the Verkada API, reusing valid tokens and refreshing them when they become stale. No more juggling token expiration or hitting limits by fetching tokens ever new run. Just instantiate a `RequestManager` object with an API key and run use the `get_token` function directly in your request header, eg.

```
import requests
from pykada.verkada_requests import RequestManager

request_manager = RequestManager(api_key="API_KEY_HERE")
url = "https://api.verkada.com/cameras/v1/devices?page_size=100"

headers = {
    "accept": "application/json",
    "x-verkada-auth": request_manager.get_token()
}

response = requests.get(url, headers=headers)

print(response.text)

```

`RequestManager` also has built in retry, backoff, and timeout handling via overrides for the `request` module that also handle token management automatically, eg.

```
from pykada.verkada_requests import RequestManager

request_manager = RequestManager(timeout_seconds=10, max_retries=3, backoff_factor=0.3, retry_delay_seconds=1,api_key="YOUR_API_KEY_HERE)

url = "https://api.verkada.com/cameras/v1/devices?page_size=100"

headers = {
    "accept": "application/json",
    "x-verkada-auth": request_manager.get_token()
}

response = request_manager.get(url=url, headers=headers)

print(response.text)
```

## Example Usage
This guide demonstrates how to use the library directly to perform some basic API calls without running the testbeds. These examples cover common operations such as retrieving data, creating resources, and updating configurations.

### Prerequisites

Ensure you have a valid API key with permissions scoped to your use case. When using the functional API, ensure you have a `.env` file with a "VERKADA_API_KEY" entry. The library uses the `python-dotenv` package to load these variables.

### Example 1: Retrieve All Cameras
Retrieve a list of all cameras in the system

```
from pykada.cameras import CamerasClient

client = CamerasClient("API_KEY_HERE")

# Fetch all cameras
cameras = client.get_all_cameras()
print("Cameras:", cameras)
```

### Example 2: Create and Delete a POI (Person of Interest)
Create a new POI and then delete it.

```
from pykada.cameras import CamerasClient

client = CamerasClient("API_KEY_HERE")

# Create a new POI
poi = client.create_poi(image_url="example.png", label="Test POI")
print("Created POI:", poi)

# Delete the POI
delete_response = client.delete_poi(person_id=poi["person_id"])
print("Deleted POI:", delete_response)
```

### Example 3: Retrieve Sensor Data
Retrieve temperature and humidity data for a specific sensor.

```
from pykada.sensors import SensorsClient
from enums import SENSOR_FIELD_ENUM
import time

client = SensorsClient("API_KEY_HERE")

sensor_id = "YOUR_SENSOR_ID_HERE"
current_time = int(time.time())

# Fetch sensor data
sensor_data = client.get_all_sensor_data(
    device_id=sensor_id,
    start_time=current_time - 3600,
    end_time=current_time,
    fields=[SENSOR_FIELD_ENUM["TEMPERATURE"], SENSOR_FIELD_ENUM["HUMIDITY"]],
    interval="5m"
)

print("Sensor Data:", sensor_data)
```

### Example 4: Get Camera Alerts
Retrieve all alerts for a specific camera within a time range.

```
import time
from pykada.cameras import CamerasClient

client = CamerasClient("API_KEY_HERE")

current_time = int(time.time())

# Fetch camera alerts
alerts = client.get_all_camera_alerts(
    start_time=current_time - 3600,
    end_time=current_time,
    include_image_url=True
)
print("Camera Alerts:", alerts)
```

### Example 5: Update Cloud Backup Settings
Update and restore cloud backup settings for a camera.
```
from pykada.cameras import CamerasClient

client = CamerasClient("API_KEY_HERE")

camera_id = "YOUR_CAMERA_ID_HERE"

# Get current settings
current_settings = client.get_cloud_backup_settings(camera_id=camera_id)
print("Current Settings:", current_settings)

# Update settings
new_settings = current_settings.copy()
new_settings["enabled"] = not current_settings["enabled"]  # Toggle enabled state
update_response = client.update_cloud_backup_settings(**new_settings)
print("Updated Settings:", update_response)

# Restore original settings
restore_response = client.update_cloud_backup_settings(**current_settings)
print("Restored Settings:", restore_response)
```
