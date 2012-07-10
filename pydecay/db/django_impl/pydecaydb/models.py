from django.db import transaction
from django.db.models import *
from django.db.utils import IntegrityError
from pydecay.db import DecayMode as DB_DecayMode, ParticleType as DB_ParticleType # Avoids circular import issues
from pydecay.db import DoesNotExist
from pydecay.settings import BRANCHING_FRACTION_PARAM
from warnings import warn
import csv


def list_to_dict_with_counts(l):
    ''' @param l: an iterable of values.
        @return: a dictionary whose keys are the unique values of l and whose values
                 are the number of times each key appeared in l.
    '''
    
    with_counts = {}
    for item in l:
        prev_count = with_counts.get(item, 0)
        with_counts[item] = prev_count + 1
    return with_counts
    
#######################################
## PDT-style information tables      ##
#######################################

class DecayMode(Model, DB_DecayMode):
    ''' Represents a decay mode in the database. '''
    
    initial = ForeignKey('ParticleType', related_name='decay_modes', null=False)
    products = ManyToManyField('ParticleType', related_name='decay_parents', through='ProductSetMembership')
    branching_fraction = FloatField(null=True, default=None)
    angular_momentum = IntegerField(default=None, null=True)
    
    @transaction.commit_on_success
    def add_products(self, products):
        ''' Add product particles to a decay, modifying counts of existing decay
            products as necessary.
            @param products: an iterable of ParticleType objects.
        '''
        
        products_with_counts = list_to_dict_with_counts(products)
        existing_memberships = ProductSetMembership.objects.filter(particle_type__in=products,
                                                                   decay_mode=self)
        
        for existing_membership in existing_memberships:
            ptype = existing_membership.particle_type
            if ptype in products:
                # Removing from products_with_counts here means only product types for
                # which the current count is 0 will be added later
                existing_membership.count += products_with_counts.pop(ptype)
                existing_membership.save()
            
        self.productsetmembership_set.add( *[ProductSetMembership(particle_type=p, count=c)
                                                         for p,c in products_with_counts.iteritems()] )
        
    @staticmethod
    def get_mode_for_particles(initial, products, angular_momentum=None):
        ''' See pydecay.db.DecayMode.get_mode_for_particles. '''
        
        product_types = list_to_dict_with_counts(products)
        
        query = DecayMode.objects.filter(initial=initial)
        if angular_momentum:
            query = query.filter(angular_momentum=angular_momentum)

        # Make sure each product we're looking for is linked to this decay via a
        # ProductSetMembership entry with the correct count            
        for product_type, count in product_types.iteritems():
            query = query.filter(products=product_type, productsetmembership__count=count )
        
        # Exclude any decays that have products other than those we're looking for
        query = query.exclude( products__in=ParticleType.objects.exclude(id__in=[x.id for x in product_types.keys()]) )
        
        try:
            return query.distinct().get()
        except DecayMode.DoesNotExist, e:
            raise DoesNotExist(*e.args)
    
    def __repr__(self):
        return '<Decay mode: %s -> %s>' % (self.initial.name,
                                           ['%s x %d' % (repr(psm.particle_type), psm.count) for psm
                                            in ProductSetMembership.objects.filter(decay_mode=self)])

class ParticleBaseType(Model):
    ''' Represents the information about a particle type that is common between that type and its conjugate. '''

    charge = DecimalField(max_digits=2, decimal_places=1, default=0)
    mass = FloatField()
    mass_err_plus = FloatField()
    mass_err_minus = FloatField()
    width = FloatField(default=0)
    width_err_plus = FloatField()
    width_err_minus = FloatField()
    spin = DecimalField(max_digits=2, decimal_places=1, default=None, null=True)
    pdg_id = IntegerField(null=True)

