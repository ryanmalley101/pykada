# Pykada: A Python Client for the Verkada API

Pykada is a Python library for the [Verkada API](https://apidocs.verkada.com). It handles API tokens, retries, pagination, and input validation, so you can work with cameras, access control, sensors, guests, and events in plain Python.

> **Disclaimer:** Pykada is not an official Verkada product. It is not affiliated with, endorsed by, or supported by Verkada Inc., and is maintained independently. For authoritative API details, see [apidocs.verkada.com](https://apidocs.verkada.com). Direct issues with the Verkada platform itself to Verkada Support.

## What's new in 2.0

Pykada 2.0 targets **Verkada API v2**. It's a breaking release; if you're upgrading from 1.x, read the [migration guide](docs/migration.rst).

- **One timestamp style.** Every time argument takes a timezone-aware `datetime` or an ISO 8601 string. Epoch integers are no longer accepted.
- **One pagination style.** Every paged endpoint has a `get_X(limit=..., cursor=...)` method for one page and a `get_all_X(...)` generator for everything.
- **A unified event feed.** `EventsClient` reads camera, access control, sensor and intercom events from one endpoint, replacing camera alerts and access events.
- **Better errors.** Exceptions carry the API's stable `error_code`, and 400, 409 and 422 responses have their own exception types.
- **New coverage,** including camera sites, PTZ presets, LPR zones, people and smart lists, QR code credentials, access level schedules, and the Guest event, host and approved list APIs.

A few endpoints have no v2 equivalent yet, and pykada still calls their v1 versions for you. See [Endpoints still on v1](#endpoints-still-on-v1).

## Installation

```
pip install pykada
```

Pykada requires Python 3.10 or later.

## Authentication

Generate an API key in Verkada Command with the permissions your integration needs. Pykada exchanges it for short-lived API tokens and refreshes them automatically.

Pass the key to a client:

```python
from pykada import CamerasClient

client = CamerasClient(api_key="YOUR_API_KEY")
```

Or put it in a `.env` file in your project root, and clients created without a key will use it:

```
VERKADA_API_KEY="YOUR_API_KEY"
```

Pykada looks for `.env` in the current working directory and its parents the first time a client needs the key, not at import. Variables already set in your environment win over `.env`, so an exported `VERKADA_API_KEY` is never replaced by a stale file. If you're working from a clone of this repository, copy [`.env.example`](.env.example) to `.env`; it also lists the IDs the live smoke scripts in `pykada/*/testbed/` need.

### Regions

Pykada talks to `api.verkada.com` (US) by default. If your organization is hosted in another region, pass `region` to the client, or set `VERKADA_REGION` in your environment or `.env`:

```python
client = CamerasClient(api_key="YOUR_API_KEY", region="eu")  # "eu", "au" or "oh"
```

Tokens and requests both go to that region's host. For a proxy or other custom host, pass `base_url="https://..."` (or set `VERKADA_BASE_URL`) instead.

## Quick start

Each Verkada product has a client. Create one and call its methods; the client reuses its token and HTTP settings across calls.

```python
from pykada import CamerasClient

client = CamerasClient(api_key="YOUR_API_KEY")

for camera in client.get_all_camera_data():
    print(camera["camera_id"], camera["name"], camera["status"])
```

Every client method also has a module-level function with the same name and arguments. These use a shared client configured from `VERKADA_API_KEY`, which is convenient for one-off scripts:

```python
import pykada.cameras as cameras

for camera in cameras.get_all_camera_data():
    print(camera["name"])
```

| Client | Covers |
|---|---|
| `CamerasClient` | Cameras and sites, footage links and thumbnails, LPR and License Plates of Interest, Persons of Interest, people and smart lists, analytics, dashboards, cloud backup, PTZ, audio, viewing stations |
| `StreamingClient` | HLS playlist URLs for live and historical footage |
| `AccessControlClient` | Access users, credentials (cards, license plates, MFA, QR codes, entry codes, BLE, face unlock), groups, access levels, doors, exception calendars, scenarios |
| `EventsClient` | Camera, access control, sensor and intercom events |
| `SensorsClient` | Environmental sensors, readings and alerts |
| `CoreCommandClient` | Users and audit logs |
| `WorkplaceClient` | Guest sites, visits, events, hosts, guest types, approved lists and deny lists |
| `HelixClient` | Helix video tagging event types, events and batch jobs |
| `ClassicAlarmsClient` | Classic alarm sites and devices |

## Conventions

**Timestamps** take a timezone-aware `datetime` or an ISO 8601 string with a timezone. Naive datetimes and epoch integers raise an error, so a missing timezone can't silently shift your query.

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
client.get_object_counts(camera_id, start_time=now - timedelta(hours=1), end_time=now)
client.get_object_counts(camera_id, start_time="2025-07-17T20:00:00Z")
```

**Durations**, such as a sensor `interval` or a thumbnail link `expiry`, take a `timedelta` or an ISO 8601 duration like `"PT5M"`.

**Pagination:** `get_X()` returns one page as `{"items": [...], "cursor": ...}`. Pass that `cursor` back in to get the next page. `get_all_X()` returns a generator that fetches pages as you iterate:

```python
page = client.get_pois(limit=50)
next_page = client.get_pois(limit=50, cursor=page["cursor"])

for poi in client.get_all_pois():  # every Person of Interest
    print(poi["label"])
```

**User IDs:** most v2 access user endpoints identify users by Verkada `user_id`. If you track users by your own external ID, look the `user_id` up first:

```python
from pykada import AccessControlClient

access = AccessControlClient(api_key="YOUR_API_KEY")
user_id = access.resolve_user_id("employee-4521")
access.set_entry_code_for_user(user_id, entry_code="482913")
```

**Errors** are raised as typed exceptions. Each carries `status_code`, `endpoint`, `response_body`, and, for v2 endpoints, the API's `error_code` and support `error_id`:

```python
from pykada import (VerkadaConflictError, VerkadaNotFoundError,
                    VerkadaRateLimitError, VerkadaValidationError)

try:
    access.add_access_schedule_event_to_access_level(level_id, "Monday", "09:00", "17:00")
except VerkadaValidationError as e:     # 422, e.g. an overlapping window
    print(e.error_code, e)
except VerkadaNotFoundError:            # 404
    print("No such access level")
except VerkadaRateLimitError as e:      # 429, after retries are exhausted
    print(f"Retry in {e.retry_after}s")
```

| Exception | Status |
|---|---|
| `VerkadaBadRequestError` | 400 |
| `VerkadaAuthError` | 401 |
| `VerkadaForbiddenError` | 403 |
| `VerkadaNotFoundError` | 404 |
| `VerkadaConflictError` | 409 |
| `VerkadaValidationError` | 422 |
| `VerkadaRateLimitError` | 429 |
| `VerkadaServerError` | 5xx |
| `VerkadaAPIError` | Any other error status. It is also the parent of the 400, 409 and 422 classes. |

All of them inherit from `VerkadaError`. Invalid arguments raise `ValueError` (or typeguard's `TypeCheckError` for wrong types) before any request is sent.

**API version pinning:** pass `api_version="..."` to any client to send the `x-verkada-api-version` header with every request.

**Retries:** `GET`, `PUT` and `DELETE` requests are retried with backoff on 429 and 5xx responses, timeouts and connection errors. `POST` and `PATCH` are retried only on 429 or a failed connection, when the server can't have acted on the request, so a create is never sent twice. After the last retry the error is raised as one of the exceptions above.

**Connections:** a client keeps its HTTP connections open between calls. Use it as a context manager, or call `close()`, to release them:

```python
with CamerasClient(api_key="YOUR_API_KEY") as client:
    cameras = list(client.get_all_camera_data())
```

**Logging:** pykada logs each request's method, URL and parameter names (never their values) at `DEBUG` on the `pykada` logger. It doesn't configure logging itself; to see these messages:

```python
import logging

logging.basicConfig()
logging.getLogger("pykada").setLevel(logging.DEBUG)
```

## Examples

### Create and delete a Person of Interest

```python
from pykada import CamerasClient

client = CamerasClient(api_key="YOUR_API_KEY")

poi = client.create_poi(image_path="face.png", label="Test POI")
client.update_poi(poi["person_id"], label="Renamed POI")
client.delete_poi(poi["person_id"])
```

### Read sensor data

```python
from datetime import datetime, timedelta, timezone

from pykada import SensorsClient
from pykada.enums import SENSOR_FIELD_ENUM

client = SensorsClient(api_key="YOUR_API_KEY")
now = datetime.now(timezone.utc)

for sensor in client.get_all_sensors():
    readings = client.get_all_sensor_data(
        device_id=sensor["device_id"],
        start_time=now - timedelta(hours=1),
        end_time=now,
        fields=[SENSOR_FIELD_ENUM["TEMPERATURE"], SENSOR_FIELD_ENUM["HUMIDITY"]],
        interval=timedelta(minutes=5),
    )
    for reading in readings:
        print(sensor["device_name"], reading["timestamp"], reading.get("temperature"))
```

### Get camera events

```python
from datetime import datetime, timedelta, timezone

from pykada import EventsClient

client = EventsClient(api_key="YOUR_API_KEY")
now = datetime.now(timezone.utc)

for event in client.get_all_events(start_time=now - timedelta(hours=1), end_time=now,
                                   product_types=["camera"],
                                   event_types=["motion", "crowd"]):
    print(event["timestamp"], event["device_id"], event["event_type"])
```

### Change a camera's cloud backup settings

`update_cloud_backup_settings` changes only the fields you pass. `replace_cloud_backup_settings` sets every field.

```python
from pykada import CamerasClient

client = CamerasClient(api_key="YOUR_API_KEY")

client.update_cloud_backup_settings(
    camera_id="YOUR_CAMERA_ID",
    backup_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    upload_window=("01:00:00", "05:00:00"),  # keep uploads out of business hours
)
```

### Set up an access level

```python
from pykada import AccessControlClient

access = AccessControlClient(api_key="YOUR_API_KEY")

group = access.create_access_group("Night Shift")
access.add_user_to_access_group(group["group_id"], user_id="USER_ID")

access.create_access_level(
    name="Night Shift Doors",
    sites=["SITE_ID"],
    access_groups=[group["group_id"]],
    doors=["DOOR_ID"],
    access_schedule_events=[
        {"weekday": day, "start_time": "18:00", "end_time": "23:59"}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    ],
)
```

### Stream footage

```python
from datetime import datetime, timedelta, timezone

from pykada import StreamingClient

streaming = StreamingClient(api_key="YOUR_API_KEY")

live_url = streaming.get_stream_playlist_url(org_id="ORG_ID", camera_id="CAMERA_ID")

start = datetime.now(timezone.utc) - timedelta(hours=2)
history_url = streaming.get_stream_playlist_url(org_id="ORG_ID", camera_id="CAMERA_ID",
                                                start_time=start,
                                                end_time=start + timedelta(minutes=30))
```

Pass either URL to an HLS player such as hls.js or VLC.

## Calling endpoints directly

For an endpoint pykada doesn't wrap, use `VerkadaRequestManager`. It adds the API token, applies the retry policy above, moves URLs onto your region's host, and raises the typed exceptions above:

```python
from pykada.verkada_requests import VerkadaRequestManager

manager = VerkadaRequestManager(api_key="YOUR_API_KEY", timeout_seconds=10, max_retries=3)

page = manager.get("https://api.verkada.com/v2/cameras", params={"limit": 50})

all_cameras = VerkadaRequestManager.iterate_cursor_results(
    lambda **kwargs: manager.get("https://api.verkada.com/v2/cameras", params=kwargs))
```

To manage tokens yourself, `manager.get_token()` returns a valid API token for the `x-verkada-auth` header.

## Endpoints still on v1

Verkada hasn't published v2 versions of these yet, so pykada uses v1 for them. Apart from Helix, they take the same timestamp and argument styles as everything else:

- **Access control:** access cards, door unlocks (admin and as a user), remote unlock, and `find_access_user` (lookup by email or employee ID).
- **Cameras:** bulk License Plate of Interest CSV upload and delete.
- **Workplace:** Guest sites, visits and deny lists.
- **Helix:** event types, events and search. These still identify events by `time_ms` (epoch milliseconds), as the v1 API does. Batch job status uses v2.
- **Classic alarms:** sites and devices.

## Known API issues

These were seen against the live API in October 2026. They are server-side, so pykada passes the request through unchanged.

- **`/v2/events` returns no camera events.** Any query whose `product_types` includes `camera`, including the default of all products, returns an empty page, while v1 camera alerts still have data. Filtering to `["access_control"]` or `["sensor"]` works. Until this is fixed, request those product types explicitly.
- **LPR zone records fail.** `get_lpr_zone_records` returns `VerkadaBadRequestError` (support ID `LZ07`) for every zone. `get_lpr_zone_metrics` works.

## License

MIT
