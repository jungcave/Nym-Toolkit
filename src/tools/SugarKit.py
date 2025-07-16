import bpy
from bpy.types import bpy_prop_collection
from bpy.app.handlers import persistent
from types import SimpleNamespace
import math
from .SugarKit_helpers import *


def Props(isRegister):
    if not isRegister:
        return

    def handleActiveVertGroupNameUpdate(self, context):
        self.vertex_groups.active.name = self.nym_active_vert_group_name

    def handleActiveBrushTextureImageUpdate(self, context):
        setActiveBrushTextureImageInContext(
            context, self.nym_active_brush_texture_image)

    if isRegister:
        bpy.types.Object.nym_active_vert_group_name = bpy.props.StringProperty(
            name="",
            update=handleActiveVertGroupNameUpdate
        )
        bpy.types.Scene.nym_active_brush_texture_image = bpy.props.PointerProperty(
            name="",
            type=bpy.types.Image,
            update=handleActiveBrushTextureImageUpdate
        )
    else:
        del bpy.types.Object.nym_active_vert_group_name
        del bpy.types.Scene.nym_active_brush_texture_image


def Menus(isRegister):
    def view3d_mt_view(self, context):
        self.layout.separator()
        self.layout.operator_context = "INVOKE_DEFAULT"
        self.layout.operator(ObjectViewportAlphaToggleOperator.bl_idname)

    if isRegister:
        bpy.types.VIEW3D_MT_view.append(view3d_mt_view)
    else:
        bpy.types.VIEW3D_MT_view.remove(view3d_mt_view)


def Subscriptions(isRegister):
    SubscribeBrushColor(isRegister)
    SubscribeWorkSpace(isRegister)


# / Window Utils


glob = SimpleNamespace()
glob.event = SimpleNamespace()


class WindowUpdateGlobalEventOperator(bpy.types.Operator):
    bl_idname = "window.nym_update_global_event"
    bl_label = ""

    def invoke(self, context, event):
        global glob
        # New SimpleNamespace event from bpy_dict event
        glob.event = simplenamespace(event)
        return {'FINISHED'}


glob.event.mouse_prev_x = -1
glob.event.mouse_prev_y = -1


def updateGlobalEvent(event=None):
    global glob
    if not event:
        # Call from bpy.msgbus.subscribe_rna
        bpy.ops.window.nym_update_global_event('INVOKE_REGION_WIN')
        return glob.event
    else:
        # Call from bpy.type.Operator invoke
        glob.event = simplenamespace(event)


def getSpaceUnderMouseFromContext(context, event=None):
    global glob
    mouseX = event.mouse_prev_x if event else glob.event.mouse_prev_x
    mouseY = event.mouse_prev_y if event else glob.event.mouse_prev_y
    for area in context.screen.areas:
        if isAreaUnderMousePointer(area, mouseX, mouseY):
            return area.spaces[0]
    return None


def isAreaUnderMousePointer(area, x, y):
    inX = x >= area.x and x <= area.x + area.width
    inY = y >= area.y and y <= area.y + area.height
    return inX and inY


# / Object Viewport Alpha/Color


class ObjectViewportAlphaToggleOperator(bpy.types.Operator):
    """Toggle object's viewport display color alpha."""
    bl_label = "Toggle Opacity"
    bl_idname = "object.nym_object_toggle_viewport_alpha"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len(context.selected_objects)

    def execute(self, context):
        actObj = context.active_object
        actObjActMat = actObj.active_material
        actObjActMatIdx = actObj.active_material_index
        noMatSlots = not actObj.material_slots or not len(
            actObj.material_slots)

        if not actObjActMat:
            if noMatSlots:
                actObjActMat = appendNewActMatToObject(actObj)
            elif not actObj.material_slots[actObjActMatIdx].material:
                actObjActMat = appendNewActMatToObject(
                    actObj, matSlot=actObj.material_slots[actObjActMatIdx])

        r, g, b, a = actObjActMat.diffuse_color

        for obj in context.selected_objects:
            # Set object materials viewport alpha
            if not obj.material_slots or not len(obj.material_slots):
                appendNewActMatToObject(
                    obj, (1.0, 1.0, 1.0, 0.3 if a == 1.0 else 1.0))
            else:
                for ms in obj.material_slots:
                    mat = ms.material
                    mR, mG, mB, mA = mat.diffuse_color
                    mat.diffuse_color = (
                        mR, mG, mB, 0.3 if a == 1.0 else 1.0)
            # Set object viewport alpha
            if 'color' not in obj:
                setattr(obj, 'color', (1.0, 1.0, 1.0, 0.3 if a == 1.0 else 1.0))
            else:
                oR, oG, oB, oA = obj.color
                obj.color = (
                    oR, oG, oB, 0.3 if a == 1.0 else 1.0)

        return {'FINISHED'}


class ObjectViewportColorSetPanelOperator(bpy.types.Operator):
    # This operator inits values for ObjectViewportColorSetPanel
    """Set object's active material viewport display color."""
    bl_label = "Set Viewport Color"
    bl_idname = "object.nym_active_material_viewport_color_panel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        obj = context.active_object

        if not obj.material_slots or not len(obj.material_slots):
            appendNewActMatToObject(obj)

        mR, mG, mB, mA = context.active_object.active_material.diffuse_color

        # Init panel picker with mat color
        context.scene.tool_settings.gpencil_paint.brush.color = (mR, mG, mB)

        try:
            paletteColors = context.scene.tool_settings.gpencil_paint.palette.colors
        except Exception as er:
            paletteColors = None

        # Init/unset panel palette with mat color
        if (paletteColors):
            unsetActive = True
            for paletteColor in paletteColors:
                pcR, pcG, pcB = paletteColor.color
                if (pcR == mR and pcG == mG and pcB == mB):
                    unsetActive = False
                    paletteColors.active = paletteColor
            if (unsetActive):
                paletteColors.active = None

        # Select only objects with active material
        bpy.ops.object.select_linked(extend=False, type='MATERIAL')

        # Activate unified color to fix layout.template_palette color add
        context.scene.tool_settings.unified_paint_settings.use_unified_color = True

        bpy.ops.wm.call_panel(
            name=ObjectViewportColorSetPanel.bl_idname)

        return {'FINISHED'}


class ObjectViewportColorSetPanel(bpy.types.Panel):
    # This panel's changes trigger SubscribeBrushColor
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Set Viewport Color"
    bl_idname = "nym_active_material_viewport_color_panel"
    bl_ui_units_x = 10  # width

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paint = context.scene.tool_settings.gpencil_paint

        if context.object:
            col = layout.column()
            col.template_color_picker(paint.brush, "color", value_slider=True)

            sub_row = layout.row(align=True)
            sub_row.prop(paint.brush, "color", text="")

            row = layout.row(align=True)
            row.template_ID(paint, "palette", new="palette.new")

            if paint.palette:
                layout.template_palette(paint, "palette", color=True)


glob.prevPaletteColor = None


