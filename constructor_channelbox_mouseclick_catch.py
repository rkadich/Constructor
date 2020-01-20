
from PySide2 import QtCore, QtGui, QtWidgets
from maya import mel
from maya import OpenMayaUI as mui
from pymel.all import *
from shiboken2 import wrapInstance
import math
import time
import  maya.OpenMaya as om
import maya.cmds as cmds
#--------------------------------------------------------------------------Dialog Window
class Dialog(QtWidgets.QWidget):

	def __init__(self, parent=None):
		super(Dialog, self).__init__(parent)
		self.constructor_ui()

	def qControl(self,mayaName):
		ptr = mui.MQtUtil.findControl(mayaName)
		if ptr is None:
			ptr = mui.MQtUtil.findLayout(mayaName)
		if ptr is None:
			ptr = mui.MQtUtil.findMenuItem(mayaName)
		return shiboken2.wrapInstance(long(ptr),QtWidgets.QWidget)

	def window_geo(self):
		win_width = 180
		win_height = 380
		# win_height = cmds.channelBox( 'adobe_macromedia_channelbox_009',q=True, h=1)
		# win_width = cmds.channelBox( 'adobe_macromedia_channelbox_009',q=True, w=1)
		print 'window size: ',	win_width, win_height
		win_posx = QtGui.QCursor.pos().x()+ 200
		win_posy = QtGui.QCursor.pos().y() - 20
		if win_posy < 1:
			win_posy = 1
		self.setGeometry(win_posx, win_posy, win_width , win_height)

	def constructor_ui(self):
		self.resize(300,200)
		self.setWindowTitle('Constructor')
		self.setWindowFlags(QtCore.Qt.Tool)      
			
		self.verticalLayout = QtWidgets.QVBoxLayout(self)
		self.verticalLayout.setContentsMargins(0,0,0,0)
		self.verticalLayout.setObjectName("mainLayout")
		
#**************************************************************************ADDING CAHNNELBOX TO LAYOUT

		# #---------------------------------------------------Switch to MEL, make layout and channelBox
		# layout = long(shiboken2.getCppPointer(self.verticalLayout)[0])
		# layoutName = mui.MQtUtil.fullName(layout)
		# cmds.setParent("mainLayout")
		# paneLayoutName = cmds.paneLayout()
		# modelPanelName = cmds.channelBox( 'adobe_macromedia_channelbox_009')
		# print 'inputs: ', windows.channelBox( 'adobe_macromedia_channelbox_009',q=True, npm=1)
		# #----------------------------------------Switch back to Pyside, add wrapped widget to main layout
		# ptr = mui.MQtUtil.findControl(paneLayoutName)
		# self.my_channel_box =  shiboken2.wrapInstance(long(ptr),QtWidgets.QWidget)
		# self.verticalLayout.addWidget(self.my_channel_box)

