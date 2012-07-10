#!/usr/bin/env python

import sys
from optparse import OptionParser

from pydecay import graphphys
from converters import BtmTclConverter, visualizers


################################################################################
################################################################################
def main(argv):

    #### Command line variables ####
    parser = OptionParser()
    parser.add_option("--outfile", dest="outfile_name", default=None,
                      help='Name of output file.')

    (options, args) = parser.parse_args()

    infile_name = args[0]

    g = graphphys.get_parser().parseFile(infile_name)
    
    if options.outfile_name != None:
        BtmTclConverter().convert_to_file(g, options.outfile_name)
    else:
        print BtmTclConverter().convert(g)

#    # Create the image of this decay chain
#    if options.outfile_name != None:
#        outfile_name = "%s" % (options.outfile_name)
#    else:
#        outfile_name = 'default'
#    visualizers.PydotVisualizer(html_labels=False).visualize_to_file(g, outfile_name)

################################################################################
################################################################################

################################################
if __name__ == "__main__":
    main(sys.argv)
