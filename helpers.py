import requests
import logging
# from flask import jsonify, make_response

logger = logging.getLogger(__name__)


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
    if 'application/json' in response.headers.get('Content-Type'):
        logger.debug(response.json())
        return response.json()
    else:
        logger.debug(response.text)
        return response.text
