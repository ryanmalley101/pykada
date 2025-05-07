import requests
import logging
from dotenv import load_dotenv
from api_tokens import get_api_token

# Load environment variables once at startup.
load_dotenv(override=True)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

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
                 timeout=DEFAULT_TIMEOUT, return_json=True, files=None):
    """
    Centralized request handler for all HTTP methods.

    :param files: Included files for the request
    :param method: HTTP method (e.g. 'get', 'post')
    :param url: Endpoint URL.
    :param payload: JSON payload for POST/PATCH requests.
    :param headers: Additional HTTP headers.
    :param params: URL parameters.
    :param timeout: Request timeout in seconds.
    :param return_json: If True, parse response as JSON; otherwise return raw content.
    :return: JSON response object.
    """
    merged_headers = get_default_headers() if headers is None else headers
    logging.info(f"Sending {method.upper()} request to {url} with params: {params}, payload: {payload}, and files: {files}")
    print(headers)
    # Allow the user to override the API auth token if they prefer
    if "x-verkada-auth" not in merged_headers:
        merged_headers["x-verkada-auth"] = get_api_token()

    try:
        response = requests.request(method, url, headers=merged_headers, json=payload, params=params, timeout=timeout, files=files, allow_redirects=False)
        print(response.content)
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


def get_request(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT):
    return send_request("get", url, headers=headers, params=params,
                        timeout=timeout, return_json=True)

def get_request_image(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT):
    return send_request("get", url, headers=headers, params=params,
                        timeout=timeout, return_json=False)

def put_request(url, payload=None, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None):
    return send_request("put", url, url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files)

def post_request(url, payload=None, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None):
    return send_request("post", url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files)

def delete_request(url, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None):
    return send_request("delete", url, headers=headers, params=params,
                        timeout=timeout, return_json=True, files=files)

def patch_request(url, payload, headers=None, params=None, timeout=DEFAULT_TIMEOUT, files=None):
    return send_request("patch", url, payload=payload, headers=headers,
                        params=params, timeout=timeout, return_json=True, files=files)