def SubscribeBrushColor(isRegister=True):
    brushColorOwner = object()

    def setObjectViewportColorSet():
        global glob

        try:
            mat = bpy.context.active_object.active_material
        except Exception as er:
            mat = None
        try:
            unifiedPaintSettings = bpy.context.scene.tool_settings.unified_paint_settings
        except Exception as er:
            unifiedPaintSettings = None
        try:
            brush = bpy.context.scene.tool_settings.gpencil_paint.brush
        except Exception as er:
            brush = None
        try:
            paletteColor = bpy.context.scene.tool_settings.gpencil_paint.palette.colors.active.color
        except Exception as er:
            paletteColor = None

        global_event = updateGlobalEvent()
        space = getSpaceUnderMouseFromContext(
            bpy.context, global_event)

        if (bpy.context.mode != 'OBJECT' or space.type != 'VIEW_3D' or not mat):
            glob.prevPaletteColor = paletteColor
            return

        def setObjectUsersOfMatWithColor(r, g, b):
            for obj in getObjectUsersOfMat(mat, bpy.data.objects):
                firstMat = list(obj.material_slots)[0].material
                if (firstMat == mat):
                    obj.color = (r, g, b, 1.0)

        if (paletteColor == glob.prevPaletteColor):
            # Color changed by picker
            if (brush and brush.color):
                bcR, bcG, bcB = brush.color
                mat.diffuse_color = (bcR, bcG, bcB, 1.0)
                if (unifiedPaintSettings):
                    unifiedPaintSettings.color = (bcR, bcG, bcB)
                setObjectUsersOfMatWithColor(bcR, bcG, bcB)
        else:
            # Color changed by palette
            if (paletteColor):
                pcR, pcG, pcB = paletteColor
                mat.diffuse_color = (pcR, pcG, pcB, 1.0)
                if (brush):
                    brush.color = (pcR, pcG, pcB)
                setObjectUsersOfMatWithColor(pcR, pcG, pcB)

        glob.prevPaletteColor = paletteColor

    def handleBrushColorChange():
        # After ObjectViewportColorSetPanel changes
        setObjectViewportColorSet()

    def subscribeBrushColor():
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Brush, 'color'),
            owner=brushColorOwner,
            args=(),
            notify=handleBrushColorChange,
            options={"PERSISTENT"}
        )

    @persistent
    def resubscribeBrushColor(dummy):
        subscribeBrushColor()

    def unsubscribeBrushColor():
        bpy.msgbus.clear_by_owner(brushColorOwner)

    if (isRegister):
        subscribeBrushColor()
        bpy.app.handlers.load_post.append(resubscribeBrushColor)
    else:
        unsubscribeBrushColor()


# / Modifier Setups


class ModifierSetupAxisBendOperator(bpy.types.Operator):
    bl_label = "Add Modifier Setup"
    bl_idname = "object.nym_modifier_setup_axis_bend"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        obj = context.active_object

        empty = bpy.data.objects.new(name="_bend_empty", object_data=None)
        bpy.context.collection.objects.link(empty)
        empty.parent = obj
        # Justifies empty's rotation (in ui its done automatically)
        empty.scale = obj.scale

        modifier = obj.modifiers.new(
            name="Simple Deform", type='SIMPLE_DEFORM')
        modifier.deform_method = 'BEND'
        modifier.origin = empty

        obj.select_set(False)
        empty.select_set(True)
        bpy.context.view_layer.objects.active = empty

        return {'FINISHED'}


class ModifierSetupRadialArrayOperator(bpy.types.Operator):
    bl_label = "Add Modifier Setup"
    bl_idname = "object.nym_setup_radial_array_modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        obj = context.active_object
        applyObjectTransformsWithContext(context, obj, ['scale'])

        empty = bpy.data.objects.new(name="_radial_empty", object_data=None)
        bpy.context.collection.objects.link(empty)
        empty.parent = obj

        modifier = obj.modifiers.new(
            name="Array", type='ARRAY')
        modifier.use_relative_offset = False
        modifier.use_object_offset = True
        modifier.offset_object = empty

        obj.select_set(False)
        empty.select_set(True)
        bpy.context.view_layer.objects.active = empty

        return {'FINISHED'}


# TODO: 3.2.x
# SetupGeoNodeModifierOperator [shift alt dbl G]
# - ask to add geo node (list existing)
# - add geo node modifier


# TODO: 3.2.x
# SetupCurveArrayModifierOperator [shift alt C A]
# * if curve not selected or many selected target objects:
#   - return
# * if many curves selected:
#   - join selected curves (to separete them alltogether later)
# * if target object not selected:
#   - sample target object
# when both curve/s and target object selected:
# - CurveAppendToObjectWithModifiersOperator


# TODO: 3.2.x
# CurveAppendToObjectWithModifiersOperator
# - separete curve by loose splines
# part 1:
# - center target origin and active curve origin
# - move target to active curve
# - apply target scale and copy rotation from active curve
# - parent active curve to target (and target to curve parent if parent exists)
# part 2:
# * if target already has array and curve mods:
#   - delete array and curve mods
# - add array modifier to target: set type to fit curve and curve to the parented curve
# - add curve modifier to target: set curve to the parented curve
# part 3:
# * for each separated curve spline do parts 1-3:
#   - duplicate parent target object (with linked data)
#   - parent duplicated object to original target
#   - set duplicated object as new target
#   - execute parts 1 and 2 (change modifiers curve target)
#
# https://blenderartists.org/t/how-to-draw-an-object-selection-eyedropper-in-an-addon/1287437/8?u=nyamba


# / Outliner Select Grouped


class OutlinerUnhideAllCollectionsOperator(bpy.types.Operator):
    bl_label = "Outliner Unhide All Collections"
    bl_idname = "outliner.nym_outliner_unhide_all_collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            collections = context.scene.view_layers[0].layer_collection.children
        except Exception as er:
            collections = None
        if not collections or not len(collections):
            return {'FINISHED'}
        for col in collections:
            col.hide_viewport = False
        return {'FINISHED'}


class OutlinerSelectGroupedOperator(bpy.types.Operator):
    bl_label = "Outliner Select Grouped"
    bl_idname = "outliner.nym_outliner_select_grouped"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        mode = getObjectModeFromContextMode(context.mode)

        if mode == 'OBJECT':
            bpy.ops.object.select_grouped(type='COLLECTION')
        else:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_grouped(type='COLLECTION')
            bpy.ops.object.mode_set(mode=mode)

        return {'FINISHED'}


class OutlinerSelectGroupedUnhideOperator(bpy.types.Operator):
    bl_label = "Outliner Select Grouped Unhide"
    bl_idname = "outliner.nym_outliner_select_grouped_unhide"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(getOutlinerActivatedObjectsFromContext(context))

    def execute(self, context):
        act = context.active_object
        group = act.users_collection
        mode = getObjectModeFromContextMode(context.mode)

        if mode == 'OBJECT':
            selectUnhideAllInGroup(group)
        else:
            bpy.ops.object.mode_set(mode='OBJECT')
            selectUnhideAllInGroup(group)
            bpy.ops.object.mode_set(mode=mode)

        return {'FINISHED'}


# / Vertex Groups


class VertexGroupRenamePanelOperator(bpy.types.Operator):
    bl_label = "Vertex Group Rename"
    bl_idname = "mesh.nym_vertex_group_rename"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            actObjVertGroup = context.active_object.vertex_groups.active
        except Exception as er:
            actObjVertGroup = None
        return actObjVertGroup

    def execute(self, context):
        vertGroupName = context.active_object.vertex_groups.active.name
        context.active_object.nym_active_vert_group_name = vertGroupName

        bpy.ops.wm.call_panel(
            name=VertexGroupRenamePanel.bl_idname, keep_open=False)
        return {'FINISHED'}


def row_with_icon(layout, icon):
    row = layout.row()
    row.activate_init = True
    row.label(icon=icon)
    return row


class VertexGroupRenamePanel(bpy.types.Panel):
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Rename Active Vertex Group"
    bl_idname = 'TOPBAR_PT_name_active_vertex_group'
    bl_ui_units_x = 14

    def draw(self, context):
        found = False

        if context.mode == 'EDIT_MESH':
            self.layout.label(text="Vertex Group Name")
            target = context.active_object
            if target:
                row = row_with_icon(self.layout, 'MESH_DATA')
                row.prop(target, "nym_active_vert_group_name", text="")
                found = True

        if not found:
            row = row_with_icon(self.layout, 'ERROR')
            row.label(text="No active vertex group")


class VertexGroupToSculptFaceSetOperator(bpy.types.Operator):
    bl_label = "Vertex Group To Sculpt Face Set"
    bl_idname = "paint.nym_vertex_group_to_sculpt_face_set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            actObjVertGroup = context.active_object.vertex_groups.active
        except Exception as er:
            actObjVertGroup = None
        return actObjVertGroup

    def execute(self, context):
        mode = getObjectModeFromContextMode(context.mode)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.mode_set(mode=mode)
        bpy.ops.sculpt.face_sets_create(mode='SELECTION')
        return {'FINISHED'}


