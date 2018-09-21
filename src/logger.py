import logging

def Logger(name):
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
