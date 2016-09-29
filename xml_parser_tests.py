import unittest
import argparse
import tempfile
import json
import os
from mock import MagicMock, PropertyMock, patch
from xml.etree.ElementTree import Element, SubElement, tostring

from doc_parser import XMLDocParser
from foi import FDAClassificationParser


__author__ = "Jonathan Sage"
__email__ = "jsage8@gmail.com"


class TestXMLParser(unittest.TestCase):
    def setUp(self):
        """
        Set up the expected dictionary output.
        """
        self.dict_obj = {
            "data": {
                "country": [
                    {
                        "attribs": {
                            "name": "Liechtenstein"
                        },
                        "year": "2008",
                        "gdppc": "141100",
                        "neighbor": [
                            {
                                "attribs": {
                                    "direction": "E",
                                    "name": "Austria"
                                }
                            },
                            {
                                "attribs": {
                                    "direction": "W",
                                    "name": "Switzerland"
                                }
                            }
                        ],
                        "rank_number": "1"
                    },
                    {
                        "attribs": {
                            "name": "Singapore"
                        },
                        "year": "2011",
                        "gdppc": "59900",
                        "neighbor": {
                            "attribs": {
                                "direction": "N",
                                "name": "Malaysia"
                            }
                        },
                        "rank_number": "4"
                    }
                ]
            }
        }

        root = Element('data')
        country1 = SubElement(root, 'country', attrib={"name": "Liechtenstein"})
        year1 = SubElement(country1, 'year')
        year1.text = "2008"
        gdppc1 = SubElement(country1, 'gdppc')
        gdppc1.text = "141100"
        rank1 = SubElement(country1, 'rankNumber')
        rank1.text = "1"
        neighbor1 = SubElement(country1, 'neighbor', attrib={"direction": "E", "name": "Austria"})
        neighbor2 = SubElement(country1, 'neighbor', attrib={"direction": "W", "name": "Switzerland"})

        country2 = SubElement(root, 'country', attrib={"name": "Singapore"})
        year2 = SubElement(country2, 'year')
        year2.text = "2011"
        gdppc2 = SubElement(country2, 'gdppc')
        gdppc2.text = "59900"
        rank2 = SubElement(country2, 'rankNumber')
        rank2.text = "4"
        neighbor3 = SubElement(country2, 'neighbor', attrib={"direction": "N", "name": "Malaysia"})

        catalog_number = SubElement(root, 'catalogNumber') # Empty element
        self.root = root

    def test_camel_to_snake_all_caps_word(self):
        """
        Check if an all caps word in the middle gets underscores placed around it correctly.
        """
        self.assertEqual(XMLDocParser._camel_to_snake("testTESTTest"), "test_test_test")

    def test_camel_to_snake_basic(self):
        """
        Check if a basic camelCase name is converted correctly.
        """
        self.assertEqual(XMLDocParser._camel_to_snake("testTest"), "test_test")

    def test_camel_to_snake_numbers(self):
        """
        Check if numbers near the underscore insertion cause a problem.
        """
        self.assertEqual(XMLDocParser._camel_to_snake("test9Test"), "test9_test")

    def test_camel_to_snake_leading_cap(self):
        """
        Make sure an underscore doesn't get erroneously added to the start when it leads with a
        capital letter.
        """
        self.assertEqual(XMLDocParser._camel_to_snake("TestTest"), "test_test")

    def test_dict_to_json_file(self):
        """
        Make sure the dict is correctly written to file as json.
        """
        expected = json.dumps(self.dict_obj, indent=2)
        temp_path = tempfile.mkstemp()[1]
        XMLDocParser._dict_to_json_file(self.dict_obj, temp_path)
        with open(temp_path, 'r') as json_out:
            result = json_out.read()
        self.assertEqual(result, expected)

    def test_tree_to_dict(self):
        """
        Create an XML document and parse it with tree_to_dict. The output should match our expected
        self.dict_obj.
        """
        self.assertEqual(XMLDocParser._tree_to_dict(self.root), self.dict_obj)

    def test_parse_search_tag(self):
        """
        Test parsing with apriori knowledge of the xml structure.
        """
        search_tag = "country"
        expected = self.dict_obj
        temp_path = tempfile.mkstemp()[1]
        with open(temp_path, 'w') as xml_out:
            xml_out.write(tostring(self.root))
        xml_parser = XMLDocParser()
        xml_parser.parse(temp_path, search_tag=search_tag)
        os.remove(temp_path)
        self.assertEqual(xml_parser.dict, expected)

    def test_parse_standard(self):
        """
        Test parsing without apriori knowledge of the xml structure.
        """
        expected = self.dict_obj
        temp_path = tempfile.mkstemp()[1]
        with open(temp_path, 'w') as xml_out:
            xml_out.write(tostring(self.root))
        xml_parser = XMLDocParser()
        xml_parser.parse(temp_path)
        os.remove(temp_path)
        self.assertEqual(xml_parser.dict, expected)

    def test_tree_to_dict_omit_empty_element(self):
        """
        Test omission of empty elements. Note that the parent element, which then becomes empty,
        is not omitted.
        """
        root = Element('data')
        catalog_number = SubElement(root, 'catalogNumber') # Empty element
        self.assertEqual(XMLDocParser._tree_to_dict(root), {'data': {}})

    def test_tree_to_dict_attributes(self):
        """
        Test element attributes.
        """
        root = Element('data')
        sub = SubElement(root, 'sub', attrib={"direction": "E", "name": "Austria"})

        expected = {
            'data': {
                'sub': {
                    'attribs': {
                        'direction': 'E',
                        'name': 'Austria'
                    }
                }
            }
        }
        self.assertEqual(XMLDocParser._tree_to_dict(root), expected)

    def test_tree_to_dict_group_elements(self):
        """
        Test grouping multiple elements.
        """
        root = Element('data')
        sub1 = SubElement(root, 'sub')
        sub1.text = 'sub1'
        sub2 = SubElement(root, 'sub')
        sub2.text = 'sub2'
        expected = {
            'data': {
                'sub': ['sub1', 'sub2']
            }
        }
        self.assertEqual(XMLDocParser._tree_to_dict(root), expected)

    def test_rec_inject_list(self):
        """
        Test recursive injection of openfda information into the xml_parser dict object when the
        mock dict contains a list.
        """
        mock_dict = {
            "device": [
                {
                    "product_codes": {
                        "fda_product_code": {
                            "product_code": "JEY",
                            "product_code_name": "Plate, Bone"
                        }
                    }
                },
                {
                    "product_codes": {
                        "fda_product_code": {
                            "product_code": "JEY",
                            "product_code_name": "Plate, Bone"
                        }
                    }
                }
            ]

        }
        expect = "DE|DE|JEY|Plate, Bone|2||N|N||872.4760|1|||||Y|N"
        fda_class = FDAClassificationParser()
        fda_class.get = MagicMock(return_value=expect)
        fda_class.rec_inject(mock_dict)
        self.assertTrue("DE|DE|JEY|Plate, Bone|2||N|N||872.4760|1|||||Y|N" in mock_dict['device'][0]['product_codes']['fda_product_code']['openfda'])
        self.assertTrue(len(mock_dict['device'][0]['product_codes']['fda_product_code']['openfda']) == 1)


    def test_rec_inject_list(self):
        """
        Test recursive injection of openfda information into the xml_parser dict object when the
        mock dict contains a list.
        """
        mock_dict = {
            "device": {
                "product_codes": {
                    "fda_product_code": [
                        {
                            "product_code": "NKB",
                            "product_code_name": "Orthosis, Spinal Pedicle Fixation, For Degenerative Disc Disease"
                        },
                        {
                            "product_code": "MNI",
                            "product_code_name": "Orthosis, Spinal Pedicle Fixation"
                        },
                        {
                            "product_code": "MNH",
                            "product_code_name": "Orthosis, Spondylolisthesis Spinal Fixation"
                        },
                        {
                            "product_code": "KWQ",
                            "product_code_name": "Appliance, Fixation, Spinal Intervertebral Body"
                        },
                        {
                            "product_code": "KWP",
                            "product_code_name": "Appliance, Fixation, Spinal Interlaminal"
                        }
                    ]
                }
            }
        }
        expect = "DE|DE|JEY|Plate, Bone|2||N|N||872.4760|1|||||Y|N"
        fda_class = FDAClassificationParser()
        fda_class.get = MagicMock(return_value=expect)
        fda_class.rec_inject(mock_dict)
        result = mock_dict['device']['product_codes']['fda_product_code'][0].get('openfda')
        self.assertTrue(expect in result)

    def test_rec_inject_dict(self):
        """
        Test recursive injection of openfda information into the xml_parser dict object.
        """
        mock_dict = {
            "product_codes": {
                "fda_product_code": {
                    "product_code": "JEY",
                    "product_code_name": "Plate, Bone"
                }
            }
        }
        fda_class = FDAClassificationParser()
        fda_class.get = MagicMock(return_value="DE|DE|JEY|Plate, Bone|2||N|N||872.4760|1|||||Y|N")
        fda_class.rec_inject(mock_dict)
        self.assertTrue('openfda' in mock_dict['product_codes']['fda_product_code'])

    def test_inject_project_code(self):
        """
        Test recursive injection of openfda information into the xml_parser dict object.
        """
        mock_dict = {
            "product_codes": {
                "fda_product_code": {
                    "product_code": "JEY",
                    "product_code_name": "Plate, Bone"
                }
            }
        }
        fda_class = FDAClassificationParser()
        fda_class.get = MagicMock(return_value="DE|DE|JEY|Plate, Bone|2||N|N||872.4760|1|||||Y|N")
        xml_parser = XMLDocParser(fda_class)
        xml_parser._dict = MagicMock(return_value=mock_dict)
        fda_class.rec_inject(mock_dict)
        self.assertTrue('openfda' in mock_dict['product_codes']['fda_product_code'])

    def test_foi_get(self):
        mock_dict = {'JEY': 'TEST'}
        index_field = "PRODUCTCODE"
        class_file = 'foiclass.txt'
        class_parser = FDAClassificationParser(index_field)
        class_parser.parse(class_file)
        self.assertTrue('JEY' in class_parser._dict)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='CLI argument parser.')
    arg_parser.add_argument('--verbose', help='Run in verbose mode.', action='store_true')
    arg_parser.set_defaults(verbose=False)
    args = arg_parser.parse_args()
    if args.verbose:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestXMLParser)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()