class ParticleType(Model, DB_ParticleType):
    ''' Represents a particle type in the database. This class is designed to look as though it possesses
        all the attributes of ParticleBaseType, but in fact it just forwards these attributes on to the
        ParticleBaseType linked by the base_type foreign key.
    '''
    
    class Meta:
        # Only allow two types -- conjugate and non-conjugate -- for each base type 
        unique_together = ('base_type', 'is_conjugate_type')

    name = CharField(max_length=50, unique=True)
    base_type = ForeignKey(ParticleBaseType)
    is_conjugate_type = BooleanField(default=False) # Indicates whether or not charges should be flipped

    ####################################################################################################
    ## Methods for making objects of this class act like they have all the data from ParticleBaseType ##
    ####################################################################################################
        
    def __init__(self, *args, **kwargs):
        self.dirty_base_fields = {}
        super(ParticleType, self).__init__(*args, **kwargs)
        
    def save(self):
        if len(self.dirty_base_fields) > 0:
            print self.dirty_base_fields
            base = self.base_type
            
            if self.is_conjugate_type:
                # If charge has been set, we need to reverse it for storing on the base type
                try:
                    charge = self.dirty_base_fields.pop('charge')
                    base.charge = -charge
                except KeyError:
                    pass
            
            for name, value in self.dirty_base_fields.iteritems():
                base.__setattr__(name, value)
            base.save()
            
            self.dirty_base_fields.clear()
        
        super(ParticleType, self).save()
    
    def __getattr__(self, attrname):
        if attrname != 'id' and attrname in ParticleBaseType._meta.get_all_field_names():
            if self.dirty_base_fields.has_key(attrname):
                return self.dirty_base_fields[attrname]
            else:
                attrval = self.base_type.__getattribute__(attrname)
                if self.is_conjugate_type and attrname == 'charge': # The effect of being a conjugate is swapped charge
                    return -attrval
                else:
                    return attrval 
            
        else:
            return super(ParticleType, self).__getattribute__(attrname)
        
    def __setattr__(self, attrname, attrval):
        if attrname != 'id' and attrname in ParticleBaseType._meta.get_all_field_names():
            self.dirty_base_fields[attrname] = attrval
        else:
            super(ParticleType, self).__setattr__(attrname, attrval) 


    #######################################
    ## Real class methods                ##
    #######################################

    @transaction.commit_on_success
    def add_decay_mode(self, products, branching_fraction=None):
        ''' @param products: an iterable of ParticleType objects
            @param branching_fraction: the branching fraction of this decay mode; if not supplied, 
                                       defaults to DecayMode.branching_fraction's default
        '''
        
        # For some reason, putting the actual value as the actual default causes REALLY weird
        # things to happen to DecayType queries, so we'll just use None to indicate default
        if branching_fraction is None:
            branching_fraction = DecayMode._meta.get_field_by_name('branching_fraction')[0].default

        dec_type = self.decay_modes.create(branching_fraction=branching_fraction)
        dec_type.add_products(products) # This causes a commit
        return dec_type
        
    @staticmethod
    def get_type_for_name(name):
        ''' See pydecay.db.ParticleType.get_type_for_name. '''
        
        try:
            return ParticleType.objects.get(name=name)
        except ParticleType.DoesNotExist, e:
            raise DoesNotExist(*e.args)
    
    
    ## There ought to be a way to implement get_types_for_names efficiently using SQL,
    ## but I don't have time to figure it out. The one below doesn't handle duplicate
    ## product types properly.
    
