
from PySide2 import QtCore, QtGui, QtWidgets
from maya import mel
from maya import OpenMayaUI as mui
from pymel.all import *
from shiboken2 import wrapInstance
import math
import unicodedata
import  maya.OpenMaya as om
import maya.cmds as cmds
import cProfile, pstats, io


#--------------------------------------------------------------------------Dialog Window
class Dialog(QtWidgets.QDialog):

	def __init__(self, parent=None):
		super(Dialog, self).__init__(parent)

		self.attrs = Attributes()
		self.props = ObjProperty()
		self.obj_attrs = self.attrs.obj_attrs

		self.constructor_ui()
		self.trigger_select()


	def window_geo(self):
		win_width = 180
		win_height = 250
		win_posx = QtGui.QCursor.pos().x()+ 200
		win_posy = QtGui.QCursor.pos().y() - 30
		if win_posy < 1:
			win_posy = 1
		self.setGeometry(win_posx, win_posy, win_width , win_height)


	def constructor_ui(self):
		self.setObjectName("my_dialog")
		self.resize(300,200)
		self.setWindowTitle('Constructor')
		self.setWindowFlags(QtCore.Qt.Tool)      
			
		self.mainLayout = QtWidgets.QVBoxLayout(self)
		self.mainLayout.setContentsMargins(0,0,0,0)
		self.mainLayout.setObjectName("mainLayout")


 # table settings
		self.tableWidget = SettingsTab(self)
		self.tableWidget.setColumnCount (2)
		header = self.tableWidget.horizontalHeader()
		vert_header = self.tableWidget.verticalHeader()
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
		header.setStretchLastSection(False)
		header.setVisible(False)
		vert_header.setVisible(False)
		vert_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		self.mainLayout.addWidget(self.tableWidget)
		self.setLayout(self.mainLayout)
		#----------------------------------resize tool window 
		self.window_geo()
		self.make_table()
		self.fitToTable()
		# self.string_menu()

	@QtCore.Slot()
	def fitToTable(self):
		self.table = self.tableWidget
		x = self.table.verticalHeader().size().width()
		for i in range(self.table.columnCount()):
			x += self.table.columnWidth(i)

		y = 0
		for i in range(self.table.rowCount()):
			y += self.table.rowHeight(i)

		self.setFixedSize(x, y)


	def make_table(self):
		self.tableWidget.clear ()
		self.tableWidget.setRowCount(0)
		
		obj_type = objectType(KeyCatch.new_obj[1])
		my_attrs = self.sort_attrs(self.obj_attrs)
		my_shapes = self.obj_attrs.keys()

		if type(my_attrs) == str:
			my_attrs = [my_attrs]
		my_attrs.insert(0, 'Shape')

		for ind, attr in enumerate(my_attrs):
			lable = attr
			value = self.props.get_value(lable)
			self.tableWidget.insertRow(ind)
			self.tableWidget.setRowHeight(ind, self.tableWidget.cell_height)
			self.tableWidget.setColumnWidth(1, 80)
			name_item = QtWidgets.QTableWidgetItem(lable+'  ')
			name_item.setBackground(QtGui.QColor(68, 68, 68))
			self.tableWidget.setItem(ind,0,name_item)
			name_item.setFlags ( QtCore.Qt.ItemIsEnabled )
			name_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter )
			
			value_item = QtWidgets.QTableWidgetItem('  '+str(value))
			# ---------------------------------make value item uneditable if it's string
			#----------------------------------custom menu will be used instead
			self.value_flags(lable, value_item)	
			self.tableWidget.setItem(ind,1,value_item)

		self.tableWidget.setMinimumHeight(self.tableWidget.cell_height*len(my_attrs))
		# if cell changed run  "set attrs" with cell row and coumn as attributes
		QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL("cellChanged(int, int)"), self.set_attr)
		print 'ROWS: ', self.tableWidget.rowCount()


	def value_flags(self, lable, item):
		print 'Setting flags for: ', lable
		if lable in self.attrs.strings:
				item.setFlags(QtCore.Qt.ItemIsEnabled )
		else:
			item.setFlags(
						  QtCore.Qt.ItemIsEnabled | 
						  QtCore.Qt.ItemIsSelectable | 
						  QtCore.Qt.ItemIsEditable
						 )


	def set_attr(self, edit_row, edit_col):
		
		table = self.tableWidget

		click_item = table.click_item
		curr_item = table.click_item
		row, col = curr_item.row(), curr_item.column()
		# if current item is lable, chenge current item to this lable's value
		if col == 0:
			curr_item = table.item(row, 1)
			row, col = curr_item.row(), 1

		if edit_row == row and edit_col == col:
			if curr_item:
				print 'cell changed, item: ',curr_item.text().strip()
				lable = table.lable
				value = curr_item.text().strip()
				print 'Thing to change: ', lable, value

				if table.lable == 'Shape':
					self.new_shape(table.shape_to_make, table, lable)

				if lable in self.attrs.integers:
					value = float(value)
					if value <= 0:
						value = 1
					self.props.set_by_value(table.lable ,value)

				if lable in self.attrs.floats:
					value = float(value)
					if lable == 'Y Rotation':
						self.props.transform_by_value(table.lable ,value)
					else:
						if value <= 0:
							value = 0.001
						self.props.set_by_value(table.lable ,value)

				if lable == 'Subdivisions':
					self.update_values(table, lable)



		else: 
			pass

	def new_shape(self, shape,table,lable):
		MakePrimitive().named_shape(shape)
		self.update_table(table)
		self.update_values(table, lable)
		
	def update_values(self,table, curr_lable):
		items = table.curr_lable_items()
		for item in items:
			lable = item.text().strip()
			if lable not in  ['Shape', curr_lable]:
				value = self.props.get_value(lable)
				row = item.row()
				new_item = QtWidgets.QTableWidgetItem(str(value))
				table.setItem(row,1,new_item)


	def sort_attrs(self, attr_dict):
		obj_type = objectType(KeyCatch.new_obj[1])
		my_attrs = attr_dict[obj_type].keys()
		map_attrs = [item[1] for item in attr_dict[obj_type].values()]
		attr_order = dict(zip(my_attrs, map_attrs))
		return sorted(my_attrs, key=attr_order.__getitem__)


	def update_table(self,table):
		my_attrs = self.sort_attrs(self.obj_attrs)
		if 'Shape' not in my_attrs:
			my_attrs.insert(0, 'Shape')
		#-------------------------make list of current table columns
		table = self.tableWidget
		curr_columns = table.curr_table_lables()
		#-----------------------convert both lists from unicode to string
		my_attrs = [it.encode('ascii','ignore') for it in my_attrs]
		curr_columns = [it.encode('ascii','ignore') for it in curr_columns]
		col_count = len(curr_columns)
		if my_attrs == curr_columns:
			pass
		else:

			def returnNotMatches(a, b):
				return [[x for x in a if x not in b], [x for x in b if x not in a]]

			extra_lables = returnNotMatches(my_attrs, curr_columns)
			to_add = extra_lables[0][::-1] #reversed order
			print 'to_add', to_add
			to_kill = extra_lables[1]
			print 'to_kill', to_kill
			if to_add:
				for ind, item in enumerate(to_add):
					table.insertRow(col_count)
					table.setRowHeight(col_count, table.cell_height)
					name_item = QtWidgets.QTableWidgetItem(item+'  ')
					name_item.setBackground(QtGui.QColor(68, 68, 68))
					table.setItem(col_count,0,name_item)
					name_item.setFlags ( QtCore.Qt.ItemIsEnabled )
					name_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter )
					value = self.props.get_value(item)
					value_item = QtWidgets.QTableWidgetItem('  '+str(value))
					self.value_flags(item, value_item)
					table.setItem(col_count,1,value_item)


			if to_kill:
				for ind, item in enumerate(to_kill):
					target = table.findItems(item + '  ',QtCore.Qt.MatchExactly)[0]
					row = target.row()
					table.removeRow(row)
			#----------------------------Adjust the table size
			self.size_update(table, width=160)
			self.fitToTable()
			table.blockSignals(True)
			table.item(0, 1).setFlags(QtCore.Qt.ItemIsEnabled )
			table.blockSignals(False)

	def current(self):
		new = None
		current = cmds.ls(sl=1,fl=1)
		try:
			new = KeyCatch.new_obj[0].nodeName()
		except:
			pass
		if new not in current:
			self.close()


	def trigger_select(self):
		self.trigger_selection = cmds.scriptJob(p="my_dialog",event=['SelectionChanged',self.current],killWithScene=False)

	#---------------------------------------------------------------------------------------------------------------

	def size_update(self,table,width=160):
		curr_columns = table.curr_lable_items()
		col_count = len(curr_columns)
		t_height = 	table.cell_height*(col_count)
		table.setMinimumHeight(t_height)
		self.resize(width,t_height)


	def closeEvent(self,event):
		eventFilter.close()

