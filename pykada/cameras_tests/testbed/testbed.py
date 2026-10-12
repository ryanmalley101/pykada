"""
Live smoke test for the pykada.cameras functional wrappers against the real
Verkada API. The wrappers read VERKADA_API_KEY.

Requires VERKADA_API_KEY, CAMERA_ID, LPR_CAMERA_ID, ORG_ID and
OCCUPANCY_TRENDS_DASHBOARD_ID in the environment / .env. Mutating tests
(POIs, LPOIs, cloud backup) clean up after themselves.
"""
import csv
import os
import random
import string
import time as time_module
from datetime import datetime, time, timedelta, timezone

from dotenv import load_dotenv
from termcolor import cprint

from pykada.camera_stream import StreamingClient
from pykada.exceptions import VerkadaBadRequestError
import pykada.cameras as cameras_client
from pykada.enums import (VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM,
                          VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM,
                          VALID_IMAGE_RESOLUTION_ENUM,
                          VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM,
                          VALID_OCCUPANCY_TRENDS_TYPES_ENUM, WEEKDAY_FULL_ENUM)

create_license_plate_csv_path = 'licenseplates.csv'
delete_license_plate_csv_path = 'delete_licenseplates.csv'

load_dotenv(override=True)

api_key = os.getenv("VERKADA_API_KEY")
org_id = os.getenv("ORG_ID")
camera_id = os.getenv("CAMERA_ID")
lpr_camera_id = os.getenv("LPR_CAMERA_ID")
dashboard_id = os.getenv("OCCUPANCY_TRENDS_DASHBOARD_ID")
current_time = datetime.now(timezone.utc)
one_hour_ago = current_time - timedelta(hours=1)


def random_plate(length: int = 6) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def write_plate_column_csv(input_csv_path: str, output_csv_path: str) -> None:
    """Copy just the 'License Plate' column of a CSV, for the bulk delete upload."""
    with open(input_csv_path, newline='', encoding='utf-8') as src:
        plates = [row["License Plate"] for row in csv.DictReader(src)]
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as dst:
        writer = csv.writer(dst, lineterminator="\n")
        writer.writerow(["License Plate"])
        writer.writerows([p] for p in plates)


def devices_test():
    cameras = list(cameras_client.get_all_camera_data())
    print(f"{len(cameras)} cameras")
    sites = list(cameras_client.get_all_camera_sites())
    print(f"{len(sites)} camera sites:", [s["path"] for s in sites])
    if sites:
        at_site = list(cameras_client.get_all_camera_data(site_ids=[sites[0]["site_id"]]))
        print(f"{len(at_site)} cameras at {sites[0]['path']}")
    print("Viewing stations:", list(cameras_client.get_all_viewing_stations()))
    cprint("Devices Test Successful", "green")


def poi_test():
    created = cameras_client.create_poi(image_path='Cary-Grant.png', label='Cary Grant Test')
    poi_id = created['person_id']
    try:
        if poi_id not in [p["person_id"] for p in cameras_client.get_all_pois()]:
            cprint("Create POI Unsuccessful", "red")
            return
        updated = cameras_client.update_poi(person_id=poi_id, label="Roger Thornhill")
        if updated["label"] != "Roger Thornhill":
            cprint("Update POI Unsuccessful", "red")
            return
    finally:
        cameras_client.delete_poi(person_id=poi_id)
    if poi_id in [p["person_id"] for p in cameras_client.get_all_pois()]:
        cprint("Delete POI Unsuccessful", "red")
        return
    print("People lists:", list(cameras_client.get_all_people_lists()))
    print("Smart lists:", list(cameras_client.get_all_smart_lists()))
    cprint("POI CRUD Test Successful", "green")


def bulk_lpoi_test():
    print(cameras_client.create_bulk_lpois(create_license_plate_csv_path))
    write_plate_column_csv(create_license_plate_csv_path, delete_license_plate_csv_path)
    time_module.sleep(3)
    print(cameras_client.delete_bulk_lpois(delete_license_plate_csv_path))
    cprint("LPOI Bulk Upload CRUD Test Successful", "green")