class VertexGroupToPaintSelectMaskOperator(bpy.types.Operator):
    bl_label = "Vertex Group To Paint Select Mask"
    bl_idname = "paint.nym_vertex_group_to_paint_select_mask"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            actObjVertGroup = context.active_object.vertex_groups.active
        except Exception as er:
            actObjVertGroup = None
        return actObjVertGroup

    def execute(self, context):
        mode = getObjectModeFromContextMode(context.mode)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}


# / Curve Tools


class CurveSelectWholeHandlePointsOperator(bpy.types.Operator):
    bl_label = "Curve Select Whole Handle Points"
    bl_idname = "curve.nym_curve_select_whole_handle_points"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        actPoint = getCurveActivePoint(context.active_object, True)
        selectWholeBezierPoint(actPoint)
        return {'FINISHED'}


class CurveToggleDepthOperator(bpy.types.Operator):
    bl_label = "Curve Toggle Depth"
    bl_idname = "curve.nym_curve_toggle_depth"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            curveData = context.active_object.data
        except Exception as er:
            curveData = None
        return curveData and context.active_object.type == "CURVE"

    def execute(self, context):
        curveData = context.active_object.data
        curveData.bevel_depth = 0.01 if curveData.bevel_depth == 0.0 else 0.0
        return {'FINISHED'}


class CurveToggleFillCapsOperator(bpy.types.Operator):
    bl_label = "Curve Toggle Fill Caps"
    bl_idname = "curve.nym_curve_toggle_fill_caps"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            curveData = context.active_object.data
        except Exception as er:
            curveData = None
        return curveData and context.active_object.type == "CURVE"

    def execute(self, context):
        curveData = context.active_object.data
        curveData.use_fill_caps = True if curveData.use_fill_caps == False else False
        return {'FINISHED'}


# TODO: 3.2.x
# CurveSeparateByLooseSplines [shift alt J]


# / Brush Tools


class BrushTextureImageSetMenuOperator(bpy.types.Operator):
    bl_label = "Brush Texture Image Set Menu"
    bl_idname = "paint.nym_brush_texture_image_set_active_menu"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tex = getActiveBrushTextureInContext(context)
        if not tex:
            self.report({'INFO'}, "Brush has no texture!")
            return {'FINISHED'}

        context.scene.nym_active_brush_texture_image = tex.image
        bpy.ops.wm.call_menu(
            name=BrushTextureImageSetMenu.bl_idname)
        return {'FINISHED'}


class BrushTextureImageSetMenu(bpy.types.Menu):
    bl_label = "Set Texture Image"
    bl_idname = "nym_brush_texture_image_set_active_menu"

    def draw(self, context):
        layout = self.layout
        layout.template_ID(
            context.scene, "nym_active_brush_texture_image", new="image.new", open="image.open")


# / Sculpt Tools


class SculptDrawCurveOperator(bpy.types.Operator):
    bl_label = "Sculpt Quick Draw Curve"
    bl_idname = "sculpt.nym_sculpt_draw_curve"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def invoke(self, context, event):
        context.tool_settings.curve_paint_settings.curve_type = 'BEZIER'
        context.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        return self.execute(context)

    def execute(self, context):
        act = context.active_object
        drawCurve = createCurveAndEditInContext(context, 'DrawCurve')
        drawCurve.data.bevel_depth = 0.01
        drawCurve.data.use_fill_caps = True
        # TODO: put the same collection as parent
        drawCurve.parent = act
        return {'FINISHED'}