class ObjProperty():

	def __init__(self):
		attrs = Attributes()
		self.obj_attrs = attrs.obj_attrs

	def set_by_value(self, obj_property, value):
		self.shape = KeyCatch.new_obj[1]
		self.obj_type = objectType(self.shape)
		if obj_property == 'Shape':
			return obj_type
		attr = self.obj_attrs[self.obj_type][obj_property][0]
		if type(attr) == str:
			attr = [attr]
		for a in attr:
			command = '''cmds.setAttr('{}.{}',{})'''.format(self.shape, a, value)
			try:
				exec(command)
			except:
				pass

	def transform_by_value(self, obj_property, value):
		self.shape = KeyCatch.new_obj[1]
		self.transform = KeyCatch.new_obj[0]
		self.obj_type = objectType(self.shape)
		attr = self.obj_attrs[self.obj_type][obj_property][0]
		if type(attr) == str:
			attr = [attr]
		for a in attr:
			command = '''cmds.setAttr('{}.{}',{})'''.format(self.transform, a, value)
			try:
				exec(command)
			except Exception as e:
				print str(e)




	def get_value(self, obj_property):
		self.shape = KeyCatch.new_obj[1]
		self.transform = KeyCatch.new_obj[0]
		node = self.shape
		if obj_property == 'Y Rotation':
			node = self.transform
		obj_type = objectType(self.shape)
		if obj_property == 'Shape':
			return obj_type
		else:
			attr = self.obj_attrs[obj_type][obj_property][0]
			print type(attr)
			if type(attr) == list or type(attr) == tuple:
				attr = attr[0]
			command = '''value = cmds.getAttr('{}.{}')'''.format(node, attr)
			exec(command)
			value = round(value, 2)
			return value


