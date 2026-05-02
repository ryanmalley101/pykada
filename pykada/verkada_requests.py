"""
HTTP request management for pykada.

:class:`VerkadaRequestManager` is the single HTTP layer used by all product
clients.  It handles token injection, configurable retry/backoff, and maps
HTTP error status codes to typed :mod:`pykada.exceptions`.

:func:`iterate_paginated_results` is a static generator that transparently
walks all pages of any paginated Verkada endpoint.
"""
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
from pykada.exceptions import (
    VerkadaError,
    VerkadaAuthError,
    VerkadaForbiddenError,
    VerkadaNotFoundError,
    VerkadaRateLimitError,
    VerkadaServerError,
    VerkadaAPIError,
)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def _raise_for_status(url: str, response: requests.Response) -> None:
    """Map an unsuccessful HTTP response to the appropriate VerkadaError subclass."""
    try:
        body = response.text
    except Exception:
        body = "<unreadable>"

    status = response.status_code
    msg = f"HTTP {status} from {url}: {body}"

    if status == 401:
        raise VerkadaAuthError(msg, status_code=status, response_body=body, endpoint=url)
    if status == 403:
        raise VerkadaForbiddenError(msg, status_code=status, response_body=body, endpoint=url)
    if status == 404:
        raise VerkadaNotFoundError(msg, status_code=status, response_body=body, endpoint=url)
    if status == 429:
        retry_after_header = response.headers.get("Retry-After")
        retry_after = int(retry_after_header) if retry_after_header and retry_after_header.isdigit() else None
        raise VerkadaRateLimitError(msg, status_code=status, response_body=body, endpoint=url, retry_after=retry_after)
    if status >= 500:
        raise VerkadaServerError(msg, status_code=status, response_body=body, endpoint=url)
    raise VerkadaAPIError(msg, status_code=status, response_body=body, endpoint=url)


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
                 timeout_seconds: int = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_TRIES,
                 backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
                 retry_delay_seconds: float = DEFAULT_RETRY_DELAY,
                 token_manager: Optional[VerkadaTokenManager] = None,
                 api_key: Optional[str] = None):
        """
        Initialize the RequestManager with customizable parameters.

        :param timeout_seconds: Default timeout for requests.
        :param max_retries: Maximum number of retries for failed requests.
        :param backoff_factor: Backoff multiplier for exponential backoff.
        :param token_manager: Optional token manager for authentication.
        """
        self.timeout = timeout_seconds
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
            logging.info("Using default token manager from environment configuration.")
            self.token_manager = get_default_token_manager()

    def _send_request(self, method: str, url: str, payload: Optional[dict] = None,
                      headers: Optional[dict] = None,
                      params: Optional[dict] = None,
                      return_json: bool = True, files: Optional[dict] = None) -> typing.Union[dict, str, bytes]:
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
        merged_headers = headers or {}
        if return_json:
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

            logging.info(
                f"Sending {method.upper()} request to {url} with params: {params}, "
                f"payload: {payload}, and files: {files}"
            )
            try:
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
            except requests.exceptions.RetryError as e:
                raise VerkadaServerError(
                    f"{method.upper()} {url} failed after {self.max_retries} retries.",
                    endpoint=url,
                ) from e
            except requests.exceptions.Timeout as e:
                raise VerkadaError(
                    f"{method.upper()} {url} timed out after {self.timeout}s.",
                    endpoint=url,
                ) from e
            except requests.exceptions.RequestException as e:
                raise VerkadaError(
                    f"{method.upper()} {url} failed: {e}",
                    endpoint=url,
                ) from e

            if not response.ok:
                logging.error(f"{method.upper()} {url} returned HTTP {response.status_code}")
                _raise_for_status(url, response)

            # Parse and return the response
            if return_json:
                try:
                    return response.json()
                except ValueError as e:
                    raise VerkadaError(
                        f"Response from {url} is not valid JSON "
                        f"(status {response.status_code}): {response.text[:200]}",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=url,
                    ) from e
            else:
                return response.content

    def get(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        return self._send_request(method="get",
                                  url=url,
                                  headers=headers,
                                  params=params,
                                  return_json=True)

    def get_image(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None) -> typing.Union[str, bytes]:
        return self._send_request(method="get", url=url, headers=headers, params=params, return_json=False)

    def put(self, url: str, payload: Optional[dict] = None, headers: Optional[dict] = None,
            params: Optional[dict] = None, files: Optional[dict] = None) -> dict:
        return self._send_request(method="put", url=url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def post(self, url: str, payload: Optional[dict] = None, headers: Optional[dict] = None,
                     params: Optional[dict] = None,
                     files: Optional[dict] = None) -> dict:
        return self._send_request("post", url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def delete(self, url: str, headers: Optional[dict] = None, params: Optional[dict] = None,
                       timeout: int = DEFAULT_TIMEOUT,
                       files: Optional[dict] = None, return_json: bool = True) -> dict:
        return self._send_request("delete", url, headers=headers, params=params,
                            return_json=return_json,
                            files=files)

    def patch(self, url: str, payload: dict, headers: Optional[dict] = None,
                      params: Optional[dict] = None,
                      files: Optional[dict] = None) -> dict:
        return self._send_request("patch", url, payload=payload, headers=headers,
                            params=params, return_json=True,
                            files=files)

    def get_default_headers(self) -> dict:
        """
        Build default headers to be merged with any customer headers later on.
        """
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-verkada-auth": self.token_manager.get_token()
        }

        return headers

    def get_token(self) -> str:
        """
        Retrieve a Verkada API Token from the token manager and return it.

        :return: A valid Verkada API token
        :rtype: string
        """
        return self.token_manager.get_token()

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
                logging.error(f"Error fetching page with token {current_page_token}: {e}")
                raise  # Re-raise the exception

            # Validate the response structure
            if not isinstance(response, dict):
                logging.warning(f"Paginated function did not return a dictionary. Response: {response}")
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
                raise ValueError("items_key was not provided and could "
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
