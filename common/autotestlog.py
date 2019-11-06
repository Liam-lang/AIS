#!/usr/bin/python
# -*- encoding: utf-8 -*-
'''
logging.py: log initialization file
created on Jan 17, 2018
author: Neo
Version: 1.0
'''
import logging, os
import logging.handlers
from common import model

# create logger
logger_name = "autotest"
log_level = logging.DEBUG

logger = logging.getLogger(logger_name)
logger.setLevel(log_level)

# create file handler
isExists = os.path.exists(model.logDir)
if not isExists:
    os.makedirs(log_path)
else:
    pass
log_file = model.logDir + "/autotest-db.log"
fh = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=4 * 1024 * 1024, backupCount=4)

# create formatter
fmt = "%(asctime)-15s %(levelname)s %(filename)s \
        %(lineno)d %(process)d %(message)s"

datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)

# add handler and formatter to logger
fh.setFormatter(formatter)
logger.addHandler(fh)
