#!/usr/bin/env python

from pydecay import *
from pydecay import graphphys

def find_bad_decays(particle):
    bad_decays = []
    for decay in particle.decays:
        # Make sure this isn't a generic decay before checking masses
        if len(decay.products) > 0 and sum([float(p.mass) for p in decay.products]) > float(particle.mass):
            bad_decays.append(decay)
        for p in decay.products:
            bad_decays += find_bad_decays(p)
            
    return bad_decays

def main(argv):
    infile_name = argv[1]
    g = graphphys.get_parser().parseFile(infile_name)

    bad_decays = []    
    for root in g.root_particles:
        bad_decays += find_bad_decays(root)
        
    if len(bad_decays) == 0:
        print 'All decays specified are kinematically possible.'
    else:
        for decay in bad_decays:
            message = 'Impossible decay specified: %s ->' % decay.parent.type
            for p in decay.products:
                message = ' '.join([message, p.type])
            print message

if __name__ == '__main__':
    import sys
    main(sys.argv)
