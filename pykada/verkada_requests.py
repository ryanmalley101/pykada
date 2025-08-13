import copy
import time
import typing
from typing import Optional

import requests
import logging
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from pykada.api_tokens import get_default_token_manager, VerkadaTokenManager

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

DEFAULT_TIMEOUT = 30
DEFAULT_MAX_TRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_RETRY_DELAY = 0.1

class VerkadaRequestManager:
    """
    Manages HTTP requests to the Verkada API with support for retries,
    exponential backoff, and token-based authentication.
    """
    def __init__(self,
                 timeout=DEFAULT_TIMEOUT,
                 max_retries=DEFAULT_MAX_TRIES,
                 backoff_factor=DEFAULT_MAX_TRIES,
                 retry_delay_seconds=DEFAULT_RETRY_DELAY,
                 token_manager:Optional[VerkadaTokenManager] = None,
                 api_key: Optional[str] = None):
        """
        Initialize the RequestManager with customizable parameters.

        :param timeout: Default timeout for requests.
        :param max_retries: Maximum number of retries for failed requests.
        :param backoff_factor: Backoff multiplier for exponential backoff.
        :param token_manager: Optional token manager for authentication.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.token_manager = token_manager if token_manager else get_default_token_manager()
        self.retry_delay_seconds = retry_delay_seconds

        if token_manager and api_key:
            raise ValueError(
                "Cannot provide both token_manager and api_key. "
                "Use one or the other."
            )

        if token_manager:
            self.token_manager = token_manager
            return

        if api_key and not api_key.strip():
            raise ValueError("api_key must be a non-empty string.")

        if api_key:
            self.token_manager = VerkadaTokenManager(
                api_key=api_key
            )
            return

        # If no token manager or api_key is provided,
        # use the default token manager
        if not self.token_manager and not api_key:
            print("Using default token manager from environment configuration.")
            self.token_manager = get_default_token_manager()

    def _send_request(self, method: str, url: str, payload=None, headers=None,
                      params=None,
                      return_json=True, files=None):
        """
        Centralized request handler for all HTTP methods with retry functionality.

        :param method: HTTP method (e.g., 'get', 'post').
        :param url: Endpoint URL.
        :param files: Included files for the request.
        :param payload: JSON payload for POST/PATCH requests.
        :param headers: Additional HTTP headers.
        :param params: URL parameters.
        :return: JSON response object or raw content.
        """
        # Merge default headers with user-provided headers
        merged_headers = {**self.get_default_headers(), **(headers or {})}

        # Add authentication token if not already provided
        if "x-verkada-auth" not in merged_headers:
            merged_headers["x-verkada-auth"] = self.token_manager.get_token()

        # Configure retries with exponential backoff
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # Use a session to apply retry logic and ensure proper resource management
        with Session() as session:
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            try:
                logging.info(
                    f"Sending {method.upper()} request to {url} with params: {params}, "
                    f"payload: {payload}, and files: {files}"
                )
                response = session.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    json=payload,
                    params=params,
                    timeout=self.timeout,
                    files=files,
                    allow_redirects=False
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logging.error(f"{method.upper()} request to {url} failed: {e}")
                raise

            # Parse and return the response
            if return_json:
                try:
                    return response.json()
                except ValueError:
                    logging.error("Response content is not valid JSON")
                    raise
            else:
                return response.content

    def get(self, url:str, headers:dict=None, params:dict=None):
        return self._send_request(method="get",
                                  url=url,
                                  headers=headers,
                                  params=params,
                                  return_json=True)

    def get_image(self, url, headers=None, params=None):
        return self._send_request(method="get", url=url, headers=headers, params=params, return_json=False)

    def put(self, url:str, payload=None, headers=None, params=None, files=None):
        return self._send_request(method="put", url=url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def post(self,url, payload=None, headers=None, params=None,
                     files=None):
        return self._send_request("post", url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def delete(self, url, headers=None, params=None, timeout=DEFAULT_TIMEOUT,
                       files=None, return_json=True):
        return self._send_request("delete", url, headers=headers, params=params,
                            return_json=return_json,
                            files=files)

    def patch(self,url, payload, headers=None, params=None,
                      files=None):
        return self._send_request("patch", url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def get_default_headers(self):
        """
        Build default headers to be merged with any customer headers later on.
        """
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-verkada-auth": self.token_manager.get_token()
        }

        return headers

    # Specialized wrappers using the centralized function
    @staticmethod
    def iterate_paginated_results(
        paginated_func: typing.Callable[..., dict],
        items_key: Optional[str] = None,
        initial_params: Optional[dict]=None,
        next_token_key: Optional[str] = None,
        default_page_size: Optional[int] = 100,
        request_delay_seconds: Optional[float] = 0
    ) -> typing.Generator[typing.Any, None, None]:
        """
        Iterates through all pages of results from a paginated function.

        Args:
            paginated_func: The function that fetches a single page of results.
                            It must accept 'page_size' and 'page_token' in its
                            parameters and return a dict containing a list of items
                            under 'items_key' and the next page token under
                            'next_token_key'.
            initial_params: A dictionary of parameters for the *first* API call,
                            excluding 'page_size' and 'page_token'. This dict
                            will be deep copied before use.
            items_key: The key in the response dictionary that contains the list
                       of items for the current page (e.g., 'alerts', 'items', 'data').
            next_token_key: The key in the response dictionary that contains the
                            token for the next page (e.g., 'next_page_token',
                            'page_token'). Should be None when there are no more pages.
            default_page_size: The page size to use if not specified in initial_params.
            request_delay_seconds: Optional delay in seconds between fetching pages.

        Yields:
            Each individual item from the paginated results across all pages.
        """
        if initial_params is None:
            initial_params = {}
        current_page_token: typing.Optional[str] = None
        # Start with a deep copy of initial_params to avoid modifying the original
        params = copy.deepcopy(initial_params)

        # Set default page size if not provided in initial_params or is None
        if 'page_size' not in params or params['page_size'] is None:
             params['page_size'] = default_page_size

        # Ensure page_token is initially absent or None, it will be added/updated below
        params.pop('page_token', None)

        while True:
            # Add or update page_token for the current iteration's request
            # On the first loop, current_page_token is None, which is correct for the first page
            params['page_token'] = current_page_token

            # Call the wrapped function to get the current page
            try:
                response = paginated_func(**params)
            except Exception as e:
                # Handle potential exceptions from the wrapped function (e.g., network errors, API errors)
                # You might want more specific error handling or retry logic here
                print(f"Error fetching page with token {current_page_token}: {e}")
                raise # Re-raise the exception

            # Validate the response structure
            if not isinstance(response, dict):
                 print(f"Warning: Paginated function did not return a dictionary. Response: {response}")
                 break # Stop iteration if response is unexpected

            response_keys = list(response.keys())
            if not next_token_key and len(response_keys):
                potential_next_token_keys = [string for string in response_keys if "token" in string]
                if len(potential_next_token_keys) == 1:
                    next_token_key = potential_next_token_keys[0]

            if not next_token_key:
                raise ValueError("next_token_key was not provided and could "
                                 "not be inferred from response")

            if not items_key and len(response_keys) == 2:
                potential_items_key = [string for string in response_keys if "token" not in string]
                if len(potential_items_key) == 1:
                    items_key = potential_items_key[0]

            if not items_key:
                raise ValueError("next_token_key was not provided and could "
                                 "not be inferred from response")

            # Extract items and the next page token using the provided keys
            items = response.get(items_key, [])

            next_page_token_from_response = response.get(next_token_key)

            # Yield items from the current page
            for item in items:
                yield item

            # Update the page token for the next iteration
            current_page_token = next_page_token_from_response

            # Check if there are more pages. If the next token is None, we are done.
            if current_page_token is None:
                break

            # Optional: Wait before making the next request
            if request_delay_seconds > 0:
                time.sleep(request_delay_seconds)

def get_default_request_manager() -> VerkadaRequestManager:
    """
    Returns a default request manager instance using the default token manager.
    This is useful for quick access without needing to instantiate a new manager.
    """
    return VerkadaRequestManager(token_manager=get_default_token_manager())
