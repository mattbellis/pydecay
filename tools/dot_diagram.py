#!/usr/bin/env python

from pydecay.converters.visualizers import PydotVisualizer
from pydecay import graphphys
from optparse import OptionParser

def main(argv):
    parser = OptionParser()
    parser.add_option("-o", "--out", dest="outfile_name", default=None,
                      help='Name of output file.')
    parser.add_option("-l", "--html", dest="html_labels", action="store_true", default=True,
                      help="Use Dot 2.x's fancy HTML labels to render parameters in output.")
    parser.add_option("-n", "--no-html", dest="html_labels", action="store_false",
                      help="Don't use Dot 2.x's fancy HTML labels to render parameters in output.")
    parser.add_option("--format", dest="output_format", default='png',
                      help='File extension of the output format (must be one of the output formats supported by Dot).'
                            + 'The filename will be corrected if necessary to include this extension.'
                            + 'The default format is png.')
    
    (options, args) = parser.parse_args(argv)

    infile_name = args[1]

    g = graphphys.get_parser().parseFile(infile_name)

    converter = PydotVisualizer(options.html_labels)
    if options.outfile_name != None:
        converter.convert_to_file(g, options.outfile_name, options.output_format)
    else:
        diagram = converter.convert(g)
        print diagram.__getattribute__('create_' + options.output_format)()

if __name__ == '__main__':
    import sys
    main(sys.argv)
