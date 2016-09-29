#!/usr/bin/env python
import argparse
from doc_parser import XMLDocParser
from foi import FDAClassificationParser


__author__ = "Jonathan Sage"
__email__ = "jsage8@gmail.com"


def main(xml_file, json_file, class_file, index_field, search, tag):
    if class_file is not None:
        class_parser = FDAClassificationParser(index_field)
        class_parser.parse(class_file)
    else:
        class_parser = None
    if not search:
        tag = None
    xml_parser = XMLDocParser(class_parser)
    xml_parser.parse(xml_file, search_tag=tag)
    xml_parser.inject_project_code()
    json_out = xml_parser.json
    xml_parser.to_json_file(json_file, pretty=True)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='CLI argument parser.')
    arg_parser.add_argument('--xml', help='Expects the path to an xml file.', required=True)
    arg_parser.add_argument('--json', help='Expects the path to an output json file.', required=True)
    arg_parser.add_argument('--classification', help='Expects the path to an FDA classification file.')
    arg_parser.add_argument(
        '--class_field',
        help='Expects the classification field used to index each classification line.',
        default="PRODUCTCODE"
    )
    arg_parser.add_argument(
        '--no_search',
        help='Assume nothing about the xml data structure. Increases memory usage.',
        action='store_true'
    )
    arg_parser.add_argument(
        '--tag',
        help='If --search use this arg to provide the tag to search by. Defaults to device.',
        default="device"
    )
    args = arg_parser.parse_args()
    xml_file = args.xml
    json_file = args.json
    class_file = args.classification
    index_field = args.class_field
    search = not args.no_search
    tag = args.tag
    main(xml_file, json_file, class_file, index_field, search, tag)