#    @classmethod
#    def get_types_for_names(ptype_class, names):
#        ''' See pydecay.db.ParticleType.get_types_for_names.
#            For this database implementation, it is more efficient to perform one filter
#            operation for this information than to repeatedly call get_type_for_name.
#        '''
#        
#        return ptype_class.objects.filter(name__in=names)
    
    @staticmethod
    @transaction.commit_on_success
    def import_from_pdg_csv(path_to_csv, flush_old=True):
        ''' Imports the PDG's CSV file of particle data from 2009 (http://pdg.lbl.gov/2009/mcdata/mass_width_2008.csv).
            This should be upgraded to import the latest (2010) version.
        '''
        
        def correct_charge(charge_val):
            charge_val = charge_val.strip()
            if charge_val == '+':
                return '1'
            elif charge_val == '-':
                return '-1'
            elif charge_val == '++':
                return '2'
            elif charge_val == '--':
                return '-2'
            else:
                return str( eval(charge_val + '.0', {"__builtins__":None}, {}) )
            
        def correct_pdg_id(id):
            stripped = id.strip()
            if stripped == '':
                return None
            return stripped # Can't hurt to kill the whitespace
        
        def charge_conjugate_name(name, a_value, charge_suffix, spin=''):
            def flip_suffix(charge_suffix):
                if charge_suffix.startswith('+'):
                    return charge_suffix.replace('+', '-')
                else:
                    return charge_suffix.replace('-', '+')
            
            a_value = a_value.strip()
            if a_value == 'B': # antiparticle name is regular name with charge flipped
                return name + flip_suffix(charge_suffix)
            elif a_value == 'F': # antiparticle name is regular name with 'bar' stuck in and charge flipped
                # Neutral mesons should not have 'bar' added into their names, PDG's protestations aside
                if charge_suffix != '0' and spin != None and spin.find('/') == -1:
                    return name + flip_suffix(charge_suffix)
                else:
                    paren_loc = name.find('(')
                    if paren_loc == -1:
                        paren_loc = len(name)
                    return name[:paren_loc] + 'bar' + name[paren_loc:] + flip_suffix(charge_suffix)
            else: # particle is its own antiparticle
                return name + charge_suffix
            
        def get_spin(spin_str):
            if spin_str.find('?') != -1:
                return None
            try:
                slash_start = spin_str.find('/2') 
                if slash_start != -1:
                    return '%d.5' % ( int(spin_str[:slash_start]) / 2 )
                else:
                    return str(int(spin_str))
            except ValueError:
                return None
        
        if flush_old:
            ParticleBaseType.objects.all().delete() # This should delete all the ParticleTypes as well
        
        reader = csv.reader( open(path_to_csv, 'rb'), skipinitialspace=True )
        
        names_without_charge = ('u', 'd', 's', 'c', 'b', 't', 'K0S', 'K0L')
        
        for i, row in enumerate(reader):
            try:
                name = row[-2].strip()
                spin = get_spin(row[8])
                
                if name in names_without_charge:
                    conj_name = charge_conjugate_name(name, row[-7], '')
                else:
                    suffix = row[-5].strip()
                    conj_name = charge_conjugate_name(name, row[-7], suffix, spin)
                    name += suffix
                    
                charge = correct_charge(row[-5])
                base = ParticleBaseType(charge=charge, mass=row[0],
                                        mass_err_plus=row[1], mass_err_minus=row[2], width=row[3],
                                        width_err_plus=row[4], width_err_minus=row[5], spin=spin,
                                        pdg_id=correct_pdg_id(row[-6]) )
                base.save()
                
                try:
                    ParticleType(base_type=base, name=name).save()
                    if conj_name != name: # We have a separate conjugate type
                        try:
                            ParticleType(base_type=base, name=conj_name, is_conjugate_type=True).save()
                        except IntegrityError:
                            warn("Ignoring repeated conjugate particle %s" % conj_name)
                except IntegrityError:
                    base.delete()
                    warn("Ignoring repeated particle type %s" % name)
            except IndexError:
                warn("Skipping badly formatted row %d" % i)
    
    def __repr__(self):
        return '<Particle type: %s>' % self.name

class ProductSetMembership(Model):
    ''' An intermediate model to track the DecayMode/ParticleType many-to-many relationship. '''
    
    class Meta:
        # Record each product type only once per decay mode;
        # for multiple products of that type, the count field should be incremented.
        unique_together = ('decay_mode', 'particle_type')
    
    decay_mode = ForeignKey(DecayMode)
    particle_type = ForeignKey(ParticleType)
    count = IntegerField(default=1)


#######################################
## Instance tables                   ##
#######################################

