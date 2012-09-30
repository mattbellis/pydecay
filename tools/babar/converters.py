import os
from pydecay.converters import visualizers
from pydecay.converters import *
from pydecay import ProcessGroup, Particle

class BtmTclConverter(Converter):
    output_type = 'BtaTupleMaker tcl file'
    
    def convert(self, obj):
        ################################################################################
        ################################################################################
        def real_name_to_variable_name(real_name):
            return real_name.replace("/",""
                                     ).replace("+","c"
                                     ).replace("-","c"
                                     ).replace("(",""
                                     ).replace(")",""
                                     ).replace("*","star")
        
            return variable_name
        
        
        ################################################################################
        ################################################################################
        def remove_double_types(particle_list):
            seen_particle_names = set()
        
            # Do this so if there are repeating particle types in the list, we still
            # remove them if there are duplicates
            org_particle_list = particle_list[:]
            for p in org_particle_list:
                ptype = p.type.replace("-","+")
                if ptype in seen_particle_names and p in particle_list:
                    particle_list.remove(p)
                else:
                    seen_particle_names.add(ptype)
        
        ################################################################################
        ################################################################################
        def get_ntp_name(particle):
            if hasattr(particle,"ntp_name"):
                return particle.ntp_name
            else:
                return real_name_to_variable_name(particle.type)
        
        ################################################################################
        ################################################################################
        def expand_decay_tree_from_top(particle):
            particles = [particle]
            for decay in particle.decays:
                for p in decay.products:
                    particles.extend( expand_decay_tree_from_top(p) )
            return particles
        
        
        ################################################################################
        ################################################################################
        def dump_file(filename, line_prefix=''):
            output = ""
            file = open(os.path.dirname(__file__) + os.sep + 'tcl_boilerplate/' + filename)
        
            for line in file:
                #print line
                output += line_prefix
                output += line
        
            return output
        
        
        ################################################################################
        ################################################################################
        def get_ntp_block_entries(particle):
        
            max_instances = 50
            default_contents = ["MCIdx", "Mass", "Momentum", "CMMomentum"]
        
            #ntpBlockContents set "B: MCIdx Mass Momentum CMMomentum Vertex VtxChi2 UsrData(BchtoJpsiKch)"
            p_type = particle.type
            #print "type %s" % (p_type)
            ntp_name = get_ntp_name(particle)
        
            # Append the fitting data
            if hasattr(particle,"fittingAlgorithm"):
                default_contents += ["Vertex", "VtxChi2"]
        
            if len(particle.decays) == 0:
                num_daughters = 0
            else: #len(particle.decays) == 1, since alternative decays not implemented
                num_daughters = len(particle.decays[0].products)
        
            output = ""
            output = '\tntpBlockConfigs  set "%-9s %-9s %-9s %d"\n' % (p_type,ntp_name,num_daughters,max_instances)
            temp = "%s:" % (ntp_name)
            output += '\tntpBlockContents set "%-9s' % (temp)
            for c in default_contents:
                output += " %s" % (c)
            output += '"\n'
        
            #print output
            return output
        
        
        ################################################################################
        ################################################################################
        def write_analysis_sequence(particle):
        
            # Check to see if this particle is coming from some already defined list.
            if hasattr(particle,"listname"):
                return 
            
            
            def get_tcl_option_string(main_key, value, subkey=''):
                if subkey and value:
                    subkey += ' '
                #print main_key,subkey,value
                return '\t%-21s set "%s%s"\n' % (main_key, subkey, value)
        
        
            def make_analysis_block(particle, seq_name=None):
                is_constrained = seq_name is not None
                
                if len(particle.decays) == 0:
                    products = []
                else: # len(particle.decays) == 1, since alternative decays aren't implemented
                    products = particle.decays[0].products

                particle_type = particle.type
                var_name = real_name_to_variable_name(particle_type)
        
                sequence_text = ''
                
                # Get the products
                if is_constrained:
                    smp_definer = "SmpRefitterDefiner"
                    keys_to_ignore = ("ntp_name",)
                    daughter_strings = [get_tcl_option_string("unrefinedListName", seq_name)]
                else:
                    smp_definer = "SmpMakerDefiner"
                    keys_to_ignore = ("ntp_name", "fittingAlgorithm", "fitConstraints", "postFitSelectors")
                    seq_name = "My_%s_to_" % var_name
                    daughter_strings = []
                    for p in products:
                        var_name = real_name_to_variable_name(p.type)
                        seq_name = "%s%s" % (seq_name,var_name)
                        if hasattr(p,"listname"):
                            daughter_seq_name = p.listname
                        else:
                            #print p.type
                            #print "Getting subdecay stuff!"
                            daughter_seq_name, next_sequence_text = write_analysis_sequence(p)
                            sequence_text += next_sequence_text
                        daughter_strings.append( get_tcl_option_string("daughterListNames", daughter_seq_name) )
                
                if is_constrained:
                    seq_name += '_Constrained'
                
                sequence_text += "mod clone %s %s\n" % (smp_definer, seq_name)
                sequence_text += "seq append AnalysisSequence %s\n" % (seq_name)
                sequence_text += "talkto %s {\n" % (seq_name)
            
                if not is_constrained:
                    reaction = "%s ->" % particle_type
                    for p in products:
                        reaction += " %s" % (p.type) 
                        
                    sequence_text += get_tcl_option_string("decayMode", reaction)
        
                for ds in daughter_strings:
                    sequence_text += ds
            
                for k,v in particle.params.iteritems():
                    if k not in keys_to_ignore:
                        # This only deals with 2 levels of nesting on the assumption that no more is necessary.
                        # If more is necessary, this should be rewritten as a recursive function call.
                        if type(v) is dict:
                            for subkey,subvalue in v.iteritems():
                                if type(subvalue) is bool:
                                    subvalue = ''
                                sequence_text += get_tcl_option_string(k, subvalue, subkey)
                        else:
                            sequence_text += get_tcl_option_string(k, v)
            
                sequence_text += "}\n"
                
                return seq_name, sequence_text
        
            seq_name, sequence_text = make_analysis_block(particle)
            seq_name, next_sequence_text = make_analysis_block(particle, seq_name)
            sequence_text += next_sequence_text
        
            return seq_name, sequence_text
        
        
        ################################################################################
        ## Actual main function definition
        ################################################################################
        
        if isinstance(obj, ProcessGroup):
            if len(obj.root_particles) > 1:
                raise ConversionError('Only one root particle allowed for conversion to BTM tcl file')
            
            elif len(obj.root_particles) == 0:
                return ''
            
            return self.convert(obj.root_particles[0])
        
        elif isinstance(obj, Particle):
            particle = obj            
            if len(particle.decays) > 1:
                raise Exception('Alternative decays not yet implemented')
            
            output = ""
            output += dump_file("top_of_tcl_file.txt")
            seq_name, sequence_text = write_analysis_sequence(particle)
            output += sequence_text
            
            # Start dumping the block
            output += dump_file('top_of_BtuTupleMaker_block.txt')
            
            #..Particle blocks to store
            output += "\tlistToDump set %s\n\n" % (seq_name)
            
            all_particles = expand_decay_tree_from_top(particle)
            remove_double_types(all_particles)
            for p in all_particles:
                output += get_ntp_block_entries(p)
                output += "\n"
                
            output += '\tntpBlockToTrk   set "'
            for p in all_particles:
                if len(p.decays)==0:
                    output += "%s " % (get_ntp_name(p))
            output += '"\n'
        
            output += dump_file('end_of_BtuTupleMaker_block.txt', '\t')
            output += dump_file('end_of_tcl_file.txt')
            
            return output
        
        else:
            return self.convert( Converter.convert(self, obj) )
        
        
    def convert_to_file(self, obj, filename, output_format='tcl'):
        if output_format != 'tcl':
            raise ConversionError('Unsupported output format for BtaTupleMaker config: %s' % output_format)
        
        return Converter.convert_to_file(self, obj, filename, output_format)