def lpoi_test():
    plate = random_plate()
    cameras_client.create_lpoi(license_plate=plate, description="Test Plate Please Delete")
    try:
        if plate not in [p["license_plate"] for p in cameras_client.get_all_lpois()]:
            cprint("Create LPOI Unsuccessful", "red")
            return
        updated = cameras_client.update_lpoi(license_plate=plate,
                                             description="Update LPOI Test Please Delete")
        if updated["description"] != "Update LPOI Test Please Delete":
            cprint("Update LPOI Unsuccessful", "red")
            return
    finally:
        cameras_client.delete_lpoi(license_plate=plate)
    if plate in [p["license_plate"] for p in cameras_client.get_all_lpois()]:
        cprint("Delete LPOI Unsuccessful", "red")
        return
    cprint("LPOI CRUD Test Successful", "green")


def get_license_plates_test():
    seen = list(cameras_client.get_all_seen_license_plates(
        camera_id=lpr_camera_id, start_time=one_hour_ago - timedelta(hours=1),
        end_time=one_hour_ago))
    print(seen)
    if seen:
        print(list(cameras_client.get_all_lpr_timestamps(
            camera_id=lpr_camera_id, license_plate=seen[0]["license_plate"],
            start_time=one_hour_ago - timedelta(hours=1), end_time=one_hour_ago)))
    for zone in cameras_client.get_all_lpr_zones():
        print(zone["zone_name"], cameras_client.get_lpr_zone_metrics(
            zone["zone_id"], start_time=one_hour_ago, end_time=current_time))
        try:
            print(list(cameras_client.get_all_lpr_zone_records(zone["zone_id"])))
        except VerkadaBadRequestError as e:
            # As of 2026-10 the API returns LZ07 for every zone's records
            print(f"LPR zone records unavailable for {zone['zone_name']}: {e}")
    cprint("Get Seen Plates Test Successful", "green")


def occupancy_trends_test():
    enabled = list(cameras_client.get_all_occupancy_trend_enabled_cameras())
    if not enabled or not enabled[0].get("presets"):
        cprint("No occupancy trends enabled cameras in organization", "green")
    else:
        print(cameras_client.get_occupancy_trends(
            camera_id=enabled[0]["camera_id"],
            preset_id=enabled[0]["presets"][0]["preset_id"],
            start_time=one_hour_ago, end_time=current_time,
            interval=VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM["15_MINUTES"],
            trend_type=VALID_OCCUPANCY_TRENDS_TYPES_ENUM["PERSON"]))

    print([d["dashboard_name"] for d in cameras_client.get_all_dashboards()])
    print(cameras_client.get_dashboard_occupancy_trend_data(dashboard_id=dashboard_id))
    print(cameras_client.get_dashboard_widget_trends(dashboard_id=dashboard_id))
    cprint("Occupancy Trends Test Successful", "green")


def object_count_test():
    all_search_zones = [[x, y] for x in range(10) for y in range(10)]
    print(cameras_client.get_max_people_vehicle_counts(
        camera_id=lpr_camera_id, start_time=one_hour_ago, end_time=current_time,
        search_zones=all_search_zones))
    print(list(cameras_client.get_all_object_counts(
        camera_id=camera_id, start_time=one_hour_ago, end_time=current_time)))
    print(cameras_client.get_object_position_mqtt(camera_id=camera_id))
    cprint("Object Count Test Successful", "green")


def camera_audio_test(enable_audio: bool = False):
    print(cameras_client.get_camera_audio_status(camera_id=camera_id))
    if enable_audio:
        print(cameras_client.set_camera_audio_status(camera_id=camera_id, enabled=True))
        print(cameras_client.get_camera_audio_status(camera_id=camera_id))


