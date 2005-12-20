#!/usr/bin/env python

from xml.dom import minidom as dom

try:
	import zlib
	__have_zlib = True
except ImportError:
	__have_zlib = False

def CreateElement( nodeName, attributes={} ):
	"Create an XML node and set the attributes from a dict"
	node = dom.Element( nodeName )
	map( lambda a: node.setAttribute( *a ), attributes.items() )
	return node

def sort_multiple( arrays ):
	"sort multiple lists (of equal size) using the first list for the sort keys"
	tuples = zip( *arrays )
	tuples.sort()
	return zip( *tuples )
	
"""def sort_multiple( arrays, lo=0, hi=None ):
	if hi is None: hi = len(arrays[0])-1
	if lo < hi:
		p = partition( arrays, lo, hi )
		sort_multiple( arrays, lo, p-1 )
		sort_multiple( arrays, p+1, hi )
	return arrays
		
def partition( arrays, lo, hi ):
	"Partition for a quick sort"
	p = arrays[0][lo]
	l = lo
	z = lo+1
	while z <= hi:
		if arrays[0][z] < p:
			l += 1
			for array in arrays:
				array[z], array[l] = array[l], array[z]
		z += 1
	for array in arrays:
		array[lo], array[l] = array[l], array[lo]
	return l
"""