class LazyParamDictionary(object):
    ''' A dictionary-like class for representing arbitrary name/value parameters that are stored
        in a database as InstanceParam objects. Nested parameters are loaded lazily, i.e. only when
        accessed, or when the whole object is converted to a dictionary.
    '''
    
    def __init__(self, parent_object, param_instances):
        self.nested = {}
        self.held_values = {}
        self.parent_object = parent_object
        
        for param in param_instances:
            if param.value is None:
                self.nested[param.name] = param
            else:
                self.held_values[param.name] = param
                
    def get_param_class(self):
        ''' @return: the type of stored parameter (presumably an InstanceParam database model) this dictionary represents. '''
        if isinstance(self.parent_object, InstanceParam):
            return self.parent_object.__class__
        else:
            return self.parent_object.param_class
    
    def __getitem__(self, key):
        if self.nested.has_key(key):
            return LazyParamDictionary(self.nested[key], self.nested[key].child_params.all() )
        else:
            return self.held_values[key].value
        
    def update(self, new_dict):
        ''' Note that this operation is NOT atomic: if an exception occurs in updating
            one parameter, all previously updated parameters will stay changed. '''
        for key, value in new_dict.iteritems():
            self[key] = value
    
    @transaction.commit_on_success
    def __setitem__(self, key, value):
        if not isinstance(value, dict) and not isinstance(value, LazyParamDictionary) and self.held_values.has_key(key):
            p = self.held_values[key]
            p.value = value
            p.save()
        else:
            # Delete parameter if present either as compound or simple
            try:
                self.held_values.pop(key).delete()
            except KeyError:
                try:
                    self.nested.pop(key).delete()
                except KeyError:
                    pass
            
            self.nested[key] = DecayElementInstance.set_params( {key:value},
                                                             self.get_param_class(),
                                                             self.parent_object 
                                                             )[0]
                                           
    def __delitem__(self, key):
        try:
            self.nested.pop(key).delete()
        except KeyError:
            self.held_values.pop(key).delete() # Will raise a KeyError if not present
            
    def has_key(self, key):
        return self.nested.has_key(key) or self.held_values.has_key(key)

    def to_dict(self):
        ''' @return: a normal dict version of this dictionary with all subparameters stored locally. '''
        values = {}
        for name, param in self.held_values.iteritems():
            # We convert everything to non-unicode strings b/c these may be used as kwargs
            values.update({str(name): str(param.value)})
        values.update( InstanceParam.instances_as_map( self.nested.values() ) )
        return values
        
    def __repr__(self):
        return '<%s object: %s>' % (self.__class__.__name__, str( self.to_dict() ) )


class InstanceParam(Model):
    ''' Abstract class representing a parameter on an instance of something - a decay instance,
        a particle instance, etc. It defines some common functions for such paramter models.
        
        To allow for subparameters, each InstanceParam has a parent_param field and an instance
        field. parent_param is a reference to the parameter that this is a subparameter of; instance
        is a reference to the object instance that this is a direct parameter of. Exactly one of these
        must be set: every name/value pair is either a direct parameter of an object or a subparameter
        of another parameter, but not both.
        
        If a given InstanceParam has subparameters, its value field should be set to None.
    '''
    class Meta:
        abstract = True

    parent_param = ForeignKey('self', related_name='child_params', null=True)
    name = CharField(max_length=100)
    value = CharField(max_length=100, blank=True, null=True)
    instance = None # Field to be overridden
    
    def get_real_value(self):
        ''' @return: the value of this parameter. If this parameter has subparameters, this will
                     construct a dictionary from the subparameters' real values and return that.
        '''
        if self.value is None:
            return self.instances_as_map( self.child_params.all() )
        else:
            return self.value
    
    @staticmethod
    def instances_as_map(instances):
        ''' @param instances: an iterable of InstanceParam objects.
            @return: a map whose keys are the names of the InstanceParam objects in instances
                     and whose values are the values of those objects.
        '''
        params = {}
        for inst_param in instances:
            params[inst_param.name] = inst_param.get_real_value()
        return params
    
    def __repr__(self):
        return "'%s': %s" % ( self.name, str( self.get_real_value() ) )
    

class ParticleInstanceParam(InstanceParam):
    ''' Model for the instance-parameters of ParticleInstance objects. '''
    instance = ForeignKey('ParticleInstance', null=True)


class DecayInstanceParam(InstanceParam):
    ''' Model for the instance-parameters of DecayInstance objects. '''
    instance = ForeignKey('DecayInstance', null=True)

    
class InstanceGroupParam(InstanceParam):
    ''' Model for the instance-parameters of InstanceGroup objects. '''
    instance = ForeignKey('InstanceGroup', null=True)

    