#***************************************************************************************************

		self.setLayout(self.verticalLayout)
		#----------------------------------resize tool window 
		self.window_geo()

	def closeEvent(self,event):
		eventFilter.close()

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
class Primitive:
	base = ls(sl=1, fl = 1)




	def __init__(self):
			# self.base = ls(sl=1, fl = 1)
		#---------------------------------------create settings in registry. Load last shape created
		self.settings = QtCore.QSettings('PixelEmbargo','Constructor')
		self.last_shape = self.settings.value('last_shape','polyCube')

		self.just_shapes = ['polyCube','polySphere','polyCylinder','polyTorus','polyPlane']

	def extrude_check(self, base):
		last = base[-1]
		if objectType(last) == 'polyExtrudeFace':
			return base[:-1]
		return base
	
	def makeShape(self,direction):
		#-------------------------------------------Make object
		arrow_d = {'right':{'step':1,'first':0},'left':{'step':-1,'first':-1}}
		base = self.base
		base = self.extrude_check(base)
		print 'my_base: ', self.base
		try:
			self.new_obj = KeyCatch.new_obj
			obj_transform, obj_shape  = self.new_obj[0],  self.new_obj[1]
			transform = obj_transform.getTransformation()
			curr_shape = objectType(obj_shape)
			sh_index = self.just_shapes.index(curr_shape)
			next_shape = self.just_shapes[sh_index+arrow_d[direction]['step']]
			print 'new shape is: ',next_shape
		except IndexError:
			#if next list index is beyond the list capacity, go to the first item in list
			next_shape = self.just_shapes[arrow_d[direction]['first']]
			#
		except:
			next_shape = self.last_shape
		try:
			delete(self.new_obj)
		except:
			pass
		command = 'self.new_obj = self.{}()'.format(str(next_shape).replace('poly', 'make'))
		exec(command)

		#-----------------------------------------prescale, snap to selection and transform
		KeyCatch.new_obj = self.new_obj
		obj_transform, obj_shape  = self.new_obj[0],  self.new_obj[1]
	
		if self.selection_mode(base) == 'Faces':
			self.bottom_pivot(obj_shape)

			if KeyCatch.snapped == None:
				self.snap_obj(self.new_obj, base)
				KeyCatch.snapped = 1
		try:
			obj_transform.setTransformation(transform)
			
		except:
			pass
		if self.selection_mode(base) == 'Faces':
			scale_ratio = self.get_radius(base, obj_shape)
			print 'scale_ratio :', scale_ratio
			[ setAttr("{}.scale{}".format(obj_transform ,axis), scale_ratio) for axis in ('X','Y','Z') ]
		select(obj_shape, addFirst=True)
		#_______________________________________ message about subdivisions
		try:
			my_info = obj_shape.getSubdivisionsAxis()
		except:
			try:
				my_info = obj_shape.getSubdivisionsHeight()
			except:
				my_info = 0

		info(message='Subdivisions: '+ str (my_info) )
		#__________________________________________________________________

		return self.new_obj

		#------------------------------------------------Rules for shape subdivision
	def subd_edit(self,direction, pase):
		shape = KeyCatch.new_obj[1]
		shape_type = objectType(shape)
		arrow_d = {'up':{'step':4, 'sl_step':1},'down':{'step':-4,'sl_step':-1}}
		new_width, new_axis = None,None

		if pase == 'slow':
			climb = arrow_d[direction]['sl_step']
		else:
			climb = arrow_d[direction]['step']

		if shape_type == 'polySphere' or shape_type == 'polyTorus':
			curr_axis = shape.getSubdivisionsAxis()
			new_axis = curr_axis + climb
			if new_axis < 3:
				new_axis = curr_axis
			shape.setSubdivisionsAxis(new_axis)
			shape.setSubdivisionsHeight(new_axis)

		if shape_type == 'polyCube':
			curr_width = shape.getSubdivisionsWidth()
			if curr_width == 1:
				new_width = 2
			else:
				new_width = curr_width + climb
			if new_width <= 0:
				new_width= 1
			shape.setSubdivisionsWidth(new_width)
			shape.setSubdivisionsHeight(new_width)
			shape.setSubdivisionsDepth(new_width)

		if shape_type == 'polyCylinder':
			curr_axis = shape.getSubdivisionsAxis()
			new_axis = curr_axis + climb
			if new_axis < 3:
				new_axis = curr_axis
			shape.setSubdivisionsAxis(new_axis)

		if shape_type == 'polyPlane':
			curr_width = shape.getSubdivisionsWidth()
			if curr_width == 1:
				new_width = 2
			else:
				new_width = curr_width + climb
			if new_width <= 0:
				new_width= 1
			shape.setSubdivisionsWidth(new_width)
			shape.setSubdivisionsHeight(new_width)
		else:
			pass
		for item in [new_width, new_axis]:
			if item:
				info(message='Subdivisions: '+ str (item) )

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

	#-------------------------------------------------Figure out the selection type

	def selection_mode(self,selection):
		obj_sel = ls(sl=1, fl = 1)
		try:
			select(selection[0])
		except:
			pass
		modeling.filterExpand( sm=32 )
		s_modes = {12 : 'objects',
				   31 : 'Vertices',
				   32 : 'Edges',
				   34 : 'Faces'
				   }

		for key,value  in s_modes.items():
			mode = modeling.filterExpand( sm=key )
			if mode:
				print s_modes[key]
				select(obj_sel)
				return s_modes[key]

	def face_center(self, my_face):
		face_points = my_face.getPoints(space='world')
		return sum(face_points)/len(face_points)
		
	def facegroup_center(self, face_list):
		face_centers = [self.face_center(face) for face in face_list]
		return sum(face_centers)/len(face_list)

	def zero_dev(self,item):
		# if item 0, prevent zero division with changing it to 000000.1
		if round(item,5) == 0:
			return 1e-10
		else:
			return item

		pass
	def deg_rotation(self,faces_list):
		# returns angle between Y axis and average normal of faces from list in world space
		norm_list = [face.getNormal(space='world') for face in faces_list]
		my_norm = sum(norm_list)/len(norm_list)
		print 'clean norm: ',my_norm
		x,y,z = my_norm[0],my_norm[1],my_norm[2]
		
		y = self.zero_dev(y)
		z = self.zero_dev(z)

		print 'final normal: ',x,' ', y,' ', z
		ytan = x/z
		yrot = math.degrees(math.atan(ytan))

		xtan = math.sqrt(x**2 + z**2)/y
		print 'mytan:', xtan
		xrot = math.degrees(math.atan(xtan))

		zrot = 0

		print 'my rotations; ',[xrot,yrot,zrot]
		return [xrot,yrot,zrot], (x,y,z)

	def snap_obj(self, my_obj, faces_list):
		snap_point = self.facegroup_center(faces_list)
		xform(my_obj, translation = (snap_point[0],snap_point[1],snap_point[2]), ws=True)
		x,y,z = self.deg_rotation(faces_list)[0][0], self.deg_rotation(faces_list)[0][1], self.deg_rotation(faces_list)[0][2]
		# n - Selection Normal
		n = self.deg_rotation(faces_list)[1]
		print 'NNN--- ', n
		nx, ny, nz = n[0], n[1], n[2]
		if nx < 0 and ny < 0 and nz >0:
			print 'do'
			x = 180+x
		if nx >= 0 and ny < 0 and nz > 0:
			print 'it'
			x= 180+x
		if ny < 0 and nz < 0:
			print 'my'
			x = 180-x 
		if ny > 0 and nz < 0:
			print 'friend'
			x = -x
	
		rotate(my_obj, [x,y,z], ws=True)

		#---------------------------------Final object space rotation(can be turned off)
		n_v = dt.Vector(n)
		y_v = dt.Vector(0,1,0)
		cross_v = n_v.cross(y_v)
		base_v = self.get_vector_to_edge(self.base)
		y_rot_quad = angleBetween(v1 = cross_v, v2 = base_v, euler = 0)
		y_rot = y_rot_quad[3]
		print 'initial rotation :', y_rot_quad
		if y_rot > 90:
			pass
			#y_rot = 180-y_rot
		print 'my y rotation is: ', y_rot
		cmds.rotate(0, y_rot, 0, r=1, os=1, fo=1)


	#------------------------------------------------------------
	def get_radius(self,base,shape):
		#convert faces to edge perimeter and flatten list
		base_edges = modeling.polyListComponentConversion( base, ff=True,te=True,bo=True )
		base_edges = ls(base_edges, fl=True)
		# return the shortest distance from central point to edge:
		radius = min( [self.distance_from_center(edge,base)[0] for edge in base_edges] )
		obj_type = objectType(shape)
		print 'WTH object is---------- ',obj_type
		if obj_type == 'polyCube' or obj_type == 'polyPlane':
			print 'it is square'
			radius *=2
		else:
			pass
		return radius

	def get_vector_to_edge(self,base):
		base_edges = modeling.polyListComponentConversion( base, ff=True,te=True,bo=True )
		base_edges = ls(base_edges, fl=True)
		vectors = [self.distance_from_center(edge,base)[1] for edge in base_edges]
		average = sum(vectors)/len(vectors)
		print 'average: ',average
		return average 

	def distance_from_center(self,edge,base):
		#convert edge to list of vertexes and flatten this list
		edge_verts = modeling.polyListComponentConversion( edge, fe=True,tv=True )
		edge_verts = ls(edge_verts, fl=True)

		def make_vector(vert):
			pos = xform(vert, q=True, ws=True, t=True )
			return om.MVector(*pos)

		edge_vectors = [make_vector(item) for item in edge_verts]

		faces_center = self.facegroup_center(base)
		center_vector = om.MVector(*faces_center)
		line_vector = edge_vectors[0] - edge_vectors[1]
		normal_line = line_vector.normal()
		a ,p ,n = edge_vectors[0], faces_center, normal_line
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
		print  'obj_type: ',type(obj)
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
		try:
			action, mkey = self.key_mod_track(event)
			if action == 'press':
				KlickCatch.pressed_mdfr = mkey
			if action == 'release' and mkey == KlickCatch.pressed_mdfr:
				KlickCatch.pressed_mdfr = None
		except:
			pass


		if event.type() == QtCore.QEvent.KeyPress:
			key = event.key()
			if (key == QtCore.Qt.Key_Escape 
			or key == QtCore.Qt.Key_Return):
				print 'escape pressed'
				self.close()
			if (event.modifiers() == QtCore.Qt.ControlModifier):
				if key == QtCore.Qt.Key_Right:
					Primitive().makeShape('right')
				if key == QtCore.Qt.Key_Left:
					Primitive().makeShape('left')
				if key == QtCore.Qt.Key_Up:
					Primitive().subd_edit('up','slow')
				if key == QtCore.Qt.Key_Down:
					Primitive().subd_edit('down','slow')
			else:
				pass

	def key_mod_track(self, event):
		modifiers = { QtCore.Qt.Key_Shift : 'shift',
					QtCore.Qt.Key_Control : 'control',
						QtCore.Qt.Key_Alt : 'alt' }
		event_types = {QtCore.QEvent.KeyPress : 'press' ,QtCore.QEvent.KeyRelease : 'release'}
		e_type = event.type()
		if e_type in event_types.keys():
			key = event.key()
			if key in modifiers.keys():
				return event_types[e_type], modifiers[key]

	
	def closeEvent(self,event):
		refresh(f=True)
		# self.new_poly = None
		try:
			last_obj_type = objectType(self.new_obj[1])
			Primitive().settings.setValue('last_shape', last_obj_type )
		except Exception as e:
			print str(e)
		try:
			maya_window = self.getMainWindow()
			maya_window.removeEventFilter(self)
			viewport.removeEventFilter(self)
			ui_window.setParent(None)
			ui_window.deleteLater()
			clickEventFilter.setParent(None)
			clickEventFilter.deleteLater()
			self.setParent(None)
			self.deleteLater()
			maya_window.setVisible(True)
		except Exception as e:
			print str(e)
		print 'Tool Closed'
		
		
