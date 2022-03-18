import logging

def setup_logger(
    log_fp=None,
    log_stdout=True,
    log_format="%(asctime)s %(levelname)-8s [Workbench] %(message)s"
):
    """
    Set up and return a logging instance.
    Logs will be printed to standard out by default (with log_stdout=True).
    If `log_fp` is provided, logs will also be appended to that file.
    """

    assert log_stdout or log_fp is not None, "Must log to either a file or STDOUT"

    # Set up logging
    logFormatter = logging.Formatter(log_format)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # If a file was provided
    if log_fp is not None:
        # Append to file
        fileHandler = logging.FileHandler(log_fp, mode="a")
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)

    # If the flag was set to log to standard out
    if log_stdout:
        # Also write to STDOUT
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)

    # Return the logger
    return logger
