import os


LOGGER_NAME = "vesperando-cli"

# Set Logger name as environment variable so that the core library can access it easily
os.environ["LOGGER_NAME"] = LOGGER_NAME