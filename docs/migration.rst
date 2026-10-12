Migrating from 1.x to 2.0
=========================

Pykada 2.0 moves to **Verkada API v2**. Most methods keep their names, but
arguments and return values follow the v2 conventions, and some methods were
renamed, merged, or removed where the API itself changed.

Work through :ref:`cross-cutting` first, since those changes touch nearly every
call. Then check the section for each client you use.

.. contents:: On this page
   :local:
   :depth: 2


.. _cross-cutting:

Changes that affect every client
--------------------------------

Timestamps
~~~~~~~~~~

Every time argument now takes a timezone-aware :class:`~datetime.datetime` or an
ISO 8601 string with a timezone. Epoch integers raise ``TypeCheckError`` and
naive datetimes raise ``ValueError``.

.. code-block:: python

   # 1.x
   client.get_object_counts(camera_id, start_time=1721250380, end_time=1721253980)

   # 2.0
   from datetime import datetime, timezone
   client.get_object_counts(camera_id,
                            start_time=datetime(2024, 7, 17, 21, 6, 20, tzinfo=timezone.utc),
                            end_time="2024-07-17T22:06:20Z")

This applies to the endpoints that are still v1 too (Guest visits, for
example); pykada converts the value for you. The exception is Helix, which still
identifies events by epoch-millisecond ``time_ms``, as the v1 Helix API does.

Timestamps in **responses** are RFC 3339 strings (``"2025-08-04T21:51:53+00:00"``)
rather than epoch integers, and several fields were renamed to match, for
example ``creation_time`` → ``created_at`` and ``last_seen`` → ``last_seen_at``.

Durations
~~~~~~~~~

Durations take a :class:`~datetime.timedelta` or an ISO 8601 duration string:

* ``SensorsClient.get_sensor_data`` ``interval``: ``"5m"`` → ``timedelta(minutes=5)`` or ``"PT5M"``.
* ``CamerasClient.get_thumbnail_link`` ``expiry``: seconds → ``timedelta(hours=1)`` or ``"PT1H"``
  (one hour to seven days).
* Dashboard intervals are ``"PT15M"``, ``"PT1H"`` or ``"PT1D"``. Per-camera occupancy
  trends still use ``"15_minutes"``, ``"1_hour"`` or ``"1_day"``; the ``6_hours``,
  ``12_hours`` and ``30_days`` values are gone.

Pagination
~~~~~~~~~~

Every paged method takes ``limit`` and ``cursor`` instead of ``page_size`` and
``page_token``, and returns ``{"items": [...], "cursor": ...}``. The cursor is
``None`` on the last page. The list key used to vary by endpoint (``cameras``,
``persons_of_interest``, ``alert_events``, and so on); it is now always ``items``.
The one exception is approved list members, which uses ``people``.

.. code-block:: python

   # 1.x
   page = client.get_camera_data(page_size=100, page_token=token)
   cameras, token = page["cameras"], page["next_page_token"]

   # 2.0
   page = client.get_camera_data(limit=100, cursor=cursor)
   cameras, cursor = page["items"], page["cursor"]

Every paged endpoint also has a ``get_all_*`` generator that walks all pages. If
you were looping over pages by hand, switch to that.

Three ``get_all_*`` methods already existed but returned a single dict, and
**now return generators**: ``get_all_access_users``, ``get_all_access_levels``
and ``get_all_door_exception_calendars``. Code that indexes the result
(``get_all_access_users()["access_members"]``) needs to iterate instead
(``list(get_all_access_users())``).

Paging arguments come last, in the order ``limit, cursor``, on every method. A
few Workplace methods previously took ``cursor, limit``. Pass them as keywords.

Deletes and empty responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2 deletes return ``204 No Content``, so delete methods return ``{}``.
``delete_access_level`` and ``delete_access_schedule_event_on_access_level``
previously returned raw ``bytes``.

Errors
~~~~~~

Exceptions gain ``error_code`` (a stable category such as ``"object_not_found"``,
safe to branch on) and ``error_id`` (a support code to quote to Verkada). Both
are ``None`` when the API didn't send them.

New exception classes cover statuses that used to raise the generic
``VerkadaAPIError``. They subclass it, so existing ``except VerkadaAPIError``
handlers still catch them:

* ``VerkadaBadRequestError``: 400
* ``VerkadaConflictError``: 409, for example a duplicate group name or entry code
* ``VerkadaValidationError``: 422, for example overlapping access schedule windows

