import logging
import logging.handlers

import config

################ 设置log ########################


def initLogger(loggerName):
    # create logger
    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    #fh = logging.FileHandler(config.LOG_FILE_PATH)
    fh = logging.handlers.RotatingFileHandler(
        config.LOG_FILE_PATH, mode='a', maxBytes=1024 * 1024 * 5, backupCount=2)
    fh.setLevel(logging.DEBUG)
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(console)
    # logger.info('testlog')


if 'myLoggerInialized' not in globals().keys():
    global myLoggerInialized
    myLoggerInialized = True
    initLogger(config.LOGGER_NAME)
    logger = logging.getLogger(config.LOGGER_NAME)
    logger.info('myLogger inialize')