#---------------------------------------Global functions
class KlickCatch(QtWidgets.QWidget):


	def eventFilter(self, obj, event):
		#print 'Current modefier: ', self.pressed_mdfr
		if event.type() == QtCore.QEvent.MouseButtonRelease:
			button = event.button()
			if button == QtCore.Qt.MouseButton.LeftButton and self.pressed_mdfr == None:
				now_sel = ls(sl=1)
				print 'selection: ',now_sel
				print 'my obj: ',KeyCatch.new_obj

				if KeyCatch.new_obj[0] not in now_sel:
					print 'deselected'
					print "CLICK"
					eventFilter.close()
		else:
			pass
			#return True
		return super(KlickCatch, self).eventFilter(obj, event)


	def closeEvent(self,event):
		eventFilter.close()


def show():
	global ui_window , key_pressed, maya_window, eventFilter, viewport, clickEventFilter
	try:
		eventFilter.close()
	except:
		pass
	
	maya_window = KeyCatch().getMainWindow()
	ui_window = Dialog(parent=maya_window)
	#----------------------------------------install Event filter into Maya main Window
	viewport = KeyCatch().getViewport()
	eventFilter = KeyCatch(maya_window)
	maya_window.installEventFilter(eventFilter)
	clickEventFilter = KlickCatch(maya_window)
	viewport.installEventFilter(clickEventFilter)
	#----------------------------------------Create the first shape
	viewport.new_poly = Primitive().makeShape('right')
	ui_window.show()
	maya_window.raise_()
	return ui_window

#show()