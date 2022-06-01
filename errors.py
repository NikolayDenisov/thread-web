#!/usr/bin/env python3

class OTNSError(Exception):
    """
    Base class for all OTNS errors.
    """


class OTNSCliError(OTNSError):
    def __init__(self, error: str):
        super(OTNSCliError, self).__init__(error)
