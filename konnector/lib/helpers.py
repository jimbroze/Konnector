import logging
import time

logger = logging.getLogger("gunicorn.error")


def reverse_lookup(lookupVal, dictionary: dict):
    """Find a dictionary key from its associated value in the dictionary"""
    return next(
        (key for key, value in dictionary.items() if value == str(lookupVal)),
        None,
    )


def max_days_future(dateIn, days) -> bool:
    """Check if a given date is within a number of days from today.
    Returns TRUE or FALSE."""
    cutoff = int((time.time() + days * 86400) * 1000)
    if dateIn is None or int(dateIn) > cutoff:
        logger.debug(f"Date {dateIn} is not before cutoff {cutoff}")
        return False
    else:
        logger.debug(f"Date {dateIn} is before cutoff {cutoff}")
        return True
