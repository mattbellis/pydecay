'''
This module defines the primary decay representation used throughout the PyDecay package.
Decay processes are represented as trees, with each particle represented by a node in the tree.
Each node (Particle object) can have multiple decays, which are assumed to be alternative subtrees. 
Every object in the tree, or the ProcessGroup objects used to group trees and global parameters,
has a 'params' attribute which contains the parameters set on this object (e.g. attributes set by the
[attrname=attrval] syntax in GraphPhys). 
'''

from settings import BRANCHING_FRACTION_PARAM
from db import DoesNotExist, PARTICLE_TYPE_IMPL, DECAY_MODE_IMPL

class DecayConsistencyError(Exception):
    pass

class DecayElement(object):    
    ''' Common code between various PyDecay tree components. This class implements
        the .attribute syntax for fetching dictionary parameters, and establishes
        the params dictionary attribute.
        
        Client code should be aware that if properties are fetched from params via the
        .attribute syntax, e.g. p.mass, the return value may need to be coerced to a float
        if it is to be used as such, since params stores parameter values as strings.
    '''
    
    def __init__(self, **params):
        if self.__class__ == DecayElement:
            raise NotImplementedError('This is an abstract class.')
        self.params = params # This will automatically be a copy, since the ** syntax creates new dicts

    def __getattr__(self, item):        
        ''' Attempts to fetch the given attribute from the params dictionary if the object doesn't have an
            attribute by that name. '''   

        try:
            return self.__getattribute__('params')[item]
        except KeyError:
            try: # This will fail if get_db_type is not defined for the subclass
                return self.get_db_type().__getattribute__(item)
            except DoesNotExist:
                return object.__getattribute__(self, item)

    def __setattr__(self, item, value):
        ''' Changes the value in the params dictionary if it's present; otherwise calls object.__setattr__. '''
        # Make sure we've been initialized sufficiently before trying to futz with params
        if hasattr(self, 'params') and object.__getattribute__(self, 'params').has_key(item):
            self.params[item] = value
        else:
            object.__setattr__(self, item, value)

    def add_param(self, name, value):
        ''' Add a new attribute to the params dictionary for this object. '''
        self.params.update({name: value})        

    def get_unique_name(self):
        ''' Gets a unique name for a decay object based on its object ID. If the node has a 'type'
            attribute, that will be included in the name. '''
            
        if hasattr(self, 'type'): # Having the type information in the Dot code could be helpful for debugging
            return '%s_%d' % (self.type, id(self))
        else:
            return '%d' % id(self)

class Particle(DecayElement):
    ''' Represents a single particle in a decay. Each particle has a type name (just a string), a
        list of Decay objects, and a params dictionary. The parent particle can also be retrieved
        via this mechanism. '''
        
    def __init__(self, type, **params):
        ''' @param type: The PDG-style name of the particle type (e.g. 'K*(892)+')
            @param params: Any name/value parameter pairs that should be set on this particle
        '''
        self.parent = None
        self.type = type
        self.decays = []
        super(Particle, self).__init__(**params)

    def set_decay(self, products, **params):
        ''' Deletes all current decays and replaces the list with one containing just the decay provided.
            @param products: The decay to replace with. Can be either a Decay object or an iterable of
                             Particle objects.
            @param params: The decay parameters. If products is a Decay object, any overlapping params
                           will be overridden by this dictionary.
        '''        
   
        self.products = []
        self.add_decay(products, **params)

    def add_decay(self, products, **params):
        ''' Adds a decay to the current list of decays. products and params arguments behave is in set_decay. '''
    
        if isinstance(products, Decay):
            products._check_product_parents()
            if self.parent:
                raise DecayConsistencyError(
                    'Decay already belongs to %s particle. Remove it from that particle before adding it to a different one.'
                        % self.parent.type)
            products.params.update(params)
        else:
            products = Decay(products, **params)
             
        self.decays.append(products)
        
        products.parent = self
        for product in products:
            product.parent = self
            
    def remove_decay(self, decay):
        ''' Removes the given decay from the current list of decays. This method should be used to perform
            this action, since otherwise the decay and its products may not have their parent attributes reset.
            @param decay: The Decay object to remove. '''
            
        self.decays.remove(decay)
        for p in decay.products:
            p.parent = None
        decay.parent = None

    def split_alternative_trees(self):
        ''' Splits the decay tree whose root particle is self into all its alternative trees. The resulting
            trees have no alternatives; the decays list of each particle in a tree returned by this method
            has a maximum length of 1.
            @return: A dictionary mapping each alternative decay tree (represented as a Particle cloned
                     from self) onto the total branching fraction for that decay tree.
        '''
    
        if len(self.decays) == 0:
            return {self: 1}
        
        alternatives_map = {}
        def add_product_set_alternatives(remaining_products, products_so_far, prob_so_far, decay_params):
            ''' For a given possible product set, this function goes through each product and clones it
                with its alternatives, multiplying the branching fractions along the way, then adding the
                set of these clones as an alternative subtree for self.
                If the branching fraction product cannot be computed, None will be recorded as the probability.
                @param remaining_products: a list of products' alternative-tree dictionaries whose probabilities
                                           have not yet been multiplied.
                @param products_so_far: a list of products whose probabilities have already been processed.
                @param prob_so_far: the multiplicative product of all the products in products_so_far.
                @param decay_params: the decay parameters to add when we finally create a Decay object for
                                     this product set.
            '''

            if len(remaining_products) == 0:
                p = self.clone(False)
                p.add_decay( products_so_far, **decay_params )
                alternatives_map[p] = prob_so_far
            else:
                next_prod_alternatives = remaining_products[0]
                for prod, prob in next_prod_alternatives.iteritems():
                    # Probability values may not be known
                    if prob is None or prob_so_far is None:
                        next_prob = None
                    else:
                        next_prob = prob_so_far * prob

                    add_product_set_alternatives(remaining_products[1:], products_so_far + [prod.clone(True)],
                                                 next_prob, decay_params)

        for decay in self.decays:
            products_with_probs = [product.split_alternative_trees() for product in decay]
            add_product_set_alternatives(products_with_probs, [], decay.get_branching_fraction(), decay.params)

        return alternatives_map
        
    def clone(self, clone_decay=True):
        ''' Deep-copy this Particle, including its parameters.
            @param clone_decay: If true, all alternative subtrees (i.e. decays) of this particle
                                will be cloned and attached to the particle clone.
        '''
        p = self.__class__(self.type, **self.params) # Calls constructor
        if clone_decay:
            p.decays = [decay.clone(p) for decay in self.decays]
        return p
    
    def get_db_type(self):
        ''' Get the database information object containing information about particles
            of this particle's type (i.e. whose type strings equal self.type). '''
        return PARTICLE_TYPE_IMPL.get_type_for_name(self.type)

    def __repr__(self):
        return '<Particle object: %s>' % self.type


