# Google Blockly wrapper for PythonJS
# by Brett Hartshorn - copyright 2013
# License: "New BSD"

BlocklyBlockGenerators = dict()  ## Blocks share a single namespace in Blockly
_blockly_selected_block = None   ## for triggering on_click_callback

with javascript: BlocklyBlockInstances = {}   ## block-uid : block instance
_blockly_instances_uid = 0

with javascript:
	NEW_LINE = String.fromCharCode(10)

def __blockinstance( result, block_uid ):
	with javascript:
		BlocklyBlockInstances[ block_uid ].pythonjs_object = result
	return result

def initialize_blockly( blockly_id='blocklyDiv', toolbox_id='toolbox', on_changed_callback=None ):
	print 'initialize_blockly'
	if len( BlocklyBlockGenerators.keys() ):
		toolbox = document.getElementById( toolbox_id )
		defaults = []
		cats = {}
		for block_name in BlocklyBlockGenerators.keys():
			b = BlocklyBlockGenerators[ block_name ]
			e = document.createElement('block')
			e.setAttribute('type', block_name)

			if b.category:
				if b.category in cats:
					cats[ b.category ].appendChild( e )
				else:
					cat = document.createElement('category')
					cat.setAttribute('name', b.category)
					cat.appendChild( e )
					toolbox.appendChild( cat )
					cats[ b.category ] = cat
			else:
				defaults.append( e )

			i = 0
			#for i in range(len(b.input_values)):  ## TODO check why this got broken
			while i < len(b.input_values):
				input = b.input_values[i]
				v = document.createElement('value')
				v.setAttribute('name', input['name'])
				e.appendChild(v)
				nb = document.createElement('block')
				nb.setAttribute('type', 'logic_null')
				v.appendChild(nb)
				i += 1


		if len(defaults):
			cat = document.createElement('category')
			cat.setAttribute('name', 'Callbacks')
			toolbox.appendChild( cat )
			for e in defaults:
				cat.appendChild( e )

	with javascript:
		Blockly.inject(
			document.getElementById( blockly_id ),
			{path : './', toolbox : document.getElementById(toolbox_id)}
		)

		def on_changed():
			global _blockly_selected_block
			if Blockly.selected != _blockly_selected_block:
				_blockly_selected_block = Blockly.selected
				if _blockly_selected_block and _blockly_selected_block.on_selected_callback:
					print 'BLOCKLY - new block selected:', _blockly_selected_block
					_blockly_selected_block.on_selected_callback()

			if on_changed_callback:  ## this gets triggered for any change, even moving a block in the workspace.
				on_changed_callback()

		Blockly.addChangeListener( on_changed )

	for block_name in BlocklyBlockGenerators.keys():
		b = BlocklyBlockGenerators[ block_name ]
		b.bind_block()
		b.bind_generator()

