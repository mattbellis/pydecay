''' This package defines a set of converters specifically for visualization. Currently
    only GraphViz Dot visualization and PyFeyn visualization are supported.
    If any of the Python libraries necessary for these forms of visualization are not
    installed, a warning will be issued and that form of visualization will not be
    available, but it will not prevent the rest of the library from loading properly.
'''

from warnings import warn
from pydecay import *
from pydecay.converters import *
from pydecay.settings import GENERIC_PRODUCT_LABEL, BRANCHING_FRACTION_PARAM

def import_warning(dependent_pkg, import_err):
    warn("Could not import %s dependency '%s'. %s visualization will not be available."
         % (dependent_pkg, str(import_err).rsplit(' ', 1)[-1], dependent_pkg) )
    

try:
    import pydot

    class PydotVisualizer(Converter):
        ''' Visualization converter for GraphViz Dot diagrams. Uses the Pydot library for managing Dot graphs. '''
        
        output_format = 'Pydot object'
        
        def __init__(self, html_labels=True, display_bf_product=True, display_bfs=False, top_level_graph=True):
            ''' @param html_labels: whether or not to decorate nodes with fancy HTML tables of attributes. If you
                                    are using a version of Dot from before mid-November 2003, you should set this to False.
                @param display_bf_product: whether or not to display branching-fraction products for the whole tree at 
                                           the top of each possible decay tree.
                @param display_bfs: whether or not to display the individual decays' branching fractions in the HTML
                                    label portion of the decays' parent particles.
                @param top_level_graph: whether or not this is the top-level converter for this graph. This is primarily
                                        for internal use, and client code should not need to use it.
            '''
            self.top_level_graph = top_level_graph
            self.html_labels = html_labels
            self.display_bf_product = display_bf_product
            self.display_bfs = display_bfs
            self.shape = ('rect', 'plaintext')[self.html_labels]
        
        def convert(self, decay_obj):
            if self.top_level_graph:
                g = pydot.Dot(graph_type='digraph')
                g.add_node(pydot.Node('node', shape=self.shape))
            else:
                g = pydot.Subgraph()
            
            if isinstance(decay_obj, Particle):
                for tree, probability in decay_obj.split_alternative_trees().iteritems():
                    subgraph = self.to_pydot(tree)
                    
                    # Add branching fraction labels if available and desired
                    if self.display_bf_product:
                        subgraph.set_name( 'cluster_%d' % id(subgraph) )
                        bf_product = (str(probability), 'Unknown')[probability is None]
                        subgraph.set_label('"BF Product: %s"' % bf_product)
                    
                    g.add_subgraph( subgraph )
                    
            elif isinstance(decay_obj, ProcessGroup):
                subvisualizer = PydotVisualizer(self.html_labels,
                                                self.display_bf_product, self.display_bfs, False)
                for particle in decay_obj.root_particles:
                    # Each particle when converted yields a subgraph, which itself has
                    # one subgraph per possible decay tree. Since the wrapping subgraph
                    # adds no value, and clusters won't work right when under a subgraph,
                    # we just add the possible-tree subgraphs directly to our top-level graph.
                    for subgraph in subvisualizer.convert(particle).get_subgraphs():
                        g.add_subgraph( subgraph )

            else:
                # Ignore g
                return self.convert( Converter.convert(self, decay_obj) )
            
            return g


        def convert_to_file(self, decay_obj, filename, output_format = 'png'):
            d = self.convert(decay_obj)
            
            filename = self.get_real_filename(filename, output_format)
                 
            try:
                write = d.__getattribute__('write_' + output_format )
            except AttributeError:
                raise ConversionError('Invalid output format: %s' % output_format)
            
            return write(filename)
        
        
        def to_pydot(self, particle):
            g = pydot.Subgraph()
            
            node_name = particle.get_unique_name()
            pydot_node = pydot.Node( node_name, label=self.make_dot_label(particle) )
            g.add_node(pydot_node)

            for decay in particle.decays: # If the tree has been flattened, there should be at most one of these
                if len(decay.products) == 0:
                    generic_node = pydot.Node(name='Generic_' + decay.get_unique_name(), label=GENERIC_PRODUCT_LABEL)
                    g.add_node(generic_node)
                    g.add_edge( pydot.Edge( particle.get_unique_name(),
                                            generic_node ) )
                else:
                    for product in decay.products:
                        g.add_edge( pydot.Edge( particle.get_unique_name(),
                                                product.get_unique_name() ) ) 
                        g.add_subgraph( self.to_pydot(product) )
            
            return g
        
        def make_dot_params_sublabel(self, params):
            if not self.html_labels:
                return ''
        
            else:
                label = ''
                
                if len(params) > 0:
                    for name, value in params.iteritems():
                        if isinstance(value, dict):
                            value = '<table border="0" cellspacing="0" cellborder="1">%s</table>' % self.make_dot_params_sublabel(value)
                            padding = 'cellpadding="8"'
                        else:
                            padding = ''
                        label += '<tr><td>%s</td><td %s>%s</td></tr>' % (name, padding, value)
            
                return label

        def make_dot_decay_params_sublabel(self, obj):
            if not self.html_labels:
                return ''
            
            sublabel = ''
            for decay in obj.decays: # We should only get one of these at most
                if len(decay.params) > 0:
                    sublabel += '<tr><td colspan="2"><font point-size="18">Decay Parameters:</font></td></tr>'
                    sublabel += self.make_dot_params_sublabel(decay.params)
            return sublabel
        
        def make_dot_label(self, obj):
            if self.html_labels:
                title = '<tr><td colspan="2"><font point-size="20">%s</font></td></tr>' % obj.type
                if self.display_bfs and len(obj.decays) == 1 and not obj.decays[0].params.has_key(BRANCHING_FRACTION_PARAM):
                    bfs = '<tr><td>Branching fraction</td><td>%f</td></tr>' % obj.decays[0].get_branching_fraction()
                else:
                    bfs = ''
                return '<<table cellspacing="0">%s%s%s%s</table>>' % (title, self.make_dot_params_sublabel(obj.params),
                                                                      bfs, self.make_dot_decay_params_sublabel(obj) )

            else:
                if hasattr(obj, 'type'):
                    return obj.type
                else:
                    return ''

