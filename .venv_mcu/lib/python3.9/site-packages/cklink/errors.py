# -*- coding:utf-8 -*-


class CKLinkException(Exception):
    """Generic CK-Link exception."""

    def __init__(self, message):
        super(CKLinkException, self).__init__(message)
        self.message = message

