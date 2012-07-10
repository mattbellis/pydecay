'''
This module defines the Converter framework for converting between decay representations.
The framework is loosely based on the visitor design pattern: to convert between representations,
client code must create a Converter object of the subtype that converts to the target representation,
passing all options in its initialization method, and then calling the convert() method on the
Converter object and passing it the object to convert.
'''

from pydecay import *
from pydecay.db import PARTICLE_TYPE_IMPL
from pydecay import graphphys
from warnings import warn

class InvalidTypeError(Exception):
    ''' Indicates that the object provided for conversion was of an unconvertable type. '''
    pass

class ConversionError(Exception):
    ''' Indicates that the conversion failed for a reason other than type problems. '''
    pass

class Converter(object):
    ''' The base implementation of a converter, which converts various types to PyDecay objects.
        If a subtype receives an object for conversion that it does not know how to handle directly,
        its last resort should be attempting to use Converter.convert to get a PyDecay object and
        then convert that.
    '''
    output_type = 'PyDecay object'
    
    def convert(self, obj):
        if isinstance(obj, DecayElement):
            return obj
        
        elif isinstance(obj, str):
            return graphphys.get_parser().parseString(obj)
        
        elif isinstance(obj, file):
            return graphphys.get_parser().parseFile(obj)
        
        # FIXME: should try importing, in case it hasn't been imported yet
        elif hasattr(PARTICLE_TYPE_IMPL.__module__, 'converters'
                     ) and hasattr(PARTICLE_TYPE_IMPL.__module__.converters, 'PyDecayConverter'):
            return PARTICLE_TYPE_IMPL.__module__.converters.PyDecayConverter().convert(obj)
            
        else:
            raise InvalidTypeError("Cannot convert %s object to %s" % ( type(obj).__name__, self.output_type ) )
        
    @staticmethod
    def get_real_filename(filename, output_format):
        ''' @param filename: the filename provided by the user.
            @param output_format: the output format extension provided by the user.
            @return: the filename, with output_format appended if filename did not already end with it.
        '''
        ext = '.' + output_format
        if not filename.endswith(ext):
            filename += ext
        return filename
        
    def convert_to_file(self, obj, filename, output_format):
        ''' Convenience method for getting an object via convert() and writing that object to a file.
            If subtypes' output formats (returned by convert()) cannot be output directly to a file,
            this method should be overridden to behave appropriately or raise an exception.  
        '''
        output = self.convert(obj)
        
        filename = self.get_real_filename(filename, output_format)
        outfile = open(filename,"w+")
        outfile.write(output)
        outfile.close()


class GraphPhysConverter(Converter):
    ''' Converter for converting decay trees into GraphPhys strings. These strings will not be
        the same every time, because they use objects' in-memory addresses (via the id() function)
        to uniquely name decay objects.
    '''
    
    output_type = 'GraphPhys string'
    
    @staticmethod
    def quote_if_necessary(s):
        ''' Adds quotes around a given ID if it contains characters that would invalidate it as a GraphPhys ID. '''
        if not isinstance(s, basestring):
            return s
        elif graphphys.is_valid_id(s):
            return s
        else:
            return '"%s"' % s
    
    def convert(self, obj):
        if isinstance(obj, str):
            return obj
        
        elif isinstance(obj, Particle):
            def get_param_list(decay_elt, braces=True):
                params_string = ''
                initial_comma = not braces
                for name, val in decay_elt.params.iteritems():
                    if initial_comma:
                        params_string += ', '
                    params_string += '%s=%s' % ( GraphPhysConverter.quote_if_necessary(name),
                                                 GraphPhysConverter.quote_if_necessary(val) )
                    initial_comma = True
                    
                if braces and params_string != '':
                    params_string = '[%s]' % params_string
                return params_string
            
            node_name = GraphPhysConverter.quote_if_necessary( obj.get_unique_name() )
            
            gp_code = ''
            for decay in obj.decays:
                for product in decay.products:
                    gp_code += self.convert(product)
 
            gp_code += '%s[type=%s%s];\n' % ( node_name, GraphPhysConverter.quote_if_necessary(obj.type), get_param_list(obj, False) )            
                       
            def get_product_names(decay):
                plist = ''
                for prod in decay.products:
                    plist = '%s %s' % ( plist, GraphPhysConverter.quote_if_necessary(prod.get_unique_name()) )
                plist += ' ' # Make it even - a space on both sides
                return plist
            for decay in obj.decays:
                gp_code += '%s -> {%s}%s;\n' % (node_name, get_product_names(decay), get_param_list(decay))
                
            return gp_code
        
        elif isinstance(obj, ProcessGroup):
            gp_code = ''
            for root in obj.root_particles:
                gp_code += self.convert(root)
                gp_code += '\n\n'
            return gp_code
        
        else:
            return self.convert( Converter.convert(self, obj) )