except ImportError, e:
    import_warning('Pydot', e)


try:
    import pyx
    from pyfeyn.user import *
    from numpy import *
    from collections import deque
    from math import *
    
    class PyFeynVisualizer(Converter):
        ''' Converter for the PyFeyn visualization format. '''
        
        @staticmethod
        def decay_line(line_pts, angle, length):
            ''' Function to branch a line off of something. '''
        
        # Convert degrees to radians
            org_x_len = line_pts[1].getX() - line_pts[0].getX()
            org_y_len = line_pts[1].getY() - line_pts[0].getY()
        
            org_angle = arctan2(org_y_len,org_x_len)
        
            # # print org_angle
            # print degrees(org_angle)
        
            angle = radians(angle)
            # print angle
        
            # Add (or don't add) the original angle
            #angle += org_angle
        
            # print angle
        
            xin = line_pts[1].getX() + 0.01
            yin = line_pts[1].getY() + 0.01
        
            # print "angles: %f %f " % (cos(angle),sin(angle))
            # print "xin/yin: %f %f " % (xin,yin)
            # print "angle: %f %f " % (angle,degrees(angle))
        
            xout = xin + length*cos(angle)
            yout = yin + length*sin(angle)
        
            # print "xout/yout: %f %f " % (xout,yout)
        
            fin = Point(xin, yin)
            fout = Point(xout, yout)
        
            return (fin,fout)
    
        def __init__(self, split_trees = True):
            self.split_trees = split_trees
    
        # TODO: Split this function up
        def convert(self, decay_obj):
            ''' @return: a pyx drawing canvas. If PyFeyn folks ever get around to putting up the
                         patch they made for giving each FeynDiagram its own canvas, this should
                         be changed to return a FeynDiagram object.
            '''
            
            fds = []
            if isinstance(decay_obj, ProcessGroup):
                for particle in decay_obj.root_particles:
                    results = self.convert(particle)
                    if isinstance(results, list): # Will happen if we are splitting trees
                        fds.extend(results)
                    else:
                        fds.append(results)
                return fds
            
            elif isinstance(decay_obj, Particle):
                if self.split_trees:
                    subvisualizer = PyFeynVisualizer(False)
                    return [subvisualizer.convert(tree) for tree in decay_obj.split_alternative_trees()]
                
                processOptions()
                fd = FeynDiagram()
                
                levels = {}
                # print "parents ------------------ "
                def record_particle_levels(particle, level):
                    # print particle.type
                
                    levels[particle] = level
                    next_level = level + 1
                    max_level = level
                    for decay in particle.decays:
                        for daughter in decay:
                            max_level = max( max_level, record_particle_levels(daughter, next_level) )
                    return max_level
    
                max_level = record_particle_levels(decay_obj, 0)
                particle_q = deque([decay_obj])
                
                
                startx = -2.0
                starty = 0.0
                
                particle_positions = {}
                
                while len(particle_q) > 0:
                    p = particle_q.popleft()
                    for decay in p.decays:
                        particle_q.extend(decay)
                    
                    mydisplace = 0.0
                    # print p
                    level = levels[p]
                    if level == 0:
                        x0 = Point(startx,starty)
                        x1 = Point(startx+1.5,starty)
                        f1 = Fermion(x0,x1)
                        xpts = (x0, x1)
                    else:
                        parent = p.parent
                        # print parent.type
                        
                        decay_angle_range = 120.0 - (20 * level)
                        siblings = []
                        for decay in parent.decays:
                            siblings.extend(decay)
                
                        sibling_index = siblings.index(p)
                        angle_division_start = decay_angle_range/2.0
                        angle_division = decay_angle_range/( len(siblings)-1 )
                        angle = angle_division_start - (angle_division * sibling_index)
                
                        if level != max_level:
                            if angle < 0:
                                mydisplace = 0.1
                            elif angle > 0:
                                mydisplace = -0.1
                
                        mylength = 1.2 - 0.2 * level
                        parent_pos = particle_positions[parent]
                        xpts = self.decay_line(parent_pos, angle, mylength)
                        # print "%f %f %f %f" % (parent_pos[0].getX(), parent_pos[0].getY(), parent_pos[1].getX(), parent_pos[1].getY())
                        # print "%f %f %f %f" % (xpts[0].getX(), xpts[0].getY(), xpts[1].getX(), xpts[1].getY())
                
                        f1 = Fermion( *xpts )
                
                    particle_positions[p] = xpts
                    
                    mypos = 0.5
                    if level == max_level:
                        mypos = 1.05
                
                    # print "mydisplace: %f" % (mydisplace)
                    f1.addArrow()
                    f1.addLabel(p.type, pos=mypos, size=pyx.text.size.small, displace=mydisplace)
                    
                return fd.drawToCanvas()
            
            else:
                return self.convert( Converter.convert(self, decay_obj) )
    
        def convert_to_file(self, decay_obj, filename, output_format = 'pdf'):
            fds = self.convert(decay_obj)
            
            if output_format != 'pdf':
                raise ConversionError('Unsupported output format for PyFeyn: %s' % output_format)
            
            filename = self.get_real_filename(filename, output_format)
    
            if isinstance(fds, pyx.canvas.canvas):
                fds.writetofile(filename)
            else:
                filename, extension = filename.rsplit('.', 1)
                for i, fd in enumerate(fds):
                    fd.writetofile( "%s_%d.%s" % (filename, i, extension) )
    
except ImportError, e:
    import_warning('PyFeyn', e)