class Attributes():
	def __init__(self):
		
		self.obj_attrs = {
					'polyCube' : 
							{
							'Subdivisions' : ( ('subdivisionsWidth','subdivisionsHeight','subdivisionsDepth'), 0 ),
							'Subdisivions Width' : ( 'subdivisionsWidth', 2 ),
							'Subdisivions Height' : ( 'subdivisionsHeight', 3),
							'Subdisivions Depth' : ( 'subdivisionsDepth', 4 ),
							'Y Rotation' : ( 'rotateY', 1 ),
							},

					'polySphere': 
							{
							'Subdivisions' : ( ('subdivisionsAxis', 'subdivisionsHeight'), 0 ),
							'Subdivisions Axis': ( 'subdivisionsAxis', 2 ),
							'Subdisivions Height' : ( 'subdivisionsHeight',3 ),
							'Y Rotation' : ( 'rotateY', 1 ),
							},
					'polyCylinder' : 
							{
							'Subdivisions' : ( 'subdivisionsAxis', 0 ),
							'Subdisivions Height' : ('subdivisionsHeight', 2),
							'Y Rotation' : ( 'rotateY', 1 ),
							},
					'polyTorus': 
							{
							'Subdivisions' : ( ('subdivisionsAxis', 'subdivisionsHeight'), 0 ), 
							'Subdivisions Axis': ( 'subdivisionsAxis', 2 ),
							'Subdisivions Height' : ( 'subdivisionsHeight', 3 ),
							'Section Radius': ( 'sectionRadius' , 4 ) ,
							'Twist' : ( 'twist', 5 ),
							'Y Rotation' : ( 'rotateY', 1 ),
							},
					'polyPlane': 
							{
							'Subdivisions' : ( ('subdivisionsWidth' ,'subdivisionsHeight'), 0 ) ,
							'Subdisivions Width' : ( 'subdivisionsWidth', 2 ),
							'Subdisivions Height' : ( 'subdivisionsHeight', 3 ),
							'Y Rotation' : ( 'rotateY', 1 ),
							},
					}
		self.ratio_list = {'polyCube' : 1, 'polyTorus': 2, 'polyPlane':1, 'polyCylinder': 2, 'polySphere': 2 }
		self.strings = ('Shape')
		self.integers = ('Subdivisions','Subdisivions Width', 'Subdisivions Height', 'Subdisivions Depth','Subdivisions Axis', 'Twist')
		self.floats = ('Section Radius','Y Rotation')
		self.scroll_pace = {'Section Radius': 0.001 , 'Twist': 0.4 , 'Y Rotation': 0.1 }

