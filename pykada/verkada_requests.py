import time

import requests
import logging
from dotenv import load_dotenv
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from pykada.api_tokens import get_api_token

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.ERROR)

DEFAULT_TIMEOUT = 10

def get_default_headers():
    """
    Build default headers and merge with any additional headers.
    """
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-verkada-auth": get_api_token()
    }

    return headers

def send_request(method, url, *, payload=None, headers=None, params=None,
                 timeout=DEFAULT_TIMEOUT, return_json=True, files=None,
                 max_retries=3, backoff_factor=0.3, delay=0):
    """
    Centralized request handler for all HTTP methods with retry functionality.

    :param files: Included files for the request
    :param method: HTTP method (e.g. 'get', 'post')
    :param url: Endpoint URL.
    :param payload: JSON payload for POST/PATCH requests.
    :param headers: Additional HTTP headers.
    :param params: URL parameters.
    :param timeout: Request timeout in seconds.
    :param return_json: If True, parse response as JSON; otherwise return raw content.
    :param max_retries: Maximum number of retries for failed requests.
    :param backoff_factor: Backoff multiplier for exponential backoff.
    :return: JSON response object or raw content.
    """
    merged_headers = get_default_headers() if headers is None else headers
    # Allow the user to override the API auth token if they prefer
    if "x-verkada-auth" not in merged_headers:
        merged_headers["x-verkada-auth"] = get_api_token()
    # If the user provides a custom auth token, use it

    # Configure retries with exponential backoff
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logging.info(f"Sending {method.upper()} request to {url} with params: {params}, payload: {payload}, and files: {files}")

    try:
        time.sleep(delay)
        response = requests.request(method, url, headers=merged_headers, json=payload, params=params, timeout=timeout, files=files, allow_redirects=False)
        logging.info(response.content)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"{method.upper()} request to {url} failed: {e}")
        raise

    if return_json:
        try:
            return response.json()
        except ValueError:
            logging.error("Response content is not valid JSON")
            raise
    else:
        return response.content

# Specialized wrappers using the centralized function


def get_request(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT, max_retries=3, backoff_factor=2):
    return send_request("get", url, headers=headers, params=params,
                        timeout=timeout, return_json=True, max_retries=max_retries, backoff_factor=backoff_factor)

def get_request_image(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT, max_retries=3, backoff_factor=2):
    return send_request("get", url, headers=headers, params=params,
                        timeout=timeout, return_json=False, max_retries=max_retries, backoff_factor=backoff_factor)

def put_request(url, payload=None, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None, max_retries=3, backoff_factor=2):
    return send_request("put", url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files, max_retries=max_retries, backoff_factor=backoff_factor)

def post_request(url, payload=None, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None, max_retries=3, backoff_factor=2):
    return send_request("post", url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files, max_retries=max_retries, backoff_factor=backoff_factor)

def delete_request(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None, max_retries=3, backoff_factor=2):
    return send_request("delete", url, headers=headers, params=params,
                        timeout=timeout, return_json=True, files=files, max_retries=max_retries, backoff_factor=backoff_factor)

def patch_request(url, payload, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None, max_retries=3, backoff_factor=2):
    return send_request("patch", url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files, max_retries=max_retries, backoff_factor=backoff_factor)