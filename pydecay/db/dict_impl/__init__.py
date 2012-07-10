'''
This module defines a database implementation based on Python dictionaries.
It is primarily useful if either you don't have Django installed, you just
don't want to bother with a heavyweight relational DBMS, or you want to try
a small custom database just to see what happens if you change some things around.

This database implementation must be populated by client code. For an example of how
to do this, see examples/dict_db_info.py.
'''

from pydecay.db import DoesNotExist, ParticleType as DB_ParticleType, DecayMode as DB_DecayMode

class OverriddenDictionary(dict):
    ''' A placeholder class for code common between KeyInclusiveDict and DotDbDictionary.
        Overrides the methods that create new dictionaries, such that any subclass of
        OverriddenDictionary can be used just like a regular dict.  
    '''
    
    def copy(self):
        ''' See dict.copy. '''
        
        return self.__class__( dict.copy(self) )
    
    @classmethod # Needs to be a classmethod because it's meant to be accessible from the
                 # class name, but we need to know what class we're creating.
    def fromkeys(klass, keys, default=None):
        ''' See dict.fromkeys. '''
        return klass( dict.fromkeys(keys, default) )

class KeyInclusiveDict(OverriddenDictionary):
    ''' A dictionary that modifies objects it returns by setting a particular attribute on
        them to the value of the key used to fetch that object.
        This is useful for making a ParticleType returned by particles[name] know the name
        by which it was fetched, preventing the need for repeating the names in code. ''' 

    _key_attribute_name = 'name'
                
    def __getitem__(self, key):
        result = dict.__getitem__(self, key)
        result.__setattr__(self._key_attribute_name, key)
        return result

class DotDbDictionary(OverriddenDictionary):
    ''' A dictionary that can be accessed via the .key syntax, i.e. mydict.key has the
        same effect as mydict[key].
    '''
    def __getattr__(self, key):
        try:
            return self[key]
        except:
            return dict.__getattribute__(self, key)

class ParticleType(DB_ParticleType, DotDbDictionary):
    ''' A .key-accessible dictionary for holding particle information. '''
    
    ''' The global dictionary of particle information. '''
    particles = KeyInclusiveDict()
    
    @staticmethod
    def get_type_for_name(type_name):
        ''' See db.ParticleType.get_type_for_name. '''
        
        try:
            return ParticleType.particles[type_name]
        except KeyError, e:
            raise DoesNotExist(*e.args)

    # Use default implementation of get_types_for_names
    
class DecayMode(DotDbDictionary, DB_DecayMode):
    ''' A .key-accessible dictionary for holding decay information. '''
    
    ''' The global dictionary of decay information. '''
    decays = {}

    def __init__(self, *args, **kwargs):
        DotDbDictionary.__init__(self, *args, **kwargs)
        self['products'] = ParticleType.get_types_for_names( self['products'] )
    
    @staticmethod
    def get_mode_for_particles(initial, products, angular_momentum=None):
        ''' See db.DecayMode.get_mode_for_particles. '''
        
        try:
            for decay_mode in DecayMode.decays[initial.type]:
                if (set([p.type for p in decay_mode.products]) == set([p.type for p in products])
                    ) and angular_momentum == decay_mode.get('angular_momentum', None):
                    return decay_mode 
        except KeyError:
            pass
        
        raise DoesNotExist('No decay found for specified particles')
