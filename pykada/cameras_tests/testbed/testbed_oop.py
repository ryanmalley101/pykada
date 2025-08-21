import os
import random
import string

from termcolor import cprint

from pykada.cameras.camera_stream import get_stream_playlist_url
from pykada.access_control.cameras import *

import pandas as pd

import vlc

from pykada.enums import VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM, \
    VALID_OCCUPANCY_TRENDS_TYPES_ENUM, VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM, \
    VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM, VALID_IMAGE_RESOLUTION_ENUM

create_license_plate_csv_path = 'licenseplates.csv'
delete_license_plate_csv_path = 'delete_licenseplates.csv'

load_dotenv(override=True)

api_key = os.getenv("SECONDARY_API_KEY")
camera_id = os.getenv("CAMERA_ID")
lpr_camera_id = os.getenv("LPR_CAMERA_ID")
dashboard_id = os.getenv("OCCUPANCY_TRENDS_DASHBOARD_ID")
current_time = int(time.time())
one_hour_ago = current_time - 3600

cameras_client = CamerasClient(api_key=api_key)

def generate_random_alphanumeric_string(length: int) -> str:
  """
  Generates a random string of uppercase alphanumeric characters.

  Args:
    length: The desired length of the random string.

  Returns:
    A random string of the specified length containing uppercase letters (A-Z)
    and digits (0-9).
  """
  # Define the pool of characters (uppercase letters and digits)
  characters = string.ascii_uppercase + string.digits

  # Use random.choice to pick characters and join them into a string
  random_string = ''.join(random.choice(characters) for i in range(length))

  return random_string