Identifying users
~~~~~~~~~~~~~~~~~

Most v2 access user endpoints take the Verkada ``user_id`` only, in the URL.
Methods that used to accept ``external_id``, ``email`` or ``employee_id`` now
take ``user_id``. To translate an external ID, call ``resolve_user_id``. It
makes one ``GET /v2/core/users`` call and needs Core read permission.

.. code-block:: python

   # 1.x
   access.set_entry_code_for_user(entry_code="1234", external_id="emp-42")

   # 2.0
   user_id = access.resolve_user_id("emp-42")
   access.set_entry_code_for_user(user_id, entry_code="1234")

To look a user up by email or employee ID, use ``find_access_user``.

Weekday names
~~~~~~~~~~~~~

v2 uses full weekday names (``"Monday"``) everywhere: access schedule events,
exception calendar recurrence rules, and cloud backup days. The two-letter codes
(``"MO"``) are rejected. Use :data:`pykada.enums.WEEKDAY_FULL_ENUM` in place of
``WEEKDAY_ENUM``.

New request options
~~~~~~~~~~~~~~~~~~~

* Every client accepts ``api_version=`` to pin the ``x-verkada-api-version`` header.
* Every client now honours a ``request_manager=`` argument. Previously it was
  silently replaced by the default manager.
* ``VerkadaRequestManager(api_key=...)`` no longer requires ``VERKADA_API_KEY``
  to be set as well.


Cameras
-------

Removed
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - 1.x
     - 2.0
   * - ``get_camera_alerts``, ``get_all_camera_alerts``
     - ``EventsClient.get_events`` / ``get_all_events`` with ``product_types=["camera"]``.
       The alert type filter becomes ``event_types``. v2 events don't include
       image URLs, so ``include_image_url`` has no replacement.

Changed
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Change
   * - ``create_poi``
     - ``image_url`` renamed to ``image_path``; it always was a local file path.
   * - ``update_cloud_backup_settings``
     - Now changes only the fields you pass (``PATCH``). Use the new
       ``replace_cloud_backup_settings`` to set everything at once. The fields are now:

       * ``enabled``: a bool (was ``1``/``0``).
       * ``backup_days``: full weekday names (was ``days_to_preserve="0,1,1,1,1,1,0"``).
       * ``backup_window`` and ``upload_window``: ``("HH:MM:SS", "HH:MM:SS")`` pairs
         (were ``time_to_preserve`` and ``upload_timeslot`` as second offsets).

       ``video_to_upload="MOTION"`` no longer silently forces ``HIGH_QUALITY``.
   * - ``get_cloud_backup_settings``
     - Returns the new field names, plus ``latest_standard_quality_segment_time`` and
       ``latest_high_quality_segment_time`` (were ``last_updated_segment_sq`` and ``_hq``).
   * - ``set_object_position_mqtt``
     - ``camera_id`` is now the first argument: ``(camera_id, broker_host_port, broker_cert, ...)``.
       Pass arguments by keyword to be safe. The password is no longer echoed back.
   * - ``get_camera_data``, ``get_all_camera_data``
     - New ``site_ids`` filter.
   * - ``get_historical_thumbnail``, ``get_thumbnail_link``
     - New optional ``start_time``/``end_time`` search window (at most four hours).
       ``resolution`` is validated (``"low-res"``/``"hi-res"``).
   * - ``get_occupancy_trends``
     - ``interval`` and ``trend_type`` are optional. In 1.x, omitting them raised
       ``ValueError``.
   * - ``get_occupancy_trend_enabled_cameras``, ``get_viewing_stations``
     - Now paged (``limit``, ``cursor``) with ``get_all_*`` generators.
   * - ``create_lpoi``
     - Plates are limited to 11 characters.
   * - ``get_streaming_token``
     - Authenticates with the API key (``x-api-key``), as the endpoint requires.
       Response fields are ``expires_in`` (ISO duration) and ``expires_at`` (RFC 3339).

New
~~~

``get_camera_sites`` / ``get_all_camera_sites``, ``get_lpr_zones``,
``get_lpr_zone_metrics``, ``get_lpr_zone_records``,
``search_ncic_license_plates`` (CJIS organizations only), ``get_people_lists``,
``delete_people_list``, ``get_smart_lists``, ``delete_smart_list``,
``get_dashboards``, ``get_object_position_mqtt``, ``get_ptz_presets`` and
``move_camera_to_ptz_preset``. Each paged one has a matching ``get_all_*``
(``search_all_*`` for the NCIC search).