#--------------------------------------------------smart table class
class SettingsTab(QtWidgets.QTableWidget):

	cell_height = 20

	def __init__(self, parent):
		super(SettingsTab, self).__init__(parent)
		self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
		self.SelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.setShowGrid(False)
		self.setFrameStyle(QtWidgets.QFrame.NoFrame)
		self.setFocusPolicy(QtCore.Qt.NoFocus)
		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.setSizePolicy(sizePolicy)

		self.mouseStartPosY = 0
		self.startValue = 0
		#---------------------------------------Bring some custom attributes
		self.attrs = Attributes()
		self.obj_attrs = self.attrs.obj_attrs
		self.shapes = self.obj_attrs.keys()
		self.pace = self.attrs.scroll_pace
		#------------------------------------------------------------------

	def mousePressEvent(self, e):
		self.prev_value = 0
		self.mouseStartPosX = e.pos().x()
		self.mouseStartPosY = e.pos().y()
		self.tab_column = self.clicked_column()
		self.ed_row = self.click_item.row()
		self.lable = self.item(self.ed_row, 0 ).text().strip()
		# self.lable = self.click_item.text().strip()
		if self.tab_column == 0:
			self.startValue = self.get_item_value()
			self.sel_status = None
			self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
			self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		#clear selection, color all white, color cliclked item red
		if self.tab_column == 0:
			QtWidgets.QAbstractItemView.clearSelection(self)
			[item.setForeground(QtCore.Qt.white) for item in self.curr_lable_items()]
			self.click_item.setForeground(QtCore.Qt.red)
		if self.tab_column == 1 and self.lable in self.attrs.strings:
			self.menu_build()
		return super(SettingsTab, self).mousePressEvent(e)

	def mouseMoveEvent(self, e):
		if self.clicked_column() == 0:
			self.setCursor(QtCore.Qt.SizeHorCursor)
			
			try:
				multiplier = self.pace[self.lable]
			except:
				multiplier = 0.02

			if self.lable in self.attrs.integers:
				valueOffset = int((self.mouseStartPosX + e.pos().x()) * multiplier)
			elif self.lable in self.attrs.strings:
				valueOffset = int((self.mouseStartPosX + e.pos().x()) * multiplier)
			elif self.lable in self.attrs.floats:
				valueOffset =(e.pos().x()-self.mouseStartPosX) * multiplier
			final_value = self.startValue + valueOffset
			if final_value != self.prev_value:
				self.data_control(self.lable, final_value)
				self.prev_value = final_value
			else:
				pass
		return super(SettingsTab, self).mouseMoveEvent(e)

	def mouseReleaseEvent(self, e):
		if self.clicked_column() == 0:
			self.unsetCursor()
			#enable selection back
			self.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
			self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
			
		return super(SettingsTab, self).mouseReleaseEvent(e)


	def curr_table_lables(self):
		return [item.text().strip() for item in self.curr_lable_items()]
		

	def clicked_column(self):
		self.click_item = self.itemAt(self.mouseStartPosX, self.mouseStartPosY)
		self.click_column = self.column(self.click_item)
		return self.click_column

	def curr_lable_items(self):
		curr_l_items = []
		self.row_count = self.rowCount()
		for idx, r in  enumerate(range(self.row_count)):
			lable = self.item(idx, 0)
			curr_l_items.append(lable)
		return curr_l_items


	def get_item_value(self):
		lable = self.lable
		row, col = self.click_item.row(), 1
		value = self.item(row, col).text().strip()

	
		
		if lable == 'Shape':
			return self.shapes.index(value)
		else:
			return float(value)


	def data_control(self, lable, value):
		if lable in self.attrs.integers:
			value = int(round(value))
			if value <=1:
				value = 1
			value_item = QtWidgets.QTableWidgetItem('  '+str(value))
			self.setItem(self.ed_row, 1, value_item)
		# if 'Shapes', just add to table
		elif lable in self.attrs.strings:
			value = value%len(self.shapes)
			shape_name = self.shapes[value]
			value_item = QtWidgets.QTableWidgetItem('  '+str(shape_name))
			self. shape_to_make = shape_name
			self.setItem(self.ed_row, 1, value_item)
		elif lable in self.attrs.floats:
			if value <=0:
				value = 0
			value_item = QtWidgets.QTableWidgetItem('  '+str(value))
			self.setItem(self.ed_row, 1, value_item)
		else:
			print 'LOOKS LIKE THIS LABLE IS UNASSIGNED YET'
			

	def menu_build(self):
		self.menu = QtWidgets. QMenu(self)
		[self.add_menu_item(x) for x in self.shapes]
		popup_point = QtGui.QCursor.pos()
		self.menu.popup(popup_point)



	def menu_action(self, shape_name):
		print 'DO This', shape_name
		self.click_item = self.item(0,0)
		value_item = QtWidgets.QTableWidgetItem('  '+str(shape_name))
		self. shape_to_make = shape_name
		self.setItem(0, 1, value_item)


	def add_menu_item(self, item_name):
		new_item = QtWidgets.QAction(item_name, self)
		new_item.triggered.connect(lambda: self.menu_action(item_name))
		self.menu.addAction(new_item)

