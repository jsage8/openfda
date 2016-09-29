# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractproperty, abstractmethod


__author__ = "Jonathan Sage"
__email__ = "jsage8@gmail.com"


class XMLParserInterface(object):

    __metaclass__ = ABCMeta

    @abstractproperty
    def dict(self):
        """
        Dictionary property containing the parsed document.
        """
        raise NotImplementedError()

    @abstractproperty
    def json(self):
        """
        JSON property containing the parsed document.
        """
        raise NotImplementedError()

    @abstractmethod
    def parse(self):
        """
        Parse the XML document and store it in the dict property.
        """
        raise NotImplementedError

    @abstractmethod
    def to_json_file(self):
        """
        Write JSON to file.
        """
        raise NotImplementedError()
