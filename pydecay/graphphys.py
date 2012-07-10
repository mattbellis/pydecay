'''
The graphphys module implements the GraphPhys decay description language.
It defines a parser for the language whose parse method returns a
pydecay.ProcessGroup object representing all the information from the file. 

An abstract grammar for the GraphPhys language:

stmt_list      : [ stmt ';' [ stmt_list ] ]
stmt           : node_stmt
                     |       edge_stmt
                     |       default_stmt
                     |       param_stmt
default_stmt    : ('particle' | 'decay' ) param_list # For defaults, like 'node' and 'edge' in Dot
param_list      : '[' [ param_sequence ] ']'
param_sequence  : ID [ '=' param_val ] [ ',' ] [ param_sequence ]
param_val       : ID | param_list | float_number
edge_stmt       : ID edgeRHS [ param_list ]
edgeRHS         : edgeop node_set
node_stmt       : ID [ param_list ]
node_set        : '{' id_list '}'
id_list         : ID [id_list]
param_stmt      : ID '=' param_val
id_chunk        : (alpha | num | '`' | '~' | '!' | '@' | '$' | '%' | '^' | '&' | '*' | '?'
                         | '(' | ')' | '_' | '+' | '|' | '\' | '/' | '<' | '>' | '.' | ':'
                         # Not allowed because of special meanings: { } [ ] , = ;
                         # - is dealt with separately below
id_continuation : '-' ~'>' id_chunk?
non_neg_id      : id_chunk id_continuation
neg_id          : '-' (~'>' id_chunk)? id_continuation
ID              : non_neg_id | neg_id | quoted_string

Literals are given in single quotes; optional elements are in square brackets.

~ indicates a look-ahead - that the next literal is not what follows the ~. (This is the only kind
of look-ahead assumed by the grammar.)

Whitespace is allowed between all tokens except within an id_continuation, a non_neg_id, and a neg_id.

The purpose of the various pieces of an ID is to ensure that the - character may appear anywhere in
an identifier, but if it is followed by a >, forming the -> symbol, it is interpreted as a decay.
'''

from pydecay import *
from pyparsing import (Literal, Word, OneOrMore, ZeroOrMore, Forward, Group, Optional,
    Combine, alphas, nums, restOfLine, cStyleComment, nums, alphanums, CaselessKeyword,
    ParseException, ParseResults, CharsNotIn, _noncomma, QuotedString, StringEnd)
import new

''' The value to assign to parameters of the form [param1, param2] '''        
DEFAULT_PARAM_VALUE = True

''' The global GraphPhys parser '''
decay_parser = None

''' The ParserElement representing a GraphPhys particle ID. Useful for validating IDs. '''
arrow_start = Literal('-')
arrow_end = Literal('>')
id_chunk = Word(alphanums + '`~!@$%^&*()_+|\/<>.:?')
id_continuation = ZeroOrMore(arrow_start + ~arrow_end + Optional(id_chunk)) # -'s in middle are OK as long as no >'s
non_neg_id = Combine(id_chunk + id_continuation)
neg_id = Combine( arrow_start + Optional(~arrow_end + id_chunk) + id_continuation)
unquoted_id =  non_neg_id | neg_id
 
ID = ( unquoted_id | QuotedString('"', multiline=False, unquoteResults=True) ).setName("particle identifier")