# TODO: 3.2.x Make modal keys setable from keymap settings
class SculptTrimCurveModalOperator(bpy.types.Operator):
    thanks = [
        'https://blenderartists.org/t/how-can-i-ask-the-user-to-draw-a-curve/1462361',
        'https://blenderartists.org/t/using-grease-pencil-annotation-from-modal-in-blender-2-8/1203973',
        "https://www.youtube.com/watch?v=3C6wVPVrPtM",
    ]
    bl_idname = "sculpt.nym_trim_curve_modal"
    bl_label = "Sculpt Trim Curve Modal"
    bl_options = {"REGISTER", "UNDO"}

    DRAW_HEADER_TEXT = "Trim Curve Innards (Draw)"
    DRAW_STATUS_TEXT = """
      Cancel: Esc | 
      Pass: Ent/Space | 
      Draw: LM
    """
    HEADER_TEXT = "Trim Curve Innards"
    EXTERIOR_HEADER_TEXT = "Trim Curve Exterior"
    STATUS_TEXT = """
      Cancel: Esc | 
      Confirm: Ent/Space | 
      Close: Shift+Ctrl+LM | 
      Select: LM | 
      Extend: Shift+LM | 
      Extrude: Dbl-LM/E | 
      Insert/Delete: Alt+LM | 
      Dissolve: Ctrl+X | 
      Move/Scale/Rotate: RM/Shift+RM/Ctrl+RM | 
      Innards/Exterior: T | 
      Cyclic: Shift+C | 
      Smooth: Shift+Alt+S | 
      Whole: Dbl+Shift | 
      Align/Free: Dbl+Ctrl | 
      Auto/Vector: Dbl+Alt/Ctrl+Dbl+Alt | 
      Recalc: Shift+R | 
      All: A | 
      Invert: Alt+A | 
      Transform: S/D/R | 
      Prop-editing: P | 
      Focus: F | 
      Redo: Shift+Ctrl+Z | 
      Undo: Ctrl+Z
    """

    view3dSpace = bpy.props.PointerProperty(type=bpy.types.SpaceView3D)
    initIsOrthographic = bpy.props.BoolProperty(name="")
    isFinish = bpy.props.BoolProperty(name="")
    isDraw = bpy.props.BoolProperty(name="")
    isExterior = bpy.props.BoolProperty(name="")
    initWorkSpace = bpy.props.PointerProperty(type=bpy.types.WorkSpace)
    targetObj = bpy.props.PointerProperty(type=bpy.types.Object)
    trimCurve = bpy.props.PointerProperty(type=bpy.types.Curve)

    disabledDrawKeymapItemsIds = []
    disabledPenKeymapItemsIds = []
    hasUnabledBackDrawKeymapItems = False
    hasUnabledBackPenKeymapItems = False

    historySteps = 0
    dbl = {}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def invoke(self, context, event):
        self.initProps(self, context, event)
        self.mapModalToolKeys(self, context, True)

        context.window_manager.modal_handler_add(self)  # required for modal

        setModalTextInContext(
            context, self.DRAW_HEADER_TEXT, self.DRAW_STATUS_TEXT)

        context.tool_settings.curve_paint_settings.curve_type = 'BEZIER'
        context.tool_settings.curve_paint_settings.depth_mode = 'CURSOR'
        context.tool_settings.use_proportional_edit = False

        return {'RUNNING_MODAL'}

    @classmethod
    def initProps(cls, self, context, event):
        self.view3dSpace = getSpaceUnderMouseFromContext(context, event)
        self.initIsOrthographic = self.view3dSpace.region_3d.is_orthographic_side_view
        self.isFinish = False
        self.isDraw = True
        self.isExterior = False
        self.initWorkSpace = findBpyObjectByName(
            context.window.workspace.name, bpy.data.workspaces)
        self.targetObj = findBpyObjectByName(context.active_object.name)
        self.trimCurve = createCurveAndEditInContext(
            context, 'TrimCurve', inFront=True)
        self.trimCurve.parent = self.targetObj

    @classmethod
    def mapModalToolKeys(cls, self, context, isSet):
        drawKeymap = getKeymapFromContext(
            context, '3D View Tool: Edit Curve, Draw', 'user')
        penKeymap = getKeymapFromContext(
            context, '3D View Tool: Edit Curve, Curve Pen', 'user')

        if isSet:
            # Disable old
            self.disabledDrawKeymapItemsIds = disableActiveKeymapItems(
                drawKeymap)
            self.disabledPenKeymapItemsIds = disableActiveKeymapItems(
                penKeymap)
            # Append new
            self.appendModalToolKeys(drawKeymap, penKeymap)
        else:
            # Remove new
            if not self.hasUnabledBackDrawKeymapItems:
                removeActiveKeymapItems(drawKeymap)
                self.hasUnabledBackDrawKeymapItems = True
            if not self.hasUnabledBackPenKeymapItems:
                removeActiveKeymapItems(penKeymap)
                self.hasUnabledBackPenKeymapItems = True
            # Unable old
            unableDisabledKeymapItems(
                drawKeymap, self.disabledDrawKeymapItemsIds)
            unableDisabledKeymapItems(
                penKeymap, self.disabledPenKeymapItemsIds)

    @classmethod
    def appendModalToolKeys(cls, drawKeymap, penKeymap):
        if drawKeymap and drawKeymap.keymap_items:
            # Draw
            kmiDrawDraw = drawKeymap.keymap_items.new(
                'curve.draw', 'LEFTMOUSE', 'PRESS')
            kmiDrawDraw.properties['wait_for_input'] = False

        if penKeymap and penKeymap.keymap_items:
            # Extend
            kmiPenExtend = penKeymap.keymap_items.new(
                'curve.pen', 'LEFTMOUSE', 'PRESS', shift=True)
            # kmiPenExtend.properties['select_point'] = True
            kmiPenExtend.properties['extend'] = True
            # Select
            kmiPenSelect = penKeymap.keymap_items.new(
                'curve.pen', 'LEFTMOUSE', 'PRESS')
            kmiPenSelect.properties['select_point'] = True
            # Quick extrude
            kmiPenExtrude = penKeymap.keymap_items.new(
                'curve.pen', 'LEFTMOUSE', 'DOUBLE_CLICK')
            kmiPenExtrude.properties['extrude_point'] = True
            # Close
            kmiPenClose = penKeymap.keymap_items.new(
                'curve.pen', 'LEFTMOUSE', 'PRESS', shift=True, ctrl=True)
            kmiPenClose.properties['close_spline'] = True
            kmiPenClose.properties['close_spline_method'] = 1
            # Insert/delete
            kmiPenInsertDelete = penKeymap.keymap_items.new(
                'curve.pen', 'LEFTMOUSE', 'PRESS', alt=True)
            kmiPenInsertDelete.properties['insert_point'] = True
            kmiPenInsertDelete.properties['delete_point'] = True
            # Quick move
            kmiPenDrag = penKeymap.keymap_items.new(
                'transform.translate', 'RIGHTMOUSE', 'CLICK_DRAG')
            kmiPenDrag.properties['use_snap_self'] = True
            kmiPenDrag.properties['use_snap_edit'] = True
            kmiPenDrag.properties['use_snap_nonedit'] = True
            # Quick rotate
            kmiPenDrag = penKeymap.keymap_items.new(
                'transform.rotate', 'RIGHTMOUSE', 'CLICK_DRAG', shift=True)
            # Quick scale
            kmiPenDrag = penKeymap.keymap_items.new(
                'transform.resize', 'RIGHTMOUSE', 'CLICK_DRAG', ctrl=True)

    def modal(self, context, event):
        # C(event.type, ": ", event.value)
        try:
            global glob
            isPen = not self.isDraw

            # / FINISHED
            if self.isFinish and not event.type == 'ESC':
                if not glob.trimCurveResolution:
                    if event.value == 'RELEASE':
                        self.isFinish = False
                        return {'RUNNING_MODAL'}
                    else:
                        return {'PASS_THROUGH'}
                else:
                    return self.finish(self, context, glob.trimCurveResolution)
            elif event.type in ['RET', 'SPACE']:
                if isPen:
                    bpy.ops.curve.nym_curve_resolution_dialog('INVOKE_DEFAULT')
                    self.isFinish = True
                    return {'RUNNING_MODAL'}
                else:
                    setModalTextInContext(
                        context, self.HEADER_TEXT, self.STATUS_TEXT)
                    bpy.ops.wm.tool_set_by_id(name='builtin.pen')
                    self.isDraw = False
                    return {'PASS_THROUGH'}

            # / CANCELLED
            elif event.type == 'ESC' and event.value == 'PRESS':
                setActiveObjectInContext(
                    context, self.targetObj, delPrev=True, mode='SCULPT')
                setModalTextInContext(context, None)
                self.mapModalToolKeys(self, context, False)
                return {'CANCELLED'}
            # Workspace has changed
            elif event.value == 'PRESS' and self.initWorkSpace.name != context.window.workspace.name:
                setModalTextInContext(context, None)
                self.mapModalToolKeys(self, context, False)
                return {'CANCELLED'}
            # Tool has changed from ui
            elif (self.isDraw and glob.workspaceActiveToolName != 'builtin.draw') or (isPen and glob.workspaceActiveToolName != 'builtin.pen'):
                setModalTextInContext(context, None)
                self.mapModalToolKeys(self, context, False)
                return {'CANCELLED'}

            # / PASSED DRAW OPS
            # Start
            elif self.isDraw and event.type == 'LEFTMOUSE':
                return {'PASS_THROUGH'}
            # End
            elif self.isDraw and len(getCurvePointsAll(context.active_object)):
                setModalTextInContext(
                    context, self.HEADER_TEXT, self.STATUS_TEXT)
                bpy.ops.wm.tool_set_by_id(name='builtin.pen')
                self.isDraw = False
                return {'PASS_THROUGH'}

            # / PASSED PEN OPS
            # Close
            elif isPen and event.type == 'LEFTMOUSE' and event.shift and event.ctrl:
                self.historySteps += 1
                return {'PASS_THROUGH'}
            # Extend
            elif isPen and event.type == 'LEFTMOUSE' and event.shift:
                self.historySteps += 1
                return {'PASS_THROUGH'}
            # Select
            elif isPen and event.type == 'LEFTMOUSE' and not self.dbl.get('LEFTMOUSE'):
                self.historySteps += 1
                self.dbl['LEFTMOUSE'] = addTimerForContext(context)
                return {'PASS_THROUGH'}
            # Extrude
            elif isPen and event.type == 'LEFTMOUSE' and self.dbl.get('LEFTMOUSE'):
                # Add point only to existing spline
                curve = context.active_object
                actPoint = getCurveActivePoint(curve)
                points = curve.data.splines[0].bezier_points
                if not actPoint or actPoint != points[0]:
                    curve.data.splines[0].bezier_points[len(
                        points) - 1].select_control_point = True

                self.dbl['LEFTMOUSE'] = removeTimerFromContext(
                    context, self.dbl.get('LEFTMOUSE'))
                return {'PASS_THROUGH'}
            # Insert/delete
            elif isPen and event.type == 'LEFTMOUSE' and event.alt:
                self.historySteps += 1
                return {'PASS_THROUGH'}
            # Drag
            elif isPen and event.type == 'RIGHTMOUSE' and event.value not in ['RELEASE', 'CLICK']:
                return {'PASS_THROUGH'}

            # / RUNNING PEN OPS
            # Toggle innards/exterior
            elif isPen and event.type == 'T' and event.value == 'PRESS':
                self.isExterior = not self.isExterior
                setModalTextInContext(
                    context, self.HEADER_TEXT if not self.isExterior else self.EXTERIOR_HEADER_TEXT, self.STATUS_TEXT)
                return {'RUNNING_MODAL'}
            # Dissolve
            elif isPen and event.type == 'X' and event.ctrl and event.value == 'PRESS':
                self.historySteps += 1
                bpy.ops.curve.dissolve_verts()
                return {'RUNNING_MODAL'}
            # Curve cyclic (close)
            elif isPen and event.type == 'C' and event.shift and event.value == 'PRESS':
                bpy.ops.curve.cyclic_toggle()
                return {'RUNNING_MODAL'}
            # Curve smooth
            elif isPen and event.type == 'S' and event.shift and event.alt and event.value == 'PRESS':
                self.historySteps += 1
                bpy.ops.curve.smooth()
                return {'RUNNING_MODAL'}
            # Extrude
            elif isPen and event.type == 'E' and event.value == 'PRESS':
                bpy.ops.curve.extrude_move('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            # Select whole handle
            elif isPen and event.type in ['LEFT_SHIFT'] and event.value == 'PRESS' and not self.dbl.get('SHIFT'):
                self.dbl['SHIFT'] = addTimerForContext(context)
                return {'PASS_THROUGH'}
            elif isPen and event.type in ['LEFT_SHIFT'] and event.value == 'PRESS' and self.dbl.get('SHIFT'):
                actPoint = getCurveActivePoint(context.active_object, True)
                selectWholeBezierPoint(actPoint)

                self.dbl['SHIFT'] = removeTimerFromContext(
                    context, self.dbl.get('SHIFT'))
                return {'RUNNING_MODAL'}
            # Handlers type aligned/free, auto, vector
            elif isPen and event.type in ['LEFT_CTRL'] and event.value == 'PRESS' and not self.dbl.get('CTRL'):
                self.dbl['CTRL'] = addTimerForContext(context)
                return {'PASS_THROUGH'}
            elif isPen and event.type in ['LEFT_CTRL'] and event.value == 'PRESS' and self.dbl.get('CTRL'):
                actPoint = getCurveActivePoint(context.active_object)
                if actPoint and actPoint.handle_left_type in ['FREE', 'VECTOR']:
                    bpy.ops.curve.handle_type_set(type='ALIGNED')
                else:
                    bpy.ops.curve.handle_type_set(type='FREE_ALIGN')
                self.dbl['CTRL'] = removeTimerFromContext(
                    context, self.dbl.get('CTRL'))
                return {'RUNNING_MODAL'}
            elif isPen and event.type in ['LEFT_ALT'] and not event.ctrl and event.value == 'PRESS' and not self.dbl.get('ALT'):
                self.dbl['ALT'] = addTimerForContext(context)
                return {'PASS_THROUGH'}
            elif isPen and event.type in ['LEFT_ALT'] and not event.ctrl and event.value == 'PRESS' and self.dbl.get('ALT'):
                bpy.ops.curve.handle_type_set(type='AUTOMATIC')
                self.dbl['ALT'] = removeTimerFromContext(
                    context, self.dbl.get('ALT'))
                return {'RUNNING_MODAL'}
            elif isPen and event.type in ['LEFT_ALT'] and event.ctrl and event.value == 'PRESS' and not self.dbl.get('ALT'):
                self.dbl['LEFT_ALT'] = addTimerForContext(context)
                return {'PASS_THROUGH'}
            elif isPen and event.type in ['LEFT_ALT'] and event.ctrl and event.value == 'PRESS' and self.dbl.get('ALT'):
                bpy.ops.curve.handle_type_set(type='VECTOR')
                self.dbl['ALT'] = removeTimerFromContext(
                    context, self.dbl.get('ALT'))
                return {'RUNNING_MODAL'}
            # Handlers recalc
            elif isPen and event.type == 'R' and event.shift and event.value == 'PRESS':
                bpy.ops.curve.normals_make_consistent()
                return {'RUNNING_MODAL'}
            # All de/select, invert
            elif isPen and event.type == 'A' and event.value == 'PRESS':
                if getCurveActivePoint(context.active_object):
                    bpy.ops.curve.select_all(action='DESELECT')
                else:
                    bpy.ops.curve.select_all(action='SELECT')
                return {'RUNNING_MODAL'}
            elif isPen and event.type == 'A' and event.alt and event.value == 'PRESS':
                bpy.ops.curve.select_all(action='INVERT')
                return {'RUNNING_MODAL'}
            # Scale, move, rotate
            elif isPen and event.type == 'S' and event.value == 'PRESS':
                bpy.ops.transform.resize('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            elif isPen and event.type == 'D' and event.value == 'PRESS':
                bpy.ops.transform.translate('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            elif isPen and event.type == 'R' and event.value == 'PRESS':
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
                return {'RUNNING_MODAL'}
            # Prop-editing
            elif isPen and event.type == 'P' and event.value == 'PRESS':
                context.tool_settings.use_proportional_edit = not context.tool_settings.use_proportional_edit
                return {'RUNNING_MODAL'}
            # Focus
            elif isPen and event.type == 'F' and event.value == 'PRESS':
                bpy.ops.view3d.view_selected(use_all_regions=False)
                return {'RUNNING_MODAL'}
            # Redo/undo
            elif isPen and event.type == 'Z' and event.shift and event.ctrl and event.value == 'PRESS':
                try:
                    bpy.ops.ed.redo()
                    self.historySteps += 1
                except Exception as er:
                    pass
                return {'RUNNING_MODAL'}
            elif isPen and event.type == 'Z' and event.ctrl and event.value == 'PRESS' and self.historySteps > 0:
                self.historySteps -= 1
                bpy.ops.ed.undo()
                return {'RUNNING_MODAL'}

            # / RUNNING BLOCKED OPS
            # Remove timers
            if event.type == 'TIMER':
                for key in self.dbl.keys():
                    self.dbl[key] = removeTimerFromContext(
                        context, self.dbl.get(key))
                return {'RUNNING_MODAL'}
            # Restore modal text after other modal commands
            elif event.type in ['NONE', 'INBETWEEN_MOUSEMOVE']:
                if self.isDraw:
                    setModalTextInContext(
                        context, self.DRAW_HEADER_TEXT, self.DRAW_STATUS_TEXT)
                else:
                    setModalTextInContext(
                        context, self.HEADER_TEXT if not self.isExterior else self.EXTERIOR_HEADER_TEXT, self.STATUS_TEXT)
                return {'RUNNING_MODAL'}
            # Block viewport and other unconditioned commands
            elif (
                event.type == 'MOUSEROTATE'
                or (event.type == 'MIDDLEMOUSE' and not event.shift and not event.ctrl)
                or (event.type == 'TRACKPADPAN' and not event.shift and not event.ctrl)
                or event.value in ['PRESS', 'RELEASE', 'CLICK']
            ):
                # Fixes ortograthic view bug
                if self.initIsOrthographic and self.initIsOrthographic != self.view3dSpace.region_3d.is_orthographic_side_view:
                    bpy.ops.view3d.view_persportho()
                    self.view3dSpace.region_3d.is_orthographic_side_view = self.initIsOrthographic
                return {'RUNNING_MODAL'}

            return {'PASS_THROUGH'}
        except Exception as er:
            self.report({'ERROR'}, "{0}".format(er))
            setModalTextInContext(context, None)
            self.mapModalToolKeys(self, context, False)
            return {'CANCELLED'}

    @classmethod
    def finish(cls, self, context, trimCurveResolution):
        viewport = self.view3dSpace.region_3d
        # Close and convert to mesh
        setCurveCyclic(self.trimCurve, True)
        self.trimCurve.data.resolution_u = trimCurveResolution
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.origin_set(
            type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
        # Fill mesh
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.editmode_toggle()
        # Add solidify modifier
        mod_solidify = self.trimCurve.modifiers.new(
            'TrimSolidify' + str(id(self.trimCurve)), 'SOLIDIFY')
        mod_solidify.thickness = math.ceil(viewport.view_distance * 2)
        mod_solidify.offset = 0.0
        # Add bool modifier
        mod_bool = self.targetObj.modifiers.new(
            'TrimBool' + str(id(self.targetObj)), 'BOOLEAN')
        moveObjectModifierAtTheEnd(self.targetObj, mod_bool)
        mod_bool.operation = 'DIFFERENCE' if not self.isExterior else 'INTERSECT'
        mod_bool.object = self.trimCurve
        mod_bool.use_hole_tolerant = True
        # Apply modifier
        setActiveObjectInContext(context, self.targetObj)
        bpy.ops.object.modifier_apply(
            modifier=mod_bool.name)  # for active object
        setActiveObjectInContext(context, self.trimCurve)
        # Restore context
        setActiveObjectInContext(
            context, self.targetObj, delPrev=True, mode='SCULPT')
        setModalTextInContext(context, None)
        self.mapModalToolKeys(self, context, False)
        return {'FINISHED'}


glob.workspaceActiveToolName = ''
glob.prevWorkspace = None
glob.actWorkspace = None


def SubscribeWorkSpace(isRegister=True):
    workSpaceOwner = object()

    def handleWorkSpaceChange():
        global glob

        try:
            glob.workspaceActiveToolName = bpy.context.workspace.tools.from_space_view3d_mode(
                bpy.context.mode, create=False).idname
        except Exception as er:
            glob.workspaceActiveToolName = ''
        try:
            glob.prevWorkspace = findBpyObjectByName(
                glob.actWorkspace.name, bpy.data.workspaces)
        except Exception as er:
            glob.prevWorkspace = None
        try:
            glob.actWorkspace = findBpyObjectByName(
                bpy.context.workspace.name, bpy.data.workspaces)
        except Exception as er:
            glob.actWorkspace = None
        # Reset status text on checkout (clears unfinished modal text)
        try:
            if glob.prevWorkspace.name != glob.actWorkspace.name:
                bpy.context.workspace.status_text_set(None)
        except Exception as er:
            pass

    def subscribeWorkSpace():
        subscribeTo = (bpy.types.WorkSpace, 'tools')
        bpy.msgbus.subscribe_rna(
            key=subscribeTo,
            owner=workSpaceOwner,
            args=(),
            notify=handleWorkSpaceChange,
            options={'PERSISTENT'}
        )

    @persistent
    def resubscribeWorkSpace(dummy):
        subscribeWorkSpace()

    def unsubscribeWorkSpace():
        bpy.msgbus.clear_by_owner(workSpaceOwner)

    if (isRegister):
        subscribeWorkSpace()
        bpy.app.handlers.load_post.append(resubscribeWorkSpace)
    else:
        unsubscribeWorkSpace()


glob.trimCurveResolution = 0


class SculptTrimCurveResolutionDialogOperator(bpy.types.Operator):
    bl_label = "Set Trim Curve"
    bl_idname = "curve.nym_curve_resolution_dialog"

    # use colon for display prop in dialog
    resolution: bpy.props.IntProperty(
        name='Resolution', default=16, min=1, max=2047)

    def invoke(self, context, event):
        global glob
        glob.trimCurveResolution = 0
        # required for dialog
        return context.window_manager.invoke_props_dialog(self, width=150)

    def execute(self, context):
        global glob
        glob.trimCurveResolution = self.resolution
        return {'FINISHED'}


class SculptSymmetrizeWeldPanelOperator(bpy.types.Operator):
    bl_label = "Sculpt Symmetrize Weld Panel"
    bl_idname = "paint.nym_sculpt_symmetrize_weld_panel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.wm.call_panel(
            name=SculptSymmetrizeWeldPanel.bl_idname, keep_open=True)
        return {'FINISHED'}


class SculptSymmetrizeWeldPanel(bpy.types.Panel):
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Symmetrize Weld"
    bl_idname = "nym_sculpt_symmetrize_weld_panel"

    def draw(self, context):
        layout = self.layout
        sculpt = context.tool_settings.sculpt
        layout.prop(sculpt, "symmetrize_direction")
        # When active_default=true, an operator button defined after this will be activated when pressing return
        layout.active_default = True
        layout.operator("sculpt.symmetrize")


# / Paint Tools


class PaintGradientSettingsPanelOperator(bpy.types.Operator):
    bl_label = "Paint Gradient Settings Panel"
    bl_idname = "paint.nym_paint_gradient_panel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            brush = context.scene.tool_settings.image_paint.brush
        except Exception as er:
            brush = None
        return brush

    def execute(self, context):
        brush = context.scene.tool_settings.image_paint.brush
        if not brush.color_type == 'GRADIENT':
            self.report({'INFO'}, "Brush color hasn't set to gradient!")
            return {'FINISHED'}

        bpy.ops.wm.call_panel(
            name=PaintGradientSettingsPanel.bl_idname)
        return {'FINISHED'}


class PaintGradientSettingsPanel(bpy.types.Panel):
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Gradient"
    bl_idname = "nym_paint_gradient_panel"

    @classmethod
    def prop_unified(
        cls,
        layout,
        context,
        brush,
        prop_name,
        unified_name=None,
        pressure_name=None,
        icon='NONE',
        text=None,
        slider=False,
        header=False,
    ):
        """ Generalized way of adding brush options to the UI,
            along with their pen pressure setting and global toggle, if they exist. """
        row = layout.row(align=True)
        ups = context.tool_settings.unified_paint_settings
        prop_owner = brush
        if unified_name and getattr(ups, unified_name):
            prop_owner = ups

        row.prop(prop_owner, prop_name, icon=icon, text=text, slider=slider)

        if pressure_name:
            row.prop(brush, pressure_name, text="")

        if unified_name and not header:
            # NOTE: We don't draw UnifiedPaintSettings in the header to reduce clutter. D5928#136281
            row.prop(ups, unified_name, text="", icon='BRUSHES_ALL')

        return row

    def draw(self, context):
        layout = self.layout
        brush = context.scene.tool_settings.image_paint.brush

        layout.template_color_ramp(brush, "gradient", expand=True)

        layout.use_property_split = True

        col = layout.column()

        if brush.image_tool == 'DRAW':
            self.prop_unified(
                col,
                context,
                brush,
                "secondary_color",
                unified_name="use_unified_color",
                text="Background Color",
                header=True,
            )

            col.prop(brush, "gradient_stroke_mode", text="Gradient Mapping")

            if brush.gradient_stroke_mode in {'SPACING_REPEAT', 'SPACING_CLAMP'}:
                col.prop(brush, "grad_spacing")


class PaintColorPalettePanelOperator(bpy.types.Operator):
    bl_label = "Paint Color Palette Panel"
    bl_idname = "paint.nym_paint_color_palette_panel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.wm.call_panel(
            name=PaintColorPalettePanel.bl_idname)
        return {'FINISHED'}


class PaintColorPalettePanel(bpy.types.Panel):
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Color Palette"
    bl_idname = "nym_paint_color_palette_panel"
    bl_ui_units_x = 10  # width

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        paint = context.scene.tool_settings.vertex_paint if (
            'VERTEX' in context.mode) else context.scene.tool_settings.image_paint
        uniPaint = context.scene.tool_settings.unified_paint_settings
        paintBrush = uniPaint if uniPaint.use_unified_color else paint.brush

        if context.object:
            sub_row = layout.row(align=True)
            sub_row.prop(paintBrush, "color", text="")

            row = layout.row(align=True)
            row.template_ID(paint, "palette", new="palette.new")

            if paint.palette:
                layout.template_palette(paint, "palette", color=True)


DIV = 100


# TODO: 3.2.x Complete resetTransformation()
# TODO: 3.2.x Add condition that object must be unwrapped (has at least one uv)
# TODO: 3.2.x Ask to create uv duplicate for mask if object has only one uv
class PaintMaskUvTransformProps(bpy.types.PropertyGroup):
    # set: bpy.types.Object.nym_paint_mask_uv_transform
    # get: context.active_object.nym_paint_mask_uv_transform

    @classmethod
    def updateProp(cls, self, context, propname, propvalue=None):
        global glob

        try:
            actObjData = context.active_object.data
        except Exception as er:
            actObjData = None
        try:
            stencilUv = context.active_object.data.uv_layer_stencil
        except Exception as er:
            stencilUv = None

        if not actObjData or not stencilUv:
            return

        origin_x = 0.5 + self.prevUvTranslationX/DIV
        origin_y = 0.5 + self.prevUvTranslationY/DIV
        scale_x = self.scale_x if not propvalue else propvalue
        scale_y = self.scale_y if not propvalue else propvalue
        SCALE_MULTIPLIER = 4  # the more the scale multiplier, the more possible scale range (min = 1) \
        INCREASE_PROPORTION = 1 + SCALE_MULTIPLIER/DIV
        DECREASE_PROPORTION = 1 - SCALE_MULTIPLIER/(DIV + 1)

        # Angle
        if propname == 'angle':
            angle = self.angle - self.prevUvRotationAngle
            rotateUv = createUvTransformer(
                math.radians(angle), (origin_x, origin_y))

            for v in actObjData.loops:
                stencilUv.data[v.index].uv = rotateUv(
                    stencilUv.data[v.index].uv)

            self.prevUvRotationAngle = self.angle
        # Offset
        elif propname == 'offset_x':
            offsetX = -1*(self.offset_x - self.prevUvTranslationX)/DIV
            translateUv = createUvTransformer(
                0, (0.5, 0.5), (offsetX, 0))

            for v in actObjData.loops:
                stencilUv.data[v.index].uv = translateUv(
                    stencilUv.data[v.index].uv)

            self.prevUvTranslationX = self.offset_x
        elif propname == 'offset_y':
            offsetY = -1*(self.offset_y - self.prevUvTranslationY)/DIV
            translateUv = createUvTransformer(
                0, (0.5, 0.5), (0, offsetY))

            for v in actObjData.loops:
                stencilUv.data[v.index].uv = translateUv(
                    stencilUv.data[v.index].uv)

            self.prevUvTranslationY = self.offset_y
        # Scale
        elif propname == 'scale_x':
            diffX = scale_x - self.prevUvScaleX
            scaleX = DECREASE_PROPORTION if diffX > 0 else INCREASE_PROPORTION
            scaleUv = createUvTransformer(
                0, (origin_x, origin_y), (0, 0), (scaleX, 1))

            for _ in range(abs(diffX)):
                for v in actObjData.loops:
                    stencilUv.data[v.index].uv = scaleUv(
                        stencilUv.data[v.index].uv)

            self.prevUvScaleX = scale_x
        elif propname == 'scale_y':
            diffY = scale_y - self.prevUvScaleY
            scaleY = DECREASE_PROPORTION if diffY > 0 else INCREASE_PROPORTION
            scaleUv = createUvTransformer(
                0, (origin_x, origin_y), (0, 0), (1, scaleY))

            for _ in range(abs(diffY)):
                for v in actObjData.loops:
                    stencilUv.data[v.index].uv = scaleUv(
                        stencilUv.data[v.index].uv)

            self.prevUvScaleY = scale_y

    @classmethod
    def updateScaleBoth(cls, self, context):
        if not self.scale_both:
            self.scale_x = self.scale_xy
            self.scale_y = self.scale_xy
        else:
            self.scale_xy = DIV

    @classmethod
    def updateScale(cls, self, context):
        self.updateProp(self, context, 'scale_x', self.scale_xy)
        self.updateProp(self, context, 'scale_y', self.scale_xy)

    @classmethod
    def resetTransformation(cls, self, context):
        C()

    prevUvRotationAngle: bpy.props.FloatProperty(name='', default=0)
    prevUvTranslationX: bpy.props.FloatProperty(name='', default=0)
    prevUvTranslationY: bpy.props.FloatProperty(name='', default=0)
    prevUvScaleX: bpy.props.IntProperty(name='', default=DIV)
    prevUvScaleY: bpy.props.IntProperty(name='', default=DIV)
    doTransformationReset: bpy.props.BoolProperty(name='Reset All',
                                                  update=lambda self, context: self.resetTransformation(self, context))

    angle: bpy.props.FloatProperty(name="Angle", default=0,  min=-180, max=180,
                                   update=lambda self, context: self.updateProp(
                                       self, context, 'angle'))
    offset_x: bpy.props.FloatProperty(name="Offset X", default=0, min=-DIV, max=DIV,
                                      update=lambda self, context: self.updateProp(
                                          self, context, 'offset_x'))
    offset_y: bpy.props.FloatProperty(name="Offset Y", default=0, min=-DIV, max=DIV,
                                      update=lambda self, context: self.updateProp(
                                          self, context, 'offset_y'))
    scale_x: bpy.props.IntProperty(name="Scale X", default=DIV, min=1, max=2*DIV,
                                   update=lambda self, context: self.updateProp(
                                       self, context, 'scale_x'))
    scale_y: bpy.props.IntProperty(name="Scale Y", default=DIV, min=1, max=2*DIV,
                                   update=lambda self, context: self.updateProp(
                                       self, context, 'scale_y'))
    scale_both: bpy.props.BoolProperty(default=True,
                                       update=lambda self, context: self.updateScaleBoth(
                                           self, context))
    scale_xy: bpy.props.IntProperty(name="Scale", default=DIV, min=1, max=2*DIV,
                                    update=lambda self, context: self.updateScale(
                                        self, context))


class PaintMaskUvTransformPanelOperator(bpy.types.Operator):
    bl_label = "Paint Mask Transform Form Panel"
    bl_idname = "paint.nym_paint_mask_uv_transform_panel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            hasStencilImage = context.tool_settings.image_paint.stencil_image
        except Exception as er:
            hasStencilImage = None

        if not hasStencilImage:
            self.report({'INFO'}, "Mask stencil image hasn't been set!")
            return {'FINISHED'}

        bpy.ops.wm.call_panel(
            name=PaintMaskUvTransformPanel.bl_idname)
        return {'FINISHED'}


class PaintMaskUvTransformPanel(bpy.types.Panel):
    bl_space_type = 'TOPBAR'  # requered panel dummy
    bl_region_type = 'HEADER'  # requered panel dummy
    bl_label = "Stencil Mask Transform"
    bl_idname = "nym_paint_mask_uv_transform_panel"
    bl_ui_units_x = 20  # width

    def draw(self, context):
        layout = self.layout
        props = context.active_object.nym_paint_mask_uv_transform

        layout.prop(props, "angle", slider=True)
        layout.prop(props, "offset_x", slider=True)
        layout.prop(props, "offset_y", slider=True)

        split = layout.split(factor=0.9)
        col1 = split.column()
        scaleRow = col1.row(align=True)
        col2 = split.column()

        if not props.scale_both:
            scaleRow.prop(props, "scale_x", slider=True)
            scaleRow.prop(props, "scale_y", slider=True)
            col2.prop(props, "scale_both", toggle=True,
                      icon="ORIENTATION_VIEW", text="")
        else:
            scaleRow.prop(props, "scale_xy", slider=True)
            col2.prop(props, "scale_both", toggle=True,
                      icon="ORIENTATION_VIEW", text="")

        # layout.prop(props, "doTransformationReset")


class PaintMaskImageInvertOperator(bpy.types.Operator):
    bl_label = "Paint Mask Image Invert"
    bl_idname = "paint.nym_paint_stencil_mask_image_invert"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            hasStencilImage = context.tool_settings.image_paint.stencil_image
        except Exception as er:
            hasStencilImage = None

        if not hasStencilImage:
            self.report({'INFO'}, "Mask stencil image hasn't been set!")
            return {'FINISHED'}

        img = context.tool_settings.image_paint.stencil_image
        bpy.ops.image.invert(
            {'edit_image': bpy.data.images[img.name]},
            invert_r=True, invert_g=True, invert_b=True)

        return {'FINISHED'}


# / Resources: Image, Shader


# Pack


class PackAllSavedOperator(bpy.types.Operator):
    """Pack all saved instances into the .blend file."""
    bl_label = "Pack All Saved"
    bl_idname = "file.nym_pack_all_saved"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            bpy.ops.file.pack_all()
            self.report({'INFO'}, "All saved resources are packed!")
        except Exception as er:
            self.report({'ERROR'}, "{0}".format(er))

        return {'FINISHED'}


class ImagePackOperator(bpy.types.Operator):
    bl_label = "Image Pack"
    bl_idname = "file.nym_image_pack"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.image.pack()
        return {'FINISHED'}


class ImageUnpackOperator(bpy.types.Operator):
    bl_label = "Image Unpack"
    bl_idname = "file.nym_image_unpack"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.image.unpack(method='WRITE_ORIGINAL')
        return {'FINISHED'}


# Create New


class ShaderCreateNewOperator(bpy.types.Operator):
    bl_label = "Shader New"
    bl_idname = "node.nym_shader_new"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'ShaderNodeTree'

    def execute(self, context):
        snode = context.space_data
        if snode.shader_type == 'OBJECT':
            mat = bpy.data.materials.new('Material')
            mat.use_nodes = True
            context.active_object.active_material = mat
        if snode.shader_type == 'WORLD':
            world = bpy.data.worlds.new("World")
            world.use_nodes = True
            context.scene.world = world
        if snode.shader_type == 'LINESTYLE':
            bpy.ops.scene.freestyle_linestyle_new()
        return {'FINISHED'}


# Set Active


class ImageSetActiveMenuOperator(bpy.types.Operator):
    bl_label = "Image Set Active Menu"
    bl_idname = "image.nym_image_set_active_menu"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        bpy.ops.wm.call_menu(name=ImageSetActiveMenu.bl_idname)
        return {'FINISHED'}


class ImageSetActiveMenu(bpy.types.Menu):
    bl_label = "Set Active"
    bl_idname = "nym_image_set_active_menu"

    def draw(self, context):
        editor_space = getSpaceUnderMouseFromContext(context)
        layout = self.layout
        with context.temp_override(space=editor_space):
            layout.template_ID(editor_space, "image")


class ShaderSetActiveMenuOperator(bpy.types.Operator):
    bl_label = "Shader Set Active Menu"
    bl_idname = "node.nym_shader_set_active_menu"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'ShaderNodeTree'

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        bpy.ops.wm.call_menu(name=ShaderSetActiveMenu.bl_idname)
        return {'FINISHED'}


class ShaderSetActiveMenu(bpy.types.Menu):
    bl_label = "Set Active"
    bl_idname = "nym_shader_set_active_menu"

    def draw(self, context):
        layout = self.layout
        editor_space = getSpaceUnderMouseFromContext(context)
        snode = context.space_data

        if snode.shader_type == 'OBJECT' and context.object:
            with context.temp_override(space=editor_space):
                layout.template_ID(
                    context.object, "active_material", new="material.new")
        if snode.shader_type == 'WORLD':
            scene = context.scene
            with context.temp_override(space=editor_space):
                layout.template_ID(
                    scene, "world", new="world.new")
        if snode.shader_type == 'LINESTYLE':
            lineset = context.view_layer.freestyle_settings.linesets.active
            with context.temp_override(space=editor_space):
                layout.template_ID(
                    lineset, "linestyle", new="scene.freestyle_linestyle_new")


# Keep Fake User


class ImageKeepFakeUserOperator(bpy.types.Operator):
    bl_label = "Image Keep Fake User"
    bl_idname = "image.nym_image_keep_fake_user"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        space = getSpaceUnderMouseFromContext(context)
        if space.image:
            space.image.use_fake_user = True if not space.image.use_fake_user else False
            # Refresh/refresh/Update/update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}


class ShaderKeepFakeUserOperator(bpy.types.Operator):
    bl_label = "Shader Keep Fake User"
    bl_idname = "node.nym_shader_keep_fake_user"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'ShaderNodeTree'

    def execute(self, context):
        snode = context.space_data

        if snode.shader_type == 'OBJECT':
            mat = context.active_object.active_material
            if mat:
                mat.use_fake_user = True if not mat.use_fake_user else False
        if snode.shader_type == 'WORLD':
            world = context.scene.world
            if world:
                world.use_fake_user = True if not world.use_fake_user else False
        if snode.shader_type == 'LINESTYLE':
            lineset = context.view_layer.freestyle_settings.linesets.active
            if lineset:
                linestyle = lineset.linestyle
                linestyle.use_fake_user = True if not linestyle.use_fake_user else False

        # Refresh/refresh/Update/update
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}


# Make Single Copy


class ImageMakeSingleCopyOperator(bpy.types.Operator):
    bl_label = "Image Make Single Copy"
    bl_idname = "image.nym_image_make_single_copy"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        space = getSpaceUnderMouseFromContext(context)
        space.image = space.image.copy()
        return {'FINISHED'}


class MaterialMakeSingleCopyOperator(bpy.types.Operator):
    bl_label = "Material Make Single Copy"
    bl_idname = "node.nym_material_make_single_copy"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'ShaderNodeTree'

    def execute(self, context):
        snode = context.space_data
        if snode.shader_type == 'OBJECT':
            for obj in context.selected_objects:
                mat = obj.active_material
                if mat:
                    obj.active_material = mat.copy()
        return {'FINISHED'}


# Close


class ImageCloseOperator(bpy.types.Operator):
    bl_label = "Image Close"
    bl_idname = "image.nym_image_close"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        space = getSpaceUnderMouseFromContext(context)
        space.image = None
        return {'FINISHED'}


class ShaderCloseOperator(bpy.types.Operator):
    bl_label = "Shader Close"
    bl_idname = "node.nym_shader_close"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'ShaderNodeTree'

    def execute(self, context):
        snode = context.space_data
        if snode.shader_type == 'OBJECT':
            context.active_object.active_material = None
        if snode.shader_type == 'WORLD':
            context.scene.world = None
        return {'FINISHED'}


# Remove


class ImageRemoveConfirmMenu(bpy.types.Menu):
    bl_label = "OK?"
    bl_idname = "nym_image_remove_confirm_menu"

    @classmethod
    def poll(cls, context):
        space = getSpaceUnderMouseFromContext(context)
        return bool(space) and bool(space.image)

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("image.nym_image_remove_confirm_menu", text="Remove")


class ImageRemoveConfirmMenuOperator(bpy.types.Operator):
    bl_label = "Image Remove Confirm Menu"
    bl_idname = "image.nym_image_remove_confirm_menu"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        updateGlobalEvent(event)
        return self.execute(context)

    def execute(self, context):
        space = getSpaceUnderMouseFromContext(context)
        if not space.image.use_fake_user:
            img = space.image
            img.user_clear()
            bpy.data.images.remove(img)
        else:
            self.report(
                {'INFO'}, "Can't remove image while fake user is turned on!")
        return {'FINISHED'}


class ShaderRemoveConfirmMenu(bpy.types.Menu):
    bl_label = "OK?"
    bl_idname = "nym_shader_remove_confirm_menu"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        hasActive = False
        if snode.shader_type == 'OBJECT':
            hasActive = bool(context.active_object.active_material)
        if snode.shader_type == 'WORLD':
            hasActive = bool(context.scene.world)
        return snode.tree_type == 'ShaderNodeTree' and hasActive

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.nym_shader_remove_confirm_menu", text="Remove")


class ShaderRemoveConfirmMenuOperator(bpy.types.Operator):
    bl_label = "Shader Remove"
    bl_idname = "node.nym_shader_remove_confirm_menu"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        snode = context.space_data
        if snode.shader_type == 'OBJECT':
            mat = context.active_object.active_material
            if not mat.use_fake_user:
                mat.user_clear()
                bpy.data.materials.remove(mat)
            else:
                self.report(
                    {'INFO'}, "Can't remove image while fake user is turned on!")
        if snode.shader_type == 'WORLD':
            world = context.scene.world
            if not world.use_fake_user:
                world.user_clear()
                bpy.data.worlds.remove(world)
            else:
                self.report(
                    {'INFO'}, "Can't remove image while fake user is turned on!")
        return {'FINISHED'}