class Decay(DecayElement):
    ''' A container for a list of decay products and a set of decay parameters.
    '''
    def __init__(self, products, **params):
        ''' @param products: any iterable of Particle objects.
            @param params: parameters for the Decay object.
        '''
        self.products = list(products)
        self._check_product_parents()
            
        self.params = params
        self.parent = None
        super(Decay, self).__init__(**params)
        
    def _check_product_parents(self):
        for p in self.products:
            if p.parent:
                raise DecayConsistencyError('Attempted to add a decay product that is already the product of another decay.')
    
    def clone(self, parent=None):
        ''' Create a clone of this Decay, cloning its products in the process.
            @param parent: the Particle whose cloning induced this method to be called, and
                           to which the parents of this decay and its products should be set.
        '''
        products = []
        for p in self:
            p = p.clone(True)
            products.append( p )
        d = self.__class__(products, **self.params)

        # Set parents now, rather than before, to prevent appears-twice-as-product check from complaining
        if parent:
            for p in products:
                p.parent = parent
            d.parent = parent
        
        return d
            
    def get_branching_fraction(self):
        ''' @return: the branching fraction of this Decay. Attempts to fetch the branching fraction 
                     from the database type of this Decay. The BRANCHING_FRACTION_PARAM can be used to
                     override the database. If the branching fraction cannot be determined, returns None.'''
        try:
            return float( self.__getattr__(BRANCHING_FRACTION_PARAM) )
        except AttributeError:
            try:
                return self.get_db_type().branching_fraction
            except DoesNotExist:
                return None #Unknown
    
    def get_db_type(self):
        ''' @return: The database decay mode type for this Decay. '''
        return DECAY_MODE_IMPL.get_mode_for_particles(PARTICLE_TYPE_IMPL.get_type_for_name(self.parent.type),
                                                 PARTICLE_TYPE_IMPL.get_types_for_names([p.type for p in self.products]) )
    
    def __iter__(self):
        ''' Allows iterating over the products of the Decay. '''
        return self.products.__iter__()
    
    def __repr__(self):
        repr = '%s -> ' % self.parent
        for i, p in enumerate(self.products):
            repr += str(p)
            if i < len(self.products) - 1:
                repr += ', '
        return repr
    
    def __len__(self):
        return len(self.products)

class ProcessGroup(DecayElement):
    ''' Represents a group of related decay trees (in fact, only one key), and any
        process-wide parameters. '''
    def __init__(self, root_particles=None, **params):
        self.root_particles = (root_particles, [])[root_particles is None]
        super(ProcessGroup, self).__init__(**params)

    def add_root_particle(self, particle):
        if not isinstance(particle, Particle):
            raise DecayConsistencyError('Non-Particle object received for adding to ProcessGroup')
        self.root_particles.append(particle)

    def __iter__(self):
        return self.root_particles.__iter__()

    def __getitem__(self, key):
        ''' Allows the ProcessGroup to be indexed as a list of Particle objects. '''
        return self.root_particles.__getitem__(key)
