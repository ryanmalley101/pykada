# List of endpoints used in the Verkada API

# Region
REGION = "api"

# Change BASE_URL based on the region you are in
BASE_URL = f"https://{REGION}.verkada.com"  # Base URL for Verkada API

# Temporary API Token Endpoint
GET_TOKEN_ENDPOINT = f"{BASE_URL}/token"

# Cameras Endpoint (v1; still used by Helix and the bulk LPOI upload)
CAMERAS_ENDPOINT = f"{BASE_URL}/cameras/v1"

# License Plate of Interest bulk CSV upload/delete (no v2 equivalent yet)
LPOI_BATCH_ENDPOINT = f"{CAMERAS_ENDPOINT}/analytics/lpr/license_plate_of_interest/batch"

# Guest (v1). Sites, visits and deny lists have no v2 endpoint yet.
GUEST_ENDPOINT = f"{BASE_URL}/guest/v1"
GUEST_SITES_ENDPOINT = f"{GUEST_ENDPOINT}/sites"
GUEST_VISITS_ENDPOINT = f"{GUEST_ENDPOINT}/visits"
GUEST_DENY_LIST_ENDPOINT = f"{GUEST_ENDPOINT}/deny_list"



# Alarms Endpoints
ALARMS_ENDPOINT = f"{BASE_URL}/alarms/v1"
ALARMS_DEVICES_ENDPOINT = f"{ALARMS_ENDPOINT}/devices"
ALARMS_SITES_ENDPOINT = f"{ALARMS_ENDPOINT}/sites"


# Access Control (v1). Only operations with no v2 equivalent yet remain:
# card credentials, door unlocks, remote unlock, and user lookup by email or
# employee ID.
ACCESS_CONTROL_ENDPOINT = f"{BASE_URL}/access/v1"
ACCESS_USER_ENDPOINT = f"{ACCESS_CONTROL_ENDPOINT}/access_users/user"
ACCESS_REMOTE_UNLOCK_ACTIVATE_ENDPOINT = f"{ACCESS_USER_ENDPOINT}/remote_unlock/activate"
ACCESS_REMOTE_UNLOCK_DEACTIVATE_ENDPOINT = f"{ACCESS_USER_ENDPOINT}/remote_unlock/deactivate"
ACCESS_CARD_ENDPOINT = f"{ACCESS_CONTROL_ENDPOINT}/credentials/card"
ACCESS_CARD_ACTIVATE_ENDPOINT = f"{ACCESS_CARD_ENDPOINT}/activate"
ACCESS_CARD_DEACTIVATE_ENDPOINT = f"{ACCESS_CARD_ENDPOINT}/deactivate"
ACCESS_ADMIN_UNLOCK_ENDPOINT = f"{ACCESS_CONTROL_ENDPOINT}/door/admin_unlock"
ACCESS_USER_UNLOCK_ENDPOINT = f"{ACCESS_CONTROL_ENDPOINT}/door/user_unlock"

# Helix URL
HELIX_URL = "/video_tagging"

# Helix Endpoints
HELIX_EVENT_TYPE_ENDPOINT = f"{CAMERAS_ENDPOINT}{HELIX_URL}/event_type"
HELIX_EVENT_ENDPOINT = f"{CAMERAS_ENDPOINT}{HELIX_URL}/event"
HELIX_SEARCH_ENDPOINT = f"{HELIX_EVENT_ENDPOINT}/search"
HELIX_BATCH_ENDPOINT = f"{HELIX_EVENT_ENDPOINT}/batch"


# ---------------------------------------------------------------------------
# v2 endpoints
#
# v2 routes follow /v2/<team>/<resources>. Path parameters (IDs) are appended
# in the client methods, e.g. f"{V2_CAMERAS_ENDPOINT}/{camera_id}/audio".
# The v1 constants above are removed as each client migrates; whatever v1
# constants remain afterwards have no v2 equivalent yet.
# ---------------------------------------------------------------------------
V2_BASE_URL = f"{BASE_URL}/v2"

# Access Control
V2_ACCESS_ENDPOINT = f"{V2_BASE_URL}/access"
V2_ACCESS_GROUPS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/access_groups"
V2_ACCESS_LEVELS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/access_levels"
V2_ACCESS_CREDENTIALS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/credentials"
V2_ACCESS_LICENSE_PLATES_ENDPOINT = f"{V2_ACCESS_CREDENTIALS_ENDPOINT}/license_plates"
V2_ACCESS_MFA_CODES_ENDPOINT = f"{V2_ACCESS_CREDENTIALS_ENDPOINT}/mfa_codes"
V2_ACCESS_DOORS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/doors"
V2_ACCESS_EXCEPTION_CALENDARS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/exception_calendars"
V2_ACCESS_SCENARIOS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/scenarios"
V2_ACCESS_USERS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/users"
V2_ACCESS_EXTERNAL_USERS_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/external_users"
V2_ACCESS_PASS_SDK_TOKEN_ENDPOINT = f"{V2_ACCESS_ENDPOINT}/user/pass/sdk_token"