def extract_license_plates_pandas(input_csv_path: str, output_csv_path: str) -> bool:
    """
    Reads a CSV file using pandas, extracts the 'License Plate' column,
    and saves it to a new CSV file.

    Note: This function expects the input CSV to have a column named
    'License Plate'. It will raise an error if this column is missing.

    Args:
        input_csv_path: The path to the input CSV file.
        output_csv_path: The path where the new CSV file will be created.

    Returns:
        True if the process was successful, False otherwise.
    """
    # Define the name of the column to extract
    column_to_extract = "License Plate"

    # Check if input file exists
    if not os.path.exists(input_csv_path):
        print(f"Error: Input file not found at '{input_csv_path}'")
        return False

    try:
        # Read the input CSV file into a pandas DataFrame
        # Use usecols to read only the necessary column to improve performance for large files
        # Error will be raised if 'License Plate' column is not found
        df = pd.read_csv(input_csv_path, usecols=[column_to_extract])

        # Ensure the column exists after reading (usecols should handle this, but as a safeguard)
        if column_to_extract not in df.columns:
             print(f"Error: Column '{column_to_extract}' not found in '{input_csv_path}'.")
             return False

        # Select the 'License Plate' column (it's already the only column due to usecols)
        # You could also explicitly select it like df[column_to_extract] if not using usecols
        df_license_plates = df

        # Save the selected column to a new CSV file
        # index=False prevents pandas from writing the DataFrame index as a column
        df_license_plates.to_csv(output_csv_path, index=False, encoding='utf-8')

        print(f"Successfully extracted '{column_to_extract}' column from '{input_csv_path}' to '{output_csv_path}' using pandas.")
        return True

    except FileNotFoundError:
        # This should be caught by the initial check, but included for robustness
        print(f"Error: Input file not found at '{input_csv_path}' during processing.")
        return False
    except ValueError as ve:
        # Catch error if 'License Plate' column is not in usecols list (i.e., not in the file)
        print(f"Error reading CSV: {ve}")
        print(f"Please ensure the input file '{input_csv_path}' contains a column named '{column_to_extract}'.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def poi_test():
    create_poi_resp = cameras_client.create_poi(image_url='Cary-Grant.png',
                                 label='Cary Grant Test')

    get_poi_response = cameras_client.get_all_pois()

    if create_poi_resp not in [p for p in get_poi_response]:
        cprint("Create POI Unsuccessful", "red")
    poi_id = create_poi_resp['person_id']
    try:
        update_poi_response = cameras_client.update_poi(person_id=poi_id, label="Roger Thornhill")
        get_poi_response = cameras_client.get_all_pois()

        if update_poi_response not in [p for p in get_poi_response]:
            cprint("Update POI Unsuccessful", "red")
            return
    finally:
        delete_poi_response = cameras_client.delete_poi(person_id=poi_id)
        get_poi_response = cameras_client.get_all_pois()
        if delete_poi_response in [p for p in get_poi_response]:
            cprint("Delete POI Unsuccessful", "red")
            return
        cprint("POI CRUD Test Successful", "green")

def bulk_lpoi_test():
    create_lpois_response  = cameras_client.create_bulk_lpois(create_license_plate_csv_path)
    print(create_lpois_response)

    if isinstance(create_lpois_response, dict):
        extract_license_plates_pandas(create_license_plate_csv_path, delete_license_plate_csv_path)

        time.sleep(3)
        delete_lpois_response = cameras_client.delete_bulk_lpois(delete_license_plate_csv_path)
        print(delete_lpois_response)

    print("LPOI Bulk Upload Crud Test Successful")

def lpoi_test():
    success = True
    create_lpoi_resp = cameras_client.create_lpoi(license_plate=generate_random_alphanumeric_string(6),
                                  description="Test Plate Please Delete")
    print(create_lpoi_resp)

    get_lpoi_response = cameras_client.get_all_lpois()

    # print([p for p in get_lpoi_response])

    if create_lpoi_resp not in [p for p in get_lpoi_response]:
        cprint("Create LPOI Unsuccessful", "red")
        return

    license_plate = create_lpoi_resp['license_plate']
    try:
        update_lpoi_response = cameras_client.update_lpoi(license_plate=license_plate,
                                         description="Update LPOI Test Please Delete")
        get_lpoi_response = cameras_client.get_all_lpois()

        if update_lpoi_response not in [p for p in get_lpoi_response]:
            cprint("Update LPOI Unsuccessful", "red")
            return
    finally:
        delete_poi_response = cameras_client.delete_lpoi(license_plate=license_plate)
        get_lpoi_response = cameras_client.get_all_lpois()
        if delete_poi_response in [p for p in get_lpoi_response]:
            cprint("Delete LPOI Unsuccessful", "red")
            return
        cprint("LPOI CRUD Test Successful", "green")


def get_license_plates_test():
    all_seen_license_plates = cameras_client.get_all_seen_license_plates(
        camera_id=lpr_camera_id,
        start_time=one_hour_ago - 3600,
        end_time=one_hour_ago
    )

    print([p for p in all_seen_license_plates])


    # Get all the plates between one and two hours ago
    all_license_plates_timestamps = cameras_client.get_all_lpr_timestamps(
        camera_id=lpr_camera_id,
        license_plate="123456",
        start_time=one_hour_ago - 3600,
        end_time=one_hour_ago)

    print([p for p in all_license_plates_timestamps])

    cprint("Get Seen Plates Test Successful", "green")

def get_camera_alerts_test():
    # Get all camera alerts between one and two hours ago
    all_camera_alerts = cameras_client.get_all_camera_alerts(
        start_time=one_hour_ago - 3600,
        end_time=one_hour_ago,
        include_image_url=True,
    )
    print(list(all_camera_alerts))

    cprint("Get All Camera Alerts Test Successful", "green")

def occupancy_trends_test():
    occupancy_trends_enabled_cameras = cameras_client.get_occupancy_trend_enabled_cameras()["cameras_tests"]

    occupancy_trend_camera_id = occupancy_trends_enabled_cameras[0]["camera_id"] \
        if len(occupancy_trends_enabled_cameras) > 0 else None

    if not occupancy_trend_camera_id:
        cprint("No occupancy trends enabled cameras_tests in organization", "green")
        return

    occupancy_trends_data = cameras_client.get_occupancy_trends(
        camera_id=occupancy_trend_camera_id,
        start_time=one_hour_ago,
        end_time=current_time,
        interval=VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM["30_DAYS"],
        type=VALID_OCCUPANCY_TRENDS_TYPES_ENUM["PERSON"],
    )

    print(occupancy_trends_data)

    occupancy_trend_dashboard_data = cameras_client.get_dashboard_occupancy_trend_data(
        dashboard_id=dashboard_id
    )

    print(occupancy_trend_dashboard_data)
    cprint("Get Occupancy Trends Dashboard Data Test Successful", "green")

def object_count_test():
    # Create an empty list to store the pairs
    all_search_zones = []

    # Iterate through all possible values for the first coordinate (0-9)
    for x in range(10):
        # Iterate through all possible values for the second coordinate (0-9)
        for y in range(10):
            # Create the coordinate pair [x, y]
            coordinate_pair = [x, y]
            # Add the coordinate pair to the list
            all_search_zones.append(coordinate_pair)

    max_people_vehicle_counts_data = cameras_client.get_max_people_vehicle_counts(
        camera_id=lpr_camera_id,
        start_time=one_hour_ago,
        end_time=current_time,
        search_zones=all_search_zones
    )

    print(max_people_vehicle_counts_data)

    people_vehicle_counts_data = cameras_client.get_all_object_counts(camera_id=camera_id,
                                                       start_time=one_hour_ago,
                                                       end_time=current_time
                                                       )

    print(list(people_vehicle_counts_data))

def camera_audio_test(enable_audio: Optional[bool] = False):
    camera_audio_status = cameras_client.get_camera_audio_status(camera_id=camera_id)
    print(camera_audio_status)

    if enable_audio is True:
        set_camera_audio_result = (
            cameras_client.set_camera_audio_status(camera_id=camera_id, enable_audio=enable_audio))
        print(set_camera_audio_result)
        camera_audio_status = cameras_client.get_camera_audio_status(camera_id=camera_id)
        print(camera_audio_status)

def cloud_backup_test():
    import random

    def generate_random_time_slot():
        start_time = random.randint(0, 86399)
        end_time = random.randint(start_time, 86399)
        return f"{start_time},{end_time}"

    def generate_random_days_to_preserve():
        return ",".join(str(random.randint(0, 1)) for _ in range(7))

    def generate_random_video_quality():
        return random.choice(list(VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM.values()))

    def generate_random_video_to_upload():
        return random.choice(list(VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values()))

    # Get the current cloud backup settings
    current_settings = cameras_client.get_cloud_backup_settings(camera_id=camera_id)
    print("Current Settings:", current_settings)

    try:
        # Generate a random, valid updated configuration
        new_settings = {
            "camera_id": camera_id,
            "days_to_preserve": generate_random_days_to_preserve(),
            "enabled": random.randint(0, 1),
            "time_to_preserve": generate_random_time_slot(),
            "upload_timeslot": generate_random_time_slot(),
            "video_quality": generate_random_video_quality(),
            "video_to_upload": generate_random_video_to_upload(),
        }

        # Update the cloud backup settings
        update_settings_response = cameras_client.update_cloud_backup_settings(**new_settings)
        print("Updated Settings Response:", update_settings_response)

        # Verify the updated settings
        updated_settings = cameras_client.get_cloud_backup_settings(camera_id=camera_id)
        print("Updated Settings:", updated_settings)

    finally:
        # Restore the original settings
        del current_settings["last_updated_segment_hq"]
        del current_settings["last_updated_segment_sq"]

        restore_response = cameras_client.update_cloud_backup_settings(**current_settings)
        print("Restored Original Settings Response:", restore_response)

        # Verify the restored settings
        restored_settings = cameras_client.get_cloud_backup_settings(camera_id=camera_id)
        print("Restored Settings:", restored_settings)

    cprint("Cloud Backup Test Successful", "green")


def camera_footage_test():
    # Get the latest footage link
    latest_footage_link = cameras_client.get_footage_link(camera_id=camera_id)
    print("Latest Footage Link:", latest_footage_link)

    historical_footage_link = cameras_client.get_footage_link(camera_id=camera_id, timestamp=one_hour_ago)
    print("Historical Footage Link:", historical_footage_link)

    historicaL_thumbnail_link = cameras_client.get_thumbnail_link(
        camera_id=camera_id,
        timestamp=one_hour_ago,
        expiry=3600
    )
    print("Historical Thumbnail Link:", historicaL_thumbnail_link)

    # Get the latest thumbnail
    latest_thumbnail_image = cameras_client.get_latest_thumbnail(camera_id=camera_id)
    print("Latest Thumbnail:", latest_thumbnail_image)

    historical_thumbnail_image = cameras_client.get_historical_thumbnail(camera_id=camera_id,
                                                         timestamp=one_hour_ago,
                                                         resolution=VALID_IMAGE_RESOLUTION_ENUM["LOW_RES"])

    print("Historical Thumbnail Image", historical_thumbnail_image)

    # Get the streaming token
    streaming_playlist = cameras_client.get_stream_playlist_url(
        camera_id=camera_id,
        start_time=one_hour_ago,
        end_time=current_time,
        codec="hevc",
        resolution="low_res",
        type="stream"
    )
    print("Streaming Playlist URL:", streaming_playlist)

    # Verify the M3U8 playlist using VLC
    try:
        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(streaming_playlist)
        player.set_media(media)
        player.play()
        time.sleep(5)  # Allow some time for the stream to start
        state = player.get_state()
        if state in [vlc.State.Playing, vlc.State.Opening]:
            print("M3U8 Playlist is valid and playable.")
        else:
            print("M3U8 Playlist is invalid or not playable.")
        player.stop()
    except Exception as e:
        print(f"Error verifying M3U8 Playlist: {e}")


    print("Camera Stream Test Successful")



poi_test()
bulk_lpoi_test()
lpoi_test()
get_license_plates_test()
get_camera_alerts_test()
occupancy_trends_test()
camera_audio_test(enable_audio=False)
cloud_backup_test()
object_count_test()
camera_footage_test()
print("Camera Testbed Test Successful")