def get_parser(force=False):
    ''' @return: a pyparsing.ParserElement object with the usual parse methods, except
                that pyparsing.ParserElement.parseString overridden to return a ProcessGroup
                object instead of a pyparsing.ParseResults object for convenience. 
    '''
    global decay_parser, ID

    ########################################
    ## Supporting parse classes
    ########################################
    
    class ParsedDecay:
        def __init__(self, start, end, params):
            self.start = start
            if isinstance(end, ParseResults):
                end = end.asList()
            self.end = end
            self.params = params

    class ParsedParam:
        def __init__(self, name, value):
            self.name = name
            self.value = value
            
    class ParsedParticle:
        def __init__(self, name, params):
            self.name = name
            self.params = params
            
    class ParsedDefault:
        def __init__(self, params, for_particle):
            self.params = params
            self.for_particle = for_particle

    ########################################
    ## Parser action functions
    ########################################

    def push_param_stmt(code_str, loc, toks):
        """ toks will be of the form [param_name, param_value] """
        return ParsedParam(toks[0], toks[1])

    def push_edge_stmt(code_str, loc, toks):
        ''' toks will be a list of the form [start_name, end (, params)] '''

        if len(toks) > 2: # Check for parameter list
            params = toks[2]
        else:
            params = {}

        end = toks[1]

        if isinstance(end, ParsedParticle):
            end_name = end.name
        else:
            end_name = end

        return ParsedDecay(toks[0], end_name, params)


    def push_node_stmt(code_str, loc, toks):
        """ toks will be a list of the form [name, params] """

        if len(toks) > 1: # Check for parameter list
            params = toks[1]
        else:
            params = {}
        return ParsedParticle(toks[0], params)


    def push_param_list(code_str, loc, toks):
        """ toks will be a list of the form [ name1, name2, '=', val2, name3, ... ] """
        params = {}
        i = 0
        l = len(toks)
        while i < l:
            param_name = toks[i]
            if i + 2 < l and toks[i + 1] == '=':
                param_value = toks[i + 2]
                increment = 3
            else:
                param_value = DEFAULT_PARAM_VALUE
                increment = 1
            params[param_name] = param_value

            i += increment
        return params
    
    def push_default_stmt(code_str, loc, toks):
        ''' toks will be of the form ["particle", param_dict] or ["decay", param_dict] '''
        return ParsedDefault(toks[1], toks[0].lower() == 'particle')

    def push_stmt_list(code_str, loc, toks):
        """ toks will be a ParseResults of Particle/ParsedDecay/ParsedParam objects """
        proc_group = ProcessGroup()
        
        seen_particles = {}
        edges = []
        
        particle_defaults = {}

        def params_for_object(obj, defaults):
            params = defaults.copy()
            params.update(obj.params)
            return params
        
        # Add particle objects we've generated already
        toks = toks.asList()
        for token in toks:
            if isinstance(token, ParsedDefault) and token.for_particle:
                particle_defaults.update(token.params)
                    
            elif isinstance(token, ParsedParticle):
                #print 'Adding ', token.name
                seen_particles[token.name] = Particle( token.params.pop('type', token.name),
                                                       **params_for_object(token, particle_defaults) )

        def find_or_insert_particle(name):
            if seen_particles.has_key(name):
                #print 'Using existing particle for %s' % name
                return seen_particles[name]
            else:
                #print 'Creating %s' % name
                seen_particles[name] = Particle(name, **particle_defaults) # Type is assumed to be the name of the particle
                return seen_particles[name]

        # Next add decays and any particles they reference that we haven't found already
        particle_defaults = {} # Reset so that we can use the right defaults at each place in the file
        decay_defaults = {}
        for token in toks:
            if isinstance(token, ParsedDefault):
                if token.for_particle:
                    particle_defaults.update(token.params)
                else:
                    decay_defaults.update(token.params)

            elif isinstance(token, ParsedDecay):
                start = find_or_insert_particle(token.start)

                end = []
                for end_point in token.end:
                    end.append( find_or_insert_particle(end_point) )
                
                params = params_for_object(token, decay_defaults)
                # If a particle was used twice, this should raise an error
                start.add_decay(end, **params)
                
            elif isinstance(token, ParsedParam):
                proc_group.add_param(token.name, token.value)

        seen_particles = seen_particles.values()
        # We allow for more than one root particle
        while len(seen_particles) > 0:
            decay_root = seen_particles[0]
            # Find the root of the current tree
            while decay_root.parent:
                decay_root = decay_root.parent
            # Now record everything under that root as dealt with, so we can see if there are more roots
            particles_to_delete = [decay_root]
            while len(particles_to_delete) > 0:
                particle = particles_to_delete.pop()
                seen_particles.remove(particle)
                decays = particle.decays
                for decay in decays:
                    particles_to_delete.extend(decay)

            proc_group.add_root_particle(decay_root)

        return proc_group
    

    ########################################
    ## Parser grammar definition
    ########################################
    
    if force or not decay_parser:
    
        # Literals
        lbrace = Literal("{")
        rbrace = Literal("}")
        lbrack = Literal("[")
        rbrack = Literal("]")
        equals = Literal("=")
        comma = Literal(",")
        semi = Literal(";")
        minus = Literal("-")
        arrow = Combine(arrow_start + arrow_end)
        
        # keywords
        particle = CaselessKeyword("particle")
        decay = CaselessKeyword("decay")

        # token definitions
        
        float_number = Combine(Optional(minus) +
                               OneOrMore(Word(nums + "."))).setName("float_number")


        param_list = Forward()
        stmt_list = Forward()

        param_val = (float_number | ID | param_list).setName("param_val")

        # We don't want to suppress the equals, since there may be parameters with no values
        param_sequence = OneOrMore(ID + Optional(equals + param_val) + 
                                  Optional(comma.suppress())).setName("param_sequence")
            
        param_list << (lbrack.suppress() + Optional(param_sequence) + 
                      rbrack.suppress()).setName("param_list")
            
        # Here a parameter statement is required, since there is no point in having a default stmt with no parameters
        default_stmt = ( (particle | decay) + param_list ).setName("default_stmt")

        node_set = Group( lbrace.suppress() + ZeroOrMore(ID) + rbrace.suppress() ).setName("node_set")

        edgeop = arrow.copy().setName('edgeop')
        edgeRHS = edgeop.suppress() + node_set
        edge_stmt = ID + edgeRHS + Optional(param_list)

        node_stmt = (ID + Optional(param_list)).setName("node_stmt")

        param_stmt = (ID + equals.suppress() + param_val).setName('param_stmt')

        ### NOTE: THE ORDER OF THE stmt OPTIONS DETERMINES THE RESOLUTION ORDER FOR WHEN IT FINDS A NODE NAME!!! ###
        # Default statements have highest priority, since we want to prevent the use of their keywords as
        # node or param names.
        
        stmt = (default_stmt | param_stmt | edge_stmt | node_stmt).setName("stmt")
        stmt_list << OneOrMore(stmt + semi.suppress())

        decay_parser = stmt_list + StringEnd()


        # Comments
        singleLineComment = Group("//" + restOfLine) | Group("#" + restOfLine)
        decay_parser.ignore(singleLineComment)
        decay_parser.ignore(cStyleComment)


        ########################################
        ## Set parse actions
        ########################################
        '''    
        def printAction(code_str, loc, toks):
            print toks
            return toks
        '''
        
        stmt_list.setParseAction(push_stmt_list)
        edge_stmt.setParseAction(push_edge_stmt)
        node_stmt.setParseAction(push_node_stmt)
        param_list.setParseAction(push_param_list)
        param_stmt.setParseAction(push_param_stmt)
        default_stmt.setParseAction(push_default_stmt)
        
            
        # Make the top-level parse method return a PyDecay object, not a ParseResults
        decay_parser.parseString = new.instancemethod(lambda self, instring, parseAll=False:
                                                        super(self.__class__, self).parseString(instring, parseAll)[0]
                                                      , decay_parser, decay_parser.__class__) 
        
    return decay_parser

def is_valid_id(name):
    ''' @param name: a possible ID to check
        @return: whether or not name can be parsed as an ID in GraphPhys '''
    global ID
    try:
        ID.parseString(name, parseAll=True)
        return True
    except ParseException:
        return False