Streaming
---------

``StreamingClient.get_stream_playlist_url``:

* For live footage, omit ``start_time`` and ``end_time`` instead of passing ``0``.
  For historical footage, pass both as datetimes or ISO strings.
* ``stream_type`` was removed; it only ever accepted ``"stream"``.
* ``codec`` and ``resolution`` are validated.


Events (new)
------------

``EventsClient`` (``pykada.events``) reads the unified ``GET /v2/events`` feed of
camera, access control, sensor and intercom events. Filters take lists:
``product_types``, ``event_types``, ``device_ids`` and ``site_ids``.

.. code-block:: python

   # 1.x
   access.get_access_events(event_type=["door_opened"], site_id="s1,s2")

   # 2.0
   from pykada import EventsClient
   EventsClient(api_key=KEY).get_all_events(product_types=["access_control"],
                                            event_types=["door_opened"],
                                            site_ids=["s1", "s2"])

v2 events have **no** ``user_id`` filter. To find events for a user, filter on
``event["event_info"]["user_info"]["user_id"]`` after fetching.


Access control
--------------

Renamed or merged
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - 1.x
     - 2.0
   * - ``activate_ble_for_access_user``, ``deactivate_ble_for_access_user``
     - ``set_ble_unlock(user_id, active)``
   * - ``activate_license_plate``, ``deactivate_license_plate``
     - ``set_license_plate_active(license_plate_number, active, user_id=... | external_id=...)``
   * - ``set_start_date_for_user``, ``set_end_date_for_user``
     - ``update_access_user_dates(user_id, start_date=..., end_date=...)``. Dates are
       datetimes or ISO strings with a timezone (were epoch seconds as strings).
   * - ``disable_face_unlock_for_user`` / ``_for_external_user``
     - ``disable_face_unlock(user_id=... | external_id=...)``
   * - ``enable_face_unlock_with_profile_photo_for_user`` / ``_for_external_user``
     - ``enable_face_unlock_with_profile_photo(user_id=... | external_id=...)``
   * - ``enable_face_unlock_with_uploaded_photo_for_user`` / ``_for_external_user``
     - ``enable_face_unlock_with_uploaded_photo(photo_path, user_id=... | external_id=...)``.
       This now actually uploads the photo; the 1.x methods never sent one.
   * - ``invite_external_user_to_enroll_face_unlock``
     - ``invite_user_to_enroll_face_unlock(external_id=...)``
   * - ``get_access_user(external_id= | email= | employee_id=)``
     - ``get_access_user(user_id)`` for the core record, or
       ``find_access_user(...)`` for lookup by any identifier and the full record,
       including credentials and groups.

Removed
~~~~~~~

* ``get_access_events``: use ``EventsClient`` (see above).

Changed
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Change
   * - ``set_entry_code_for_user``, ``remove_entry_code_for_user``,
       ``send_pass_app_invite_for_user``, ``get_profile_photo``,
       ``upload_profile_photo``, ``delete_profile_photo``
     - Take ``user_id`` (first argument) only. ``entry_code`` must be 4-16 digits.
       ``send_pass_app_invite_for_user`` accepts ``invitation_methods``.
   * - ``add_user_to_access_group``, ``remove_user_from_access_group``
     - ``(group_id, user_id)`` only.
   * - ``get_access_groups``
     - Paged; returns ``items`` of ``{group_id, name}`` (was ``access_groups``).
   * - ``create_access_level``
     - ``(name, sites, access_groups, doors, access_schedule_events)``, all required,
       with at least one site. Events are dicts like
       ``{"weekday": "Monday", "start_time": "09:00", "end_time": "17:00"}``;
       ``build_access_schedule_event`` builds the v2 shape if you need it.
   * - ``update_access_level``
     - Changes only the fields you pass. It can no longer change schedule events;
       use the ``*_access_schedule_event*`` methods.
   * - ``add_access_schedule_event_to_access_level``,
       ``update_access_schedule_event_on_access_level``
     - Argument order is now ``weekday, start_time, end_time``, with full weekday
       names. Update changes only the fields you pass.
   * - ``get_doors``
     - ``door_id_list`` / ``site_id_list`` renamed to ``door_ids`` / ``site_ids``
       (mutually exclusive). Paged, with ``get_all_doors``.
   * - ``create_door_exception_calendar``, ``update_door_exception_calendar``
     - Arguments reordered: ``create(name, doors, exceptions)`` and
       ``update(calendar_id, name, doors, exceptions)``. Calendar responses use
       ``calendar_id`` (was ``door_exception_calendar_id``) and ``exception_id`` on
       their exceptions; the single-exception methods still return
       ``door_exception_id``. Recurrence ``by_day`` takes full weekday names
       everywhere (pykada translates for the endpoints that still expect two-letter
       codes), and times may be ``HH:MM`` or ``HH:MM:SS``.
   * - ``get_door_exception_calendar``
     - Returns the one calendar. In 1.x it queried the list endpoint and returned
       every calendar.
   * - ``get_door_exception_calendars``
     - New paged method. ``last_updated_after`` is a datetime or ISO string.
   * - ``get_access_scenarios``
     - ``types`` renamed to ``scenario_types``. Paged, with ``get_all_access_scenarios``.
   * - ``add_card_to_user``
     - ``card_type`` is now the first, required argument. ``card_number_base36`` was
       removed (the API never accepted it). Only ``user_id`` or ``external_id``
       identify the user.