#-------------------------------------------------------------------------Message Class
class Message():
	def __init__(self):
		self.optionVar_name = "inViewMessageEnable"
		self.inView_opt = optionVar.get("inViewMessageEnable")
		self.colours = {'green': 'style=\"color:#33CC33;\"',
						'red': 'style=\"color:#FF0000;\"',
						'yellow': 'style=\"color:#FFFF00;\"',
						'pink': 'style=\"color:#F05A5A;\" '
						}

	def disable_messages(self):
		optionVar(intValue=(Message().optionVar_name, 0))
		pass

	def enable_messages(self):
		optionVar(intValue=(Message().optionVar_name, 1))
		pass


# pink info message
class info(Message):
	def __init__(self, position="midCenter", prefix="", message="", fadeStayTime=1000, fadeOutTime=2.0, fade=True, color='pink'):
		msg_color = Message().colours[color]
		Message().enable_messages()
		inViewMessage(amg='''<p {}> {}'''.format(msg_color,message),
						 pos=position,
						 fadeStayTime=fadeStayTime,
						 fadeOutTime=fadeOutTime,
						 fade=fade)
		Message().disable_messages()

#-------------------------------------------------------------------------Primitive CLASS
class MakePrimitive:
	base = ls(sl=1, fl = 1)

	def __init__(self):
			# self.base = ls(sl=1, fl = 1)
		#---------------------------------------create settings in registry. Load last shape created
		self.settings = QtCore.QSettings('PixelEmbargo','Constructor')
		self.last_shape = self.settings.value('last_shape','polyCube')

		attrs = Attributes()
		self.obj_attrs = attrs.obj_attrs
		self.just_shapes = self.obj_attrs.keys()
		self.ratio_list = attrs.ratio_list

	def extrude_check(self, base):
		if base:
			last = base[-1]
			if objectType(last) == 'polyExtrudeFace':
				return base[:-1]
		return base

	

	def makeShape(self,direction):
		#-------------------------------------------Get the name of the next shape
		arrow_d = {'right':{'step':1,'first':0},'left':{'step':-1,'first':-1}}
		base = self.base
		base = self.extrude_check(base)
		try:
			self.new_obj = KeyCatch.new_obj
			obj_transform, obj_shape  = self.new_obj[0],  self.new_obj[1]
			self.transform = obj_transform.getTransformation()
			curr_shape = objectType(obj_shape)
			sh_index = self.just_shapes.index(curr_shape)
			next_shape = self.just_shapes[sh_index+arrow_d[direction]['step']]
		except IndexError:
			#if next list index is beyond the list capacity, go to the first item in list
			next_shape = self.just_shapes[arrow_d[direction]['first']]
			#
		except:
			next_shape = self.last_shape
		

		self.named_shape(next_shape)

	


	def named_shape(self, object_name):

		try:
			obj_transform, obj_shape  = KeyCatch.new_obj[0],  KeyCatch.new_obj[1]
			transform = obj_transform.getTransformation()
			self.old_scale = obj_transform.getScale()
			delete(KeyCatch.new_obj)
		except Exception as e:
			print str(e)
		# Make next shape
		base = self.base
		curr_sel = ls(sl=1, fl=1)

		command = 'self.new_obj = self.{}()'.format(str(object_name).replace('poly', 'make'))
		print 'command: ', command
		exec(command)

		#-----------------------------------------prescale, snap to selection and transform
		KeyCatch.new_obj = self.new_obj
		obj_transform, obj_shape  = self.new_obj[0],  self.new_obj[1]
		self.sel_mode = self.selection_mode(base)
		self.obj_type = objectType(obj_shape)
	
		#-----------------------------------fix scale
		

		if self.sel_mode in ['Faces','Vertices', 'Edges']:
			self.bottom_pivot(obj_shape)

			if KeyCatch.snapped == None:
				self.snap_obj(self.new_obj, base)
				KeyCatch.corr_scale = self.ratio_list[self.obj_type]
				KeyCatch.init_scale = obj_transform.getScale()
				fix_scale = [s*2/KeyCatch.corr_scale for s in KeyCatch.init_scale]
				obj_transform.setScale( scale = fix_scale )
				KeyCatch.snapped = 1
								
			else:
				# first transform
				obj_transform.setTransformation(transform)
				# then fix scale issues
				# if object was scaled, update initial scale
				if KeyCatch.final_scale != self.old_scale:
					KeyCatch.init_scale = [item/KeyCatch.fixture for item in obj_transform.getScale()]

				KeyCatch.corr_scale = self.ratio_list[self.obj_type]
				fix_scale = [s*2/KeyCatch.corr_scale for s in KeyCatch.init_scale]
				obj_transform.setScale( scale = fix_scale )

			KeyCatch.final_scale = obj_transform.getScale()
			# save scale ratio of this object for use in the next loop
			KeyCatch.fixture = ( (self.ratio_list[self.obj_type])*0.5 )**(-1)

		else:
			try:
				obj_transform.setTransformation(transform)
			except:
				pass

		cmds.xform( self.new_obj, p=True, roo='yzx' )
		return self.new_obj

	def now_selected(self):
		return cmds.ls(selection=True, type ='transform', flatten=True)

	#-------------------------------------------------------Shape making code here
	def makeCube(self):
		return polyCube(sz=1, sy=1, sx=1, d=1, cuv=4, h=1, ch=1, w=1, ax=(0, 1, 0))

	def makeSphere(self):
		return polySphere(cuv=2, sy=16, ch=1, sx=16, r=1, ax=(0, 1, 0))

	def makeCylinder(self):
		return polyCylinder(sz=1, sy=1, sx=8, cuv=3, ch=1, h=2, rcp=0, r=1, ax=(0, 1, 0))

	def makeTorus(self):
		return polyTorus(cuv=1, sy=16, sx=16, ch=1, sr=0.25, r=1, tw=0, ax=(0, 1, 0))

	def makePlane(self):
		return polyPlane(cuv=2, sy=1, sx=1, h=1, ch=1, w=1, ax=(0, 1, 0))


	def snap_obj(self, my_obj, component_list):
		# -------------------------------------Find the center of base selection
		obj_transform, obj_shape  = my_obj[0],  my_obj[1]
		if self.sel_mode == 'Faces':
			snap_point = self.compgroup_center(component_list)
			faces_list = component_list
		if self.sel_mode == 'Vertices':
			snap_point = self.vertgroup_center(component_list)
			faces_list = modeling.polyListComponentConversion( component_list, fv=True,tf=True,bo=True )
			faces_list = ls(faces_list, fl=True)
		if self.sel_mode == 'Edges':
			snap_point = self.compgroup_center(component_list)
			faces_list = modeling.polyListComponentConversion( component_list, fe=True,tf=True,bo=True )
			faces_list = ls(faces_list, fl=True)


		perimetr_vec = zip(*self.perimeter_vectors(faces_list, snap_point))
		rad_point_list = perimetr_vec[0]
		rad_vector_list = perimetr_vec[1]

		#--------------------------------------------Snap object to Snap Point
		xform(my_obj, translation = (snap_point[0], snap_point[1], snap_point[2]), ws=True)

		rot_angle = self.deg_rotation(faces_list, rad_vector_list)
		xy_rot, wy_rot = rot_angle[0], rot_angle[1]

		#-------------------------------Initial_worldspace_rotation
		rotate(my_obj, xy_rot, ws=True)

		#---------------------------------Final object space rotation(can be turned off)
		cmds.rotate(0, wy_rot, 0, r=1, os=1, fo=1)

		
		#---------------------------------Scale object to match initial selection
		
		scale_ratio = self.get_radius(obj_shape, rad_point_list)
		[ setAttr("{}.scale{}".format(obj_transform ,axis), scale_ratio) for axis in ('X','Y','Z') ]


	#-------------------------------------------------Figure out the selection type

	def selection_mode(self,selection):
		obj_sel = ls(sl=1, fl = 1)
		try:
			select(selection[0])
		except:
			pass
		modeling.filterExpand( sm=32 )
		s_modes = {12 : 'Objects',
				   31 : 'Vertices',
				   32 : 'Edges',
				   34 : 'Faces'
				   }

		for key,value  in s_modes.items():
			mode = modeling.filterExpand( sm=key )
			if mode:
				select(obj_sel)
				return s_modes[key]

