''' This module defines an abstract database interface for PyDecay to use for
    looking up particle information. The classes defined in the top-level module
    always indicate that they have no information on any particle or decay.
    Any pair of classes implementing the interfaces given here can be used as databases.
    Which class is actually used by pydecay is configured by the
    pydecay.settings.PARTICLE_TYPE_IMPL and pydecay.settings.DECAY_MODE_IMPL
    settings.
    
    Implementation modules may also provide particle and decay instance classes,
    representing specific particles of a given type that users have actually specified
    in decays (e.g. particles from a GraphPhys simulation-configuration file). 
'''

import sys

class DoesNotExist(Exception):
    ''' An exception indicating that the requested information was not found in the database. '''

    pass

class ParticleType(object):
    ''' A common interface for retrieving particle information.
        Classes supporting this interface should provide both methods listed
        here, and should support the .property syntax for retrieving information
        from the returned objects (e.g. if get_type_for_name('pi+') returned x, 
        then x.mass should evaluate to the mass of the pi+ particle). All implementations
        should support at least the 'name' property (returning, e.g., 'pi+'), and several
        tools require 'mass' as well.
        Instances of ParticleType subclasses should be the actual containers
        for object information, i.e. x in the previous example would be an instance of
        the ParticleType subclass being used.
    ''' 

    @staticmethod
    def get_type_for_name(type_name):
        ''' @return: an object of whichever implementation-class for ParticleType is being used.
            @raise DoesNotExist: if there is no particle type matching this name.
        '''

        raise DoesNotExist("Unknown particle name '%s'" % type_name)
    
    @classmethod
    def get_types_for_names(klass, type_names):
        ''' @return: an iterable of instances of whichever implementation-class
                     for ParticleType is being used.
            @raise DoesNotExist: if one of type_names has no matching particle type.
        '''

        return [klass.get_type_for_name(name) for name in type_names]


class DecayMode(object):
    ''' A common interface for retrieving particle-to-products decay information. As with
        ParticleType, subclasses should provide the .property syntax for accessing
        decay properties (e.g. branching fraction).''' 

    @staticmethod
    def get_mode_for_particles(initial, products, angular_momentum=None):
        """
        Gets a decay mode with associated decay information given the parameters defining a
        decay. Expects particle type parameters to be objects of the type returned by
        ParticleInformation.get_type_for_name.
        @param initial: the initial particle type
        @param products: an iterable of final particle types
        @param angular_momentum: the total angular momentum of a decay process.
                                (There can be decays with identical initial/final states but
                                different intermediate angular momenta.)
        @raise DoesNotExist: if no decay type matches the parameters given.
        """
        
        raise DoesNotExist("No decay mode in database for %s to %s" % (initial.name, [p.name for p in products]) )


''' PARTICLE_TYPE_IMPL will be set to the database class supporting the ParticleType
    interface. Likewise for DECAY_MODE_IMPL.
    
    Thus, to access these classes via pydecay.db, use pydecay.db.PARTICLE_TYPE_IMPL and
    pydecay.db.DECAY_MODE_IMPL.
'''
from pydecay.settings import DATABASE_IMPL

if isinstance(DATABASE_IMPL, str):
    DATABASE_IMPL = __import__(DATABASE_IMPL, globals(), locals(), ['*'])
    PARTICLE_TYPE_IMPL = DATABASE_IMPL.__getattribute__('ParticleType')
    DECAY_MODE_IMPL = DATABASE_IMPL.__getattribute__('DecayMode')
else:
    (PARTICLE_TYPE_IMPL, DECAY_MODE_IMPL) = DATABASE_IMPL

