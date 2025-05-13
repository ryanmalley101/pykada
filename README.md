# Pykada: A Python Client for the Verkada API
## Introduction to Pykada
Navigating the Verkada Public API directly can present certain complexities. Pykada was developed to serve as a dedicated Python library aimed at simplifying these interactions. The core objective is to provide developers with a Pythonic and intuitive interface, abstracting the lower-level details of direct API calls. This library is designed to enhance developer efficiency when integrating Verkada's physical security solutions into custom applications and workflows.

## About Verkada
Verkada is recognized as a leader in cloud-based physical security. Their mission is centered on protecting people and places while prioritizing privacy. They achieve this through a unified system accessible via their cloud platform, Verkada Command.

Verkada offers a comprehensive suite of integrated product lines:

Video Security
Access Control
Environmental sensors
Alarms
Workplace (Guest and Mailroom)
Intercoms
Gateways (Cell and WiFi)

Pykada is designed to interface with the APIs governing these systems, enabling programmatic access and management of data within the Verkada ecosystem.

## Important Disclaimer:

Please be aware that Pykada is not an official Verkada product. It is not affiliated with, endorsed by, or supported by Verkada Inc. This library is maintained independently.

For the most accurate and current information regarding the Verkada API, developers should always refer to the official Verkada API documentation at apidocs.verkada.com. Any support requests or issues related to the Verkada platform itself should be directed to Verkada Support.

## Key Features of Pykada
Pykada offers several features designed to streamline the use of the Verkada API:

Manages the intricacies of API token generation and management, including the automatic refreshing of short-lived tokens.

Provides Python objects representing Verkada entities (e.g., Cameras, Doors, Alerts), offering a more intuitive approach compared to handling raw JSON responses.

Retrieve lists and detailed information for Verkada cameras.

Access camera alerts, including motion, crowd, person of interest, online/offline status, and tamper events.

Fetch camera analytics such as occupancy trends and License Plate Recognition (LPR) data.

List Verkada access control doors and retrieve their details.

Access access control event logs.

Programmatically unlock doors (requires specific configuration within Verkada Command).

Automated Pagination Handling: Simplifies the retrieval of large datasets by automatically managing paginated API responses.

Clear Error Handling: Translates API error responses into descriptive Python exceptions for easier debugging.

Region Management: Facilitates targeting the correct API endpoint based on the organization's Verkada service region.

The primary value of Pykada lies in the abstraction and ease of use it provides. For example, the automatic handling of short-lived API token refreshing allows developers to concentrate on application logic rather than authentication management.

## Requirements
Python Version: Python 3.8 or higher is required.

External Dependencies: Pykada relies on libraries such as requests for making HTTP API calls. These dependencies are typically installed automatically when Pykada is installed via pip.

Verkada Account & API Access:

A valid Verkada organization account is mandatory.

API access must be enabled for the organization within Verkada Command.

An API Key must be generated from the Verkada Command platform; this key serves as the primary credential for API interaction.