#------------------------------------------------------------------Find selection center
	def comp_center(self, component):
		# break the list to pieces 3 items each, that represent x,y,z of each face vertex
		vert_coords = xform(component, q=True, t=True, ws=True)
		vert_coords = [vert_coords [i:i + 3] for i in range(0, len(vert_coords ), 3)]
		# find average for x, y, z of face coords
		return self.average_coords(vert_coords)
		
	def compgroup_center(self, comp_list):
		comp_centers = [self.comp_center(comp) for comp in comp_list]
		return self.average_coords(comp_centers)

	def vertgroup_center(self, vert_list):
		vert_coords = [xform(vert, q=True, t=True, ws=True) for vert in vert_list]
		return self.average_coords(vert_coords)


	def average_coords(self, coord_list):
		vert_count = len(coord_list)
		vert_sum = [sum(item) for item in zip(*coord_list)]
		average = [item/vert_count for item in vert_sum]
		return average
#-----------------------------------------------------------------------------------

	def zero_dev(self,item):
		# if item 0, prevent zero division with changing it to 000000.1
		if round(item,5) == 0:
			return 1e-10
		else:
			return item

		pass
	def deg_rotation(self, faces_list, rad_vector_list):
		# returns angle between Y axis and average normal of faces from list in world space
		norm_list = [face.getNormal(space='world') for face in faces_list]
		my_norm = sum(norm_list)/len(norm_list)
		print 'clean norm: ',my_norm
		nx,ny,nz = my_norm[0],my_norm[1],my_norm[2]
		
		ny = self.zero_dev(ny)
		nz = self.zero_dev(nz)

		print 'final normal: ',nx,' ', ny,' ', nz
		ytan = nx/nz
		yrot = math.degrees(math.atan(ytan))

		xtan = math.sqrt(nx**2 + nz**2)/ny
		print 'mytan:', xtan
		xrot = math.degrees(math.atan(xtan))

		n = (nx,ny,nz)

		zrot = 0
		#-------------------------------Initial_worldspace_rotation
		if nx < 0 and ny < 0 and nz >0:
			print 'do'
			xrot = 180+xrot
		if nx >= 0 and ny < 0 and nz > 0:
			print 'it'
			xrot= 180+xrot
		if ny < 0 and nz < 0:
			print 'my'
			xrot = 180-xrot
		if ny > 0 and nz < 0:
			print 'friend'
			xrot = -xrot

		#---------------------------------Final object space rotation(can be turned off)
		n_v = dt.Vector(n)
		y_v = dt.Vector(0,1,0)
		cross_v = n_v.cross(y_v)
		print 'getting vector to edge'
		base_v = self.get_vector_to_edge(rad_vector_list)
		print 'getting that angle....'
		wy_rot_quad = angleBetween(v1 = cross_v, v2 = base_v, euler = 0)
		wy_rot = wy_rot_quad[3]
		print 'initial rotation :', wy_rot_quad
		if wy_rot > 90:
			pass
			#y_rot = 180-y_rot
		print 'my y rotation is: ', wy_rot


		print 'my rotations; ',[xrot,yrot,zrot]
		return [xrot,yrot,zrot], wy_rot


	#------------------------------------------------------------
	def get_radius(self,shape, rad_point_list ):
		# return the shortest distance from central point to edge:
		radius = min( rad_point_list )
		obj_type = self.obj_type
		return radius

	def get_vector_to_edge(self, vectors):
		int_vectors = [(vector[0],vector[1],vector[2],) for vector in vectors]
		average = self.average_coords(int_vectors)
		return average 

	def perimeter_vectors(self, base, center_point):
		#convert faces to edge perimeter and flatten list
		base_edges = modeling.polyListComponentConversion( base, ff=True,te=True,bo=True )
		base_edges = ls(base_edges, fl=True)
		# find radius vector and distance to edge for each edge
		return [self.distance_from_center(edge,center_point) for edge in base_edges]


	def distance_from_center(self,edge, center_point):
		#convert edge to list of vertexes and flatten this list
		edge_verts = modeling.polyListComponentConversion( edge, fe=True,tv=True )
		edge_verts = ls(edge_verts, fl=True)

		def make_vector(vert):
			pos = xform(vert, q=True, ws=True, t=True )
			return om.MVector(*pos)

		edge_vectors = [make_vector(item) for item in edge_verts]


		center_vector = om.MVector(*center_point)
		line_vector = edge_vectors[0] - edge_vectors[1]
		normal_line = line_vector.normal()
		a, p, n = edge_vectors[0], center_vector, normal_line
		# find vector for projection from dot to edge
		d_vec= (a-p)-n*((a-p)*n)
		return self.vectror_mod(d_vec), d_vec

	def vectror_mod(self, vec):
		#formula to calculate vector module
		return math.sqrt( vec[0]**2 + vec[1]**2 + vec[2]**2 )

	def bottom_pivot(self,obj):
		#move object pivot to it's bottom
		obj_transform = obj.listConnections(d=True, s=False, t='shape')[0]
		obj_shape = obj_transform.listRelatives()[0]

		try:
			self.p_ratio = obj.getHeight()/2
		except:
			if type(obj) == PolyTorus:
				self.p_ratio = obj.getRadius()/4
			else:
				self.p_ratio = obj.getRadius()
		if type(obj) != PolyPlane:
			cmds.move(0, -self.p_ratio, 0, '{}.scalePivot'.format(obj_transform), '{}.rotatePivot'.format(obj_transform), r=1)
			cmds.move(0, self.p_ratio, 0, r=1, os=1, wd=1)
			#freeze transformation
			makeIdentity(n=0, s=1, r=1, t=1, apply=True, pn=1)
		else:
			pass

