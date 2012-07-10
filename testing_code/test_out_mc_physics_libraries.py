#!/usr/bin/env python

import sys
from ROOT import *

from mc_physics_libraries import *

################################################################################
################################################################################
def main(argv):

    max = int(sys.argv[1])

    # Generate some events according to a BW distribution
    peak = 0.770
    width = 0.150
    # Generate over a range 0-2.0

    rnd = TRandom3()

    bw_max = breit_wigner_max(peak,width)

    n=0
    while n<max:

        # Generate random numbers from 0-2.0
        x = 2.0*rnd.Rndm()
        
        bw_val = breit_wigner(x,peak,width)

        test_val = bw_max*rnd.Rndm()

        if test_val<=bw_val:
            print x
            n += 1 


################################################################################
if __name__ == "__main__":
    main(sys.argv)