class Graph( object ):
	"""=== Base object for generating SVG Graphs

== Synopsis

This class is only used as a superclass of specialized charts.  Do not
attempt to use this class directly, unless creating a new chart type.

For examples of how to subclass this class, see the existing specific
subclasses, such as SVG.Pie.

== Examples

For examples of how to use this package, see either the test files, or
the documentation for the specific class you want to use.

* file:test/plot.rb
* file:test/single.rb
* file:test/test.rb
* file:test/timeseries.rb

== Description

This package should be used as a base for creating SVG graphs.

== Acknowledgements

Sean E. Russel for creating the SVG::Graph Ruby package from which this
Python port is derived.

Leo Lapworth for creating the SVG::TT::Graph package which the Ruby
port is based on.

Stephen Morgan for creating the TT template and SVG.

== See

* SVG.BarHorizontal
* SVG.Bar
* SVG.Line
* SVG.Pie
* SVG.Plot
* SVG.TimeSeries

== Author

Jason R. Coombs <jaraco@jaraco.com>

Copyright 2005 Sandia National Laboratories
"""
	defaults = {
		'width':                500,
		'height':               300,
		'show_x_guidelines':    False,
		'show_y_guidelines':    True,
		'show_data_values':     True,
		'min_scale_value':      0,
		'show_x_labels':        True,
		'stagger_x_labels':     False,
		'rotate_x_labels':      False,
		'step_x_labels':        1,
		'step_include_first_x_label':   True,
		'show_y_labels':        True,
		'rotate_y_labels':		False,
		'stagger_y_labels':		False,
		'scale_integers':		False,
		'show_x_title':			False,
		'x_title':				'X Field names',
		'show_y_title':			False,
		'y_title_text_direction':	'bt',
		'y_title':				'Y Scale',
		'show_graph_title':		False,
		'graph_title':			'Graph Title',
		'show_graph_subtitle':	False,
		'graph_subtitle':		'Graph Subtitle',
		'key':					True,
		'key_position':			'right', # 'bottom' or 'right',
		
		'font_size':			12,
		'title_font_size':		16,
		'subtitle_font_size':	14,
		'x_label_font_size':	12,
		'x_title_font_size':	14,
		'y_label_font_size':	12,
		'y_title_font_size':	14,
		'key_font_size':		10,
		
		'no_css':				False,
		'add_popups':			False,
		}
	#__slots__ = tuple( defaults ) + ( '__dict__', '__weakref__' )

	def __init__( self, config ):
		"""Initialize the graph object with the graph settings.  You won't
instantiate this class directly; see the subclass for options.
"""
		self.top_align = self.top_font = self.right_align = self.right_font = 0
		self.load_config()
		self.load_config( config )
		self.clear_data()

	def load_config( self, config = None ):
		if not config: config = self.defaults
		map( lambda pair: setattr( self, *pair ), config.items() )
		
	def add_data( self, conf ):
		"""This method allows you do add data to the graph object.
		It can be called several times to add more data sets in.
		
		>>> data_sales_02 = [12, 45, 21]
		>>> graph.add_data({
		...  'data': data_sales_02,
		...  'title': 'Sales 2002'
		... })
"""
		self.validate_data( conf )
		self.process_data( conf )
		self.data.append( conf )

	def validate_data( self, data ):
		try:
			assert( isinstance( conf['data'], ( tuple, list ) ) )
		except TypeError, e:
			raise TypeError, "conf should be dictionary with 'data' and other items"
		except AssertionError:
			if not hasattr( conf['data'], '__iter__' ):
				raise TypeError, "conf['data'] should be tuple or list or iterable"

	def process_data( data ): pass
	
	def clear_data( self ):
		"""This method removes all data from the object so that you can
reuse it to create a new graph but with the same config options.

>>> graph.clear_data()
"""
		self.data = []
		
	def burn( self ):
		"""      # This method processes the template with the data and
config which has been set and returns the resulting SVG.

This method will croak unless at least one data set has
been added to the graph object.

Ex: graph.burn()
"""
		if not self.data: raise ValueError( "No data available" )
		
		if hasattr( self, 'calculations' ): self.calculations()
		
		self.start_svg()
		self.calculate_graph_dimensions()
		self.foreground = dom.Element( "g" )
		self.draw_graph()
		self.draw_titles()
		self.draw_legend()
		self.draw_data()
		self.graph.add_element( self.foreground )
		self.style()
		
		data = self._doc.toprettyxml()
		
		if self.compress:
			if __have_zlib:
				data = zlib.compress( data )
			else:
				data += '<!-- Python zlib not available for SVGZ -->'
				
		return data
	
	KEY_BOX_SIZE = 12
	
	def calculate_left_margin( self ):
		"""Override this (and call super) to change the margin to the left
of the plot area.  Results in border_left being set."""
		bl = 7
		# Check for Y labels
		if self.rotate_y_labels:
			max_y_label_height_px = self.y_label_font_size
		else:
			label_lengths = map( len, self.get_y_labels() )
			max_y_label_len = reduce( max, label_lengths )
			max_y_label_height_px = 0.6 * max_y_label_len * self.y_label_font_size
		if show_y_labels: bl += max_y_label_height_px
		if stagger_y_labels: bl += max_y_label_height_px + 10
		if show_y_title: bl += self.y_title_font_size + 5
		self.border_left = bl
		
	def max_y_label_width_px( self ):
		"""Calculates the width of the widest Y label.  This will be the
character height if the Y labels are rotated."""
		if self.rotate_y_labels:
			return self.font_size
		
	def calculate_right_margin( self ):
		"""Override this (and call super) to change the margin to the right
of the plot area.  Results in border_right being set."""
		br = 7
		if self.key and self.key_position == 'right':
			max_key_len = max( map( len, self.keys ) )
			br += max_key_len * self.key_font_size * 0.6
			br += self.KEY_BOX_SIZE
			br += 10		# Some padding around the box
		self.border_right = br
		
	def calculate_top_margin( self ):
		"""Override this (and call super) to change the margin to the top
of the plot area.  Results in border_top being set."""
		self.border_top = 5
		if self.show_graph_title: self.border_top += self.title_font_size
		self.border_top += 5
		if self.show_graph_subtitle: self.border_top += self.subtitle_font_size
		
	def add_popup( self, x, y, label ):
		"Adds pop-up point information to a graph."
		txt_width = len( label ) * self.font_size * 0.6 + 10
		tx = x + [5,-5](x+txt_width > width)
		t = dom.Element( 'text' )
		anchor = ['start', 'end'][x+txt_width > self.width]
		style = 'fill: #000; text-anchor: %s;' % anchor
		id = 'label-%s' % label
		attributes = { 'x': str( tx ),
					  'y': str( y - self.font_size ),
					  'visibility': 'hidden',
					  'style': style,
					  'text': label,
					  'id': id
					   }
		map( lambda a: t.setAttribute( *a ), attributes.items() )
		self.foreground.appendChild( t )
		
		visibility = "document.getElementById(%s).setAttribute('visibility', %%s )" % id
		t = dom.Element( 'circle' )
		attributes = { 'cx': str( x ),
					  'cy': str( y ),
					  'r': 10,
					  'style': 'opacity: 0;',
					  'onmouseover': visibility % 'visible',
					  'onmouseout': visibility % 'hidden',
		}
		map( lambda a: t.setAttribute( *a ), attributes.items() )

	def calculate_bottom_margin( self ):
		"""Override this (and call super) to change the margin to the bottom
of the plot area.  Results in border_bottom being set."""
		bb = 7
		if self.key and self.key_position == 'bottom':
			bb += len( self.data ) * ( self.font_size + 5 )
			bb += 10
		if self.show_x_labels:
			max_x_label_height_px = self.x_label_font_size
			if self.rotate_x_labels:
				label_lengths = map( len, self.get_x_labels() )
				max_x_label_len = reduce( max, label_lengths )
				max_x_label_height_px *= 0.6 * max_x_label_len
			bb += max_x_label_height_px
			if self.stagger_x_labels: bb += max_x_label_height_px + 10
		if self.show_x_title: bb += self.x_title_font_size + 5
		self.border_bottom = bb
		
	def draw_graph( self ):
		transform = 'translate ( %s %s )' % ( self.border_left, self.border_top )
		self.graph = CreateElement( 'g', { 'transform': transform } )
		self.root.appendChild( self.graph )
		
		self.graph.appendChild( CreateElement( 'rect', {
			'x': '0',
			'y': '0',
			'width': str( self.graph_width ),
			'height': str( self.graph_height ),
			'class': 'graphBackground'
			} ) )
		
		#Axis
		self.graph.appendChild( CreateElement( 'path', {
			'd': 'M 0 0 v%s' % self.graph_height,
			'class': 'axis',
			'id': 'xAxis'
		} ) )
		self.graph.appendChild( CreateElement( 'path', {
			'd': 'M 0 %s h%s' % ( self.graph_height, self.graph_width ),
			'class': 'axis',
			'id': 'yAxis'
		} ) )
		
		self.draw_x_labels()
		self.draw_y_labels()
	
	def x_label_offset( self, width ):
		"""Where in the X area the label is drawn
Centered in the field, should be width/2.  Start, 0."""
		return 0

	def make_datapoint_text( self, x, y, value, style='' ):
		if self.show_data_values:
			e = CreateElement( 'text', {
				'x': str( x ),
				'y': str( y ),
				'class': 'dataPointLabel',
				'style': '%(style)s stroke: #fff; stroke-width: 2;' % vars(),
			} )
			e.nodeValue = value
			self.foreground.appendChild( e )

	def draw_x_labels( self ):
		"Draw the X axis labels"
		if self.show_x_labels:
			label_width = self.field_width
			
			labels = self.get_x_labels()
			count = len( labels )
			
			labels = enumerate( iter( labels ) )
			start = int( not self.step_include_first_x_label )
			labels = itertools.islice( labels, start, None, self.step_x_labels )
			map( self.draw_x_label, labels )
			self.draw_x_guidelines( label_width, count )
	
	def draw_x_label( self, label, label_width ):
		index, label = label
		text = CreateElement( 'text', { 'class': 'xAxisLabels' } )
		text.appendChild( self._doc.createTextNode( label ) )
		self.graph.appendChild( text )
		
		x = index * label_width + self.x_label_offset( label_width )
		y = self.graph_height + self.x_label_font_size + 3
		t = 0 - ( self.font_size / 2 )
		
		if self.stagger_x_labels and  (index % 2 ):
			stagger = self.x_label_font_size + 5
			y += stagger
			graph_height = self.graph_height
			path = CreateElement( 'path', {
				'd': 'M%(x)d %(graph_height)d v%(stagger)d' % vars(),
				'class': 'staggerGuideLine'
			} )
			self.graph.appendChild( path )
			
		text.setAttribute( 'x', str( x ) )
		text.setAttribute( 'y', str( y ) )
		
		if self.rotate_x_labels:
			transform = 'rotate( 90 %d %d ) translate( 0 -%d )' % \
				( x, y-self.x_label_font_size, x_label_font_size/4 )
			text.setAttribute( 'transform', transform )
			text.setAttribute( 'style', 'text-anchor: start' )
		else:
			text.setAttribute( 'style', 'text-anchor: middle' )
			
	def y_label_offset( self, height ):
		"""Where in the Y area the label is drawn
Centered in the field, should be width/2.  Start, 0."""
		return 0
	
	def get_field_width( self ):
		return float( self.graph_width - font_size*2*right_font ) / \
			( len( self.get_x_labels() ) - self.right_align )
	field_width = property( get_field_width )
	
	def get_field_height( self ):
		return float( self.graph_height - self.font_size*2*self.top_font ) / \
			( len( self.get_y_labels() ) - self.top_align )
	field_height = property( self.get_field_height )

	def draw_y_labels( self ):
		"Draw the Y axis labels"
		if self.show_y_labels:
			label_height = self.field_height
			
			labels = self.get_y_labels()
			count = len( labels )
			
			labels = enumerate( iter( labels ) )
			start = int( not self.step_include_first_y_label )
			labels = itertools.islice( labels, start, None, self.step_y_labels )
			map( self.draw_y_label, labels )
			self.draw_y_guidelines( label_height, count )

	def get_y_offset( self ):
		result = self.graph_height + self.y_label_offset( self.label_height )
		if self.rotate_y_labels: result += self.font_size/1.2
		return result
	y_offset = property( get_y_offset )
	
	def draw_y_label( self, label ):
		index, label = label
		text = CreateElement( 'text', { 'class': 'yAxisLabels' } )
		text.appendChild( self._doc.createTextNode( label ) )
		self.graph.appendChild( text )
		
		y = self.y_offset - ( self.label_height * index )
		x = {True: 0, False:-3}[self.rotate_y_labels]
		
		if self.stagger_x_labels and  (index % 2 ):
			stagger = self.y_label_font_size + 5
			x -= stagger
			path = CreateElement( 'path', {
				'd': 'M%(x)d %(y)d v%(stagger)d' % vars(),
				'class': 'staggerGuideLine'
			} )
			self.graph.appendChild( path )
			
		text.setAttribute( 'x', str( x ) )
		text.setAttribute( 'y', str( y ) )
		
		if self.rotate_y_labels:
			transform = 'translate( -%d 0 ) rotate ( 90 %d %d )' % \
				( self.font_size, x, y )
			text.setAttribute( 'transform', transform )
			text.setAttribute( 'style', 'text-anchor: middle' )
		else:
			text.setAttribute( 'y', str( y - self.y_label_font_size/2 ) )
			text.setAttribute( 'style', 'text-anchor: middle' )
		
	def draw_x_guidelines( self, label_height, count ):
		"Draw the X-axis guidelines"
		# skip the first one
		for count in range(1,count):
			start = label_height*count
			stop = self.graph_height
			path = CreateElement( 'path', {
				'd': 'M %(start)s h%(stop)s' % vars(),
				'class': 'guideLines' } )
			self.graph.appendChild( path )
			

	def draw_y_guidelines( self, label_height, count ):
		"Draw the Y-axis guidelines"
		for count in range( 1, count ):
			start = self.graph_height - label_height*count
			stop = self.graph_width
			path = CreateElement( 'path', {
				'd': 'MO %(start)s h%(stop)s' % vars(),
				'class': 'guideLines' } )
			self.graph.appendChild( path )

	def draw_titles( self ):
		"Draws the graph title and subtitle"
		if self.show_graph_title: draw_graph_title()
		if self.show_graph_subtitle: draw_graph_subtitle()
		if self.show_x_title: draw_x_title()
		if self.show_y_title: draw_y_title()

	def draw_graph_title( self ):
		text = CreateElement( 'text', {
			'x': str( self.width / 2 ),
			'y': str( self.title_font_size ),
			'class': 'mainTitle' } )
		text.appendChild( self._doc.createTextNode( self.graph_title ) )
		self.root.appendChild( text )

	def draw_graph_subtitle( self ):
		raise NotImplementedError
	draw_x_title = draw_y_title = draw_graph_subtitle

	def keys( self ):
		return map( operator.itemgetter( 'title' ), self.data )
	
	def draw_legend( self ):
		if self.key:
			group = CreateElement( 'g' )
			root.appendChild( group )
			
			for key_count, key_name in enumerate( self.keys() ):
				y_offset = ( self.KEY_BOX_SIZE * key_count ) + (key_count * 5 )
				rect = group.CreateElement( 'rect', {
					'x': '0',
					'y': str( y_offset ),
					'width': str( self.KEY_BOX_SIZE ),
					'height': str( self.KEY_BOX_SIZE ),
					'class': 'key%s' % key_count + 1,
				} )
				group.appendChild( rect )
				text = group.CreateElement( 'text', {
					'x': str( self.KEY_BOX_SIZE + 5 ),
					'y': str( y_offset + self.KEY_BOX_SIZE ),
					'class': 'keyText' } )
				text.appendChild( doc.createTextNode( key_name ) )
				group.appendChild( text )
			
			if self.key_position == 'right':
				x_offset = self.graph_width, self.border_left + 10
				y_offset = border_top + 20
			if self.key_position == 'bottom':
				raise NotImplementedError
			group.setAttribute( 'transform', 'translate(%(x_offset)d %(y_offset)d)' % vars() )
			
	def style( self ):
		"hard code the styles into the xml if style sheets are not used."
		if self.no_css:
			styles = self.parse_css()
			for node in xpath.Evaluate( '//*[@class]', self.root ):
				cl = node.getAttribute( 'class' )
				style = styles[ cl ]
				if node.hasAttribute( 'style' ):
					style += node.getAtrtibute( 'style' )
				node.setAttribute( 'style', style )

	def parse_css( self ):
		"""Take a .css file (classes only please) and parse it into a dictionary
		of class/style pairs."""
		css = self.get_style()
		result = {}
		for match in re.finditer( '^(?<names>\.(\w+)(?:\s*,\s*\.\w+)*)\s*\{(?<content>[^}]+)\}' ):
			names = match.group_dict()['names']
			# apperantly, we're only interested in class names
			names = filter( None, re.split( '\s*,?\s*\.' ) )
			content = match.group_dict()['content']
			# convert all whitespace to 
			content = re.sub( '\s+', ' ', content )
			for name in names:
				result[name] = ';'.join( result[name], content )
		return result
			
	def add_defs( self, defs ):
		"Override and place code to add defs here"
		pass
	
	def start_svg( self ):
		"Base SVG Document Creation"
		impl = dom.getDOMImplementation()
		#dt = impl.createDocumentType( 'svg', 'PUBLIC'
		self._doc = impl.createDocument( None, 'svg', None )
		self.root = self._doc.documentElement()
		if self.style_sheet:
			pi = self._doc.createProcessingInstruction( 'xml-stylesheet',
												  'href="%s" type="text/css"' % self.style_sheet )
		attributes = {
			'width': str( self.width ),
			'height': str( self.height ),
			'viewBox': '0 0 %s %s' % ( width, height ),
			'xmlns': 'http://www.w3.org/2000/svg',
			'xmlns:xlink': 'http://www.w3.org/1999/xlink',
			'xmlns:a3': 'http://ns.adobe.com/AdobeSVGViewerExtensions/3.0/',
			'a3:scriptImplementation': 'Adobe' }
		map( lambda a: self.root.setAttribute( *a ), attributes.items() )
		self.root.appendChild( self._doc.createComment( ' Created with SVG.Graph ' ) )
		self.root.appendChild( self._doc.createComment( ' SVG.Graph by Jason R. Coombs ' ) )
		self.root.appendChild( self._doc.createComment( ' Based on SVG::Graph by Sean E. Russel ' ) )
		self.root.appendChild( self._doc.createComment( ' Based on Perl SVG:TT:Graph by Leo Lapworth & Stephan Morgan ' ) )
		self.root.appendChild( self._doc.createComment( ' '+'/'*66 ) )

		defs = self._doc.createElement( 'defs' )
		self.add_defs( defs )
		if not self.style_sheet and not self.no_css:
			self.root.appendChild( self._doc.createComment( ' include default stylesheet if none specified ' ) )
			style = CreateElement( 'style', { 'type': 'text/css' } )
			defs.appendChild( style )
			style.createCDataNode( self.get_style() )
			
		self.root.appendChild( self._doc.createComment( 'SVG Background' ) )
		rect = CreateElement( 'rect', {
			'width': str( width ),
			'height': str( height ),
			'x': '0',
			'y': '0',
			'class': 'svgBackground' } )
		
	def calculate_graph_dimensions( self ):
		self.calculate_left_margin()
		self.calculate_right_margin()
		self.calculate_bottom_margin()
		self.calculate_top_margin()
		self.graph_width = self.width - self.border_left - self.border_right
		self.graph_height = self.height - self.border_top - self.border_bottom
		
	def get_style( self ):
		return """/* Copy from here for external style sheet */
.svgBackground{
  fill:#ffffff;
}
.graphBackground{
  fill:#f0f0f0;
}

/* graphs titles */
.mainTitle{
  text-anchor: middle;
  fill: #000000;
  font-size: #{title_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}
.subTitle{
  text-anchor: middle;
  fill: #999999;
  font-size: #{subtitle_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.axis{
  stroke: #000000;
  stroke-width: 1px;
}

.guideLines{
  stroke: #666666;
  stroke-width: 1px;
  stroke-dasharray: 5 5;
}

.xAxisLabels{
  text-anchor: middle;
  fill: #000000;
  font-size: #{x_label_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.yAxisLabels{
  text-anchor: end;
  fill: #000000;
  font-size: #{y_label_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.xAxisTitle{
  text-anchor: middle;
  fill: #ff0000;
  font-size: #{x_title_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.yAxisTitle{
  fill: #ff0000;
  text-anchor: middle;
  font-size: #{y_title_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.dataPointLabel{
  fill: #000000;
  text-anchor:middle;
  font-size: 10px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}

.staggerGuideLine{
  fill: none;
  stroke: #000000;
  stroke-width: 0.5px;  
}

%s

.keyText{
  fill: #000000;
  text-anchor:start;
  font-size: #{key_font_size}px;
  font-family: "Arial", sans-serif;
  font-weight: normal;
}
/* End copy for external style sheet */
""" % self.get_css()