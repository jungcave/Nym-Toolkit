import bpy
from bpy.app.handlers import persistent
import math
from .src.tools.SugarKit_helpers import C, CD, CL
from .src.tools.SugarKit_helpers import (
    restoreDefaultKeymaps,
    buildNewActiveKeyconfig,
    disableMacOsKeyBindingsInKeyconfig,
    addAddonKeymapItem,
    removeAllInactiveKeymapItemsInKeyconfig,
    saveAndExportKeyconfig,
)
from .src.tools.SugarKit_helpers import addActiveKeymapItem as add
from .src.tools.SugarKit_helpers import disableActiveKeymapItem as disable


NUMBERS = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
           'SIX', 'SEVEN', 'EIGHT', 'NINE', 'ZERO']
NUMBERS_IDX = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE',
               'SIX', 'SEVEN', 'EIGHT', 'NINE']


class BuildNymKeyconfigOperator(bpy.types.Operator):
    bl_label = "Build Nym Keyconfig"
    bl_idname = "window.nym_build_nym_keyconfig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restoreDefaultKeymaps()
        nkc = buildNewActiveKeyconfig('Nym Keyconfig')
        disableMacOsKeyBindingsInKeyconfig(
            nkc, excludes=['cmd A', 'cmd S', 'cmd D', 'cmd Z', 'shift cmd Z', 'cmd X', 'cmd C'])

        # INTERFACE
        self.addInterfaceHotkeys()
        # VIEW
        self.addViewHotkeys()
        # OBJECT
        self.addObjectHotkeys()
        # OUTLINER
        self.addOutlinerHotkeys()
        # TRANSFORMATIONS
        self.addTransformationsHotkeys()
        # PROPERTIES
        self.addPropertiesHotkeys()
        # ANIMATION
        self.addAnimationHotkeys()
        # EDIT MESH
        self.addEditMeshHotkeys()
        # CURVES
        self.addCurvesHotkeys()
        # SCULPT
        self.addSculptHotkeys()
        # PAINT
        self.addPaintHotkeys()
        # IMAGE/UV
        self.addImageAndUvHotkeys()
        # FILE BROWSER
        self.addFileBrowserHotkeys()
        # SHADER
        self.addShaderHotkeys()

        removeAllInactiveKeymapItemsInKeyconfig(nkc)
        saveAndExportKeyconfig('Nym_Keyconfig.py')

        return {'FINISHED'}

    @classmethod
    def addInterfaceHotkeys(cls):
        disable('Window', 'wm.quit_blender', 'Q ctrl')
        disable('Window', 'wm.doc_view_manual_ui_context', 'F1')
        disable('Window', {'wm.call_menu': {
                'name': 'TOPBAR_MT_file_context_menu'}}, 'F4')

        # file
        add('Window', 'wm.save_as_mainfile',
            'S ctrl alt', disableOld='S shift ctrl')
        add('Window', 'wm.obj_import', 'I shift ctrl')
        add('Window', 'import_scene.fbx', 'I shift ctrl alt')
        add('Window', 'wm.obj_impobj_exportort', 'E shift ctrl')
        add('Window', 'export_scene.fbx', 'E shift ctrl alt')
        add('Window', 'wm.append', 'A shift ctrl alt')

        # edit preferences
        add('Screen', 'screen.userpref_show',
            'SPACE shift ctrl alt', disableOld=True)

        # cycle workspace
        for k, v in {'RIGHT_ARROW': 'NEXT', 'LEFT_ARROW': 'PREV'}.items():
            add('Screen', 'screen.workspace_cycle',
                k + ' shift ctrl', setKmiProps=lambda kmi: setDirectionProp(kmi, v))

        # viewport area
        add('Screen', 'screen.area_close',
            'X shift ctrl alt')
        for k, v in {
            'ONE': 'VIEW_3D',
            'TWO': 'IMAGE_EDITOR',
            'THREE': 'NODE_EDITOR',
            'FOUR': 'GRAPH_EDITOR',
            'FIVE': 'SEQUENCE_EDITOR',
            'SIX': 'CLIP_EDITOR',
            'SEVEN': 'TEXT_EDITOR',
            'EIGHT': 'CONSOLE',
            'NINE': 'OUTLINER',
            'ZERO': 'PROPERTIES'
        }.items():
            add('Window', 'screen.space_type_set_or_cycle',
                k + ' shift ctrl', disableOld=True, setKmiProps=lambda kmi: setSpaceTypeProp(kmi, v))
        disable('Window', 'screen.space_type_set_or_cycle', 'F11 shift')
        disable('Window', 'screen.space_type_set_or_cycle', 'F12 shift')

    @classmethod
    def addViewHotkeys(cls):
        # zoom, pan, rotate
        disable('3D View', 'view3d.view_all', 'C shift')
        for kmn in ['View2D', '3D View', 'Image']:
            disable(kmn, '*.zoom_border', 'B shift')
        disable('3D View', 'view3d.zoom', 'MINUS shift ctrl')
        disable('3D View', 'view3d.zoom', 'EQUAL shift ctrl')
        add('Image', 'image.view_pan', 'TRACKPADPAN shift ANY')
        add('Node Editor', 'view2d.pan', 'TRACKPADPAN shift ANY')

        for k, v in {'ONE': 'RIGHT', 'TWO': 'FRONT', 'THREE': 'TOP'}.items():
            add('3D View', 'view3d.view_axis',
                k + ' alt', disableOld=True, setKmiProps=lambda kmi: setTypeProp(kmi, v))
            add('3D View', {'view3d.view_axis': {'align_active': True}},
                k + ' alt DOUBLE_CLICK', disableOld=True, setKmiProps=lambda kmi: setTypeProp(kmi, v))

        for k, v in {
            'FOUR': 'ORBITLEFT',
            'FIVE': 'ORBITDOWN',
            'SIX': 'ORBITLEFT',
            'SEVEN': 'ORBITRIGHT',
            'EIGHT': 'ORBITDOWN',
            'NINE': 'ORBITUP'
        }.items():
            id = {'view3d.view_orbit': {'angle': math.radians(180)}} if (
                k == 'FOUR' or k == 'FIVE') else 'view3d.view_orbit'
            add('3D View', id,
                k + ' alt', setKmiProps=lambda kmi: setTypeProp(kmi, v))
        for i in [2, 4, 6, 8, 9]:
            disable('3D View', 'view3d.view_orbit', 'NUMPAD_' + str(i))

        # quick annotations
        add('Grease Pencil', {'gpencil.annotate': {'wait_for_input': False}},
            'LEFTMOUSE X', disableOld='LEFTMOUSE D', setKmiProps=lambda kmi: setModeProp(kmi, 'DRAW'))
        for k in ['LEFTMOUSE shift D', 'LEFTMOUSE alt D', 'LEFTMOUSE shift alt D']:
            disable('Grease Pencil', 'gpencil.annotate', k)
        add('Grease Pencil', {'gpencil.annotate': {'wait_for_input': True}},
            'RIGHTMOUSE X', setKmiProps=lambda kmi: setModeProp(kmi, 'DRAW_POLY'))
        add('Grease Pencil', {'gpencil.annotate': {'wait_for_input': False}},
            'LEFTMOUSE Z', disableOld='RIGHTMOUSE D', setKmiProps=lambda kmi: setModeProp(kmi, 'ERASER'))
        for kmn in ['Annotate', 'Annotate Line', 'Annotate Polygon']:
            add('Generic Tool: ' + kmn, {'gpencil.annotate': {'wait_for_input': False}},
                'LEFTMOUSE Z', setKmiProps=lambda kmi: setModeProp(kmi, 'ERASER'))

        # veiw
        add('3D View', 'view3d.navigate',
            'SPACE', disableOld='ACCENT_GRAVE shift')
        for kmn, v in {
            'Outliner': 'OUTLINER',
            'Dopesheet': 'DOPESHEET',
            '3D View': 'VIEW3D',
            'Graph Editor': 'GRAPH',
            'Image Generic': 'IMAGE',
            'Node Editor': 'NODE',
            'File Browser': 'FILEBROWSER',
            'NLA Editor': 'NLA',
            'Sequencer': 'SEQUENCER',
            'SequencerPreview': 'SEQUENCER_',
            'Clip': 'CLIP'
        }.items():
            add(kmn, {'wm.call_menu_pie': {'name': v + '_MT_view_pie'}},
                'ACCENT_GRAVE ctrl', disableOld='ACCENT_GRAVE')

        add('3D View', 'view3d.view_persportho',
            'ACCENT_GRAVE alt', disableOld='NUMPAD_5')
        add('Screen', 'screen.region_quadview',
            'Q shift ctrl alt', disableOld='Q ctrl alt')

        # view camera
        add('3D View', 'view3d.view_camera',
            'ZERO', disableOld='NUMPAD_0')
        add('3D View', 'view3d.object_as_camera',
            'ZERO ctrl', disableOld='NUMPAD_0 ctrl')
        add('3D View', 'view3d.camera_to_view',
            'ZERO shift', disableOld='NUMPAD_0 ctrl alt')

        # view region
        add('3D View', 'view3d.render_border',
            'Z X', disableOld='B ctrl')
        add('3D View', 'view3d.clear_render_border',
            'Z X alt', disableOld='B ctrl alt')
        add('Image', 'image.render_border',
            'Z X', disableOld='B ctrl')
        add('Image', 'image.clear_render_border',
            'Z X alt', disableOld='B ctrl alt')
        add('Node Editor', 'node.viewer_border',
            'Z X', disableOld='B ctrl')
        add('Node Editor', 'node.clear_viewer_border',
            'Z X alt', disableOld='B ctrl alt')
        add('3D View', 'view3d.clip_border',
            'Z X shift', disableOld='B alt')

        # view interface
        add('Screen', 'screen.screen_full_area',
            'BACK_SLASH', disableOld='SPACE ctrl')
        add('Screen', {'screen.screen_full_area': {'use_hide_panels': True}},
            'BACK_SLASH alt', disableOld='SPACE ctrl alt')
        for kmn in [
            'Dopesheet Generic',
            '3D View Generic',
            'Graph Editor Generic',
            'Image Generic',
            'Node Generic',
            'File Browser',
            'NLA Generic',
            'SequencerCommon',
            'Clip',
            'Spreadsheet Generic'
        ]:
            add(kmn, {'wm.context_toggle': {'data_path': 'space_data.show_region_ui'}},
                'SLASH', disableOld='N')
        for kmn in [
            '3D View Generic',
            'Image Generic',
            'Node Generic',
            'File Browser',
            'SequencerCommon',
            'Clip',
            'Spreadsheet Generic'
        ]:
            add(kmn, {'wm.context_toggle': {'data_path': 'space_data.show_region_toolbar'}},
                'SLASH alt', disableOld='T')
        add('Window', 'wm.toolbar',
            'SLASH shift', disableOld='SPACE shift')
        add('Window', {'wm.context_toggle': {'data_path': 'space_data.show_region_tool_header'}},
            'SLASH ctrl')

        # gizmo
        for kmn in ['3D View', 'UV Editor', 'Image', 'SequencerPreview']:
            add(kmn, {'wm.context_toggle': {'data_path': 'space_data.show_gizmo'}},
                'COMMA alt', disableOld='ACCENT_GRAVE ctrl')

        # overlays
        for kmn in ['3D View', 'UV Editor', 'Image', 'Node Editor', 'Sequencer', 'SequencerPreview']:
            add(kmn, {'wm.context_toggle': {'data_path': 'space_data.overlay.show_overlays'}},
                'PERIOD alt', disableOld='Z shift alt')
        for k, v in {'PERIOD': 'show_floor', 'SLASH': 'show_relationship_lines', 'W': 'show_wireframes', 'X': 'show_extras', 'N': 'show_face_orientation'}.items():
            add('Window', {'wm.context_toggle': {'data_path': 'space_data.overlay.' + v}},
                k + ' ctrl alt')

        # x-ray
        add('3D View', 'view3d.toggle_xray',
            'COMMA', disableOld='Z alt')

        # shading
        add('3D View', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_shading_pie'}},
            'PERIOD shift', disableOld='Z')
        add('3D View', {'wm.context_menu_enum': {'data_path': 'space_data.shading.type'}},
            'Z shift')
        add('3D View', 'view3d.toggle_shading',
            'PERIOD', disableOld='Z shift')

        add('3D View', 'view3d.toggle_shading',
            'PERIOD DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'SOLID'))
        add('3D View', 'view3d.toggle_shading',
            'Z alt DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'SOLID'))

        add('3D View', 'view3d.toggle_shading',
            'Z alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'MATERIAL'))

        for kmn in ['Object Mode', 'Mesh', 'Sculpt']:
            add(kmn, {'wm.context_menu_enum': {'data_path': 'space_data.shading.color_type'}},
                'Z shift alt')
        for k, v in {'C': 'show_cavity', 'E': 'use_scene_world'}.items():
            add('3D View', {'wm.context_toggle': {'data_path': 'space_data.shading.' + v}},
                k + ' ctrl alt')

        # render
        add('Screen', {'render.render': {'use_viewport': True}},
            'R shift ctrl alt', disableOld='F12')
        add('Screen', {'render.render': {'use_viewport': True, 'animation': True}},
            'QUOTE shift ctrl alt', disableOld='F12 ctrl')
        add('Screen', 'render.view_show',
            'V shift ctrl alt', disableOld='F11')
        add('Screen', 'render.play_rendered_anim',
            'SEMI_COLON shift ctrl alt', disableOld='F11 ctrl')

    @classmethod
    def addObjectHotkeys(cls):
        # mode
        add('Object Non-modal', 'view3d.object_mode_pie_or_toggle',
            'TAB shift', disableOld='TAB ctrl')
        add('Sequencer', {'wm.context_set_int': {'data_path': 'scene.sequence_editor.overlay_frame', 'value': 0}},
            'TAB ctrl', disableOld='O')

        add('Object Non-modal', {'object.mode_set': {'toggle': False}},
            'TAB alt', setKmiProps=lambda kmi: setModeProp(kmi, 'OBJECT'))
        add('Object Non-modal', 'object.transfer_mode',
            'RET ctrl', disableOld='Q alt')
        add('Object Non-modal', 'object.transfer_mode',
            'RIGHTMOUSE ctrl CLICK')
        for k, v in {
            'ONE': 'OBJECT',
            'TWO': 'EDIT',
            'THREE': 'SCULPT',
            'FOUR': 'VERTEX_PAINT',
            'FOUR_DBL': 'WEIGHT_PAINT',
            'FIVE': 'TEXTURE_PAINT'
        }.items():
            hotkey = k + ' ctrl' if k != 'FOUR_DBL' else 'FOUR ctrl DOUBLE_CLICK'
            add('Object Non-modal', 'object.mode_set',
                hotkey, setKmiProps=lambda kmi: setModeProp(kmi, v))

        # tools
        for kmn in ['3D View', 'UV Editor', 'Node Editor']:
            disable(kmn, {'wm.tool_set_by_id': {'name': 'builtin.select_box', 'cycle': True}},
                    'W')
            add('Window', {'wm.tool_set_by_id': {'name': 'builtin.select_box'}},
                'W DOUBLE_CLICK')
        add('Window', {'wm.tool_set_by_id': {'name': 'builtin.select'}},
            'W')
        add('Window', 'wm.toolbar_fallback_pie',
            'W shift', disableOld='W alt')

        add('Window', {'wm.tool_set_by_id': {'name': 'builtin.cursor'}},
            'Q')
        add('3D View', 'view3d.cursor3d',
            'RIGHTMOUSE shift CLICK', disableOld='RIGHTMOUSE shift')
        for kmn, v in {
            'Dopesheet': 'DOPESHEET',
            'Grease Pencil Stroke Edit Mode': 'GPENCIL',
            '3D View': 'VIEW3D',
            'UV Editor': 'IMAGE',
            'Graph Editor': 'GRAPH',
            'NLA Editor': 'NLA'
        }.items():
            add(kmn, {'wm.call_menu_pie': {'name': v + '_MT_snap_pie'}},
                'Q shift', disableOld='S shift')
        add('3D View', 'view3d.snap_cursor_to_selected',
            'Q shift ctrl')
        add('3D View', 'view3d.snap_cursor_to_center',
            'Q alt')

        add('3D View', {'wm.tool_set_by_id': {'name': 'builtin.transform'}},
            'T')
        add('3D View', {'wm.tool_set_by_id': {'name': 'builtin.move'}},
            'T DOUBLE_CLICK')
        add('3D View', {'wm.context_set_enum': {'data_path': 'scene.tool_settings.workspace_tool_type'}},
            'T RELEASE', setKmiProps=lambda kmi: setValueProp(kmi, 'DEFAULT'))

        # view
        for kmn, v in {
            'Dopesheet': 'action.',
            '3D View': 'view3d.',
            'Animation Channels': 'anim.channels_',
            'Graph Editor': 'graph.',
            'Image': 'image.',
            'Node Editor': 'node.',
            'File Browser Main': 'file.',
            'NLA Editor': 'nla.',
            'Sequencer': 'sequencer.',
            'SequencerPreview': 'sequencer.',
            'Clip Editor': 'clip.'
        }.items():
            if kmn == '3D View':
                add('3D View', {'view3d.view_selected': {'use_all_regions': False}},
                    'F', disableOld='NUMPAD_PERIOD')
                disable('3D View', 'view3d.view_selected', 'NDOF_BUTTON_FIT')
            else:
                add(kmn, v + 'view_selected', 'F', disableOld='NUMPAD_PERIOD')
        for kmn, v in {
            'Dopesheet': 'action.view_all',
            '3D View': {'view3d.view_all': {'center': False}},
            'Graph Editor': 'graph.view_all',
            'NLA Editor': 'nla.view_all',
            'Sequencer': 'sequencer.view_all',
            'SequencerPreview': 'sequencer.view_all_preview',
            'Clip Editor': 'clip.view_all',
            'Clip Graph Editor': 'clip.graph_view_all',
            'Clip Dopesheet Editor': 'clip.dopesheet_view_all',
        }.items():
            add(kmn, v, 'F DOUBLE_CLICK')
        add('3D View', 'view3d.localview', 'V DOUBLE_CLICK', disableOld='SLASH')
        add('3D View', 'view3d.localview', 'RET shift', disableOld='NUMPAD_SLASH')
        add('3D View', {'view3d.select': {'center': True}},
            'LEFTMOUSE V')
        add('3D View', 'view3d.localview_remove_from',
            'LEFTMOUSE V RELEASE', disableOld='SLASH alt')
        add('3D View', 'view3d.localview_remove_from',
            'RET shift alt', disableOld='NUMPAD_SLASH alt')

        for kmn, v in {
            'Grease Pencil Stroke Edit Mode': 'gpencil.',
            'Grease Pencil Stroke Paint Mode': 'gpencil.',
            'Paint Face Mask (Weight, Vertex, Texture)': 'paint.face_vert_',
            'Paint Vertex Selection (Weight, Vertex)': 'paint.face_vert_',
            'Weight Paint': 'paint.face_vert_',
            'Vertex Paint': 'paint.face_vert_',
            'Pose': 'pose.',
            'Curve': 'curve.',
            'Sculpt': 'sculpt.',  # _all
            'Mesh': 'mesh.',
            'Armature': 'armature.',
            'Metaball': 'mball.',  # _metaelems
            'Particle': 'particle.',
            'UV Editor': 'uv.',
            'Graph Editor Generic': 'graph.'
        }.items():
            if v == 'sculpt.':
                postfix = '_all'
            elif v == 'mball.':
                postfix = '_metaelems'
            else:
                postfix = ''
            add(kmn, v + 'reveal' + postfix, 'H DOUBLE_CLICK', disableOld='H alt')
        add('Object Mode', 'object.hide_view_clear',
            'H DOUBLE_CLICK', disableOld='H alt')
        add('Object Mode', {'object.hide_view_clear': {
            'select': False}}, 'H alt')
        for kmn in ['Object Mode', 'Outliner']:
            add(kmn, {'wm.context_toggle': {
                'data_path': 'object.hide_select'}}, 'L')
        for kmn in ['Pose', 'Object Mode']:
            for i, n in enumerate(NUMBERS):
                disable(kmn, 'object.hide_collection', n)
                disable(kmn, 'object.hide_collection', n + ' alt')
                add(kmn, {'object.hide_collection': {'collection_index': i + 1, 'extend': True}},
                    n + ' ctrl alt', disableOld=n + ' shift')
                add(kmn, {'object.hide_collection': {'collection_index': i + 11, 'extend': True}},
                    n + ' shift ctrl alt', disableOld=n + ' shift alt')
        add('Object Mode', 'object.hide_collection',
            'H shift ctrl', disableOld='H ctrl')

        # quick select
        disable('*', '*.select_box', 'B')
        disable('*', '*.select_circle', 'C')
        disable('*', '*.select_lasso', 'RIGHTMOUSE ctrl CLICK_DRAG')
        disable('*', '*.select_lasso', 'RIGHTMOUSE shift ctrl CLICK_DRAG')

        add('3D View', 'view3d.select_box',
            'LEFTMOUSE CLICK_DRAG')
        add('3D View', 'view3d.select_box',
            'LEFTMOUSE shift CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('3D View', 'view3d.select_box',
            'LEFTMOUSE shift ctrl CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))
        add('3D View', 'view3d.select_circle',
            'LEFTMOUSE alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('3D View', 'view3d.select_circle',
            'LEFTMOUSE ctrl alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))
        add('View3D Gesture Circle', 'SUBTRACT', 'LEFT_BRACKET alt')
        add('View3D Gesture Circle', 'SUBTRACT', 'LEFT_BRACKET ctrl alt')
        add('View3D Gesture Circle', 'ADD', 'RIGHT_BRACKET alt')
        add('View3D Gesture Circle', 'ADD', 'RIGHT_BRACKET ctrl alt')
        add('3D View', 'view3d.select_lasso',
            'LEFTMOUSE shift alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('3D View', 'view3d.select_lasso',
            'LEFTMOUSE shift ctrl alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))

        # select tools
        for kmn, v in {
            "3D View Tool: Select ": 'view3d.',
            "Image Editor Tool: Uv, Select ": 'uv.',
            "Node Tool: Select ": 'node.',
        }.items():
            for tool, id in {
                'Box': 'select_box',
                'Circle': 'select_circle',
                'Lasso': 'select_lasso'
            }.items():
                for t in ['', ' (fallback)']:
                    # intersect (disable)
                    if kmn == "3D View Tool: Select " and tool != 'Circle':
                        disable(kmn + tool + t, {v + id: {'mode': 4}},
                                'LEFTMOUSE shift ctrl CLICK_DRAG')

        # select
        add('Object Mode', 'object.select_by_type', 'T shift')

        for kmn, v in {
            'Markers': 'marker.',
            'Dopesheet': 'action.select_all',
            'Grease Pencil Stroke Edit Mode': 'gpencil.',
            'Grease Pencil Stroke Paint Mode': 'gpencil.',
            'Grease Pencil Stroke Vertex Mode': 'gpencil.',
            'Paint Face Mask (Weight, Vertex, Texture)': 'paint.face_',
            'Paint Vertex Selection (Weight, Vertex)': 'paint.vert_',
            'Pose': 'pose.',
            'Object Mode': 'object.',
            'Curve': 'curve.',
            'Curves': 'curves.',
            'Mesh': 'mesh.',
            'Armature': 'armature.',
            'Metaball': 'mball.',
            'Lattice': 'lattice.',
            'Particle': 'particle.',
            'Sculpt Curves': 'curves.',
            'Animation Channels': 'anim.channels_',
            'UV Editor': 'uv.',
            'Mask Editing': 'mask.',
            'Graph Editor': 'graph.',
            'Node Editor': 'node.',
            'Info': 'info.',
            'File Browser Main': 'file.',
            'NLA Editor': 'nla.',
            'Sequencer': 'sequencer.',
            'SequencerPreview': 'sequencer.',
            'Clip Editor': 'clip.',
            'Clip Graph Editor': 'clip.graph_',  # _markers
        }.items():
            add(kmn, v + 'select_all' + ('_markers' if kmn == 'Clip Graph Editor' else ''),
                'A DOUBLE_CLICK', disableOld='A', setKmiProps=lambda kmi: setActionProp(kmi, 'SELECT'))
            add(kmn, v + 'select_all' + ('_markers' if kmn == 'Clip Graph Editor' else ''),
                'A', disableOld='A alt', setKmiProps=lambda kmi: setActionProp(kmi, 'DESELECT'))
            add(kmn, v + 'select_all' + ('_markers' if kmn == 'Clip Graph Editor' else ''),
                'A alt', disableOld='I ctrl', setKmiProps=lambda kmi: setActionProp(kmi, 'INVERT'))
            disable(kmn, {v + 'select_all' + ('_markers' if kmn == 'Clip Graph Editor' else ''): {'action': 2}},
                    'A DOUBLE_CLICK')

        for kmn, v in {
            'Pose': 'pose.',
            'Object Mode': 'object.',
            'Armature': 'armature.',
        }.items():
            add(kmn, {v + 'select_hierarchy': {'extend': False}},
                'EQUAL alt', disableOld='LEFT_BRACKET', setKmiProps=lambda kmi: setDirectionProp(kmi, 'PARENT'))
            add(kmn, {v + 'select_hierarchy': {'extend': True}},
                'EQUAL shift alt', disableOld='LEFT_BRACKET shift', setKmiProps=lambda kmi: setDirectionProp(kmi, 'PARENT'))
            add(kmn, {v + 'select_hierarchy': {'extend': False}},
                'MINUS alt', disableOld='RIGHT_BRACKET', setKmiProps=lambda kmi: setDirectionProp(kmi, 'CHILD'))
            add(kmn, {v + 'select_hierarchy': {'extend': True}},
                'MINUS shift alt', disableOld='RIGHT_BRACKET shift', setKmiProps=lambda kmi: setDirectionProp(kmi, 'CHILD'))

        # object
        for kmn, v in {
            'Object Mode': 'VIEW3D_MT_object_context_menu',
            'Mesh': 'VIEW3D_MT_edit_mesh_context_menu',
            'Curve': 'VIEW3D_MT_edit_curve_context_menu',
            'UV Editor': 'IMAGE_MT_uvs_context_menu',
            'Graph Editor': 'GRAPH_MT_context_menu',
            'Node Editor': 'NODE_MT_context_menu'
        }.items():
            add(kmn, {'wm.call_menu': {'name': v}},
                'RIGHTMOUSE CLICK', disableOld='RIGHTMOUSE')
        for k, v in {
            'ACCENT_GRAVE': 'object.empty_add',
            'ONE': 'mesh.primitive_plane_add',
            'TWO': 'mesh.primitive_cube_add',
            'THREE': 'mesh.primitive_circle_add',
            'FOUR': 'mesh.primitive_cylinder_add',
            'FIVE': 'curve.primitive_bezier_curve_add',
        }.items():
            add('Object Mode', v, {k: ['shift']})
        add('Object Mode', {'object.transform_apply': {'location': True, 'rotation': True, 'scale': True}},
            'T shift ctrl repeat')
        add('Object Mode', {'object.transform_apply': {'location': False, 'rotation': True, 'scale': True}},
            'A shift ctrl repeat')

        add('Object Mode', 'object.convert',
            'M shift ctrl', setKmiProps=lambda kmi: setTargetProp(kmi, 'MESH'))

        add('Object Mode', 'object.convert',
            'C shift ctrl', setKmiProps=lambda kmi: setTargetProp(kmi, 'CURVE'))

        for kmn, v in {
            'Window': 'TOPBAR_PT_name',
            'Markers': 'TOPBAR_PT_name_marker'
        }.items():
            add(kmn, {'wm.call_panel': {'name': v, 'keep_open': False}},
                'R ctrl', disableOld='F2')
            add(kmn, {'wm.call_panel': {'name': v, 'keep_open': False}},
                'RET alt')

        # copy attrs {b}
        for kmn, v in {
            'Pose': 'VIEW3D_MT_posecopypopup',
            'Object Mode': 'VIEW3D_MT_copypopup'
        }.items():
            addAddonKeymapItem(kmn, {'wm.call_menu': {'name': v}},
                               'C shift', disableOld='C ctrl')

        for kmn, v in {
            'Property Editor': 'constraint.copy',
            'Markers': 'marker.duplicate',
            'Dopesheet': 'action.duplicate_move',
            'Grease Pencil Stroke Edit Mode': 'gpencil.duplicate_move',
            'Object Mode': 'object.duplicate_move',
            'Curve': 'curve.duplicate_move',
            'Mesh': 'mesh.duplicate_move',
            'Armature': 'armature.duplicate_move',
            'Metaball': 'mball.duplicate_move',
            'Mask Editing': 'mask.duplicate_move',
            'Graph Editor': 'graph.duplicate_move',
            'Node Editor': 'node.duplicate_move',
            'NLA Editor': 'nla.duplicate_move',
            'Sequencer': 'sequencer.duplicate_move',
        }.items():
            add(kmn, v, 'D ctrl', disableOld='D shift')

        for kmn, v in {
            'Object Mode': 'object.duplicate_move_linked',
            'Node Editor': 'node.duplicate_move_linked',
            'NLA Editor': 'nla.duplicate_linked_move'
        }.items():
            add(kmn, v, 'D ctrl alt', disableOld='D alt')

        for kmn, v in {
            'Dopesheet': 'action.mirror',
            'Grease Pencil Stroke Edit Mode': 'transform.mirror',
            '3D View': 'transform.mirror',
            'UV Editor': 'transform.mirror',
            'Graph Editor': 'graph.mirror',
        }.items():
            add(kmn, v, 'I ctrl', disableOld='M ctrl')

        # object delete
        for kmn, v in {
            'Property Editor': 'constraint.delete',
            'Outliner': 'outliner.delete',
            'Markers': 'marker.delete',
            'Paint Curve': 'paintcurve.delete_point',
            'Object Mode': 'object.delete',
            'Metaball': 'mball.delete_metaelems',
            'Particle': 'particle.delete',
            'Animation Channels': 'anim.channels_delete',
            'Mask Editing': 'mask.delete',
            'Info': 'info.report_delete',
            'File Browser': 'file.delete',
            'NLA Channels': 'nla.tracks_delete',
            'NLA Editor': 'nla.delete',
            'Sequencer': 'sequencer.delete',
            'SequencerPreview': 'sequencer.delete',
            'Clip Editor': 'clip.delete_track',
            'Clip Graph Editor': 'clip.graph_delete_curve',
        }.items():
            add(kmn, v if kmn != 'Object Mode' else {v: {'confirm': False}},
                'X ctrl', disableOld='X')
            add(kmn, v if kmn not in ['Markers', 'Object Mode', 'Metaball', 'Mask Editing', 'Clip Editor', 'Clip Graph Editor'] else {v: {'confirm': False}},
                'BACK_SPACE', disableOld='DEL')
        for kmn, v in {
            'Dopesheet': 'DOPESHEET_MT_delete',
            'Grease Pencil Stroke Edit Mode': 'VIEW3D_MT_edit_gpencil_delete',
            'Grease Pencil Stroke Paint Mode': 'GPENCIL_MT_gpencil_draw_delete',
            'Armature': 'VIEW3D_MT_edit_armature_delete',
            'Graph Editor': 'GRAPH_MT_delete',
        }.items():
            add(kmn, {'wm.call_menu': {'name': v}},
                'X ctrl', disableOld='X')
            if kmn == 'Dopesheet':
                add(kmn, {'action.delete': {'confirm': False}},
                    'BACK_SPACE', disableOld='DEL')
            elif kmn == 'Graph Editor':
                add(kmn, {'graph.delete': {'confirm': False}},
                    'BACK_SPACE', disableOld='DEL')
            else:
                add(kmn, {'wm.call_menu': {'name': v}},
                    'BACK_SPACE', disableOld='DEL')
        for kmn, v in {
            'Grease Pencil Stroke Edit Mode': 'gpencil.active_frames_delete_all',
            'Grease Pencil Stroke Paint Mode': 'gpencil.active_frames_delete_all',
            'Grease Pencil Stroke Sculpt Mode': 'gpencil.active_frames_delete_all',
            'Grease Pencil Stroke Vertex Mode': 'gpencil.active_frames_delete_all',
            'Grease Pencil Stroke Weight Mode': 'gpencil.active_frames_delete_all',
            'Object Mode': 'object.delete',  # 'use_global': True
            'Clip Editor': 'clip.delete_marker',
            'Clip Graph Editor': 'clip.graph_delete_knot',
        }.items():
            if kmn.startswith('Grease Pencil Stroke '):
                add(kmn, v, 'X shift ctrl', disableOld='X shift')
                add(kmn, v, 'BACK_SPACE shift', disableOld='DEL shift')
            elif kmn == 'Object Mode':
                add(kmn, {v: {'use_global': True}},
                    'X shift ctrl', disableOld='X shift')
                add(kmn, {v: {'use_global': True, 'confirm': False}},
                    'BACK_SPACE shift', disableOld='DEL shift')
            else:
                add(kmn, v, 'X shift ctrl', disableOld='X shift')
                add(kmn, {v: {'confirm': False}},
                    'BACK_SPACE shift', disableOld='DEL shift')

        # shade
        add('Object Mode', 'object.shade_smooth', 'EIGHT')
        add('Object Mode', 'object.shade_flat', 'EIGHT DOUBLE_CLICK')
        add('Object Mode', {'object.shade_smooth': {
            'use_auto_smooth': True}}, 'EIGHT shift')

        # linked
        add('Object Mode', 'object.select_linked',
            'LEFT_SHIFT alt DOUBLE_CLICK')

        add('Object Mode', 'object.select_linked',
            'S shift', setKmiProps=lambda kmi: setTypeProp(kmi, 'OBDATA'))

        add('Object Mode', 'object.select_linked',
            'M shift', setKmiProps=lambda kmi: setTypeProp(kmi, 'MATERIAL'))

        add('Object Mode', {'object.make_single_user': {'object': True, 'obdata': True}},
            'L alt')
        add('Object Mode', {'object.make_single_user': {'material': True}},
            'M ctrl alt')
        add('Object Mode', {'object.make_single_user': {'object': True, 'obdata': True, 'material': True, 'animation': True, 'obdata_animation': True}},
            'L ctrl alt')

        for kmn in ['Outliner', 'Object Mode']:
            add(kmn, 'object.link_to_collection',
                'L shift ctrl', disableOld='M shift')

        # parent
        for kmn in ['Object Mode', 'Outliner']:
            add(kmn, {'object.parent_set': {'keep_transform': True}},
                'P shift ctrl', setKmiProps=lambda kmi: setTypeProp(kmi, 'OBJECT'))
            add(kmn, {'object.parent_set': {'keep_transform': True}},
                'LEFT_CTRL shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'OBJECT'))
            add(kmn, 'object.parent_clear',
                'P ctrl alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'CLEAR_KEEP_TRANSFORM'))
            add(kmn, 'object.parent_clear',
                'LEFT_CTRL alt DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'CLEAR_KEEP_TRANSFORM'))

        # collection group
        disable('Object Mode', 'collection.create', 'G ctrl')
        disable('Object Mode', 'collection.objects_add_active', 'G shift ctrl')
        disable('Object Mode', 'collection.objects_remove_all', 'G shift ctrl alt')

        for kmn in ['Outliner', 'Object Mode']:
            add(kmn, 'object.move_to_collection', 'G ctrl', disableOld='M')
        add('Object Mode', {'object.move_to_collection': {'collection_index': 0, 'is_new': True}},
            'G shift ctrl')
        add('Object Mode', {'object.move_to_collection': {'collection_index': 0}},
            'G alt')
        add('Object Mode', 'collection.objects_remove',
            'G ctrl alt', disableOld='G alt')

        add('Object Mode', 'object.select_grouped',
            'G', setKmiProps=lambda kmi: setTypeProp(kmi, 'COLLECTION'))
        add('Object Mode', {'object.select_grouped': {'extend': True}},
            'D shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'CHILDREN_RECURSIVE'))
        add('Object Mode', {'object.select_grouped': {'extend': True}},
            'D shift', setKmiProps=lambda kmi: setTypeProp(kmi, 'PARENT'))

    @classmethod
    def addOutlinerHotkeys(cls):
        # view
        add('Outliner', 'outliner.show_active',
            'F', disableOld='PERIOD')
        add('Outliner', 'outliner.show_hierarchy',
            'ZERO')
        add('Outliner', {'outliner.show_one_level': {'open': False}},
            'MINUS', disableOld="NUMPAD_MINUS")
        add('Outliner', {'outliner.show_one_level': {'open': True}},
            'EQUAL', disableOld="NUMPAD_PLUS")

        # hide
        add('Outliner', 'outliner.collection_show',
            'H DOUBLE_CLICK')
        add('Outliner', {'object.hide_view_clear': {'select': True}},
            'H DOUBLE_CLICK')

        # select
        add('Outliner', {'outliner.item_activate': {'extend': True, 'deselect_all': True}},
            'LEFTMOUSE shift CLICK', disableOld='LEFTMOUSE ctrl CLICK')
        add('Outliner', {'outliner.item_activate': {'extend_range': True, 'deselect_all': True}},
            'LEFTMOUSE ctrl CLICK', disableOldExactOpts='LEFTMOUSE shift CLICK')

        add('Outliner', 'outliner.select_all',
            'A DOUBLE_CLICK', disableOld='A', setKmiProps=lambda kmi: setActionProp(kmi, 'SELECT'))
        add('Outliner', 'outliner.select_all',
            'A', disableOld='A alt', setKmiProps=lambda kmi: setActionProp(kmi, 'DESELECT'))
        add('Outliner', 'outliner.select_all',
            'A alt', disableOld='I ctrl', setKmiProps=lambda kmi: setActionProp(kmi, 'INVERT'))
        disable('Outliner', {'outliner.select_all': {'action': 2}},
                'A DOUBLE_CLICK')

        add('Outliner', 'outliner.collection_objects_select',
            'G')

        # object
        add('Outliner', 'object.duplicate',
            'D ctrl')
        add('Outliner', 'outliner.collection_duplicate',
            'D shift ctrl')
        add('Outliner', 'object.join',
            'J ctrl')

        add('Outliner', 'outliner.id_operation',
            'L ctrl alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'SINGLE'))

        add('Outliner', 'outliner.id_operation',
            'X ctrl alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'UNLINK'))

        add('Outliner', 'outliner.collection_new',
            'M shift ctrl', disableOld='C')

        add('Outliner', {'outliner.delete': {'hierarchy': True}},
            'X shift ctrl')

        for kmn, v in {
            'User Interface': 'anim.driver_button_add',
            'Outliner': 'outliner.drivers_add_selected'
        }.items():
            add(kmn, v,
                'D shift', disableOld='D ctrl')
        for kmn, v in {
            'User Interface': 'anim.driver_button_remove',
            'Outliner': 'outliner.drivers_delete_selected'
        }.items():
            add(kmn, v,
                'D shift alt', disableOld='D ctrl alt')

        add('Outliner', {'outliner.item_rename': {'use_active': True}},
            'R ctrl', disableOld='F2')
        add('Outliner', {'outliner.item_rename': {'use_active': True}},
            'RET alt')

    @classmethod
    def addTransformationsHotkeys(cls):
        # actions
        add('Window', 'wm.search_menu',
            'SPACE ctrl', disableOld='F3')
        add('Window', {'wm.call_menu': {'name': 'SCREEN_MT_user_menu'}},
            'SPACE shift', disableOld='Q')
        disable('Screen', 'screen.redo_last', 'F9')
        add('Screen', 'ed.undo_history',
            'Z shift ctrl alt')
        add('Screen', 'screen.repeat_last',
            'Z ctrl alt', disableOld='R shift')

        # move
        for kmn in [
            'Markers', 'Grease Pencil Stroke Edit Mode', 'Paint Curve',
            '3D View', 'UV Editor', 'Mask Editing',
            'Graph Editor', 'Node Editor', 'SequencerPreview',
            'Clip Editor', 'Clip Graph Editor'
        ]:
            if kmn == 'Markers':
                add(kmn, 'marker.move',
                    'D', disableOld='G')
                add(kmn, {'marker.move': {'tweak': True}},
                    'RIGHTMOUSE CLICK_DRAG', disableOld='LEFTMOUSE CLICK_DRAG')
            else:
                add(kmn, 'transform.translate',
                    'D', disableOld='G')
                add(kmn, 'transform.translate',
                    'RIGHTMOUSE CLICK_DRAG', disableOld='LEFTMOUSE CLICK_DRAG')
        add('Object Mode', {'object.location_clear': {'clear_delta': False}},
            'D alt', disableOld='G alt')
        add('3D View', {'view3d.snap_selected_to_cursor': {'use_offset': True}},
            'D shift ctrl')
        add('Transform Modal Map', 'TRANSLATE', 'D', disableOld='G')

        # object
        for kmn in ['Grease Pencil Stroke Edit Mode', '3D View', 'Mask Editing']:
            add(kmn, 'transform.tosphere',
                'T ctrl', disableOld='S shift alt')
        for kmn in ['Grease Pencil Stroke Edit Mode', '3D View']:
            add(kmn, 'transform.bend',
                'B ctrl', disableOld='W shift')
        add('3D View', 'transform.push_pull',
            'W ctrl')
        add('Object Mode', {'object.randomize_transform': {'use_scale': False, 'loc': (0.5, -0.5, 0.0), 'rot': (0.0, 0.0, 0.7854)}},
            'R shift ctrl')

        # orientation
        add('3D View', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_orientations_pie'}},
            'O shift alt', disableOld='COMMA')
        add('3D View', {'transform.create_orientation': {'use': True}},
            'COMMA shift ctrl')
        add('3D View', 'transform.delete_orientation',
            'COMMA ctrl alt')

        # pivot
        for kmn, v in {
            '3D View': 'VIEW3D_MT_pivot_pie',
            'Graph Editor': 'GRAPH_MT_pivot_pie',
            'Image': 'IMAGE_MT_pivot_pie',
            'SequencerPreview': 'SEQUENCER_MT_pivot_pie',
            'Clip Editor': 'CLIP_MT_pivot_pie'
        }.items():
            add(kmn, {'wm.call_menu_pie': {'name': v}},
                'P shift alt', disableOld='PERIOD')
        add('Object Mode', {'wm.context_toggle': {'data_path': 'tool_settings.use_transform_data_origin'}},
            'V shift', disableOld='PERIOD ctrl')

        add('Object Mode', 'object.origin_set',
            'V alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'ORIGIN_GEOMETRY'))
        add('Object Mode', 'object.origin_set',
            'C alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'ORIGIN_CENTER_OF_VOLUME'))
        add('Object Mode', 'object.origin_set',
            'V shift ctrl', setKmiProps=lambda kmi: setTypeProp(kmi, 'ORIGIN_CURSOR'))

        # snapping
        add('3D View', {'wm.context_toggle': {'data_path': 'tool_settings.use_snap'}},
            'O', disableOld='TAB shift')
        add('3D View', {'wm.call_panel': {'name': 'VIEW3D_PT_snapping'}},
            'O shift', disableOld={'TAB': ['shift', 'ctrl']})
        add('UV Editor', {'wm.context_toggle': {'data_path': 'tool_settings.use_snap_uv'}},
            'O', disableOld='TAB shift')
        add('UV Editor', {'wm.context_menu_enum': {'data_path': 'tool_settings.snap_uv_element'}},
            'O shift', disableOld={'TAB': ['shift', 'ctrl']})
        add('Node Editor', {'wm.context_toggle': {'data_path': 'tool_settings.use_snap_node'}},
            'O', disableOld='TAB shift')
        add('Node Editor', {'wm.context_menu_enum': {'data_path': 'tool_settings.snap_node_element'}},
            'O shift', disableOld={'TAB': ['shift', 'ctrl']})
        add('Sequencer', {'wm.context_toggle': {'data_path': 'tool_settings.use_snap_sequencer'}},
            'O', disableOld='TAB shift')

        # proportional edit
        for kmn, v in {
            'Dopesheet': 'tool_settings.use_proportional_action',
            'Grease Pencil Stroke Edit Mode': 'tool_settings.use_proportional_edit',
            'Object Mode': 'tool_settings.use_proportional_edit_objects',
            'Curve': 'tool_settings.use_proportional_edit',
            'Curves': 'tool_settings.use_proportional_edit',
            'Mesh': 'tool_settings.use_proportional_edit',
            'Metaball': 'tool_settings.use_proportional_edit',
            'Lattice': 'tool_settings.use_proportional_edit',
            'Particle': 'tool_settings.use_proportional_edit',
            'UV Editor': 'tool_settings.use_proportional_edit',
            'Mask Editing': 'tool_settings.use_proportional_edit_mask',
            'Graph Editor': 'tool_settings.use_proportional_fcurve',
        }.items():
            add(kmn, {'wm.context_toggle': {'data_path': v}}, 'P')
            disable(kmn, {'wm.context_toggle': {'data_path': v}}, 'O')
            add(kmn, {'wm.call_menu_pie': {'name': 'VIEW3D_MT_proportional_editing_falloff_pie'}},
                'P shift', disableOld='O shift')
            if kmn in ['Grease Pencil Stroke Edit Mode', 'Curve', 'Curves', 'Mesh', 'Metaball']:
                add(kmn, {'wm.context_toggle': {'data_path': 'tool_settings.use_proportional_connected'}},
                    'P alt', disableOld='O alt')

    @classmethod
    def addPropertiesHotkeys(cls):
        # modifiers
        add('Object Mode', 'object.modifier_add',
            'A shift alt')
        for k, modType in {
            'N W': 'WEIGHTED_NORMAL',
            'T D': 'DATA_TRANSFER',
            'I DOUBLE_CLICK': 'MIRROR',
            'B DOUBLE_CLICK': 'BEVEL',
            'S DOUBLE_CLICK': 'SKIN',
            'F S': 'SOLIDIFY',
            'D DOUBLE_CLICK': 'DISPLACE',
            'C DOUBLE_CLICK': 'CURVE',
            'L DOUBLE_CLICK': 'LATTICE',
            'S W': 'SHRINKWRAP',
            'S D': 'SIMPLE_DEFORM',
            'C D': 'SURFACE_DEFORM',
            'X DOUBLE_CLICK': 'ARRAY',
            'S C': 'SCREW',
            'R DOUBLE_CLICK': 'REMESH',
            'D E': 'DECIMATE',
            'T DOUBLE_CLICK': 'TRIANGULATE',
            'B L': 'BOOLEAN'
        }.items():
            add('Object Mode', 'object.modifier_add',
                k + ' shift alt', setKmiProps=lambda kmi: setTypeProp(kmi, modType))

        # bool tool {b}
        add('Object Mode', {'wm.call_menu': {'name': 'VIEW3D_MT_booltool_menu'}},
            'B shift alt T', disableOld='B shift ctrl')
        add('Object Mode', 'object.booltool_auto_difference',
            'MINUS shift alt DOUBLE_CLICK', disableOld='NUMPAD_MINUS shift ctrl')
        add('Object Mode', 'object.booltool_auto_union',
            'EQUAL shift alt DOUBLE_CLICK', disableOld='NUMPAD_PLUS shift ctrl')
        add('Object Mode', 'object.booltool_auto_intersect',
            'EIGHT shift alt DOUBLE_CLICK', disableOld='NUMPAD_ASTERIX shift ctrl')
        add('Object Mode', 'object.booltool_auto_slice',
            'SLASH shift alt DOUBLE_CLICK', disableOld='NUMPAD_SLASH shift ctrl')

        for kmn in ['Object Mode', 'Sculpt']:
            for i, n in enumerate(NUMBERS_IDX):
                if i < 6:
                    add(kmn, {'object.subdivision_set': {'level': i, 'relative': False}},
                        n + ' shift alt DOUBLE_CLICK', disableOld=n + ' ctrl')

        # actions
        add('Property Editor', 'object.modifier_copy',
            'D ctrl', disableOld='D shift')
        add('Property Editor', 'object.gpencil_modifier_copy',
            'D ctrl', disableOld='D shift')
        add('Property Editor', {'object.modifier_remove': {'report': True}},
            'X ctrl', disableOld='X')
        add('Property Editor', {'object.modifier_remove': {'report': True}},
            'BACK_SPACE', disableOld='DEL')

    @classmethod
    def addAnimationHotkeys(cls):
        add('Frames', 'screen.animation_play',
            'QUOTE', disableOld='SPACE')
        add('Frames', {'screen.animation_play': {'reverse': True}},
            'SEMI_COLON', disableOld='SPACE shift ctrl')

        for kmn, v in {
            'User Interface': 'anim.keyframe_insert_button',  # all: True
            'Outliner': 'anim.keyframe_insert',
            'Dopesheet': 'action.keyframe_insert',
            'Pose': 'anim.keyframe_insert_menu',
            'Object Mode': 'anim.keyframe_insert_menu',
            'Graph Editor': 'graph.keyframe_insert',
            'Clip Editor': 'clip.keyframe_insert',
        }.items():
            add(kmn, v if kmn != 'User Interface' else {v: {'all': True}},
                'K shift', disableOld='I')

        for kmn, v in {
            'User Interface': 'anim.keyframe_delete_button',  # all: True
            'Outliner': 'anim.keyframe_delete',
            'Pose': 'anim.keyframe_delete_v3d',
            'Object Mode': 'anim.keyframe_delete_v3d',
            'Clip Editor': 'clip.keyframe_delete',
        }.items():
            if kmn == 'User Interface':
                add(kmn, {v: {'all': True}}, 'K alt', disableOld='I')
            elif kmn == 'Object Mode':
                add(kmn, {v: {'confirm': False}}, 'K alt', disableOld='I')
            else:
                add(kmn, v, 'K alt', disableOld='I')

        add('User Interface', {'anim.keyframe_clear_button': {'all': True}},
            'K shift alt', disableOld='I shift alt')

        for kmn in ['Object Mode', 'Pose']:
            add(kmn, 'anim.keying_set_active_set',
                'K ctrl', disableOld='I shift ctrl alt')

        for kmn, v in {
            'User Interface': 'anim.keyingset_button_add',
            'Outliner': 'outliner.keyingset_add_selected'
        }.items():
            add(kmn, v, 'K shift ctrl', disableOld='K')

        for kmn, v in {
            'User Interface': 'anim.keyingset_button_remove',
            'Outliner': 'outliner.keyingset_remove_selected'
        }.items():
            add(kmn, v, 'K ctrl alt', disableOld='K alt')

    @classmethod
    def addEditMeshHotkeys(cls):
        # mode
        for n in ['ONE', 'TWO', 'THREE']:
            for kmn in ['Mesh', 'UV Editor']:
                disable(kmn, 'mesh.select_mode', n + ' ctrl')
                disable(kmn, 'mesh.select_mode', n + ' shift ctrl')

        for k, v in {
            'V': 'vertices', 'E': 'edges', 'F': 'faces'
        }.items():
            disable('Mesh', 'wm.call_menu', k + ' ctrl')

        # symmetry
        for k in ['X', 'Y', 'Z']:
            add('Window', {'wm.context_toggle': {'data_path': 'object.use_mesh_mirror_' + k.lower()}},
                k + ' DOUBLE_CLICK')

        # auto merge
        add('Mesh', {'wm.context_toggle': {'data_path': 'scene.tool_settings.use_mesh_automerge'}},
            'J')

        # select
        for kmn, v in {
            'Curve': 'curve.select_similar',
            'Mesh': {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_select_similar'}},
            'Armature': 'armature.select_similar',
            'Metaball': 'mball.select_similar',
            'UV Editor': 'uv.select_similar'
        }.items():
            add(kmn, v, 'S shift', disableOld='G shift')
        add('Mesh', 'mesh.region_to_loop', 'B shift')
        add('Mesh', 'mesh.loop_to_region', 'R shift')
        add('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_select_by_trait'}},
            'T shift')
        add('Mesh', 'mesh.edges_select_sharp', 'E shift')
        add('Mesh', 'mesh.faces_select_linked_flat', 'F shift')
        add('Mesh', 'mesh.select_nth', 'C shift')

        for kmn, v in {
            'Dopesheet': 'action.select_',
            'Grease Pencil Stroke Edit Mode': 'gpencil.select_',
            'Grease Pencil Stroke Sculpt Mode': 'gpencil.select_',
            'Grease Pencil Stroke Vertex Mode': 'gpencil.select_',
            'Paint Face Mask (Weight, Vertex, Texture)': 'paint.face_select_',
            'Paint Vertex Selection (Weight, Vertex)': 'paint.vert_select_',
            'Object Mode': 'object.select_',
            'Curve': 'curve.select_',
            'Curves': 'curves.select_',
            'Mesh': 'mesh.select_',
            'Armature': 'armature.select_',
            'Lattice': 'lattice.select_',
            'Particle': 'particle.select_',
            'UV Editor': 'uv.select_',
            'Mask Editing': 'mask.select_',
            'Graph Editor': 'graph.select_',
            'Sequencer': 'sequencer.select_',
        }.items():
            for m in ['less', 'more']:
                add(kmn, v + m,
                    ('MINUS' if m == 'less' else 'EQUAL') + ' shift',
                    disableOld=('NUMPAD_MINUS' if m == 'less' else 'NUMPAD_PLUS') + ' ctrl')

        add('Mesh', 'mesh.select_prev_item', 'MINUS shift alt',
            disableOld='NUMPAD_MINUS shift ctrl')
        add('Mesh', 'mesh.select_next_item', 'EQUAL shift alt',
            disableOld='NUMPAD_PLUS shift ctrl')

        for kmn, v in {
            'Pose': 'pose.select_mirror',
            'Mesh': {'mesh.select_mirror': {'extend': True}},
            'Armature': {'armature.select_mirror': {'extend': False}}
        }.items():
            add(kmn, v, 'I', disableOld='M shift ctrl')

        for kmn, v in {
            'Paint Face Mask (Weight, Vertex, Texture)': {'paint.face_select_linked_pick': {'deselect': True}},
            'Paint Vertex Selection (Weight, Vertex)': {'paint.vert_select_linked_pick': {'select': False}},
            'Curve': {'curve.select_linked_pick': {'deselect': True}},
            'Mesh': {'mesh.select_linked_pick': {'deselect': True}},
            'Armature': {'armature.select_linked_pick': {'deselect': True}},
            'Particle': {'particle.select_linked_pick': {'deselect': True}},
            'UV Editor': {'uv.select_linked_pick': {'deselect': True}},
            'Mask Editing': {'mask.select_linked_pick': {'deselect': True}},
        }.items():
            add(kmn, v, 'L DOUBLE_CLICK', disableOld='L shift')

        for kmn, v in {
            'Mesh': 'mesh.select_linked',
            'Curve': 'curve.select_linked',
            'Paint Face Mask (Weight, Vertex, Texture)': 'paint.face_select_linked',
            'Paint Vertex Selection (Weight, Vertex)': 'paint.vert_select_linked'
        }.items():
            add(kmn, v, 'LEFT_SHIFT alt DOUBLE_CLICK')

        # mesh
        add('3D View', 'mesh.select_linked',
            'M shift', setKmiProps=lambda kmi: setDelimitProp(kmi, 'MATERIAL'))
        for kmn, v in {
            'Mesh': 'VIEW3D_MT_edit_mesh_merge',
            'UV Editor': 'IMAGE_MT_uvs_merge'
        }.items():
            add(kmn, {'wm.call_menu': {'name': v}},
                'M shift', disableOld='M')
        for k, v in {
            'M': 'LAST',
            'M ctrl': 'CENTER',
            'C shift alt': 'COLLAPSE'
        }.items():
            add('Mesh', 'mesh.merge', k,
                setKmiProps=lambda kmi: setTypeProp(kmi, v))
        add('Mesh', {'mesh.remove_doubles': {'threshold': 0.001}},
            'M shift alt')

        for kmn, v in {
            'Mesh': 'mesh.split',
            'Armature': 'armature.split',
            'UV Editor': 'uv.select_split',
            'NLA Editor': 'nla.split'
        }.items():
            add(kmn, v, 'M ctrl alt', disableOld='Y')
            add(kmn, v, 'LEFT_CTRL alt DOUBLE_CLICK')
        add('Grease Pencil Stroke Edit Mode', 'gpencil.stroke_split',
            'M ctrl alt', disableOld='V')

        for kmn, v in {
            'Grease Pencil Stroke Edit Mode': 'gpencil.stroke_separate',
            'Mesh': 'mesh.separate',
            'Armature': 'armature.separate',
            'Node Editor': 'node.group_separate',
        }.items():
            add(kmn, v, 'J alt', disableOld='P')
        add('Sequencer', 'sequencer.images_separate', 'J alt', disableOld='Y')
        add('Mesh', 'mesh.separate',
            'J ctrl alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'SELECTED'))

        add('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_delete'}},
            'X shift', disableOld='X')
        disable('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_delete'}},
                'DEL')
        add('Mesh', 'mesh.delete', 'X shift ctrl')
        add('Mesh', 'mesh.delete', 'BACK_SPACE shift')
        add('Mesh', 'mesh.delete_loose', 'X shift alt')
        add('Mesh', 'mesh.dissolve_mode', 'BACK_SPACE', disableOld='DEL ctrl')
        add('Mesh', 'mesh.dissolve_limited', 'D shift alt')

        # connect
        add('Mesh', 'mesh.vert_connect_path', 'C shift ctrl', disableOld='J')
        add('Mesh', 'mesh.bridge_edge_loops', 'B shift ctrl')
        add('Mesh', 'mesh.edge_face_add', 'M shift ctrl', disableOld='F')
        add('Mesh', 'mesh.edge_face_add', 'LEFT_CTRL shift DOUBLE_CLICK')
        add('Mesh', 'mesh.fill', 'F shift ctrl', disableOld='F alt')
        add('Mesh', 'mesh.fill_grid', 'F shift ctrl alt')

        # divide
        add('Mesh', 'mesh.subdivide', 'D ctrl alt')

        def setQuadAndNgonMethodProp(kmi, *args):
            kmi.properties.quad_method = args[0]
            kmi.properties.ngon_method = args[1]
        add('Mesh', 'mesh.quads_convert_to_tris',
            'T ctrl alt', disableOld='T ctrl', setKmiProps=lambda kmi: setQuadAndNgonMethodProp(kmi, 'BEAUTY', 'BEAUTY'))
        disable('Mesh', 'mesh.quads_convert_to_tris', 'T shift ctrl')

        add('Mesh', 'mesh.poke', 'P ctrl alt')

        # combine
        add('Mesh', 'mesh.unsubdivide', 'U shift alt')
        add('Mesh', 'mesh.tris_convert_to_quads',
            'Q shift alt', disableOld='J alt')

        # mesh normals
        add('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_normals'}},
            'N shift', disableOld='N alt')
        add('Mesh', 'mesh.flip_normals', 'N alt')
        add('Mesh', {'mesh.normals_make_consistent': {'inside': False}},
            'N alt DOUBLE_CLICK', disableOld='N shift')
        disable('Mesh', {'mesh.normals_make_consistent': {
                'inside': True}}, 'N shift ctrl')
        add('Mesh', 'mesh.point_normals', 'N shift ctrl', disableOld='L alt')

        # mesh transforms
        add('Mesh', {'transform.vertex_random': {'offset': -0.1}},
            'R shift ctrl')
        add('Mesh', {'transform.vertex_warp': {'offset_angle': math.radians(15), 'mix': -0.1, 'max': 0.1}},
            'W alt')
        add('Mesh', 'mesh.knife_project', 'K ctrl')
        add('3D View', {'view3d.select': {'object': True, 'center': True, 'deselect_all': True}},
            'LEFTMOUSE ctrl CLICK')
        disable('3D View', {'view3d.select': {'object': True, 'center': True}},
                'LEFTMOUSE ctrl CLICK')

        # quick tools
        add('Mesh', {'mesh.dupli_extrude_cursor': {'rotate_source': True}},
            'RIGHTMOUSE alt CLICK', disableOld='RIGHTMOUSE ctrl CLICK')
        add('Mesh', {'mesh.dupli_extrude_cursor': {'rotate_source': False}},
            'RIGHTMOUSE ctrl alt CLICK', disableOld='RIGHTMOUSE shift ctrl CLICK')
        add('Curve', 'curve.vertex_add',
            'RIGHTMOUSE alt CLICK', disableOld='RIGHTMOUSE ctrl CLICK')

        add('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_edit_mesh_extrude'}},
            'E ctrl', disableOld='E alt')
        add('Mesh', 'view3d.edit_mesh_extrude_move_shrink_fatten',
            'E alt')
        add('Mesh', 'mesh.inset', 'N', disableOld='I')

        add('Mesh', 'mesh.bevel',
            'B', disableOld='B ctrl', setKmiProps=lambda kmi: setAffectProp(kmi, 'EDGES'))
        add('Mesh', 'mesh.bevel',
            'B alt', disableOld='B shift ctrl', setKmiProps=lambda kmi: setAffectProp(kmi, 'VERTICES'))

        add('Mesh', {'mesh.loopcut_slide': {'release_confirm': False}},
            'C', disableOld='R ctrl')
        add('Mesh', {'mesh.knife_tool': {'use_occlude_geometry': False, 'only_selected': True}},
            'K alt', disableOld='K shift')

        add('Transform Modal Map', 'VERT_EDGE_SLIDE',
            'D DOUBLE_CLICK', disableOld='G')
        disable('Mesh', 'transform.vert_slide', 'V shift')
        add('Mesh', {'mesh.offset_edge_loops_slide': {'release_confirm': False}},
            'D shift', disableOld='R shift ctrl')

        add('Mesh', {'mesh.rip_move': {'use_fill': False}},
            'V alt', disableOld='V')
        add('Mesh', {'mesh.rip_move': {'use_fill': True}},
            'V shift alt', disableOld='V alt')

        add('Mesh', 'transform.shrink_fatten',
            'F ctrl', disableOld='S alt')

        for kmn in ['Grease Pencil Stroke Edit Mode', '3D View', 'UV Editor', 'Mask Editing']:
            add(kmn, 'transform.shear', 'R alt', disableOld='S shift ctrl alt')

        add('Mesh', 'mesh.vertices_smooth', 'S shift alt')
        add('Mesh', 'transform.edge_crease', 'C alt', disableOld='E shift')

        # f2 {b}
        addAddonKeymapItem('Mesh', 'mesh.f2', 'F alt', disableOld='F')

        # tools
        add('Mesh', {'wm.tool_set_by_id': {'name': 'builtin.spin'}},
            'T alt')
        add('Mesh', {'wm.tool_set_by_id': {'name': 'builtin.rip_region'}},
            'Y alt')

        # uv
        add('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_uv_map'}},
            'U shift', disableOld='U')
        add('UV Editor', {'wm.call_menu': {'name': 'IMAGE_MT_uvs_unwrap'}},
            'U shift', disableOld='U')
        for kmn, v in {
            'Mesh': 'mesh.',
            'UV Editor': 'uv.'
        }.items():
            add(kmn, v + 'mark_seam', 'U')
            add(kmn, {v + 'mark_seam': {'clear': True}}, 'U DOUBLE_CLICK')
            add(kmn, 'uv.unwrap', 'U ctrl')
        add('Mesh', 'uv.smart_project', 'U shift ctrl')
        add('Mesh', 'uv.cube_project', 'B ctrl alt')
        add('Mesh', 'uv.project_from_view', 'V ctrl alt')

        # shade
        add('Mesh', 'mesh.faces_shade_smooth', 'EIGHT')
        add('Mesh', 'mesh.faces_shade_flat', 'EIGHT DOUBLE_CLICK')
        add('Mesh', 'mesh.mark_sharp', 'SEVEN')
        add('Mesh', {'mesh.mark_sharp': {'clear': True}}, 'SEVEN DOUBLE_CLICK')

        # vertex groups
        disable('Mesh', {'wm.call_menu': {'name': 'VIEW3D_MT_vertex_group'}},
                'G ctrl')
        disable('Mesh', 'object.vertex_group_remove_from', 'G ctrl alt')
        for kmn in ['Mesh', 'Sculpt', 'Vertex Paint', 'Weight Paint', 'Image Paint', 'UV Editor']:
            add(kmn, {'wm.call_menu': {'name': 'VIEW3D_MT_vertex_group'}},
                'G shift')
        for kmn in ['Mesh', 'UV Editor']:
            add(kmn, 'object.vertex_group_assign_new', 'G shift ctrl')
            add(kmn, 'object.vertex_group_select', 'G')
            add(kmn, 'object.vertex_group_assign', 'G ctrl')
            add(kmn, 'object.vertex_group_remove_from', 'G alt')
            add(kmn, {'object.vertex_group_remove_from': {'use_all_verts': True}},
                'G alt DOUBLE_CLICK')
            add(kmn, 'object.vertex_group_remove', 'G ctrl alt')

        # overlays
        add('Mesh', {'wm.context_toggle': {'data_path': 'space_data.overlay.show_extra_edge_length'}},
            'L ctrl alt')

    @classmethod
    def addCurvesHotkeys(cls):
        # quick transforms
        add('Curve', 'transform.rotate', 'RIGHTMOUSE shift CLICK_DRAG')
        add('Curve', 'transform.resize', 'RIGHTMOUSE ctrl CLICK_DRAG')

        # curve
        add('Curve', 'curve.spline_type_set', 'T shift ctrl')
        add('Curve', 'curve.spline_type_set',
            'B shift ctrl', setKmiProps=lambda kmi: setTypeProp(kmi, 'BEZIER'))
        for kmn, v in {
            'Curve': 'curve.cyclic_toggle',
            'Mask Editing': 'mask.cyclic_toggle'
        }.items():
            add(kmn, v, 'C shift ctrl', disableOld='C alt')
        add('Curve', 'curve.switch_direction', 'D shift')

        add('Curve', 'curve.split', 'M ctrl alt', disableOld='Y')
        add('Curve', 'curve.split', 'LEFT_CTRL alt DOUBLE_CLICK')
        add('Curve', {'curve.separate': {'confirm': False}},
            'J ctrl alt')

        # segments
        add('Curve', 'curve.make_segment', 'M shift ctrl', disableOld='F')
        add('Curve', 'curve.make_segment', 'LEFT_CTRL shift DOUBLE_CLICK')
        add('Curve', 'curve.subdivide', 'D ctrl alt')
        add('Curve', 'curve.smooth', 'S shift alt')

        # vertex points
        add('Curve', 'curve.handle_type_set',
            'V shift', disableOld='V')
        add('Curve', 'curve.handle_type_set',
            'LEFT_CTRL DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'TOGGLE_FREE_ALIGN'))
        add('Curve', 'curve.handle_type_set',
            'LEFT_ALT DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'AUTOMATIC'))
        add('Curve', 'curve.handle_type_set',
            'LEFT_ALT ctrl DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'VECTOR'))

        for kmn, v in {
            'Curve': {'wm.call_menu': {'name': 'VIEW3D_MT_edit_curve_delete'}},
            'Curves': 'curves.delete'
        }.items():
            add(kmn, v, 'X shift', disableOld='X')
            disable(kmn, v, 'DEL')
        add('Curve', 'curve.delete',
            'X shift ctrl', setKmiProps=lambda kmi: setTypeProp(kmi, 'VERT'))
        add('Curve', 'curve.dissolve_verts', 'BACK_SPACE', disableOld='DEL ctrl')

        for kmn, v in {
            'Curve': 'curve.normals_make_consistent',
            'Armature': 'armature.calculate_roll',
            'Mask Editing': 'mask.normals_make_consistent'
        }.items():
            add(kmn, v, 'R shift', disableOld='N shift')

        add('Curve', 'transform.tilt', 'T alt', disableOld='T ctrl')
        add('Curve', 'curve.tilt_clear', 'T ctrl alt', disableOld='T alt')

        # tools
        add('Curve', {'wm.tool_set_by_id': {'name': 'builtin.draw'}},
            'C DOUBLE_CLICK')
        add('Curve', {'wm.tool_set_by_id': {'name': 'builtin.pen'}},
            'C')

        add('3D View Tool: Edit Curve, Curve Pen', {'curve.pen': {'select_point': True, 'extrude_point': False, 'move_segment': False, 'move_point': False}},
            'LEFTMOUSE', disableOld='LEFTMOUSE', setKmiProps=lambda kmi: setCloseSplineProp(kmi, 'OFF'))
        add('3D View Tool: Edit Curve, Curve Pen', {'curve.pen': {'extrude_point': True, 'toggle_vector': False, 'cycle_handle_type': False}},
            'LEFTMOUSE DOUBLE_CLICK', disableOld='LEFTMOUSE DOUBLE_CLICK')
        add('3D View Tool: Edit Curve, Curve Pen', {'curve.pen': {'insert_point': True, 'delete_point': True}},
            'LEFTMOUSE alt', disableOld='LEFTMOUSE ctrl')
        add('3D View Tool: Edit Curve, Curve Pen', {'curve.pen': {'close_spline': True}},
            'LEFTMOUSE shift ctrl', setKmiProps=lambda kmi: setCloseSplineProp(kmi, 'ON_PRESS'))

        # overlays
        add('Curve', {'wm.context_toggle': {'data_path': 'space_data.overlay.show_curve_normals'}},
            'L ctrl alt')

    @classmethod
    def addSculptHotkeys(cls):
        # brush
        for kmn, v in {
            'Sculpt': 'VIEW3D_PT_sculpt_context_menu',
            'Vertex Paint': 'VIEW3D_PT_paint_vertex_context_menu',
            'Weight Paint': 'VIEW3D_PT_paint_weight_context_menu',
            'Image Paint': 'VIEW3D_PT_paint_texture_context_menu'
        }.items():
            add(kmn, {'wm.call_panel': {'name': v}},
                'RIGHTMOUSE CLICK', disableOld='RIGHTMOUSE')
        add('Sculpt', {'wm.call_panel': {'name': 'VIEW3D_PT_tools_brush_select'}},
            'B shift')

        # size/strenth effect
        for kmn, v in {
            'Sculpt': 'tool_settings.sculpt.brush',
            'Sculpt Curves': 'tool_settings.curves_sculpt.brush',
            'Weight Paint': 'tool_settings.weight_paint.brush',
            'Image Editor Tool: Uv, Sculpt Stroke': 'tool_settings.uv_sculpt.brush',
        }.items():
            add(kmn, {'wm.radial_control': {
                'data_path_primary': v + '.size',
                'data_path_secondary': 'tool_settings.unified_paint_settings.size',
                'use_secondary': 'tool_settings.unified_paint_settings.use_unified_size',
                'rotation_path': v + '.texture_slot.angle',
                'color_path': v + '.cursor_color_add',
                'image_id': v}},
                'S', disableOld='F')
            add(kmn, {'wm.radial_control': {
                'data_path_primary': v + '.strength',
                'data_path_secondary': 'tool_settings.unified_paint_settings.strength',
                'use_secondary': 'tool_settings.unified_paint_settings.use_unified_strength',
                'rotation_path': v + '.texture_slot.angle',
                'color_path': v + '.cursor_color_add',
                'image_id': v}},
                'E', disableOld='F shift')

        for kmn, v in {
            'Grease Pencil Stroke Paint Mode': 'tool_settings.gpencil_paint.brush',
            'Grease Pencil Stroke Sculpt Mode': 'tool_settings.gpencil_sculpt_paint.brush',
            'Grease Pencil Stroke Vertex Mode': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Vertex (Draw)': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Vertex (Blur)': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Vertex (Average)': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Vertex (Smear)': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Vertex (Replace)': 'tool_settings.gpencil_vertex_paint.brush',
            'Grease Pencil Stroke Weight Mode': 'tool_settings.gpencil_weight_paint.brush',
            'Particle': 'tool_settings.particle_edit.brush',
        }.items():
            add(kmn, {'wm.radial_control': {'data_path_primary': v + '.size'}},
                'S', disableOld='F')
            if kmn != 'Grease Pencil Stroke Vertex (Replace)':
                cmd = '.gpencil_settings.pen_strength' if kmn != 'Particle' else '.strength'
                add(kmn, {'wm.radial_control': {'data_path_primary': v + cmd}},
                    'E', disableOld='F shift')

        # softness
        add('Sculpt', {'wm.radial_control': {'data_path_primary': 'tool_settings.sculpt.brush.hardness'}},
            'S alt')
        # units
        add('Sculpt', {'wm.context_toggle_enum': {'data_path': 'scene.tool_settings.unified_paint_settings.use_locked_size'}},
            'U DOUBLE_CLICK', setKmiProps=lambda kmi: setContextToggleValues(kmi, 'VIEW', 'SCENE'))

        # texture
        for kmn, v in {
            'Sculpt': 'tool_settings.sculpt.brush',
            'Vertex Paint': 'tool_settings.vertex_paint.brush',
            'Image Paint': 'tool_settings.image_paint.brush',
        }.items():
            add(kmn, {'wm.call_panel': {'name': 'VIEW3D_PT_tools_brush_texture'}},
                'T shift')
            # Angle (rotation)
            add(kmn, {'wm.radial_control': {
                'data_path_primary': v + '.texture_slot.angle',
                'rotation_path': v + '.texture_slot.angle',
                'color_path': v + '.cursor_color_add',
                'fill_color_path': '' if kmn == 'Sculpt' else v + '.color',
                'fill_color_override_path': '' if kmn == 'Sculpt' else 'tool_settings.unified_paint_settings.color',
                'fill_color_override_test_path': '' if kmn == 'Sculpt' else 'tool_settings.unified_paint_settings.use_unified_color',
                'image_id': v}},
                'R alt', disableOld='F ctrl')

        # stroke
        for kmn, v in {
            'Sculpt': 'sculpt',
            'Weight Paint': 'weight_paint',
            'Vertex Paint': 'vertex_paint',
            'Image Paint': 'image_paint'
        }.items():
            # smooth
            add(kmn, {'wm.context_toggle': {'data_path': 'tool_settings.' + v + '.brush.use_smooth_stroke'}},
                'LEFTMOUSE shift ctrl', disableOld='S shift')
            # smooth radius
            add(kmn, {'wm.radial_control': {'data_path_primary': 'tool_settings.' + v + '.brush.smooth_stroke_radius'}},
                'R')
            # method
            add(kmn, {'wm.context_menu_enum': {'data_path': 'tool_settings.' + v + '.brush.stroke_method'}},
                'S shift', disableOld='E')
            # method line
            add(kmn, {'wm.context_toggle_enum': {'data_path': 'tool_settings.' + v + '.brush.stroke_method'}},
                'LEFTMOUSE alt DOUBLE_CLICK', setKmiProps=lambda kmi: setContextToggleValues(kmi, 'LINE', 'SPACE'))
            # method curve
            add(kmn, {'wm.context_toggle_enum': {'data_path': 'tool_settings.' + v + '.brush.stroke_method'}},
                'LEFTMOUSE shift alt', setKmiProps=lambda kmi: setContextToggleValues(kmi, 'CURVE', 'SPACE'))
            # falloff
            add(kmn, {'wm.context_menu_enum': {'data_path': 'tool_settings.' + v + '.brush.curve_preset'}},
                'F shift')

        add('Paint Curve', 'paintcurve.add_point_slide',
            'LEFTMOUSE DOUBLE_CLICK', disableOld='RIGHTMOUSE ctrl')

        # dyntopo
        add('Sculpt', 'sculpt.dyntopo_detail_size_edit', 'D shift', disableOld='R')
        add('Sculpt', {'wm.tool_set_by_id': {'name': 'builtin_brush.Simplify'}},
            'D alt')

        # remesh
        add('Sculpt', 'object.voxel_size_edit', 'R shift', disableOld='R')
        add('Sculpt', 'object.voxel_remesh', 'R ctrl')
        add('Sculpt', 'object.quadriflow_remesh', 'R ctrl alt')

        # quick mask
        add('Sculpt', {'paint.mask_box_gesture': {'value': 1.0}},
            'RIGHTMOUSE shift')
        add('Sculpt', {'paint.mask_box_gesture': {'value': 1.0, 'use_front_faces_only': True}},
            'B', disableOld='B')
        add('Sculpt', {'paint.mask_box_gesture': {'value': 0.0}},
            'RIGHTMOUSE shift ctrl')
        add('Sculpt', {'paint.mask_box_gesture': {'value': 0.0, 'use_front_faces_only': True}},
            'B ctrl')
        add('Sculpt', {'paint.mask_line_gesture': {'value': 1.0}},
            'RIGHTMOUSE alt')
        disable('Gesture Straight Line', 'CANCEL', 'RIGHTMOUSE')
        add('Sculpt', {'paint.mask_line_gesture': {'value': 0.0}},
            'RIGHTMOUSE ctrl alt')
        add('Sculpt', {'paint.mask_lasso_gesture': {'value': 1.0}},
            'RIGHTMOUSE shift alt', disableOld='LEFTMOUSE shift ctrl')
        add('Sculpt', {'paint.mask_lasso_gesture': {'value': 0.0}},
            'RIGHTMOUSE shift ctrl alt')

        # mask
        add('Sculpt', 'paint.brush_select',
            'ONE shift', disableOld='M', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'MASK'))
        add('Sculpt', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_sculpt_mask_edit_pie'}},
            'Q shift', disableOld='A')
        add('Grease Pencil Stroke Sculpt Mode', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_sculpt_gpencil_automasking_pie'}},
            'Q shift alt', disableOld='A ctrl alt')
        add('Sculpt', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_sculpt_automasking_pie'}},
            'Q shift alt', disableOld='A alt')

        add('Sculpt', {'paint.mask_flood_fill': {'value': 1.0}},
            'Q DOUBLE_CLICK', setKmiProps=lambda kmi: setModeProp(kmi, 'VALUE'))
        add('Sculpt', {'paint.mask_flood_fill': {'value': 0.0}},
            'Q', disableOld='M alt', setKmiProps=lambda kmi: setModeProp(kmi, 'VALUE'))
        add('Sculpt', 'paint.mask_flood_fill',
            'Q alt', disableOld='I ctrl', setKmiProps=lambda kmi: setModeProp(kmi, 'INVERT'))

        def setTargetAndFalloffTypeProp(kmi, *args):
            kmi.properties.target = args[0]
            kmi.properties.falloff_type = args[1]
        add('Sculpt', {'sculpt.expand': {'use_mask_preserve': True}},
            'Q ctrl', disableOld='A shift',
            setKmiProps=lambda kmi: setTargetAndFalloffTypeProp(kmi, 'MASK', 'TOPOLOGY_DIAGONALS'))
        add('Sculpt', {'sculpt.expand': {'use_mask_preserve': True}},
            'Q shift ctrl', disableOld='A shift alt',
            setKmiProps=lambda kmi: setTargetAndFalloffTypeProp(kmi, 'MASK', 'NORMALS'))

        add('Sculpt', 'sculpt.mask_filter',
            'EQUAL shift', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'GROW'))
        add('Sculpt', 'sculpt.mask_filter',
            'MINUS shift', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'SHRINK'))
        add('Sculpt', 'sculpt.mask_filter',
            'EQUAL shift alt', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'SMOOTH'))
        add('Sculpt', 'sculpt.mask_filter',
            'MINUS shift alt', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'SHARPEN'))
        add('Sculpt', 'sculpt.mask_filter',
            'EQUAL shift ctrl', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'CONTRAST_INCREASE'))
        add('Sculpt', 'sculpt.mask_filter',
            'MINUS shift ctrl', setKmiProps=lambda kmi: setFilterTypeProp(kmi, 'CONTRAST_DECREASE'))

        add('Sculpt', 'mesh.paint_mask_slice', 'S ctrl alt')

        # face sets (areas)
        add('Sculpt', {'wm.tool_set_by_id': {'name': 'builtin_brush.Draw Face Sets'}},
            'TWO shift')
        add('Sculpt', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_sculpt_face_sets_edit_pie'}},
            'A shift', disableOld='W')
        add('Sculpt', {'wm.call_menu': {'name': 'VIEW3D_MT_face_sets_init'}},
            'A shift alt', disableOld='')
        add('Sculpt', 'sculpt.face_sets_create',
            'A DOUBLE_CLICK', setKmiProps=lambda kmi: setModeProp(kmi, 'VISIBLE'))
        add('Sculpt', 'sculpt.face_sets_create',
            'A alt', setKmiProps=lambda kmi: setModeProp(kmi, 'MASKED'))
        add('Sculpt', 'sculpt.face_sets_create',
            'W alt', setKmiProps=lambda kmi: setModeProp(kmi, 'SELECTION'))

        add('Sculpt', {'sculpt.expand': {'use_mask_preserve': False, 'use_modify_active': False}},
            'A ctrl', disableOld='W shift',
            setKmiProps=lambda kmi: setTargetAndFalloffTypeProp(kmi, 'FACE_SETS', 'TOPOLOGY_DIAGONALS'))
        add('Sculpt', {'sculpt.expand': {'use_mask_preserve': False, 'use_modify_active': True}},
            'A shift ctrl', disableOld='W shift alt',
            setKmiProps=lambda kmi: setTargetAndFalloffTypeProp(kmi, 'FACE_SETS', 'BOUNDARY_FACE_SET'))

        add('Sculpt', 'sculpt.face_set_edit',
            'EQUAL alt', disableOld='W ctrl', setKmiProps=lambda kmi: setModeProp(kmi, 'GROW'))
        add('Sculpt', 'sculpt.face_set_edit',
            'MINUS alt', disableOld='W ctrl alt', setKmiProps=lambda kmi: setModeProp(kmi, 'SHRINK'))

        add('Sculpt', 'sculpt.face_set_change_visibility',
            'H', disableOld='H shift', setKmiProps=lambda kmi: setModeProp(kmi, 'HIDE_ACTIVE'))
        add('Sculpt', 'sculpt.face_set_change_visibility',
            'H shift', setKmiProps=lambda kmi: setModeProp(kmi, 'TOGGLE'))
        disable(
            'Sculpt', {'sculpt.face_set_change_visibility': {'mode': 0}}, 'H')
        add('Sculpt', 'paint.hide_show', 'H ctrl')
        add('Sculpt', 'sculpt.reveal_all', 'H DOUBLE_CLICK', disableOld='H alt')
        add('Sculpt', 'sculpt.reveal_all', 'H alt DOUBLE_CLICK')
        add('Sculpt', 'sculpt.face_set_invert_visibility', 'H alt')

        add('Sculpt', 'mesh.face_set_extract', 'D shift ctrl')

        # quick trim/project
        add('Sculpt', 'sculpt.trim_box_gesture', 'X shift')
        add('Sculpt', 'sculpt.project_line_gesture', 'X alt')
        add('Sculpt', 'sculpt.trim_lasso_gesture', 'X ctrl')

        # modifiers
        add('Sculpt', 'sculpt.mesh_filter',
            'S shift alt', setKmiProps=lambda kmi: setTypeProp(kmi, 'SMOOTH'))

        # brushes
        add('Sculpt', 'paint.brush_select',
            'ONE', disableOld='X', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'DRAW'))
        add('Sculpt', 'paint.brush_select',
            'D', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'DRAW_SHARP'))
        add('Sculpt', 'paint.brush_select',
            'C alt', disableOld='C shift', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'CREASE'))
        add('Sculpt', 'paint.brush_select',
            'TWO', disableOld='C', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'CLAY'))
        add('Sculpt', 'paint.brush_select',
            'C', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'CLAY_STRIPS'))
        add('Sculpt', {'paint.brush_select': {'toggle': True, 'create_missing': True}},
            'THREE shift', disableOld='S shift', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'SMOOTH'))
        add('Sculpt', 'paint.brush_select',
            'THREE', disableOld='T shift', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'FLATTEN'))
        add('Sculpt', 'paint.brush_select',
            'F alt', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'FILL'))
        add('Sculpt', 'paint.brush_select',
            'FOUR', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'SCRAPE'))
        add('Sculpt', 'paint.brush_select',
            'M', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'MULTIPLANE_SCRAPE'))
        add('Sculpt', 'paint.brush_select',
            'E alt', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'ELASTIC_DEFORM'))
        add('Sculpt', 'paint.brush_select',
            'FIVE', disableOld='K', setKmiProps=lambda kmi: setSculptToolProp(kmi, 'SNAKE_HOOK'))

        add('Sculpt', {'wm.tool_set_by_id': {'name': 'builtin.scale'}},
            'T DOUBLE_CLICK')

        # pivot
        add('Sculpt', 'sculpt.set_pivot_position',
            'V shift ctrl', setKmiProps=lambda kmi: setModeProp(kmi, 'SURFACE'))
        add('Sculpt', 'sculpt.set_pivot_position',
            'V alt', setKmiProps=lambda kmi: setModeProp(kmi, 'ORIGIN'))

        # overlays
        add('Sculpt', {'wm.context_toggle': {'data_path': 'scene.tool_settings.sculpt.show_mask'}},
            'Q ctrl alt', disableOld='M ctrl')
        add('Sculpt', {'wm.context_toggle': {'data_path': 'space_data.overlay.show_sculpt_face_sets'}},
            'A ctrl alt')

    @classmethod
    def addPaintHotkeys(cls):
        # slot
        add('Image Paint', {'wm.call_panel': {'name': 'VIEW3D_PT_slots_projectpaint'}},
            'TAB ctrl')

        # selection mask
        for kmn, v in {
            'Vertex Paint': 'vertex',
            'Weight Paint': 'weight',
            'Image Paint': 'image'
        }.items():
            add(kmn, {'wm.context_toggle': {'data_path': v + '_paint_object.data.use_paint_mask'}},
                'ONE', disableOld='M')
            if kmn != 'Image Paint':
                add(kmn, {'wm.context_toggle': {'data_path': v + '_paint_object.data.use_paint_mask_vertex'}},
                    'TWO', disableOld='V')

        # size/strenth effect
        for kmn, v in {
            'Vertex Paint': 'tool_settings.vertex_paint.brush',
            'Image Paint': 'tool_settings.image_paint.brush',
        }.items():
            add(kmn, {'wm.radial_control': {
                'data_path_primary': v + '.size',
                'data_path_secondary': 'tool_settings.unified_paint_settings.size',
                'use_secondary': 'tool_settings.unified_paint_settings.use_unified_size',
                'rotation_path': v + '.texture_slot.angle',
                'color_path': v + '.cursor_color_add',
                'image_id': v,
                'fill_color_path': v + '.color',
                'fill_color_override_path': 'tool_settings.unified_paint_settings.color',
                'fill_color_override_test_path': 'tool_settings.unified_paint_settings.use_unified_color',
                'zoom_path': 'space_data.zoom' if kmn == 'Image Paint' else '',
                'secondary_tex': True if kmn == 'Image Paint' else False}},
                'S', disableOld='F')
            add(kmn, {'wm.radial_control': {
                'data_path_primary': v + '.strength',
                'data_path_secondary': 'tool_settings.unified_paint_settings.strength',
                'use_secondary': 'tool_settings.unified_paint_settings.use_unified_strength',
                'rotation_path': v + '.texture_slot.angle',
                'color_path': v + '.cursor_color_add',
                'image_id': v,
                'fill_color_path': v + '.color',
                'fill_color_override_path': 'tool_settings.unified_paint_settings.color',
                'fill_color_override_test_path': 'tool_settings.unified_paint_settings.use_unified_color',
                'zoom_path': '',
                'secondary_tex': True if kmn == 'Image Paint' else False}},
                'E', disableOld='F shift')

        # weight
        add('Weight Paint', {'wm.radial_control': {
            'data_path_primary': 'tool_settings.weight_paint.brush.weight',
            'data_path_secondary': 'tool_settings.unified_paint_settings.weight',
            'use_secondary': 'tool_settings.unified_paint_settings.use_unified_weight',
            'rotation_path': 'tool_settings.weight_paint.brush.texture_slot.angle',
            'color_path': 'tool_settings.weight_paint.brush.cursor_color_add',
            'image_id': 'tool_settings.weight_paint.brush',
            'secondary_tex': False}},
            'W alt', disableOld='F ctrl')

        # unified color
        add('Image Paint', {'wm.context_toggle': {'data_path': 'scene.tool_settings.unified_paint_settings.use_unified_color'}},
            'U alt')

        # stencil texture
        for kmn in ['Vertex Paint', 'Image Paint', 'Sculpt']:
            add(kmn, 'brush.stencil_control',
                'RIGHTMOUSE CLICK_DRAG', disableOld='RIGHTMOUSE', setKmiProps=lambda kmi: setModeProp(kmi, 'TRANSLATION'))
            disable(kmn, {'brush.stencil_control': {'mode': 0, 'texmode': 1}})
            add(kmn, 'brush.stencil_control',
                'RIGHTMOUSE ctrl CLICK_DRAG', disableOld='RIGHTMOUSE shift', setKmiProps=lambda kmi: setModeProp(kmi, 'SCALE'))
            disable(kmn, {'brush.stencil_control': {'mode': 1, 'texmode': 1}})
            add(kmn, 'brush.stencil_control',
                'RIGHTMOUSE shift CLICK_DRAG', disableOld='RIGHTMOUSE ctrl', setKmiProps=lambda kmi: setModeProp(kmi, 'ROTATION'))
            disable(kmn, {'brush.stencil_control': {'mode': 2, 'texmode': 1}})

        # blend
        for kmn, v in {
            'Vertex Paint': 'tool_settings.vertex_paint.',
            'Image Paint': 'tool_settings.image_paint.',
        }.items():
            add(kmn, {'wm.context_menu_enum': {'data_path': v + 'brush.blend'}},
                'D shift')
        add('Image Paint', {'wm.context_toggle_enum': {'data_path': 'tool_settings.image_paint.brush.blend'}},
            'LEFTMOUSE ctrl alt', setKmiProps=lambda kmi: setContextToggleValues(kmi, 'ERASE_ALPHA', 'MIX'))

        # color
        disable('Sculpt', 'sculpt.sample_color', 'S')
        for kmn in ['Vertex Paint', 'Image Paint']:
            add(kmn, 'paint.sample_color', 'LEFTMOUSE shift', disableOld='S')
            add(kmn, 'paint.sample_color', 'LEFTMOUSE shift DOUBLE_CLICK')
            add(kmn, 'paint.brush_colors_flip', 'X shift', disableOld='X')

        add('Weight Paint', {'wm.tool_set_by_id': {'name': 'builtin.sample_weight'}},
            'LEFTMOUSE shift DOUBLE_CLICK')

        add('User Interface', {'ui.reset_default_button': {'all': True}},
            'BACK_SPACE alt', disableOld='BACK_SPACE')
        add('User Interface', {'ui.reset_default_button': {'all': True}},
            'X alt')

        # weights
        add('Weight Paint', 'paint.weight_set', 'W shift', disableOld='K shift')
        add('Weight Paint', {'wm.call_menu_pie': {'name': 'VIEW3D_MT_wpaint_vgroup_lock_pie'}},
            'L', disableOld='K')

        # mask
        add('Image Paint', {'wm.tool_set_by_id': {'name': 'builtin_brush.Mask'}},
            'ONE shift')
        add('Image Paint', {'wm.call_panel': {'name': 'VIEW3D_PT_mask'}},
            'Q shift')
        add('Image Paint', {'wm.context_toggle': {'data_path': 'scene.tool_settings.image_paint.use_stencil_layer'}},
            'Q ctrl alt')

        # tools
        for kmn in ['Weight Paint', 'Vertex Paint', 'Image Paint']:
            add(kmn, {'wm.tool_set_by_id': {'name': 'builtin_brush.Draw'}},
                'D')
            add(kmn, {'wm.tool_set_by_id': {'name': 'builtin_brush.Smear'}},
                'S alt')
        for kmn in ['Weight Paint', 'Vertex Paint']:
            add(kmn, {'wm.tool_set_by_id': {'name': 'builtin_brush.Blur'}},
                'THREE shift')
            add(kmn, {'wm.tool_set_by_id': {'name': 'builtin_brush.Average'}},
                'V alt')
        add('Image Paint', {'wm.tool_set_by_id': {'name': 'builtin_brush.Soften'}},
            'THREE shift')
        add('Weight Paint', {'wm.tool_set_by_id': {'name': 'builtin.gradient'}},
            'G alt')
        add('Image Paint', {'wm.tool_set_by_id': {'name': 'builtin_brush.Fill'}},
            'F alt')
        add('Vertex Paint', 'paint.vertex_color_set',
            'F alt DOUBLE_CLICK')
        add('Image Paint', {'wm.tool_set_by_id': {'name': 'builtin_brush.Clone'}},
            'C alt')

    @classmethod
    def addImageAndUvHotkeys(cls):
        # image
        add('Image Generic', 'image.save_as',
            'S ctrl alt', disableOld='S shift alt')
        add('Window', 'image.save_all_modified',
            'S shift ctrl')
        add('Image Generic', 'image.reload',
            'R shift ctrl alt', disableOld='R alt')
        add('Image', {'image.invert': {'invert_r': True, 'invert_g': True, 'invert_b': True}},
            'I shift alt')
        add('Image', {'image.invert': {'invert_r': True}},
            'ONE shift alt')
        add('Image', {'image.invert': {'invert_g': True}},
            'TWO shift alt')
        add('Image', {'image.invert': {'invert_b': True}},
            'THREE shift alt')
        add('Image', {'image.invert': {'invert_a': True}},
            'FOUR shift alt')
        add('Image', 'image.resize', 'R shift alt')
        add('Image', {'image.flip': {'use_flip_x': True}},
            'H shift alt')
        add('Image', {'image.flip': {'use_flip_y': True}},
            'V shift alt')
        add('Image Generic', 'image.read_viewlayers',
            'Z X', disableOld='R ctrl')
        add('Image Generic', 'image.cycle_render_slot',
            'EQUAL', disableOld='J')
        add('Image Generic', {'image.cycle_render_slot': {'reverse': True}},
            'MINUS', disableOld='J alt')

        # view
        add('Image', {'image.view_all': {'fit_view': True}},
            'F DOUBLE_CLICK')

        # mode
        add('Image', {'wm.context_menu_enum': {'data_path': 'space_data.ui_mode'}},
            'TAB shift')
        add('UV Editor', {'wm.call_menu': {'name': 'IMAGE_MT_uvs_select_mode'}},
            'TAB shift')

        # uv
        add('UV Editor', {'wm.context_toggle': {'data_path': 'scene.tool_settings.use_uv_select_sync'}},
            'ACCENT_GRAVE')
        add('UV Editor', {'wm.context_menu_enum': {'data_path': 'scene.tool_settings.uv_sticky_select_mode'}},
            'ACCENT_GRAVE shift')
        add('UV Editor', {'wm.context_toggle': {'data_path': 'space_data.uv_editor.lock_bounds'}},
            'B alt')
        add('UV Editor', 'uv.seams_from_islands', 'U alt')

        add('UV Editor', {'wm.context_toggle': {'data_path': 'space_data.uv_editor.use_live_unwrap'}},
            'L ctrl')

        add('UV Editor', 'uv.follow_active_quads', 'F shift ctrl')
        add('UV Editor', 'uv.average_islands_scale', 'A shift ctrl')
        add('UV Editor', {'uv.pack_islands': {'rotate': False, 'margin': 0.01, 'pin': True}},
            'P shift ctrl')
        add('UV Editor', {'uv.minimize_stretch': {'iterations': 50}},
            'S shift alt')

        add('UV Editor', 'uv.pin', 'N', disableOld='P')
        add('UV Editor', {'uv.pin': {'clear': False}},
            'N DOUBLE_CLICK', disableOld='P alt')
        add('UV Editor', 'uv.select_pinned', 'N shift', disableOld='P shift')
        add('UV Editor', {'uv.select_box': {'pinned': True}},
            'B', disableOld='B ctrl')

        add('UV Editor', {'wm.call_menu': {'name': 'IMAGE_MT_uvs_align'}},
            'A shift', disableOld='W shift')
        add('UV Editor', 'uv.rip_move', 'V alt', disableOld='V')
        add('UV Editor', 'uv.stitch', 'D alt', disableOld='V alt')

        # view
        add('Image', 'image.view_cursor_center',
            'Q alt DOUBLE_CLICK', disableOld='C shift')

        # quick select
        add('UV Editor', 'uv.select_box',
            'LEFTMOUSE shift CLICK_DRAG')
        add('UV Editor', 'uv.select_box',
            'LEFTMOUSE shift CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('UV Editor', 'uv.select_box',
            'LEFTMOUSE shift ctrl CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))
        add('UV Editor', 'uv.select_circle',
            'LEFTMOUSE alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('UV Editor', 'uv.select_circle',
            'LEFTMOUSE ctrl alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))
        add('UV Editor', 'uv.select_lasso',
            'LEFTMOUSE shift alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('UV Editor', 'uv.select_lasso',
            'LEFTMOUSE shift ctrl alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))

        # tools
        add('UV Editor', 'uv.snap_cursor',
            'Q alt', setKmiProps=lambda kmi: setTargetProp(kmi, 'ORIGIN'))
        add('UV Editor', 'uv.snap_cursor',
            'Q shift ctrl', setKmiProps=lambda kmi: setTargetProp(kmi, 'SELECTED'))
        add('UV Editor', 'uv.snap_selected',
            'D shift ctrl', setKmiProps=lambda kmi: setTargetProp(kmi, 'CURSOR'))

        add('UV Editor', {'wm.tool_set_by_id': {'name': 'builtin_brush.Grab'}},
            'G alt')
        add('UV Editor', {'wm.tool_set_by_id': {'name': 'builtin_brush.Relax'}},
            'R alt')
        add('UV Editor', {'wm.tool_set_by_id': {'name': 'builtin_brush.Pinch'}},
            'C alt')

        # overlays
        add('Image', {'wm.context_toggle': {'data_path': 'space_data.uv_editor.show_texpaint'}},
            'U ctrl alt')
        add('UV Editor', {'wm.context_toggle': {'data_path': 'space_data.uv_editor.show_stretch'}},
            'A ctrl alt')

    @classmethod
    def addFileBrowserHotkeys(cls):
        add('File Browser', 'file.rename',
            'R ctrl', disableOld='F2')
        add('File Browser', 'file.rename',
            'RET alt')

        add('File Browser', {'file.directory_new': {'confirm': False}},
            'M shift ctrl', disableOld='I')

        add('File Browser', 'file.next',
            'LEFT_BRACKET', disableOld='BACK_SPACE')
        add('File Browser', 'file.previous',
            'RIGHT_BRACKET', disableOld='BACK_SPACE shift')
        add('File Browser', 'file.parent',
            'BACK_SLASH', disableOld='P')

        for k, v in {
            'ONE': 'LIST_VERTICAL',
            'TWO': 'LIST_HORIZONTAL',
            'THREE': 'THUMBNAIL'
        }.items():
            add('File Browser', {'wm.context_set_enum': {'data_path': 'space_data.params.display_type'}},
                k, setKmiProps=lambda kmi: setValueProp(kmi, v))

    @classmethod
    def addShaderHotkeys(cls):
        # mode
        add('Node Editor', {'wm.context_menu_enum': {'data_path': 'space_data.shader_type'}},
            'TAB shift')

        # slot
        add('Node Editor', {'wm.call_panel': {'name': 'NODE_PT_material_slots'}},
            'TAB ctrl')

        # node
        disable('Node Editor', 'node.translate_attach', 'G')
        add('Node Editor', {'node.duplicate_move_keep_inputs': {'keep_inputs': True}},
            'D shift ctrl', disableOld='D shift ctrl')

        add('Node Editor', 'node.hide_socket_toggle',
            'U', disableOld='H ctrl')
        add('Node Editor', 'node.hide_socket_toggle',
            'T')
        add('Node Editor', 'node.options_toggle',
            'N')
        add('Node Editor', 'node.options_toggle',
            'T RELEASE')

        add('Node Editor', 'node.delete',
            'X ctrl', disableOld='X')
        add('Node Editor', 'node.delete',
            'BACK_SPACE', disableOld='DEL')
        add('Node Editor', 'node.delete_reconnect',
            'X', disableOld='X ctrl')
        disable('Node Editor', 'node.delete_reconnect', 'DEL ctrl')

        disable('Node Editor', 'node.move_detach_links_release',
                'RIGHTMOUSE alt CLICK_DRAG')

        add('Node Editor', {'node.link_make': {'replace': False}},
            'C', disableOld='F')
        add('Node Editor', {'node.link_make': {'replace': True}},
            'C DOUBLE_CLICK', disableOld='F shift')

        # quick select
        add('Node Editor', 'node.select_box',
            'LEFTMOUSE shift CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('Node Editor', 'node.select_box',
            'LEFTMOUSE shift ctrl CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))
        add('Node Editor', 'node.select_lasso',
            'LEFTMOUSE shift alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'ADD'))
        add('Node Editor', 'node.select_lasso',
            'LEFTMOUSE shift ctrl alt CLICK_DRAG', setKmiProps=lambda kmi: setModeProp(kmi, 'SUB'))

        # select
        disable('Node Editor', 'node.select', 'LEFTMOUSE shift')
        add('Node Editor', 'node.select_linked_to',
            'EQUAL shift', disableOld='L shift')
        add('Node Editor', 'node.select_linked_from',
            'MINUS shift', disableOld='L')
        add('Node Editor', {'node.select_same_type_step': {'prev': False}},
            'EQUAL alt', disableOld='RIGHT_BRACKET shift')
        add('Node Editor', {'node.select_same_type_step': {'prev': True}},
            'MINUS alt', disableOld='LEFT_BRACKET shift')

        # links
        add('Node Editor', 'node.add_reroute',
            'LEFTMOUSE ctrl CLICK_DRAG', disableOld='RIGHTMOUSE shift CLICK_DRAG')
        add('Node Editor', 'node.links_cut',
            'RIGHTMOUSE alt CLICK_DRAG', disableOld='RIGHTMOUSE ctrl CLICK_DRAG')

        # frame (block)
        add('Node Editor', 'node.join', 'B', disableOld='J ctrl')
        add('Node Editor', 'node.parent_set', 'B ctrl', disableOld='P ctrl')
        add('Node Editor', 'node.detach', 'B alt', disableOld='P alt')

        # group
        add('Node Editor', 'node.group_separate',
            'G alt', disableOld='P')
        add('Node Editor', {'node.group_edit': {'exit': False}},
            'E ctrl', disableOld='TAB')
        add('Node Editor', {'node.group_edit': {'exit': False}},
            'RET')
        add('Node Editor', {'node.group_edit': {'exit': True}},
            'ESC')
        add('Node Editor', {'node.select': {'deselect': True}},
            'ESC RELEASE')

        # add
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'S shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeBsdfPrincipled'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'S shift M', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeMixShader'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'ONE shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeValue'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'THREE shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeRGB'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'C shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeVertexColor'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'T shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeTexImage'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'T shift N', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeTexNoise'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'T shift V', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeTexVoronoi'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'U shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeHueSaturation'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'K shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeRGBCurve'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'M shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeMix'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'R shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeValToRGB'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'V shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeMapping'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'N shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeNormalMap'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'B shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeBump'))
        add('Node Editor', {'node.add_node': {'use_transform': True}},
            'E shift DOUBLE_CLICK', setKmiProps=lambda kmi: setTypeProp(kmi, 'ShaderNodeTexEnvironment'))

        # backimage
        disable('Node Editor', 'node.backimage_sample', 'RIGHTMOUSE alt')
        add('Node Editor', {'node.backimage_zoom': {'factor': 0.8}},
            'EQUAL', disableOld='V')
        add('Node Editor', {'node.backimage_zoom': {'factor': 1.2}},
            'MINUS', disableOld='V alt')

        # node wrangler {b}
        addAddonKeymapItem('Node Editor', {'node.nw_preview_node': {'run_in_geometry_nodes': False}},
                           'RIGHTMOUSE ctrl CLICK', disableOld='LEFTMOUSE shift ctrl')
        addAddonKeymapItem('Node Editor', {'node.nw_preview_node': {'run_in_geometry_nodes': True}},
                           'RIGHTMOUSE shift ctrl CLICK', disableOld='LEFTMOUSE shift alt')
        addAddonKeymapItem('Node Editor', 'node.nw_link_out',
                           'V DOUBLE_CLICK', disableOld='O')
        addAddonKeymapItem('Node Editor', 'node.nw_link_out',
                           'RET shift')
        addAddonKeymapItem('Node Editor', {'wm.call_menu': {'name': 'NODE_MT_nw_switch_node_type_menu'}},
                           'S alt', disableOld='S shift')
        addAddonKeymapItem('Node Editor', {'node.nw_lazy_connect': {'with_menu': False}},
                           'RIGHTMOUSE shift CLICK_DRAG', disableOld='RIGHTMOUSE alt')
        addAddonKeymapItem('Node Editor', {'node.nw_lazy_connect': {'with_menu': True}},
                           'RIGHTMOUSE ctrl CLICK_DRAG', disableOld='RIGHTMOUSE shift alt')
        addAddonKeymapItem('Node Editor', 'node.nw_lazy_mix',
                           'RIGHTMOUSE shift ctrl CLICK_DRAG', disableOld='RIGHTMOUSE shift ctrl')
        addAddonKeymapItem('Node Editor', {'wm.call_menu': {'name': 'NODE_MT_nw_link_active_to_selected_menu'}},
                           'C shift ctrl', disableOld='BACK_SLASH')
        addAddonKeymapItem('Node Editor', {'node.nw_link_active_to_selected': {'replace': True, 'use_outputs_names': False, 'use_node_names': False}},
                           'C alt', disableOld='K shift')
        addAddonKeymapItem('Node Editor', {'node.nw_link_active_to_selected': {'replace': False, 'use_outputs_names': False, 'use_node_names': False}},
                           'C alt', disableOld='K')
        addAddonKeymapItem('Node Editor', 'node.nw_detach_outputs',
                           'D alt', disableOld='D shift alt')
        addAddonKeymapItem('Node Editor', 'node.nw_del_unused',
                           'X shift alt', disableOld='X alt')
        addAddonKeymapItem('Node Editor', 'node.nw_align_nodes',
                           'A shift ctrl', disableOld='EQUAL shift')
        addAddonKeymapItem('Node Editor', 'node.nw_reload_images',
                           'R shift ctrl alt', disableOld='R alt')
        addAddonKeymapItem('Node Editor', 'node.nw_reset_nodes',
                           'R alt', disableOld='BACK_SPACE')
        addAddonKeymapItem('Node Editor', 'node.nw_bg_reset',
                           'Z alt', disableOld='Z')
        addAddonKeymapItem('Node Editor', {'wm.call_menu': {'name': 'NODE_MT_nw_copy_node_properties_menu'}},
                           'C shift alt', disableOld='C shift')
        addAddonKeymapItem('Node Editor', 'node.nw_frame_selected',
                           'B shift ctrl', disableOld='P shift')
        addAddonKeymapItem('Node Editor', 'node.nw_copy_label',
                           'L', disableOld='V shift')
        addAddonKeymapItem('Node Editor', 'node.nw_clear_label',
                           'L alt', disableOld='L alt')
        addAddonKeymapItem('Node Editor', 'node.nw_modify_labels',
                           'L shift ctrl', disableOld='L shift alt')


# KMI PROPS SETTERS


def setTypeProp(kmi, *args): kmi.properties.type = args[0]


def setFilterTypeProp(kmi, *args): kmi.properties.filter_type = args[0]


def setModeProp(kmi, *args): kmi.properties.mode = args[0]


def setDirectionProp(kmi, *args): kmi.properties.direction = args[0]


def setActionProp(kmi, *args): kmi.properties.action = args[0]


def setTargetProp(kmi, *args): kmi.properties.target = args[0]


def setAffectProp(kmi, *args): kmi.properties.affect = args[0]


def setSpaceTypeProp(kmi, *args): kmi.properties.space_type = args[0]


def setDelimitProp(kmi, *args): kmi.properties.delimit = args[0]


def setValueProp(kmi, *args): kmi.properties.value = args[0]


def setCloseSplineProp(
    kmi, *args): kmi.properties.close_spline_method = args[0]


def setSculptToolProp(
    kmi, *args): kmi.properties.sculpt_tool = args[0]  # ['DRAW', 'DRAW_SHARP', 'CLAY', 'CLAY_STRIPS', 'CLAY_THUMB', 'LAYER', 'INFLATE', 'BLOB', 'CREASE', 'SMOOTH', 'FLATTEN', 'FILL', 'SCRAPE', 'MULTIPLANE_SCRAPE', 'PINCH', 'GRAB', 'ELASTIC_DEFORM', 'SNAKE_HOOK', 'THUMB', 'POSE', 'NUDGE', 'ROTATE', 'TOPOLOGY', 'CLOTH', 'SIMPLIFY', 'MASK', 'PAINT', 'SMEAR', 'DRAW_FACE_SETS'] \


def setContextToggleValues(kmi, v1, v2):
    kmi.properties.value_1 = v1
    kmi.properties.value_2 = v2
