from django.db import transaction, models
from django.db.models.fields import AutoField
from django.db.models.fields.related import RelatedField
from pydecay import *
from pydecay import db
from pydecay.converters import Converter
from warnings import warn

PARAM_NAMES_TO_COLUMN_NAMES = {BRANCHING_FRACTION_PARAM : 'branching_fraction'}
DATABASE_MODULE = db.PARTICLE_TYPE_IMPL.__module__ # Same module for both; arbitrarily chose particle

class DBInstanceConverter(Converter):
    ''' Converter for converting a decay tree to ParticleInstance/DecayInstance/etc. database entries. '''
    
    output_type = 'PyDecay database instance'
    
    def convert(self, obj):
        ''' Note: NOT atomic! '''
        
        if isinstance(obj, db.DECAY_MODE_IMPL.__module__.DecayElementInstance):
            return obj
        
        elif isinstance(obj, Particle):
            ptype = db.PARTICLE_TYPE_IMPL.get_type_for_name(obj.type)
            p = DATABASE_MODULE.ParticleInstance( type=ptype )
            p.save()
            p.params = obj.params
            for decay in obj.decays:
                dec = DATABASE_MODULE.DecayInstance( initial=p )
                dec.save()
                dec.params = decay.params
                
                dec.products = [self.convert(x) for x in decay.products]
            return p
        
        elif isinstance(obj, ProcessGroup):
            g = DATABASE_MODULE.InstanceGroup()
            g.save()
            db_particles = [self.convert(p) for p in obj.root_particles]
            g.root_particles = db_particles
            g.params = obj.params
            return g
        
        else:
            return self.convert( Converter.convert(self, obj) )
        
    def convert_to_file(self, *args, **kwargs):
        raise NotImplementedError("DB objects cannot be stored in a file")
            

class DBTypeConverter(Converter):
    ''' Converter for converting a decay tree to ParticleType/DecayMode database entries. '''
    
    output_type = 'PyDecay database type'
    
    ''' Wrapper to make conversion process atomic at the DB level '''
    @transaction.commit_on_success
    def convert(self, obj):
        return self.do_convert(obj)
    
    ''' Actual conversion method, which does not commit every time a recursive call succeeds '''
    def do_convert(self, obj, modified_ptypes=None):
        if modified_ptypes is None:
            modified_ptypes = set()
        
        if isinstance(obj, (db.PARTICLE_TYPE_IMPL, db.DECAY_MODE_IMPL) ):
            return obj
        
        elif isinstance(obj, Particle):
            try:
                ptype = db.PARTICLE_TYPE_IMPL.get_type_for_name(obj.type)
            except db.DoesNotExist:
                ptype = db.PARTICLE_TYPE_IMPL(name=obj.type)
            
            def try_to_set_attribute(db_obj, name, value):
                name = PARAM_NAMES_TO_COLUMN_NAMES.get(name, name)
                if name in db_obj._meta.get_all_field_names():
                    #print 'setting', name, 'to', value
                    db_obj.__setattr__(name, value)
                else:
                    warn('Could not set attribute %s to %s: only column names are allowed as parameters for DB types' %
                         (str(name), str(value) ) )
                    
            def clone_attributes(pydecay_obj, db_obj):
                for name, value in pydecay_obj.params.iteritems():
                    try_to_set_attribute(db_obj, name, value)                
                db_obj.save()
                
            clone_attributes(obj, ptype)

            for decay in obj.decays:
                try:
                    dec_type = db.DECAY_MODE_IMPL.get_mode_for_particles( obj.get_db_type(),
                                                  db.PARTICLE_TYPE_IMPL.get_types_for_names([p.type for p in decay.products]) )
                except db.DoesNotExist:
                    products = [self.do_convert(p, modified_ptypes) for p in decay.products]
                    dec_type = ptype.add_decay_mode(products)
                
                clone_attributes(decay, dec_type)
                
            return ptype
        
        elif isinstance(obj, ProcessGroup):
            types = []
            for p in obj.root_particles:
                types.append(self.do_convert(p))
            return types
        
        else:
            return self.convert( Converter.convert(self, obj) )
        
    def convert_to_file(self, *args, **kwargs):
        raise NotImplementedError("DB objects cannot be stored in a file")

''' Since the converter module cannot know in advance what the db class will be,
    it dynamically loads this converter as part of its builtin PyDecayConverter 
    if it finds it in the db module '''
class PyDecayConverter(Converter):
    output_type = 'PyDecay object'
    
    def convert(self, obj):
        if isinstance(obj, DATABASE_MODULE.ParticleInstance):
            p = Particle( obj.type.name, **obj.params.to_dict() )
            no_decay_specified = True
            for decay in obj.decays.all():
                no_decay_specified = False
                # Parents get set for free
                p.add_decay( [self.convert(p) for p in decay.products.all()],
                             decay.get_branching_fraction(),
                             **decay.params.to_dict() )
                
            return p
        
        else:
            # Do not call main Converter function...that was probably how we got here in the first place
            raise InvalidTypeError("Cannot convert %s object to %s" % ( type(obj).__name__), self.output_type )
