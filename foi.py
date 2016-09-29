# -*- coding: utf-8 -*-
import copy


__author__ = "Jonathan Sage"
__email__ = "jsage8@gmail.com"


class FDAClassificationParser(object):
    """
    An FDA Classification document parser.
    """

    def __init__(self, index_field="PRODUCTCODE"):
        self.index_field = index_field
        self._dict = {}

    def get(self, class_code):
        """
        The xml document's python dictionary representation.
        """
        if not self._dict:
            raise Exception("No document has been parsed. Try calling parse()")
        return self._dict.get(class_code)

    def parse(self, classification_file):
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
        with open(classification_file, 'r') as class_file:
            header = next(class_file)
            index = header.split("|").index(self.index_field)
            for line in class_file:
                self._dict[line.split("|")[index]] = line.strip()

    def rec_inject(self, obj):
        """
        Inject product code information into a dictionary's structure recursively. This method is
        currently inflexible and would benefit from better parameterization.

        :param dict_obj: The dict or list to recurse over.
        :ptype dict_obj: dict or list
        :return: The same dict with new values injected for product codes.
        :rtype: dict
        """
        if isinstance(obj, dict):
            for key, value in obj.iteritems():
                if key == 'fda_product_code':
                    if isinstance(value, dict):
                        obj[key]['openfda'] = self.rec_get_products(value, products=[])
                    elif isinstance(value, list):
                        for index, element in enumerate(value):
                            obj[key][index]['openfda'] = self.rec_get_products(element, products=[])
                else:
                    obj[key] = self.rec_inject(value)
        elif isinstance(obj, list):
            for index, element in enumerate(obj):
                obj[index] = self.rec_inject(element)
        return obj

    def rec_get_products(self, obj, products=[]):
        """
        Recursively retrieve the product openfda classifiers.

        :param obj: The dict or list to get products out of.
        :ptype obj: dict or list
        :return: The
        """
        if isinstance(obj, dict):
            for key, value in obj.iteritems():
                if key == 'product_code':
                    products.append(self.get(value))
                else:
                    self.rec_get_products(value, products)
        elif isinstance(obj, list):
            for index, element in enumerate(obj):
                self.rec_get_products(element, products)
        return products
