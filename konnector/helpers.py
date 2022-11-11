import requests
import logging
import time

logger = logging.getLogger("gunicorn.error")


def max_days_future(dateIn, days):
    """Check if a date is within a number of days from today.
    Returns TRUE or FALSE."""
    cutoff = int((time.time() + days * 86400) * 1000)
    if dateIn is None or int(dateIn) > cutoff:
        logger.debug(f"Date {dateIn} is not before cutoff {cutoff}")
        return False
    else:
        logger.debug(f"Date {dateIn} is before cutoff {cutoff}")
        return True


def send_request(url, headers, reqType="GET", data={}):
    try:
        if not data:
            response = requests.request(reqType, url, headers=headers)
        else:
            response = requests.request(reqType, url, headers=headers, json=data)

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(e)
        logger.error(f"request type {reqType}. headers: {headers}. data: {data}")

        raise
    if "application/json" in response.headers.get("Content-Type"):
        logger.debug(response.json())
        return response.json()
    else:
        logger.debug(response.text)
        return response.text