class DecayElementInstance(Model):
    ''' Represents a database table for some decay process element that has parameters.
        This class defines the operation of the 'params' attribute of such element models.
    '''
    
    param_class = None # To be overridden

    class Meta:
        abstract = True

    def __getattr__(self, attrname):
        if attrname == 'params':
            return LazyParamDictionary( self, self.get_params_set().all() )

        else:
            return Model.__getattribute__(self, attrname)        
        
    @transaction.commit_on_success
    def __setattr__(self, attrname, attrval):
        if attrname == 'params':
            self.get_params_set().all().delete()
            DecayElementInstance.set_params(attrval, self.param_class, self)
        else:
            Model.__setattr__(self, attrname, attrval)
        
    def get_params_set(self):
        return self.__getattribute__( self.param_class.__name__.lower() + '_set' )
    
    @staticmethod
    def set_params(params, param_class, parent):
        ''' Sets the parameters of parent to be params.
            @param params: a dictionary of parameters to be set.
            @param param_class: the type of parameter object to create for
                                each name/value pair in params.
            @param parent: the database object (either an InstanceParam or a DecayElementInstance)
                           whose parameters these are   
        '''
        
        ids = []
        for name, val in params.iteritems():
            p = param_class(name=name)
            if isinstance(parent, InstanceParam):
                p.parent_param = parent
            else:
                p.instance = parent
    
            def process_dict_val(p, val):
                p.value = None
                p.save()
                DecayElementInstance.set_params(val, param_class, p)
                
            if isinstance(val, LazyParamDictionary):
                process_dict_val( p, val.to_dict() )
            elif isinstance(val, dict):
                process_dict_val(p, val)
            else:
                p.value = val
                p.save()
            ids.append(p.id)
        return ids


class InstanceGroup(DecayElementInstance):
    ''' Database representation for pydecay.ProcessGroup. '''
    
    param_class = InstanceGroupParam

class ParticleInstance(DecayElementInstance):
    ''' Database representation for pydecay.Particle. '''
    
    type = ForeignKey(ParticleType)
    product_of = ForeignKey('DecayInstance', related_name='products', null=True)
    group = ForeignKey(InstanceGroup, related_name='root_particles', null=True, default=None)
    
    param_class = ParticleInstanceParam
    
#    ''' Whole-model validation '''
#    def clean(self):
#        if self.group != None and self.product_of != None:
#            raise ValidationError('A particle instance may not be associated with a group if it is not a root particle.')
#        
#    def save(self):
#        self.clean()
#        super(ParticleInstance, self).save()
    
    @transaction.commit_on_success
    def add_decay(self, products, **params):
        ''' Add a DecayInstance to this ParticleInstance.
            @param products: the ParticleInstance objects that are the products of this decay.
            @param params: the decay parameters.
        '''
        dec = DecayInstance(**params)
        self.decays.add(dec)
        dec.products = products
        return dec
    
    def __repr__(self):
        return '<Particle instance of type %s>' % self.type.name
    

class DecayInstance(DecayElementInstance):
    ''' Database representation for pydecay.Decay. '''
    
    initial = ForeignKey(ParticleInstance, related_name='decays')
    
    param_class = DecayInstanceParam

    def get_decay_mode(self):
        ''' @return: the DecayMode whose properties match those of this DecayInstance.
            @raise pydecay.db.DoesNotExist: if there is no DecayType matching this DecayInstance. 
        '''
        # TODO: Test me!!!! Especially on decay modes with repeated particle types!
        return DecayMode.get_mode_for_particles( self.initial.type, [p for p in self.products.all() ],
                                                  self.params.get('angular_momentum', None) )
    
    def get_branching_fraction(self):
        ''' @return: the branching fraction specified by BRANCHING_FRACTION_PARAM, if present, or the branching
                     fraction of the DecayType matching this decay otherwise. If no DecayType matches, returns None. '''
        if self.params.has_key(BRANCHING_FRACTION_PARAM):
            return float( self.params[BRANCHING_FRACTION_PARAM] )
        else:
            try:
                self.get_decay_mode().branching_fraction
            except DoesNotExist:
                return None