#---------------------------------------------------------------------Key Catcher
class KeyCatch(QtWidgets.QWidget):
	#--------------------------data to remember
	snapped = None
	#----------------------------------------

	def __init__(self, parent=None):
		super(KeyCatch,self).__init__(parent)
	#--------------------------------------------Get Maya main window
	def getMainWindow(self):
		ptr = mui.MQtUtil.mainWindow()
		mainWin = wrapInstance(long(ptr), QtWidgets.QWidget)
		return mainWin

	def getViewport(self):
		view = mui.M3dView.active3dView()
		viewport = shiboken2.wrapInstance(long(view.widget()), QtCore.QObject)
		return viewport


	def eventFilter(self, obj, event):
		# try:
		# 	action, mkey = self.key_mod_track(event)
		# 	if action == 'press':
		# 		KlickCatch.pressed_mdfr = mkey
		# 	if action == 'release' and mkey == KlickCatch.pressed_mdfr:
		# 		KlickCatch.pressed_mdfr = None
		# except:
		# 	pass


		if event.type() == QtCore.QEvent.KeyPress:
			key = event.key()
			if (key == QtCore.Qt.Key_Escape 
			or key == QtCore.Qt.Key_Return):
				self.close()
			# if (event.modifiers() == QtCore.Qt.ControlModifier):
			# 	if key == QtCore.Qt.Key_Right:
			# 		MakePrimitive().makeShape('right')
			# 		ui_window.make_table()
			# 	if key == QtCore.Qt.Key_Left:
			# 		MakePrimitive().makeShape('left')
			# 		ui_window.make_table()
			# 	if key == QtCore.Qt.Key_Up:
			# 		MakePrimitive().subd_edit('up','slow')
			# 	if key == QtCore.Qt.Key_Down:
			# 		MakePrimitive().subd_edit('down','slow')
			else:
				pass

	# def key_mod_track(self, event):
	# 	modifiers = { QtCore.Qt.Key_Shift : 'shift',
	# 				QtCore.Qt.Key_Control : 'control',
	# 					QtCore.Qt.Key_Alt : 'alt' }
	# 	event_types = {QtCore.QEvent.KeyPress : 'press' ,QtCore.QEvent.KeyRelease : 'release'}
	# 	e_type = event.type()
	# 	if e_type in event_types.keys():
	# 		key = event.key()
	# 		if key in modifiers.keys():
	# 			return event_types[e_type], modifiers[key]

	
	def closeEvent(self,event):
		try:
			last_obj_type = objectType(self.new_obj[1])
			MakePrimitive().settings.setValue('last_shape', last_obj_type )
		except Exception as e:
			print str(e)
		try:
			maya_window = self.getMainWindow()
			maya_window.removeEventFilter(self)
			viewport.removeEventFilter(self)
			ui_window.setParent(None)
			ui_window.deleteLater()
			# clickEventFilter.setParent(None)
			# clickEventFilter.deleteLater()
			self.setParent(None)
			self.deleteLater()
			maya_window.setVisible(True)
		except Exception as e:
			print str(e)
		print 'Tool Closed'
		
		
