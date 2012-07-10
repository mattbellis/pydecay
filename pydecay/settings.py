'''
Settings for the pydecay framework. This is particularly useful for
setting up database options, including which database implementation
classes to use.
'''

''' Name of the parameter which should be considered a DB override for decay branching fraction. '''
BRANCHING_FRACTION_PARAM = 'fraction'

''' Name of the GraphPhys parameter that should override the particle name to indicate type. '''
TYPE_PARAM = 'type'

''' The symbol to use in visualizations to represent the products of a generic decay '''
GENERIC_PRODUCT_LABEL = '?'

''' The DB_... settings are used for the Django database implementation. '''
DB_NAME = '/home/jesse/Desktop/test.sqlite'
DB_ENGINE = 'django.db.backends.sqlite3'
# The other DB stuff isn't used with sqlite
DB_HOST = ''
DB_PORT = ''
DB_USER = ''
DB_PASSWORD = ''

''' This parameter should either be a pair of type objects (ParticleType, DecayMode),
    representing the particle type and decay mode types from the database implementation,
    or a string with the fully qualified name of a module containing classes by those names.
    The following package names are available in the default PyDecay distribution:
        * 'pydecay.db.django_impl' (relational database)
        * 'pydecay.db.dict_impl'   (dictionary-based "database")
        * 'pydecay.db'             (null implementation on which lookup always fails)
    For more information on each of these implementations, consult their respective definitions.    
 '''
DATABASE_IMPL = 'pydecay.db.dict_impl' 
