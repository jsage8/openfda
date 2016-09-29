# -*- coding: utf-8 -*-
import json
import re
from xml.etree import cElementTree as ElementTree
from collections import defaultdict
from parser_interface import XMLParserInterface


__author__ = "Jonathan Sage"
__email__ = "jsage8@gmail.com"


class XMLDocParser(XMLParserInterface):
    """
    An XML document parser.

    Currently supported outputs:
        python dictionary
        json
    """

    def __init__(self, class_parser=None):
        self._dict = {}
        self._json = None
        self.class_parser = class_parser

    @property
    def dict(self):
        """
        The xml document's python dictionary representation.
        """
        if not self._dict:
            raise Exception("No document has been parsed. Try calling parse()")
        return self._dict

    @property
    def json(self):
        """
        The xml document's json representation.
        """
        if not self._json:
            self._json = self._dict_to_json(self.dict)
        return self._json

    def parse(self, xml_file, search_tag=None):
        """
        Parse an xml file that is located at the path represented by xml_file. This can be done in
        one of two ways. With apriori knowledge of the file structure we can use iterparse, which
        can help reduce memory usage. Without we have to parse starting at the root element and load
        the full object into memory. Both functions store the result in the dict property.

        :param xml_file: The path to the xml file to parse.
        :ptype xml_file: str
        :param search_tag: The tag we know about apriori.
        :ptype search_tag: str
        :rtype: void
        """
        # Assume apriori knowledge of the xml structure to reduce memory footprint
        if search_tag:
            self._iter_parse(xml_file, search_tag)
        # Parse starting from root element
        else:
            self._std_parse(xml_file)

    def to_json_file(self, json_file, pretty=False):
        """
        Write the xml document as json to a file.

        :param pretty: Pretty print json?
        :ptype pretty: bool
        """
        if pretty:
            self._dict_to_json_file(self.dict, json_file)
        else:
            self._json_to_file(self.json, json_file)

    def _std_parse(self, xml_file):
        """
        Parse an xml file that is located at the path represented by xml_file. Parse starting at
        the root element and load the full object into memory. Parse the tree structure into a dict
        and store it in the dict property.

        :param xml_file: The path to the xml file to parse.
        :ptype xml_file: str
        :rtype: void
        """
        tree = ElementTree.parse(xml_file)
        root = tree.getroot()
        self._dict = self._tree_to_dict(root)

    def _iter_parse(self, xml_file, search_tag):
        """
        Parse an xml file that is located at the path represented by xml_file. Parse each element
        that matches the search_tag. Clear elements from the tree structure that have already been
        parsed to reduce memeory load. Parse the tree structure into a dict and store it in the
        dict property.

        NOTE: This could probably benefit greatly from concurrency.

        :param xml_file: The path to the xml file to parse.
        :ptype xml_file: str
        :param search_tag: The tag we know about apriori.
        :ptype search_tag: str
        :rtype: void
        """
        self._dict['data'] = {search_tag: []}
        for event, element in ElementTree.iterparse(xml_file, events=("end",)):
            tag = self._strip_namespace(element.tag)
            snake_tag = self._camel_to_snake(tag)
            if event == "end" and snake_tag == search_tag:
                self._dict['data'][search_tag].append(self._tree_to_dict(element)[search_tag])
                element.clear()

    @classmethod
    def _camel_to_snake(cls, name):
        """
        Convert a camelCase variable name to a snake_case variable name.

        :param name: The camelCase variable name.
        :ptype name: str
        :return: The snake_case variable name.
        :rtype: str
        """
        # Add an underscore between any character followed by an uppercase letter and a lowercase
        # letter
        temp = re.sub('(.)([A-Z][a-z])', r'\1_\2', name)
        # Add an underscore between any lowercase character or number followed by an uppercase
        # letter, then lowercase the whole string
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', temp).lower()

    @classmethod
    def _strip_namespace(cls, name):
        if '}' in name:
            name = name.split('}', 1)[1]
        return name

    @classmethod
    def _dict_to_json(cls, dict_obj):
        """
        Convert a dictionary to json.

        :param dict_obj: The dictionary to convert.
        :ptype dict_obj: dict
        :return: A json representation of the dict.
        :rtype: json
        """
        return json.dumps(dict_obj)

    @classmethod
    def _dict_to_json_file(cls, dict_obj, json_file):
        """
        Pretty print a dictionary to a json file.

        :param dict_obj: The dictionary object to print to file.
        :ptype dict_obj: dict_obj
        :param json_file: The path of the json file to write to.
        :ptype json_file: str
        """
        with open(json_file, 'w') as json_out:
            json.dump(dict_obj, json_out, indent=2)

    @classmethod
    def _json_to_file(cls, json_obj, json_file):
        """
        Write raw json to file.

        :param dict_obj: The dictionary object to print to file.
        :ptype dict_obj: dict_obj
        :param json_file: The path of the json file to write to.
        :ptype json_file: str
        """
        with open(json_file, 'w') as json_out:
            json_out.write(json_obj)

    @classmethod
    def _tree_to_dict(cls, tree):
        """
        Convert an ElementTree object to a dictionary

        :param tree: A parsed XML object. Each tree element may contain child trees. Each tree
            element may have attribute values. Each tree element may have associated text.
        :ptype tree: ElementTree
        :return: A dictionary representation of the parsed XML tree object. Note that order is not
            maintained.
        :rtype: dict
        """
        attributes = tree.attrib
        children = list(tree)
        text = tree.text
        # Omit empty elements
        tree_dict = {}
        if text or children or attributes:
            tag = cls._strip_namespace(tree.tag)
            # Convert the camelCase tree.tag to snake_case
            snake_tag = cls._camel_to_snake(tag)
            tree_dict = {snake_tag: {} if attributes else None}
            # Recursively build the dict for child trees
            if children:
                dd = defaultdict(list)
                for child_tree_dict in map(cls._tree_to_dict, children):
                    for k, v in child_tree_dict.iteritems():
                        dd[k].append(v)
                tree_dict = {snake_tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
            # Check if the element has attributes and add them to an 'attribs' key in the dict
            if attributes:
                tree_dict[snake_tag]['attribs'] = {attrib: value for attrib, value in attributes.iteritems()}
            # Check if the element has text
            if text:
                strip_text = text.strip()
                if children or attributes:
                    if strip_text:
                        tree_dict[snake_tag]['text'] = strip_text
                else:
                    tree_dict[snake_tag] = strip_text
        return tree_dict

    def inject_project_code(self):
        """
        Call the class_parser's rec_inject method to inject information into the _dict instance
        variable.

        :rtype: void
        """
        if self.class_parser is not None:
            self._dict = self.class_parser.rec_inject(self.dict)