def ptz_test():
    presets = cameras_client.get_ptz_presets(camera_id=camera_id)["items"]
    print("PTZ presets:", presets)
    home = next((p for p in presets if p["is_home"]), None)
    if home:
        cameras_client.move_camera_to_ptz_preset(camera_id=camera_id,
                                                 preset_id=home["preset_id"])
    cprint("PTZ Test Successful", "green")


def cloud_backup_test():
    def random_window():
        start = random.randint(0, 22)
        return time(start, 0), time(random.randint(start + 1, 23), 59, 59)

    original = cameras_client.get_cloud_backup_settings(camera_id=camera_id)
    print("Current Settings:", original)
    try:
        print("Partial Update:", cameras_client.update_cloud_backup_settings(
            camera_id=camera_id, enabled=not original["enabled"]))
        print("Replaced Settings:", cameras_client.replace_cloud_backup_settings(
            camera_id=camera_id,
            enabled=random.choice([True, False]),
            video_to_upload=random.choice(list(VALID_CLOUD_BACKUP_VIDEO_TO_UPLOAD_ENUM.values())),
            video_quality=random.choice(list(VALID_CLOUD_BACKUP_VIDEO_QUALITY_ENUM.values())),
            backup_days=random.sample(list(WEEKDAY_FULL_ENUM.values()), 3),
            backup_window=random_window(),
            upload_window=random_window()))
    finally:
        cameras_client.replace_cloud_backup_settings(
            camera_id=camera_id,
            enabled=original["enabled"],
            video_to_upload=original["video_to_upload"],
            video_quality=original["video_quality"],
            backup_days=original["backup_days"],
            backup_window=(original["backup_window"]["start_time"],
                           original["backup_window"]["end_time"]),
            upload_window=(original["upload_window"]["start_time"],
                           original["upload_window"]["end_time"]))
        print("Restored Settings:", cameras_client.get_cloud_backup_settings(camera_id=camera_id))
    cprint("Cloud Backup Test Successful", "green")


def camera_footage_test():
    print("Latest Footage Link:", cameras_client.get_footage_link(camera_id=camera_id))
    print("Historical Footage Link:",
          cameras_client.get_footage_link(camera_id=camera_id, timestamp=one_hour_ago))
    print("Historical Thumbnail Link:", cameras_client.get_thumbnail_link(
        camera_id=camera_id, timestamp=one_hour_ago, expiry=timedelta(hours=1)))
    print("Latest Thumbnail bytes:", len(cameras_client.get_latest_thumbnail(camera_id=camera_id)))
    print("Historical Thumbnail bytes:", len(cameras_client.get_historical_thumbnail(
        camera_id=camera_id, timestamp=one_hour_ago,
        resolution=VALID_IMAGE_RESOLUTION_ENUM["LOW_RES"])))

    streaming_playlist = StreamingClient(api_key=api_key).get_stream_playlist_url(
        org_id=org_id, camera_id=camera_id,
        start_time=one_hour_ago, end_time=one_hour_ago + timedelta(minutes=10))
    print("Streaming Playlist URL:", streaming_playlist)

    try:
        import vlc
    except ImportError:
        print("python-vlc not installed; skipping playback check.")
    else:
        player = vlc.Instance().media_player_new()
        player.set_media(vlc.Instance().media_new(streaming_playlist))
        player.play()
        time_module.sleep(5)  # Allow some time for the stream to start
        playable = player.get_state() in [vlc.State.Playing, vlc.State.Opening]
        print("M3U8 Playlist is", "playable." if playable else "NOT playable.")
        player.stop()
    cprint("Camera Footage Test Successful", "green")


devices_test()
poi_test()
bulk_lpoi_test()
lpoi_test()
get_license_plates_test()
occupancy_trends_test()
camera_audio_test(enable_audio=False)
ptz_test()
cloud_backup_test()
object_count_test()
camera_footage_test()
print("Camera Testbed Test Successful")
