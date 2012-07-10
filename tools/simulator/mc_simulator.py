#!/usr/bin/env python
#

################################################################################
# Import the needed modules
################################################################################
import os
import sys
from array import array

from pydecay import *
from pydecay import graphphys, db
from mc_physics_libraries import *
from ROOT import *


def gen_bw_val(particle_type):
    bw_max = breit_wigner_max( float(particle_type.mass), float(particle_type.width) )
    while(True):
        # Generate random numbers from 0-2.0
        x = 2.0*rnd.Rndm()
        bw_val = breit_wigner( x, float(particle_type.mass), float(particle_type.width) )        
        test_val = bw_max * rnd.Rndm()
        if test_val <= bw_val:
            return x

prob_lineshapes = {
    # Each shape name maps to a function f: Particle -> mass
    'BW' : lambda p: gen_bw_val( db.PARTICLE_TYPE_IMPL.get_type_for_name(p.type) )
}

################################################################################
# Return the masses of particles
################################################################################

def get_mass(particle):
    # Lineshape overrides any mass specified explicitly on the particle
    if hasattr(particle, 'lineshape'):
        return prob_lineshapes[ particle.lineshape ](particle)
    else:
        return particle.mass


################################################################################
################################################################################
if __name__ == '__main__':
    
    ################################################################################
    # Parse the command line options
    ################################################################################
    input_file = sys.argv[1]
    max_events = int(sys.argv[2])

    # print input_file
    # print max_events

    ################################################################################
    # Read the input file
    ################################################################################
    try:
        [root_particle] = graphphys.get_parser().parseFile( input_file )
    except ValueError: # Occurs if there are too many list elements in the return value
        raise Exception('Multiple root nodes not allowed in a simulation')


    rnd = TRandom3()

    ################################################################################
    # Walk the particle tree and check that the decays are all valid
    ################################################################################
    get_end_masses = lambda products: array('d', [ get_mass(x) for x in products ])

    # print get_end_masses
    # print get_mass(root_particle)

    initial_vector = TLorentzVector( 0.0, 0.0, 0.0, get_mass(root_particle) )
    event = TGenPhaseSpace()

    def validate_decay(decay):
        if decay is None:
            return
        
        products = decay.products
        end_masses = get_end_masses(products)
        n_products = len(end_masses)
        
        if not event.SetDecay(initial_vector, n_products, end_masses, ''):
            raise Exception('Kinematically invalid decay requested')
        for product in products:
            for decay in product.decays:
                validate_decay( decay )
    for decay in root_particle.decays:
        validate_decay(decay)


    ################################################################################
    # Generate the events
    ################################################################################


    def simulate_decay(particle, particle_vector):
        def weighted_choice(items, rand_func):
            # items is a list of tuples in the form (item, weight);
            # rand_func is a 1-argument function that takes an upper bound u
            # and returns a random number uniformly distributed between 0 and u

            weight_total = sum((item[1] for item in items))
            n = rand_func(weight_total) # Generates a random # between 0 and total weight
            for item, weight in items:
                if n < weight:
                    return item
                n = n - weight
            return item

        # Create a new event object for each level of the recursion stack so that particles
        # down the tree don't muck with results from this level of the tree
        event = TGenPhaseSpace() 

        # Start with defining the inital state as a particle at rest
        products = weighted_choice( [(d, d.prob) for d in particle.decays],
                                    lambda upper_bound: rnd.Rndm() * upper_bound
                                    ).products
            
        # print 'Simulating decay of %s (%f) to %s' % (particle.type, particle_vector.M(), [p.type for p in products])
        
        end_masses = get_end_masses(products)
        n_products = len(end_masses)

        event.SetDecay(particle_vector, n_products, end_masses, '')
        event.Generate()

        # print "end_masses: " 
        # print end_masses

        for i, product in enumerate(products):
            # If our decay products will decay further, don't print anything yet;
            # just recursively generate those products
            if len(product.decays) > 0:
                simulate_decay( product, event.GetDecay(i) )
            else:
                print "end state:", product.type
                end_vector = event.GetDecay(i)
                print "%f %f %f %f" % (end_vector.E(), end_vector.X(), end_vector.Y(), \
                                       end_vector.Z())

    for n in range(max_events):
        # Write the 4vector of the initial state
        print "-------------"
        print "initial:", root_particle.type
        print "%f %f %f %f" % (initial_vector.E(), initial_vector.X(), initial_vector.Y(), \
                               initial_vector.Z())
        
        simulate_decay(root_particle, initial_vector)