#---------------------------------------Global functions
# class KlickCatch(QtWidgets.QWidget):

# 	pressed_mdfr = None

# 	def eventFilter(self, obj, event):
# 		#print 'Current modefier: ', self.pressed_mdfr
# 		if event.type() == QtCore.QEvent.MouseButtonRelease:
# 			button = event.button()
# 			if button == QtCore.Qt.MouseButton.LeftButton and self.pressed_mdfr == None:
# 				now_sel = ls(sl=1, fl=1)
# 				print 'selection: ',now_sel
# 				print 'my obj: ',KeyCatch.new_obj

# 				if KeyCatch.new_obj[0] not in now_sel:
# 					self.close()
# 		else:
# 			pass
# 			#return True
# 		return super(KlickCatch, self).eventFilter(obj, event)


# 	def closeEvent(self,event):
# 		eventFilter.close()

def show():
	global ui_window , key_pressed, maya_window, eventFilter, viewport   #, clickEventFilter
	try:
		eventFilter.close()
	except:
		pass
	

	#----------------------------------------Create the first shape
	new_poly = MakePrimitive().makeShape('right')

	maya_window = KeyCatch().getMainWindow()
	ui_window = Dialog(parent=maya_window)
	#----------------------------------------install Event filter into Maya main Window
	viewport = KeyCatch().getViewport()
	eventFilter = KeyCatch(maya_window)
	maya_window.installEventFilter(eventFilter)
	# clickEventFilter = KlickCatch(maya_window)
	# viewport.installEventFilter(clickEventFilter)
	ui_window.show()
	maya_window.raise_()
	return ui_window

#show()