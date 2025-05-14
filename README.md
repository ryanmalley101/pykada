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

**Control Doors**Programmatically unlock doors (requires specific configuration within Verkada Command).

**Clear Error Handling:** Translates API error responses into descriptive Python exceptions for easier debugging.

The primary value of Pykada lies in the abstraction and ease of use it provides. For example, the automatic handling of short-lived API token refreshing allows developers to concentrate on application logic rather than authentication management.

## Requirements
Python Version: Python 3.8 or higher is required.

External Dependencies: Pykada relies on libraries such as requests for making HTTP API calls. These dependencies are typically installed automatically when Pykada is installed via pip.

**Verkada Account & API Access:**

A valid Verkada organization account is mandatory.

API access must be enabled for the organization within Verkada Command.

An API Key must be generated from the Verkada Command platform; this key serves as the primary credential for API interaction. 

That API key must be placed in a `.env` file in the root directory of the project. The file should contain a line in the format:

```
VERKADA_API_KEY="YOUR_API_KEY_HERE"
```

## Example Usage
This guide demonstrates how to use the library directly to perform some basic API calls without running the testbeds. These examples cover common operations such as retrieving data, creating resources, and updating configurations.

Prerequisites
Ensure your `.env` file has a valid API key "VERKADA_API_KEY". The library uses the `python-dotenv` package to load these variables.

### Example 1: Retrieve All Cameras
Retrieve a list of all cameras in the system

```
from cameras.cameras import get_all_cameras

# Fetch all cameras
cameras = get_all_cameras()
print("Cameras:", cameras)
```

### Example 2: Create and Delete a POI (Person of Interest)
Create a new POI and then delete it.

```
from cameras.cameras import create_poi, delete_poi

# Create a new POI
poi = create_poi(image_url="example.png", label="Test POI")
print("Created POI:", poi)

# Delete the POI
delete_response = delete_poi(person_id=poi["person_id"])
print("Deleted POI:", delete_response)
```

### Example 3: Retrieve Sensor Data
Retrieve temperature and humidity data for a specific sensor.

```
import os
from sensors.sensors import get_all_sensor_data
from helpers import SENSOR_FIELD_ENUM
import time

sensor_id = "YOUR_SENSOR_ID_HERE"
current_time = int(time.time())

# Fetch sensor data
sensor_data = get_all_sensor_data(
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
from cameras.cameras import get_all_camera_alerts
import time

current_time = int(time.time())

# Fetch camera alerts
alerts = get_all_camera_alerts(
    start_time=current_time - 3600,
    end_time=current_time,
    include_image_url=True
)
print("Camera Alerts:", alerts)
```

### Example 5: Update Cloud Backup Settings
Update and restore cloud backup settings for a camera.
```
from cameras.cameras import get_cloud_backup_settings, update_cloud_backup_settings
import os

camera_id = "YOUR_CAMERA_ID_HERE"

# Get current settings
current_settings = get_cloud_backup_settings(camera_id=camera_id)
print("Current Settings:", current_settings)

# Update settings
new_settings = current_settings.copy()
new_settings["enabled"] = not current_settings["enabled"]  # Toggle enabled state
update_response = update_cloud_backup_settings(**new_settings)
print("Updated Settings:", update_response)

# Restore original settings
restore_response = update_cloud_backup_settings(**current_settings)
print("Restored Settings:", restore_response)
```