New
~~~

``resolve_user_id``, ``find_access_user``, ``get_access_users`` (paged),
``create_pass_sdk_token``, ``add_qr_code_to_user``, ``update_qr_code_state``,
``delete_qr_code_from_user`` and ``get_access_schedule_event``.

Still on v1
~~~~~~~~~~~

Cards, ``unlock_door_as_admin``, ``unlock_door_as_user``, remote unlock and
``find_access_user`` keep working as before; v2 has no equivalent endpoints yet.


Sensors
-------

* ``get_sensor_data`` calls ``/v2/environment/sensors/{device_id}/data``.
  ``interval`` is a ``timedelta`` or ISO duration. Readings are in ``items``, each
  with an RFC 3339 ``timestamp`` (was ``data`` with epoch ``time``).
* ``get_sensor_alerts``: alerts are in ``items`` (was ``alert_events``), with RFC
  3339 ``start_time`` and ``end_time``.
* New ``get_sensors`` / ``get_all_sensors`` to list sensors and the readings
  each one reports.


Core Command
------------

* ``update_user`` is a ``PATCH``. ``external_id`` now only identifies the user; to
  change it, pass ``new_external_id``.
* ``create_user`` requires at least one of ``email``, ``first_name`` or
  ``last_name``, as v2 does. ``external_id`` is optional.
* Audit logs: entries are in ``items`` and no longer include ``organization_id``.
  ``get_all_audit_logs`` accepts ``use_processed_timestamp`` and fixes
  ``end_time`` to the time of the first request, so pages stay stable.
* New ``resolve_user_id(external_id)``.


Workplace
---------

* ``get_guest_visits`` and ``get_all_guest_visits`` take datetimes or ISO strings
  (were epoch ints). ``get_all_guest_visits`` now splits ranges longer than a day
  into the 24-hour windows the endpoint requires; in 1.x those requests failed.
* ``get_guest_events`` and ``create_guest_event`` accept datetimes in
  ``start_time``/``end_time``.
* Limits are enforced: 200 per page for events, hosts and guest types; 1000 for
  approved lists and members; 1-100 people per add/remove call; 1-30 event times.
* ``delete_guest_event`` returns ``{}``. ``reset_approved_list`` works; it raised
  ``TypeError`` in 1.x.
* New ``get_all_guest_events``, ``get_all_guest_hosts``, ``get_all_guest_types``,
  ``get_all_approved_lists`` and ``get_all_approved_list_members``.


Helix and classic alarms
------------------------

No breaking changes. Helix gains ``create_helix_events_batch`` and
``get_batch_job_status``.


Enums
-----

* New: ``WEEKDAY_FULL_ENUM``, ``EVENT_PRODUCT_TYPES_ENUM``,
  ``CAMERA_EVENT_TYPES_ENUM``, ``SENSOR_EVENT_TYPES_ENUM``,
  ``DASHBOARD_INTERVAL_ENUM``, ``DASHBOARD_WIDGET_TYPES_ENUM``,
  ``LPR_ZONE_VEHICLE_STATUS_ENUM``, ``STREAM_CODEC_ENUM`` and
  ``STREAM_RESOLUTION_ENUM``.
* ``VALID_OCCUPANCY_TRENDS_INTERVALS_ENUM`` now lists only the three intervals v2 accepts.