class BlocklyBlock:
	'''
	Instead of using this class directly, you should use StatementBlock or ValueBlock subclasses below.
	notes:
		. a block is not allowed to have previous or next statement notches and have an output.
		. a bare block can have no inputs or output, and no previous or next statement notches.

	'''
	def __init__(self, block_name=None, title=None, color=None, category=None):
		self.setup( block_name=block_name, title=title, color=color, category=None )

	def setup(self, block_name=None, title=None, color=None, category=None):
		if block_name is None: block_name = '_generated_block' + str(len(BlocklyBlockGenerators.keys()))
		if block_name in BlocklyBlockGenerators: raise TypeError
		BlocklyBlockGenerators[ block_name ] = self
		self.name = block_name
		self.title = title
		self.color = color
		self.category = category
		self.input_values = []
		self.input_statements = []
		self.output = None
		self.stackable = False
		self.stack_input = False
		self.stack_output = False
		self.is_statement = False
		self.external_function = None
		self.external_javascript_function = None
		self.on_click_callback = None

	def javascript_callback(self, jsfunc):
		print '@callback', jsfunc
		self.set_external_function( jsfunc.NAME, javascript=True )
		with javascript: arr = jsfunc.args_signature
		for i in range(arr.length): self.add_input_value( arr[i] )
		return jsfunc

	def callback(self, jsfunc):  ## decorator
		print '@callback', jsfunc
		self.set_external_function( jsfunc.NAME )
		with javascript: arr = jsfunc.args_signature
		for i in range(arr.length): self.add_input_value( arr[i] )
		return jsfunc

	def set_on_click_callback(self, callback):
		self.on_click_callback = callback

	def set_external_function(self, func_name, javascript=False):
		if javascript: self.external_javascript_function = func_name
		else: self.external_function = func_name
		if not self.title: self.title = func_name

	def set_output(self, output):
		if self.stack_input: raise TypeError
		elif self.stack_output: raise TypeError
		elif output == 'Number': pass
		elif output == 'String': pass
		elif output == 'Array': pass
		elif output == '*': pass
		else: raise TypeError
		self.output = output

	def make_statement(self, stack_input=None, stack_output=None):
		if self.output: raise TypeError
		elif stack_input: pass
		elif stack_output: pass
		else: raise TypeError
		self.stack_input = stack_input
		self.stack_output = stack_output
		self.is_statement = True

	def add_input_value(self, name=None, type=None, title=None):
		if name is None: raise TypeError
		elif type == 'Number': pass
		elif type == 'String': pass
		elif type == 'Array': pass
		#else: raise TypeError
		if title is None: title = name
		self.input_values.append(
			{'name':name, 'type':type, 'title':title}
		)

	def add_input_statement(self, name=None, title=None, callback=None):
		if name is None: raise TypeError
		if title is None: title = name
		self.input_statements.append(
			{'name':name, 'title':title, 'callback':callback}
		)


	def bind_block(self):
		global _blockly_instances_uid

		block_name = self.name
		stack_input = self.stack_input
		stack_output = self.stack_output
		output = self.output
		if stack_input or stack_output:
			if output:
				raise TypeError

		title = self.title
		color = self.color
		input_values = self.input_values.js_object
		input_statements = self.input_statements.js_object
		external_function = self.external_function
		external_javascript_function = self.external_javascript_function
		is_statement = self.is_statement

		with javascript:
			def init():
				block_uid = _blockly_instances_uid
				_blockly_instances_uid += 1
				BlocklyBlockInstances[ block_uid ] = this
				this.uid = block_uid  ## note that blockly has its own id called: this.id

				this.__input_values = input_values
				this.__input_statements = input_statements
				this.__external_function = external_function
				this.__external_javascript_function = external_javascript_function
				this.__is_statement = is_statement

				if color:
					this.setColour( color )

				if title:
					this.appendDummyInput().appendTitle(title)

				if stack_input:
					this.setPreviousStatement( True )
				if stack_output:
					this.setNextStatement( True )

				i = 0
				while i < input_values.length:
					input = input_values[i][...]
					if input['type']:
						this.appendValueInput(input['name'] ).setCheck( input['type'] ).appendTitle( '<'+input['type']+'> '+input['title'] ).setAlign(Blockly.ALIGN_RIGHT)
					else:
						this.appendValueInput(input['name'] ).appendTitle( input['title'] ).setAlign(Blockly.ALIGN_RIGHT)
					i += 1
				i = 0
				while i < input_statements.length:
					input = input_statements[i][...]
					this.appendStatementInput( input['name'] ).appendTitle( input['title'] )
					i += 1

				if output == '*':
					this.setOutput( True, null )  ## allows output of any type
				elif output:
					this.setOutput( True, output )

			print 'binding block:', block_name
			Blockly.Blocks[ block_name ] = {'init':init}  ## register the block type with Blockly

	def bind_generator(self):
		block_name = self.name

		## this is not safe with recursive functions? or this was due to the bad local scope bug below? (see input=null)
		#external_function = self.external_function
		#external_javascript_function = self.external_javascript_function
		#is_statement = self.is_statement
		#input_values = self.input_values.js_object
		#input_statements = self.input_statements.js_object

		with javascript:
			def generator(block):
				input_values = block.__input_values
				input_statements = block.__input_statements
				external_function = block.__external_function
				external_javascript_function = block.__external_javascript_function
				is_statement = block.__is_statement

				code = ''
				input = null  ## TODO fix local scope generator in python_to_pythonjs.py - need to traverse whileloops - the bug pops up here because this is recursive?
				args = []

				i = 0
				while i < input_values.length:
					input = input_values[i][...]
					if external_javascript_function:
						a = Blockly.JavaScript.valueToCode(block, input['name'], Blockly.JavaScript.ORDER_NONE)
					else:
						a = Blockly.Python.valueToCode(block, input['name'], Blockly.Python.ORDER_NONE)
					if a is not null:  ## blockly API not correct? is says this will return null when nothing is connected.
						args.push( a )
					i += 1

				## input statements are used for dynamic updates
				if block.pythonjs_object:
					print 'dynamic blockly js-------'
					wrapper = block.pythonjs_object[...]
					print 'dynamic wrapper:', wrapper
					i = 0
					while i < input_statements.length:
						input = input_statements[i][...]
						#if Object.hasOwnProperty(wrapper, input['name']):  ## this fails on THREE.Mesh.position, why?
						attr = wrapper[ input['name'] ]
						if attr:
							print 'dynamic wrapper has attr:', input['name']
							js = Blockly.JavaScript.statementToCode(block, input['name'])
							if input['callback']:
								print 'DYNAMIC--calling:', js
								input['callback']( attr, eval(js) )
							else:
								print 'WARN - input is missing callback', input
						i += 1

				if external_function:
					code += external_function + '(' + ','.join(args) + ')'
				elif external_javascript_function:
					## TODO what about pure javascript functions?
					if is_statement and block.parentBlock_:  ## TODO request Blockly API change: "parentBlock_" to "parentBlock"
						code += external_javascript_function + '( [' + ','.join(args) + '] )'  ## calling from js a pyjs function

				else:  ## this should be a simple series of statements?
					for a in args:
						code += a + ';'

				if is_statement:
					return code + NEW_LINE	## statements can directly return
				else:
					code = '__blockinstance(  ' + code + '  ,' + block.uid + ')'
					return [ code, Blockly.Python.ORDER_NONE ]  ## return Array

			Blockly.Python[ block_name ] = generator
			Blockly.JavaScript[ block_name ] = generator



class StatementBlock( BlocklyBlock ):
	'''
	A statement-block has a previous and/or next statement notch: stack_input and/or stack_output
	'''
	def __init__(self, block_name=None, title=None, stack_input=False, stack_output=False, color=170, category=None):
		self.setup( block_name=block_name, title=title, color=color, category=category )
		self.make_statement( stack_input=stack_input, stack_output=stack_output)


class ValueBlock( BlocklyBlock ):
	def __init__(self, block_name=None, title=None, output='*', color=100, category=None):
		if output is None: raise TypeError
		self.setup( block_name=block_name, title=title, color=color, category=category )
		self.set_output( output )





