from functools import wraps

import logging, sys


def Logger(name=""):
    LOG_FILE = 'app.log'
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(ch)

    return log

logger = Logger()
def logged(log='trace'):
    def wrap(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(log)
            logger.debug("Calling function '{}' with args={} kwargs={}"
                             .format(function.__name__, args, kwargs))
            try:
                response = function(*args, **kwargs)
            except Exception as error:
                logger.debug("Function '{}' raised {} with error '{}'"
                                 .format(function.__name__,
                                         error.__class__.__name__,
                                         str(error)))
                raise error
            logger.debug("Function '{}' returned {}"
                             .format(function.__name__,
                                     response))
            return response
        return wrapper
    return wrap
