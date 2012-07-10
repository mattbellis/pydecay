''' This module provides a Django ORM-based implementation of the particle/decay
    database interface. It also provides functionality for storing and querying
    particle/decay "instances" -- that is, particles/decays users have actually
    created (e.g. via GraphPhys), with all their parameters.
    
    Because of Django's odd expectations for directory structure, the actual database
    implementation is stored under the pydecaydb package and just imported here. 
'''

import settings as project_settings
from django.conf import settings
if not settings.configured:
    settings.configure(**project_settings.__dict__) 
import pydecaydb
import sys
# For some reason, this is necessary to help Django find the app module
if not sys.modules.has_key('pydecaydb'):
    sys.modules['pydecaydb'] = pydecaydb

# Main stuff to be made available (meant to hide Django-specific module structure)
from pydecaydb.models import ParticleType, DecayMode, ParticleInstance, DecayInstance, InstanceGroup, DecayElementInstance
