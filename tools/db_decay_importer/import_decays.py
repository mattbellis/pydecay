from pydecay.db import *
from pydecay import graphphys
import sys
from decays import decay_root

# Assumes we have a 'converters' submodule within the database module,
# and that DBTypeConverter is among the converters in it
__import__(PARTICLE_TYPE.__module__.__name__, fromlist=['converters'])
PARTICLE_TYPE.__module__.converters.DBTypeConverter().convert( decay_root )