# Analytics
V2_ANALYTICS_ENDPOINT = f"{V2_BASE_URL}/analytics"
V2_ANALYTICS_CAMERAS_ENDPOINT = f"{V2_ANALYTICS_ENDPOINT}/cameras"
V2_OPERATIONAL_DASHBOARD_ENDPOINT = f"{V2_ANALYTICS_ENDPOINT}/operational_dashboard"

# Batch jobs
V2_BATCH_JOBS_ENDPOINT = f"{V2_BASE_URL}/batch/jobs"

# Cameras
V2_CAMERAS_ENDPOINT = f"{V2_BASE_URL}/cameras"
V2_CAMERA_SITES_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/sites"
V2_CAMERA_FOOTAGE_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/footage"
V2_FOOTAGE_LINK_ENDPOINT = f"{V2_CAMERA_FOOTAGE_ENDPOINT}/link"
V2_THUMBNAIL_ENDPOINT = f"{V2_CAMERA_FOOTAGE_ENDPOINT}/thumbnails"
V2_THUMBNAIL_LINK_ENDPOINT = f"{V2_THUMBNAIL_ENDPOINT}/link"
V2_STREAMING_TOKEN_ENDPOINT = f"{V2_CAMERA_FOOTAGE_ENDPOINT}/token"
V2_STREAM_FOOTAGE_ENDPOINT = f"{V2_CAMERA_FOOTAGE_ENDPOINT}/stream/stream.m3u8"
V2_LPR_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/lpr"
V2_LPOI_ENDPOINT = f"{V2_LPR_ENDPOINT}/license_plates_of_interest"
V2_LPR_ZONES_ENDPOINT = f"{V2_LPR_ENDPOINT}/zones"
V2_NCIC_PLATE_SEARCH_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/ncic/license_plates/search"
V2_OCCUPANCY_TRENDS_CAMERAS_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/occupancy_trends"
V2_PEOPLE_ENDPOINT = f"{V2_CAMERAS_ENDPOINT}/people"
V2_PEOPLE_LISTS_ENDPOINT = f"{V2_PEOPLE_ENDPOINT}/people_lists"
V2_PEOPLE_LIST_ENDPOINT = f"{V2_PEOPLE_ENDPOINT}/people_list"
V2_SMART_LISTS_ENDPOINT = f"{V2_PEOPLE_ENDPOINT}/smart_lists"
V2_SMART_LIST_ENDPOINT = f"{V2_PEOPLE_ENDPOINT}/smart_list"
V2_POI_ENDPOINT = f"{V2_PEOPLE_ENDPOINT}/persons_of_interest"

# Core
V2_CORE_ENDPOINT = f"{V2_BASE_URL}/core"
V2_AUDIT_LOGS_ENDPOINT = f"{V2_CORE_ENDPOINT}/audit_logs"
V2_CORE_USERS_ENDPOINT = f"{V2_CORE_ENDPOINT}/users"

# Environment (sensors)
V2_ENVIRONMENT_ENDPOINT = f"{V2_BASE_URL}/environment"
V2_SENSOR_ALERTS_ENDPOINT = f"{V2_ENVIRONMENT_ENDPOINT}/alerts"
V2_SENSORS_ENDPOINT = f"{V2_ENVIRONMENT_ENDPOINT}/sensors"

# Events (camera, access control, sensor and intercom)
V2_EVENTS_ENDPOINT = f"{V2_BASE_URL}/events"

# Guest
V2_GUEST_ENDPOINT = f"{V2_BASE_URL}/guest"
V2_GUEST_EVENTS_ENDPOINT = f"{V2_GUEST_ENDPOINT}/guest_events"
V2_GUEST_HOSTS_ENDPOINT = f"{V2_GUEST_ENDPOINT}/hosts"
V2_GUEST_TYPES_ENDPOINT = f"{V2_GUEST_ENDPOINT}/guest_types"
V2_GUEST_APPROVED_LISTS_ENDPOINT = f"{V2_GUEST_ENDPOINT}/approved_lists"

# Viewing Stations
V2_VIEWING_STATIONS_ENDPOINT = f"{V2_BASE_URL}/viewing_stations"
