# SPDX-License-Identifier: GPL-2.0-or-later

# For documentation on tool definitions: see "bl_ui.space_toolsystem_common.ToolDef"
# where there are comments for each field and their use.

# For now group all tools together
# we may want to move these into per space-type files.
#
# For now keep this in a single file since it's an area that may change,
# so avoid making changes all over the place.

import bpy
from bpy.types import Panel

from bl_ui.space_toolsystem_common import (
    ToolSelectPanelHelper,
    ToolDef,
)

from bpy.app.translations import pgettext_tip as tip_


def kmi_to_string_or_none(kmi):
    return kmi.to_string() if kmi else "<none>"


def generate_from_enum_ex(
        _context, *,
        idname_prefix,
        icon_prefix,
        type,
        attr,
        cursor='DEFAULT',
        tooldef_keywords=None,
        icon_map=None,
        use_separators=True,
):
    if tooldef_keywords is None:
        tooldef_keywords = {}

    tool_defs = []

    enum_items = getattr(
        type.bl_rna.properties[attr],
        "enum_items_static_ui" if use_separators else
        "enum_items_static",
    )

    for enum in enum_items:
        if use_separators:
            if not (name := enum.name):
                # Empty string for a UI Separator.
                tool_defs.append(None)
                continue
            if not (idname := enum.identifier):
                # This is a heading, there is no purpose in showing headings here.
                continue
        else:
            name = enum.name
            idname = enum.identifier

        icon = icon_prefix + idname.lower()
        if icon_map is not None:
            icon = icon_map.get(icon, icon)

        tool_defs.append(
            ToolDef.from_dict(
                dict(
                    idname=idname_prefix + name,
                    label=name,
                    description=enum.description,
                    icon=icon,
                    cursor=cursor,
                    data_block=idname,
                    **tooldef_keywords,
                ),
            ),
        )
    return tuple(tool_defs)


# Use for shared widget data.
class _template_widget:
    class VIEW3D_GGT_xform_extrude:
        @staticmethod
        def draw_settings(_context, layout, tool):
            props = tool.gizmo_group_properties("VIEW3D_GGT_xform_extrude")
            layout.prop(props, "axis_type", expand=True)

    class VIEW3D_GGT_xform_gizmo:
        @staticmethod
        def draw_settings_with_index(context, layout, index):
            scene = context.scene
            orient_slot = scene.transform_orientation_slots[index]
            layout.prop(orient_slot, "type")


class _defs_view3d_generic:
    @ToolDef.from_fn
    def cursor():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("view3d.cursor3d")
            layout.prop(props, "use_depth")
            layout.prop(props, "orientation")
        return dict(
            idname="builtin.cursor",
            label="Cursor",
            description=(
                "Set the cursor location, drag to transform"
            ),
            icon="ops.generic.cursor",
            keymap="3D View Tool: Cursor",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def cursor_click():
        return dict(
            idname="builtin.none",
            label="None",
            icon="ops.generic.cursor",
            keymap=(),
        )

    @ToolDef.from_fn
    def ruler():
        def description(_context, _item, km):
            if km is not None:
                kmi_add = km.keymap_items.find_from_operator(
                    "view3d.ruler_add")
                kmi_remove = km.keymap_items.find_from_operator(
                    "view3d.ruler_remove")
            else:
                kmi_add = None
                kmi_remove = None
            return tip_(
                "Measure distance and angles.\n"
                "\u2022 %s anywhere for new measurement.\n"
                "\u2022 Drag ruler segment to measure an angle.\n"
                "\u2022 %s to remove the active ruler.\n"
                "\u2022 Ctrl while dragging to snap.\n"
                "\u2022 Shift while dragging to measure surface thickness"
            ) % (
                kmi_to_string_or_none(kmi_add),
                kmi_to_string_or_none(kmi_remove),
            )
        return dict(
            idname="builtin.measure",
            label="Measure",
            description=description,
            icon="ops.view3d.ruler",
            widget="VIEW3D_GGT_ruler",
            keymap="3D View Tool: Measure",
        )


class _defs_annotate:

    def draw_settings_common(context, layout, tool):
        gpd = context.annotation_data
        region_type = context.region.type

        if gpd is not None:
            if gpd.layers.active_note is not None:
                text = gpd.layers.active_note
                maxw = 25
                if len(text) > maxw:
                    text = text[:maxw - 5] + '..' + text[-3:]
            else:
                text = ""

            gpl = context.active_annotation_layer
            if gpl is not None:
                layout.label(text="Annotation:")
                if context.space_data.type in {'VIEW_3D', 'SEQUENCE_EDITOR'}:
                    if region_type == 'TOOL_HEADER':
                        sub = layout.split(align=True, factor=0.5)
                        sub.ui_units_x = 6.5
                        sub.prop(gpl, "color", text="")
                    else:
                        sub = layout.row(align=True)
                        sub.prop(gpl, "color", text="")
                    sub.popover(
                        panel="TOPBAR_PT_annotation_layers",
                        text=text,
                    )
                else:
                    layout.prop(gpl, "color", text="")

        space_type = tool.space_type
        tool_settings = context.tool_settings

        if space_type == 'VIEW_3D':
            row = layout.row(align=True)
            row.prop(tool_settings,
                     "annotation_stroke_placement_view3d", text="Placement")
            if tool_settings.gpencil_stroke_placement_view3d == 'CURSOR':
                row.prop(tool_settings.gpencil_sculpt, "lockaxis")
            elif tool_settings.gpencil_stroke_placement_view3d in {'SURFACE', 'STROKE'}:
                row.prop(tool_settings, "use_gpencil_stroke_endpoints")

        elif space_type in {'IMAGE_EDITOR', 'NODE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR'}:
            row = layout.row(align=True)
            row.prop(tool_settings,
                     "annotation_stroke_placement_view2d", text="Placement")

        if tool.idname == "builtin.annotate_line":
            props = tool.operator_properties("gpencil.annotate")
            if region_type == 'TOOL_HEADER':
                row = layout.row()
                row.ui_units_x = 15
                row.prop(props, "arrowstyle_start", text="Start")
                row.separator()
                row.prop(props, "arrowstyle_end", text="End")
            else:
                col = layout.row().column(align=True)
                col.prop(props, "arrowstyle_start", text="Style Start")
                col.prop(props, "arrowstyle_end", text="End")
        elif tool.idname == "builtin.annotate":
            props = tool.operator_properties("gpencil.annotate")
            if region_type == 'TOOL_HEADER':
                row = layout.row()
                row.prop(props, "use_stabilizer", text="Stabilize Stroke")
                subrow = layout.row(align=False)
                subrow.active = props.use_stabilizer
                subrow.prop(props, "stabilizer_radius",
                            text="Radius", slider=True)
                subrow.prop(props, "stabilizer_factor",
                            text="Factor", slider=True)
            else:
                layout.prop(props, "use_stabilizer", text="Stabilize Stroke")
                col = layout.column(align=False)
                col.active = props.use_stabilizer
                col.prop(props, "stabilizer_radius",
                         text="Radius", slider=True)
                col.prop(props, "stabilizer_factor",
                         text="Factor", slider=True)

    @ToolDef.from_fn.with_args(draw_settings=draw_settings_common)
    def scribble(*, draw_settings):
        return dict(
            idname="builtin.annotate",
            label="Annotate",
            icon="ops.gpencil.draw",
            cursor='PAINT_BRUSH',
            keymap="Generic Tool: Annotate",
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )

    @ToolDef.from_fn.with_args(draw_settings=draw_settings_common)
    def line(*, draw_settings):
        return dict(
            idname="builtin.annotate_line",
            label="Annotate Line",
            icon="ops.gpencil.draw.line",
            cursor='PAINT_BRUSH',
            keymap="Generic Tool: Annotate Line",
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )

    @ToolDef.from_fn.with_args(draw_settings=draw_settings_common)
    def poly(*, draw_settings):
        return dict(
            idname="builtin.annotate_polygon",
            label="Annotate Polygon",
            icon="ops.gpencil.draw.poly",
            cursor='PAINT_BRUSH',
            keymap="Generic Tool: Annotate Polygon",
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )

    @ToolDef.from_fn
    def eraser():
        def draw_settings(context, layout, _tool):
            # TODO: Move this setting to tool_settings
            prefs = context.preferences
            layout.prop(prefs.edit, "grease_pencil_eraser_radius",
                        text="Radius")
        return dict(
            idname="builtin.annotate_eraser",
            label="Annotate Eraser",
            icon="ops.gpencil.draw.eraser",
            cursor='ERASER',
            keymap="Generic Tool: Annotate Eraser",
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )


class _defs_transform:

    def draw_transform_sculpt_tool_settings(context, layout):
        if context.mode != 'SCULPT':
            return
        layout.prop(context.tool_settings.sculpt, "transform_mode")

    @ToolDef.from_fn
    def translate():
        def draw_settings(context, layout, _tool):
            _defs_transform.draw_transform_sculpt_tool_settings(
                context, layout)
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 1)
        return dict(
            idname="builtin.move",
            label="Move",
            # cursor='SCROLL_XY',
            icon="ops.transform.translate",
            widget="VIEW3D_GGT_xform_gizmo",
            operator="transform.translate",
            keymap="3D View Tool: Move",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def rotate():
        def draw_settings(context, layout, _tool):
            _defs_transform.draw_transform_sculpt_tool_settings(
                context, layout)
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 2)
        return dict(
            idname="builtin.rotate",
            label="Rotate",
            # cursor='SCROLL_XY',
            icon="ops.transform.rotate",
            widget="VIEW3D_GGT_xform_gizmo",
            operator="transform.rotate",
            keymap="3D View Tool: Rotate",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def scale():
        def draw_settings(context, layout, _tool):
            _defs_transform.draw_transform_sculpt_tool_settings(
                context, layout)
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 3)
        return dict(
            idname="builtin.scale",
            label="Scale",
            # cursor='SCROLL_XY',
            icon="ops.transform.resize",
            widget="VIEW3D_GGT_xform_gizmo",
            operator="transform.resize",
            keymap="3D View Tool: Scale",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def scale_cage():
        def draw_settings(context, layout, _tool):
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 3)
        return dict(
            idname="builtin.scale_cage",
            label="Scale Cage",
            icon="ops.transform.resize.cage",
            widget="VIEW3D_GGT_xform_cage",
            operator="transform.resize",
            keymap="3D View Tool: Scale",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def shear():
        def draw_settings(context, layout, _tool):
            # props = tool.operator_properties("transform.shear")
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 2)
        return dict(
            idname="builtin.shear",
            label="Shear",
            icon="ops.transform.shear",
            widget="VIEW3D_GGT_xform_shear",
            keymap="3D View Tool: Shear",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def transform():
        def draw_settings(context, layout, tool):
            if layout.use_property_split:
                layout.label(text="Gizmos:")

            show_drag = True
            tool_settings = context.tool_settings
            if tool_settings.workspace_tool_type == 'FALLBACK':
                show_drag = False

            if show_drag:
                props = tool.gizmo_group_properties("VIEW3D_GGT_xform_gizmo")
                layout.prop(props, "drag_action")

            _defs_transform.draw_transform_sculpt_tool_settings(
                context, layout)
            _template_widget.VIEW3D_GGT_xform_gizmo.draw_settings_with_index(
                context, layout, 1)

        return dict(
            idname="builtin.transform",
            label="Transform",
            description=(
                "Supports any combination of grab, rotate, and scale at once"
            ),
            icon="ops.transform.transform",
            widget="VIEW3D_GGT_xform_gizmo",
            keymap="3D View Tool: Transform",
            draw_settings=draw_settings,
        )


class _defs_view3d_select:

    @ToolDef.from_fn
    def select():
        return dict(
            idname="builtin.select",
            label="Tweak",
            icon="ops.generic.select",
            widget=None,
            keymap="3D View Tool: Tweak",
        )

    @ToolDef.from_fn
    def box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("view3d.select_box")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_box",
            label="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap="3D View Tool: Select Box",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("view3d.select_lasso")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_lasso",
            label="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap="3D View Tool: Select Lasso",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("view3d.select_circle")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            layout.prop(props, "radius")

        def draw_cursor(_context, tool, xy):
            from gpu_extras.presets import draw_circle_2d
            props = tool.operator_properties("view3d.select_circle")
            radius = props.radius
            draw_circle_2d(xy, (1.0,) * 4, radius, segments=32)

        return dict(
            idname="builtin.select_circle",
            label="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap="3D View Tool: Select Circle",
            draw_settings=draw_settings,
            draw_cursor=draw_cursor,
        )


class _defs_view3d_add:

    @staticmethod
    def description_interactive_add(context, _item, _km, *, prefix):
        km = context.window_manager.keyconfigs.user.keymaps["View3D Placement Modal"]

        def keymap_item_from_propvalue(propvalue):
            for item in km.keymap_items:
                if item.propvalue == propvalue:
                    return item
            return None

        if km is not None:
            kmi_snap = keymap_item_from_propvalue('SNAP_ON')
            kmi_center = keymap_item_from_propvalue('PIVOT_CENTER_ON')
            kmi_fixed_aspect = keymap_item_from_propvalue('FIXED_ASPECT_ON')
        else:
            kmi_snap = None
            kmi_center = None
            kmi_fixed_aspect = None
        return tip_(
            "%s\n"
            "\u2022 %s toggles snap while dragging.\n"
            "\u2022 %s toggles dragging from the center.\n"
            "\u2022 %s toggles fixed aspect"
        ) % (
            prefix,
            kmi_to_string_or_none(kmi_snap),
            kmi_to_string_or_none(kmi_center),
            kmi_to_string_or_none(kmi_fixed_aspect),
        )

    # Layout tweaks here would be good to avoid,
    # this shows limits in layout engine, as buttons are using a lot of space.
    @staticmethod
    def draw_settings_interactive_add(layout, tool_settings, tool, extra):
        show_extra = False
        if not extra:
            row = layout.row()
            row.label(text="Depth:")
            row = layout.row()
            row.prop(tool_settings, "plane_depth", text="")
            row = layout.row()
            row.label(text="Orientation:")
            row = layout.row()
            row.prop(tool_settings, "plane_orientation", text="")
            row = layout.row()
            row.prop(tool_settings, "snap_elements_tool")

            region_is_header = bpy.context.region.type == 'TOOL_HEADER'
            if region_is_header:
                # Don't draw the "extra" popover here as we might have other settings & this should be last.
                show_extra = True
            else:
                extra = True

        if extra:
            props = tool.operator_properties("view3d.interactive_add")
            layout.use_property_split = True
            layout.row().prop(tool_settings, "plane_axis", expand=True)
            layout.row().prop(tool_settings, "plane_axis_auto")

            layout.label(text="Base")
            layout.row().prop(props, "plane_origin_base", expand=True)
            layout.row().prop(props, "plane_aspect_base", expand=True)
            layout.label(text="Height")
            layout.row().prop(props, "plane_origin_depth", expand=True)
            layout.row().prop(props, "plane_aspect_depth", expand=True)
        return show_extra

    @ToolDef.from_fn
    def cube_add():
        def draw_settings(context, layout, tool, *, extra=False):
            show_extra = _defs_view3d_add.draw_settings_interactive_add(
                layout, context.tool_settings, tool, extra)
            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")

        return dict(
            idname="builtin.primitive_cube_add",
            label="Add Cube",
            icon="ops.mesh.primitive_cube_add_gizmo",
            description=lambda *args: _defs_view3d_add.description_interactive_add(
                *args, prefix=tip_("Add cube to mesh interactively"),
            ),
            widget="VIEW3D_GGT_placement",
            keymap="3D View Tool: Object, Add Primitive",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def cone_add():
        def draw_settings(context, layout, tool, *, extra=False):
            show_extra = _defs_view3d_add.draw_settings_interactive_add(
                layout, context.tool_settings, tool, extra)
            if extra:
                return

            props = tool.operator_properties("mesh.primitive_cone_add")
            layout.prop(props, "vertices")
            layout.prop(props, "end_fill_type")

            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")

        return dict(
            idname="builtin.primitive_cone_add",
            label="Add Cone",
            icon="ops.mesh.primitive_cone_add_gizmo",
            description=lambda *args: _defs_view3d_add.description_interactive_add(
                *args, prefix=tip_("Add cone to mesh interactively"),
            ),
            widget="VIEW3D_GGT_placement",
            keymap="3D View Tool: Object, Add Primitive",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def cylinder_add():
        def draw_settings(context, layout, tool, *, extra=False):
            show_extra = _defs_view3d_add.draw_settings_interactive_add(
                layout, context.tool_settings, tool, extra)
            if extra:
                return

            props = tool.operator_properties("mesh.primitive_cylinder_add")
            layout.prop(props, "vertices")
            layout.prop(props, "end_fill_type")

            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
        return dict(
            idname="builtin.primitive_cylinder_add",
            label="Add Cylinder",
            icon="ops.mesh.primitive_cylinder_add_gizmo",
            description=lambda *args: _defs_view3d_add.description_interactive_add(
                *args, prefix=tip_("Add cylinder to mesh interactively"),
            ),
            widget="VIEW3D_GGT_placement",
            keymap="3D View Tool: Object, Add Primitive",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def uv_sphere_add():
        def draw_settings(context, layout, tool, *, extra=False):
            show_extra = _defs_view3d_add.draw_settings_interactive_add(
                layout, context.tool_settings, tool, extra)
            if extra:
                return

            props = tool.operator_properties("mesh.primitive_uv_sphere_add")
            layout.prop(props, "segments")
            layout.prop(props, "ring_count")

            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
        return dict(
            idname="builtin.primitive_uv_sphere_add",
            label="Add UV Sphere",
            icon="ops.mesh.primitive_sphere_add_gizmo",
            description=lambda *args: _defs_view3d_add.description_interactive_add(
                *args, prefix=tip_("Add sphere to mesh interactively"),
            ),
            widget="VIEW3D_GGT_placement",
            keymap="3D View Tool: Object, Add Primitive",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def ico_sphere_add():
        def draw_settings(context, layout, tool, *, extra=False):
            show_extra = _defs_view3d_add.draw_settings_interactive_add(
                layout, context.tool_settings, tool, extra)
            if extra:
                return

            props = tool.operator_properties("mesh.primitive_ico_sphere_add")
            layout.prop(props, "subdivisions")

            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
        return dict(
            idname="builtin.primitive_ico_sphere_add",
            label="Add Ico Sphere",
            icon="ops.mesh.primitive_sphere_add_gizmo",
            description=lambda *args: _defs_view3d_add.description_interactive_add(
                *args, prefix=tip_("Add sphere to mesh interactively"),
            ),
            widget="VIEW3D_GGT_placement",
            keymap="3D View Tool: Object, Add Primitive",
            draw_settings=draw_settings,
        )


# -----------------------------------------------------------------------------
# Object Modes (named based on context.mode)

class _defs_edit_armature:

    @ToolDef.from_fn
    def roll():
        return dict(
            idname="builtin.roll",
            label="Roll",
            icon="ops.armature.bone.roll",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def bone_envelope():
        return dict(
            idname="builtin.bone_envelope",
            label="Bone Envelope",
            icon="ops.transform.bone_envelope",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def bone_size():
        return dict(
            idname="builtin.bone_size",
            label="Bone Size",
            icon="ops.transform.bone_size",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            idname="builtin.extrude",
            label="Extrude",
            icon="ops.armature.extrude_move",
            widget="VIEW3D_GGT_xform_extrude",
            keymap=(),
            draw_settings=_template_widget.VIEW3D_GGT_xform_extrude.draw_settings,
        )

    @ToolDef.from_fn
    def extrude_cursor():
        return dict(
            idname="builtin.extrude_to_cursor",
            label="Extrude to Cursor",
            cursor='CROSSHAIR',
            icon="ops.armature.extrude_cursor",
            widget=None,
            keymap=(),
        )


class _defs_edit_mesh:

    @ToolDef.from_fn
    def rip_region():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.rip_move")
            props_macro = props.MESH_OT_rip
            layout.prop(props_macro, "use_fill")

        return dict(
            idname="builtin.rip_region",
            label="Rip Region",
            icon="ops.mesh.rip",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def rip_edge():
        return dict(
            idname="builtin.rip_edge",
            label="Rip Edge",
            icon="ops.mesh.rip_edge",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def poly_build():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties(
                "mesh.polybuild_face_at_cursor_move")
            props_macro = props.MESH_OT_polybuild_face_at_cursor
            layout.prop(props_macro, "create_quads")
        return dict(
            idname="builtin.poly_build",
            label="Poly Build",
            icon="ops.mesh.polybuild_hover",
            widget="VIEW3D_GGT_mesh_preselect_elem",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def edge_slide():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("transform.edge_slide")
            layout.prop(props, "correct_uv")

        return dict(
            idname="builtin.edge_slide",
            label="Edge Slide",
            icon="ops.transform.edge_slide",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def vert_slide():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("transform.vert_slide")
            layout.prop(props, "correct_uv")

        return dict(
            idname="builtin.vertex_slide",
            label="Vertex Slide",
            icon="ops.transform.vert_slide",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def spin():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.spin")
            layout.prop(props, "steps")
            props = tool.gizmo_group_properties("MESH_GGT_spin")
            layout.prop(props, "axis")

        return dict(
            idname="builtin.spin",
            label="Spin",
            icon="ops.mesh.spin",
            widget="MESH_GGT_spin",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def spin_duplicate():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.spin")
            layout.prop(props, "steps")
            props = tool.gizmo_group_properties("MESH_GGT_spin")
            layout.prop(props, "axis")

        return dict(
            idname="builtin.spin_duplicates",
            label="Spin Duplicates",
            icon="ops.mesh.spin.duplicate",
            widget="MESH_GGT_spin",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def inset():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.inset")
            layout.prop(props, "use_outset")
            layout.prop(props, "use_individual")
            layout.prop(props, "use_even_offset")
            layout.prop(props, "use_relative_offset")

        return dict(
            idname="builtin.inset_faces",
            label="Inset Faces",
            icon="ops.mesh.inset",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            widget_properties=[
                ("radius", 75.0),
                ("backdrop_fill_alpha", 0.0),
            ],
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def bevel():
        def draw_settings(context, layout, tool, *, extra=False):
            props = tool.operator_properties("mesh.bevel")

            region_is_header = context.region.type == 'TOOL_HEADER'

            edge_bevel = props.affect == 'EDGES'

            if not extra:
                if region_is_header:
                    layout.prop(props, "offset_type", text="")
                else:
                    layout.row().prop(props, "affect", expand=True)
                    layout.separator()
                    layout.prop(props, "offset_type")

                layout.prop(props, "segments")

                if region_is_header:
                    layout.prop(props, "affect", text="")

                layout.prop(props, "profile", text="Shape", slider=True)

                if region_is_header:
                    layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
                else:
                    extra = True

            if extra:
                layout.use_property_split = True
                layout.use_property_decorate = False

                layout.prop(props, "material")

                col = layout.column()
                col.prop(props, "harden_normals")
                col.prop(props, "clamp_overlap")
                col.prop(props, "loop_slide")

                col = layout.column(heading="Mark")
                col.active = edge_bevel
                col.prop(props, "mark_seam", text="Seam")
                col.prop(props, "mark_sharp", text="Sharp")

                col = layout.column()
                col.active = edge_bevel
                col.prop(props, "miter_outer", text="Miter Outer")
                col.prop(props, "miter_inner", text="Inner")
                if props.miter_inner == 'ARC':
                    col.prop(props, "spread")

                layout.separator()

                col = layout.column()
                col.active = edge_bevel
                col.prop(props, "vmesh_method", text="Intersections")

                layout.prop(props, "face_strength_mode", text="Face Strength")

                layout.prop(props, "profile_type")

                if props.profile_type == 'CUSTOM':
                    tool_settings = context.tool_settings
                    layout.template_curveprofile(
                        tool_settings, "custom_bevel_profile_preset")

        return dict(
            idname="builtin.bevel",
            label="Bevel",
            icon="ops.mesh.bevel",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            idname="builtin.extrude_region",
            label="Extrude Region",
            # The operator description isn't useful in this case, give our own.
            description=(
                "Extrude freely or along an axis"
            ),
            icon="ops.mesh.extrude_region_move",
            widget="VIEW3D_GGT_xform_extrude",
            # Important to use same operator as 'E' key.
            operator="view3d.edit_mesh_extrude_move_normal",
            keymap=(),
            draw_settings=_template_widget.VIEW3D_GGT_xform_extrude.draw_settings,
        )

    @ToolDef.from_fn
    def extrude_manifold():
        return dict(
            idname="builtin.extrude_manifold",
            label="Extrude Manifold",
            description=(
                "Extrude, dissolves edges whose faces form a flat surface and intersect new edges"
            ),
            icon="ops.mesh.extrude_manifold",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
        )

    @ToolDef.from_fn
    def extrude_normals():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties(
                "mesh.extrude_region_shrink_fatten")
            props_macro = props.TRANSFORM_OT_shrink_fatten
            layout.prop(props_macro, "use_even_offset")
        return dict(
            idname="builtin.extrude_along_normals",
            label="Extrude Along Normals",
            icon="ops.mesh.extrude_region_shrink_fatten",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            operator="mesh.extrude_region_shrink_fatten",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude_individual():
        return dict(
            idname="builtin.extrude_individual",
            label="Extrude Individual",
            icon="ops.mesh.extrude_faces_move",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
        )

    @ToolDef.from_fn
    def extrude_cursor():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.dupli_extrude_cursor")
            layout.prop(props, "rotate_source")

        return dict(
            idname="builtin.extrude_to_cursor",
            label="Extrude to Cursor",
            cursor='CROSSHAIR',
            icon="ops.mesh.dupli_extrude_cursor",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def loopcut_slide():

        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.loopcut_slide")
            props_macro = props.MESH_OT_loopcut
            layout.prop(props_macro, "number_cuts")
            props_macro = props.TRANSFORM_OT_edge_slide
            layout.prop(props_macro, "correct_uv")

        return dict(
            idname="builtin.loop_cut",
            label="Loop Cut",
            icon="ops.mesh.loopcut_slide",
            widget="VIEW3D_GGT_mesh_preselect_edgering",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def offset_edge_loops_slide():
        return dict(
            idname="builtin.offset_edge_loop_cut",
            label="Offset Edge Loop Cut",
            icon="ops.mesh.offset_edge_loops_slide",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def vertex_smooth():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.vertices_smooth")
            layout.prop(props, "repeat")
        return dict(
            idname="builtin.smooth",
            label="Smooth",
            icon="ops.mesh.vertices_smooth",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def vertex_randomize():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("transform.vertex_random")
            layout.prop(props, "uniform")
            layout.prop(props, "normal")
            layout.prop(props, "seed")
        return dict(
            idname="builtin.randomize",
            label="Randomize",
            icon="ops.transform.vertex_random",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def tosphere():
        return dict(
            idname="builtin.to_sphere",
            label="To Sphere",
            icon="ops.transform.tosphere",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def shrink_fatten():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("transform.shrink_fatten")
            layout.prop(props, "use_even_offset")

        return dict(
            idname="builtin.shrink_fatten",
            label="Shrink/Fatten",
            icon="ops.transform.shrink_fatten",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def push_pull():
        return dict(
            idname="builtin.push_pull",
            label="Push/Pull",
            icon="ops.transform.push_pull",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
        )

    @ToolDef.from_fn
    def knife():
        def draw_settings(_context, layout, tool, *, extra=False):
            show_extra = False
            props = tool.operator_properties("mesh.knife_tool")
            if not extra:
                layout.prop(props, "use_occlude_geometry")
                layout.prop(props, "only_selected")
                layout.prop(props, "xray")
                region_is_header = bpy.context.region.type == 'TOOL_HEADER'
                if region_is_header:
                    show_extra = True
                else:
                    extra = True
            if extra:
                layout.use_property_decorate = False
                layout.use_property_split = True

                layout.prop(props, "visible_measurements")
                layout.prop(props, "angle_snapping")
                layout.label(text="Angle Snapping Increment")
                layout.prop(props, "angle_snapping_increment", text="")
            if show_extra:
                layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
        return dict(
            idname="builtin.knife",
            label="Knife",
            cursor='KNIFE',
            icon="ops.mesh.knife_tool",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )

    @ToolDef.from_fn
    def bisect():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("mesh.bisect")
            layout.prop(props, "use_fill")
            layout.prop(props, "clear_inner")
            layout.prop(props, "clear_outer")
            layout.prop(props, "threshold")
        return dict(
            idname="builtin.bisect",
            label="Bisect",
            icon="ops.mesh.bisect",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )


class _defs_edit_curve:

    @ToolDef.from_fn
    def draw():
        def draw_settings(context, layout, _tool, *, extra=False):
            # Tool settings initialize operator options.
            tool_settings = context.tool_settings
            cps = tool_settings.curve_paint_settings
            region_type = context.region.type

            if region_type == 'TOOL_HEADER':
                if not extra:
                    layout.prop(cps, "curve_type", text="")
                    layout.prop(cps, "depth_mode", expand=True)
                    layout.popover("TOPBAR_PT_tool_settings_extra", text="...")
                    return

            layout.use_property_split = True
            layout.use_property_decorate = False

            if region_type != 'TOOL_HEADER':
                layout.prop(cps, "curve_type")
                layout.separator()
            if cps.curve_type == 'BEZIER':
                layout.prop(cps, "fit_method")
                layout.prop(cps, "error_threshold")
                if region_type != 'TOOL_HEADER':
                    row = layout.row(heading="Detect Corners", align=True)
                else:
                    row = layout.row(heading="Corners", align=True)
                row.prop(cps, "use_corners_detect", text="")
                sub = row.row(align=True)
                sub.active = cps.use_corners_detect
                sub.prop(cps, "corner_angle", text="")
                layout.separator()

            col = layout.column(align=True)
            col.prop(cps, "radius_taper_start",
                     text="Taper Start", slider=True)
            col.prop(cps, "radius_taper_end", text="End", slider=True)
            col = layout.column(align=True)
            col.prop(cps, "radius_min", text="Radius Min")
            col.prop(cps, "radius_max", text="Max")
            col.prop(cps, "use_pressure_radius")

            if region_type != 'TOOL_HEADER' or cps.depth_mode == 'SURFACE':
                layout.separator()

            if region_type != 'TOOL_HEADER':
                row = layout.row()
                row.prop(cps, "depth_mode", expand=True)
            if cps.depth_mode == 'SURFACE':
                col = layout.column()
                col.prop(cps, "surface_offset")
                col.prop(cps, "use_offset_absolute")
                col.prop(cps, "use_stroke_endpoints")
                if cps.use_stroke_endpoints:
                    colsub = layout.column(align=True)
                    colsub.prop(cps, "surface_plane")

        return dict(
            idname="builtin.draw",
            label="Draw",
            cursor='PAINT_BRUSH',
            icon="ops.curve.draw",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            idname="builtin.extrude",
            label="Extrude",
            icon="ops.curve.extrude_move",
            widget="VIEW3D_GGT_xform_extrude",
            keymap=(),
            draw_settings=_template_widget.VIEW3D_GGT_xform_extrude.draw_settings,
        )

    @ToolDef.from_fn
    def extrude_cursor():
        return dict(
            idname="builtin.extrude_cursor",
            label="Extrude to Cursor",
            cursor='CROSSHAIR',
            icon="ops.curve.extrude_cursor",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def pen():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("curve.pen")
            layout.prop(props, "close_spline")
            layout.prop(props, "extrude_handle")
        return dict(
            idname="builtin.pen",
            label="Curve Pen",
            cursor='CROSSHAIR',
            icon="ops.curve.pen",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def tilt():
        return dict(
            idname="builtin.tilt",
            label="Tilt",
            icon="ops.transform.tilt",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def curve_radius():
        return dict(
            idname="builtin.radius",
            label="Radius",
            description=(
                "Expand or contract the radius of the selected curve points"
            ),
            icon="ops.curve.radius",
            widget="VIEW3D_GGT_tool_generic_handle_free",
            keymap=(),
        )

    @ToolDef.from_fn
    def curve_vertex_randomize():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("transform.vertex_random")
            layout.prop(props, "uniform")
            layout.prop(props, "normal")
            layout.prop(props, "seed")
        return dict(
            idname="builtin.randomize",
            label="Randomize",
            icon="ops.curve.vertex_random",
            widget="VIEW3D_GGT_tool_generic_handle_normal",
            keymap=(),
            draw_settings=draw_settings,
        )


class _defs_edit_text:

    @ToolDef.from_fn
    def select_text():
        return dict(
            idname="builtin.select_text",
            label="Select Text",
            cursor='TEXT',
            icon="ops.generic.select_box",
            widget=None,
            keymap=(),
        )


class _defs_pose:

    @ToolDef.from_fn
    def breakdown():
        return dict(
            idname="builtin.breakdowner",
            label="Breakdowner",
            icon="ops.pose.breakdowner",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def push():
        return dict(
            idname="builtin.push",
            label="Push",
            icon="ops.pose.push",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def relax():
        return dict(
            idname="builtin.relax",
            label="Relax",
            icon="ops.pose.relax",
            widget=None,
            keymap=(),
        )


class _defs_particle:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.particle.",
            type=bpy.types.ParticleEdit,
            attr="tool",
        )


class _defs_sculpt:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.sculpt.",
            type=bpy.types.Brush,
            attr="sculpt_tool",
            # TODO(@ideasman42): we may want to enable this,
            # it causes awkward grouping with 2x column button layout.
            use_separators=False,
        )

    @ToolDef.from_fn
    def hide_border():
        return dict(
            idname="builtin.box_hide",
            label="Box Hide",
            icon="ops.sculpt.border_hide",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def mask_border():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("paint.mask_box_gesture")
            layout.prop(props, "use_front_faces_only", expand=False)

        return dict(
            idname="builtin.box_mask",
            label="Box Mask",
            icon="ops.sculpt.border_mask",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def mask_lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("paint.mask_lasso_gesture")
            layout.prop(props, "use_front_faces_only", expand=False)

        return dict(
            idname="builtin.lasso_mask",
            label="Lasso Mask",
            icon="ops.sculpt.lasso_mask",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def mask_line():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("paint.mask_line_gesture")
            layout.prop(props, "use_front_faces_only", expand=False)
            layout.prop(props, "use_limit_to_segment", expand=False)

        return dict(
            idname="builtin.line_mask",
            label="Line Mask",
            icon="ops.sculpt.line_mask",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def face_set_box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.face_set_box_gesture")
            layout.prop(props, "use_front_faces_only", expand=False)

        return dict(
            idname="builtin.box_face_set",
            label="Box Face Set",
            icon="ops.sculpt.border_face_set",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def face_set_lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.face_set_lasso_gesture")
            layout.prop(props, "use_front_faces_only", expand=False)

        return dict(
            idname="builtin.lasso_face_set",
            label="Lasso Face Set",
            icon="ops.sculpt.lasso_face_set",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def trim_box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.trim_box_gesture")
            layout.prop(props, "trim_mode", expand=False)
            layout.prop(props, "trim_orientation", expand=False)
            layout.prop(props, "trim_extrude_mode", expand=False)
            layout.prop(props, "use_cursor_depth", expand=False)
        return dict(
            idname="builtin.box_trim",
            label="Box Trim",
            icon="ops.sculpt.box_trim",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def trim_lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.trim_lasso_gesture")
            layout.prop(props, "trim_mode", expand=False)
            layout.prop(props, "trim_orientation", expand=False)
            layout.prop(props, "trim_extrude_mode", expand=False)
            layout.prop(props, "use_cursor_depth", expand=False)
        return dict(
            idname="builtin.lasso_trim",
            label="Lasso Trim",
            icon="ops.sculpt.lasso_trim",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def project_line():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.project_line_gesture")
            layout.prop(props, "use_limit_to_segment", expand=False)

        return dict(
            idname="builtin.line_project",
            label="Line Project",
            icon="ops.sculpt.line_project",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def mesh_filter():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.mesh_filter")
            layout.prop(props, "type", expand=False)
            layout.prop(props, "strength")
            row = layout.row(align=True)
            row.prop(props, "deform_axis")
            layout.prop(props, "orientation", expand=False)
            if props.type == 'SURFACE_SMOOTH':
                layout.prop(
                    props, "surface_smooth_shape_preservation", expand=False)
                layout.prop(
                    props, "surface_smooth_current_vertex", expand=False)
            elif props.type == 'SHARPEN':
                layout.prop(props, "sharpen_smooth_ratio", expand=False)
                layout.prop(
                    props, "sharpen_intensify_detail_strength", expand=False)
                layout.prop(
                    props, "sharpen_curvature_smooth_iterations", expand=False)

        return dict(
            idname="builtin.mesh_filter",
            label="Mesh Filter",
            icon="ops.sculpt.mesh_filter",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def cloth_filter():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.cloth_filter")
            layout.prop(props, "type", expand=False)
            layout.prop(props, "strength")
            row = layout.row(align=True)
            row.prop(props, "force_axis")
            layout.prop(props, "orientation", expand=False)
            layout.prop(props, "cloth_mass")
            layout.prop(props, "cloth_damping")
            layout.prop(props, "use_face_sets")
            layout.prop(props, "use_collisions")

        return dict(
            idname="builtin.cloth_filter",
            label="Cloth Filter",
            icon="ops.sculpt.cloth_filter",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def color_filter():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.color_filter")
            layout.prop(props, "type", expand=False)
            if props.type == 'FILL':
                layout.prop(props, "fill_color", expand=False)
            layout.prop(props, "strength")

        return dict(
            idname="builtin.color_filter",
            label="Color Filter",
            icon="ops.sculpt.color_filter",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def mask_by_color():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.mask_by_color")
            layout.prop(props, "threshold")
            layout.prop(props, "contiguous")
            layout.prop(props, "invert")
            layout.prop(props, "preserve_previous_mask")

        return dict(
            idname="builtin.mask_by_color",
            label="Mask by Color",
            icon="ops.sculpt.mask_by_color",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def face_set_edit():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sculpt.face_set_edit")
            layout.prop(props, "mode", expand=False)
            layout.prop(props, "modify_hidden")

        return dict(
            idname="builtin.face_set_edit",
            label="Edit Face Set",
            icon="ops.sculpt.face_set_edit",
            widget=None,
            keymap="3D View Tool: Sculpt, Face Set Edit",
            draw_settings=draw_settings,
        )


class _defs_vertex_paint:

    @staticmethod
    def poll_select_mask(context):
        if context is None:
            return True
        ob = context.active_object
        return (ob and ob.type == 'MESH' and
                (ob.data.use_paint_mask or
                 ob.data.use_paint_mask_vertex))

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.paint_vertex.",
            type=bpy.types.Brush,
            attr="vertex_tool",
        )


class _defs_texture_paint:

    @staticmethod
    def poll_select_mask(context):
        if context is None:
            return True
        ob = context.active_object
        return (ob and ob.type == 'MESH' and
                (ob.data.use_paint_mask))

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.paint_texture.",
            type=bpy.types.Brush,
            attr="image_tool",
            cursor='PAINT_CROSS',
        )


class _defs_weight_paint:

    @staticmethod
    def poll_select_mask(context):
        if context is None:
            return True
        ob = context.active_object
        return (ob and ob.type == 'MESH' and
                (ob.data.use_paint_mask or
                 ob.data.use_paint_mask_vertex))

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.paint_weight.",
            type=bpy.types.Brush,
            attr="weight_tool",
        )

    @ToolDef.from_fn
    def sample_weight():
        def draw_settings(context, layout, _tool):
            if context.tool_settings.unified_paint_settings.use_unified_weight:
                weight = context.tool_settings.unified_paint_settings.weight
            elif context.tool_settings.weight_paint.brush:
                weight = context.tool_settings.weight_paint.brush.weight
            else:
                return
            layout.label(text="Weight: %.3f" % weight)
        return dict(
            idname="builtin.sample_weight",
            label="Sample Weight",
            icon="ops.paint.weight_sample",
            cursor='EYEDROPPER',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def sample_weight_group():
        return dict(
            idname="builtin.sample_vertex_group",
            label="Sample Vertex Group",
            icon="ops.paint.weight_sample_group",
            cursor='EYEDROPPER',
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def gradient():
        def draw_settings(context, layout, tool):
            brush = context.tool_settings.weight_paint.brush
            if brush is not None:
                from bl_ui.properties_paint_common import UnifiedPaintPanel
                UnifiedPaintPanel.prop_unified(
                    layout,
                    context,
                    brush,
                    "weight",
                    unified_name="use_unified_weight",
                    slider=True,
                    header=True,
                )
                UnifiedPaintPanel.prop_unified(
                    layout,
                    context,
                    brush,
                    "strength",
                    unified_name="use_unified_strength",
                    header=True,
                )

            props = tool.operator_properties("paint.weight_gradient")
            layout.prop(props, "type", expand=True)
            layout.popover("VIEW3D_PT_tools_weight_gradient")

        return dict(
            idname="builtin.gradient",
            label="Gradient",
            icon="ops.paint.weight_gradient",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )


class _defs_image_generic:

    @staticmethod
    def poll_uvedit(context):
        if context is None:
            return True
        ob = context.edit_object
        if ob is not None:
            data = ob.data
            if data is not None:
                return bool(getattr(data, "uv_layers", False))
        return False

    @ToolDef.from_fn
    def cursor():
        return dict(
            idname="builtin.cursor",
            label="Cursor",
            description=(
                "Set the cursor location, drag to transform"
            ),
            icon="ops.generic.cursor",
            keymap=(),
        )

    # Currently a place holder so we can switch away from the annotation tool.
    # Falls back to default image editor action.
    @ToolDef.from_fn
    def sample():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("image.sample")
            layout.prop(props, "size")
        return dict(
            idname="builtin.sample",
            label="Sample",
            description=(
                "Sample pixel values under the cursor"
            ),
            icon="ops.paint.weight_sample",  # XXX, needs own icon.
            keymap="Image Editor Tool: Sample",
            draw_settings=draw_settings,
        )


class _defs_image_uv_transform:

    @ToolDef.from_fn
    def translate():
        return dict(
            idname="builtin.move",
            label="Move",
            icon="ops.transform.translate",
            widget="IMAGE_GGT_gizmo2d_translate",
            operator="transform.translate",
            keymap="Image Editor Tool: Uv, Move",
        )

    @ToolDef.from_fn
    def rotate():
        return dict(
            idname="builtin.rotate",
            label="Rotate",
            icon="ops.transform.rotate",
            widget="IMAGE_GGT_gizmo2d_rotate",
            operator="transform.rotate",
            keymap="Image Editor Tool: Uv, Rotate",
        )

    @ToolDef.from_fn
    def scale():
        return dict(
            idname="builtin.scale",
            label="Scale",
            icon="ops.transform.resize",
            widget="IMAGE_GGT_gizmo2d_resize",
            operator="transform.resize",
            keymap="Image Editor Tool: Uv, Scale",
        )

    @ToolDef.from_fn
    def transform():
        return dict(
            idname="builtin.transform",
            label="Transform",
            description=(
                "Supports any combination of grab, rotate, and scale at once"
            ),
            icon="ops.transform.transform",
            widget="IMAGE_GGT_gizmo2d",
            # No keymap default action, only for gizmo!
        )


class _defs_image_uv_select:

    @ToolDef.from_fn
    def select():
        return dict(
            idname="builtin.select",
            label="Tweak",
            icon="ops.generic.select",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("uv.select_box")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_box",
            label="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("uv.select_lasso")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_lasso",
            label="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("uv.select_circle")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            layout.prop(props, "radius")

        def draw_cursor(_context, tool, xy):
            from gpu_extras.presets import draw_circle_2d
            props = tool.operator_properties("uv.select_circle")
            radius = props.radius
            draw_circle_2d(xy, (1.0,) * 4, radius, segments=32)

        return dict(
            idname="builtin.select_circle",
            label="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
            draw_cursor=draw_cursor,
        )


class _defs_image_uv_edit:

    @ToolDef.from_fn
    def rip_region():
        return dict(
            idname="builtin.rip_region",
            label="Rip Region",
            icon="ops.mesh.rip",
            # TODO: generic operator (UV version of `VIEW3D_GGT_tool_generic_handle_free`).
            widget=None,
            keymap=(),
            options={'KEYMAP_FALLBACK'},
        )


class _defs_image_uv_sculpt:

    @staticmethod
    def generate_from_brushes(context):
        def draw_cursor(context, _tool, xy):
            from gpu_extras.presets import draw_circle_2d
            tool_settings = context.tool_settings
            uv_sculpt = tool_settings.uv_sculpt
            if not uv_sculpt.show_brush:
                return
            ups = tool_settings.unified_paint_settings
            if ups.use_unified_size:
                radius = ups.size
            else:
                brush = tool_settings.uv_sculpt.brush
                if brush is None:
                    return
                radius = brush.size
            draw_circle_2d(xy, (1.0,) * 4, radius)

        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.uv_sculpt.",
            type=bpy.types.Brush,
            attr="uv_sculpt_tool",
            tooldef_keywords=dict(
                operator="sculpt.uv_sculpt_stroke",
                keymap="Image Editor Tool: Uv, Sculpt Stroke",
                draw_cursor=draw_cursor,
                options={'KEYMAP_FALLBACK'},
            ),
        )


class _defs_gpencil_paint:

    @staticmethod
    def gpencil_primitive_toolbar(context, layout, _tool, props):
        paint = context.tool_settings.gpencil_paint
        brush = paint.brush

        if brush is None:
            return False

        gp_settings = brush.gpencil_settings

        row = layout.row(align=True)
        tool_settings = context.scene.tool_settings
        settings = tool_settings.gpencil_paint
        row.template_ID_preview(settings, "brush", rows=3,
                                cols=8, hide_buttons=True)

        from bl_ui.properties_paint_common import (
            brush_basic_gpencil_paint_settings,
            brush_basic__draw_color_selector,
        )

        brush_basic__draw_color_selector(
            context, layout, brush, gp_settings, props)
        brush_basic_gpencil_paint_settings(
            layout, context, brush, compact=True)
        return True

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.gpencil_draw.",
            type=bpy.types.Brush,
            attr="gpencil_tool",
            cursor='DOT',
            tooldef_keywords=dict(
                operator="gpencil.draw",
            ),
        )

    @ToolDef.from_fn
    def cutter():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("gpencil.stroke_cutter")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "flat_caps")
        return dict(
            idname="builtin.cutter",
            label="Cutter",
            icon="ops.gpencil.stroke_cutter",
            cursor='KNIFE',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def line():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_line")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.line",
            label="Line",
            icon="ops.gpencil.primitive_line",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def polyline():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_polyline")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.polyline",
            label="Polyline",
            icon="ops.gpencil.primitive_polyline",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def box():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_box")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.box",
            label="Box",
            icon="ops.gpencil.primitive_box",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_circle")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.circle",
            label="Circle",
            icon="ops.gpencil.primitive_circle",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def arc():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_curve")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.arc",
            label="Arc",
            icon="ops.gpencil.primitive_arc",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def curve():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.primitive_curve")
            _defs_gpencil_paint.gpencil_primitive_toolbar(
                context, layout, tool, props)

        return dict(
            idname="builtin.curve",
            label="Curve",
            icon="ops.gpencil.primitive_curve",
            cursor='CROSSHAIR',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def eyedropper():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("ui.eyedropper_gpencil_color")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", expand=True)
        return dict(
            idname="builtin.eyedropper",
            label="Eyedropper",
            icon="ops.paint.eyedropper_add",
            cursor='EYEDROPPER',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def interpolate():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("gpencil.interpolate")
            layout.prop(props, "layers")
            layout.prop(props, "exclude_breakdowns")
            layout.prop(props, "flip")
            layout.prop(props, "smooth_factor")
            layout.prop(props, "smooth_steps")

        return dict(
            idname="builtin.interpolate",
            label="Interpolate",
            icon="ops.pose.breakdowner",
            cursor='DEFAULT',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )


class _defs_gpencil_edit:
    def is_segment(context):
        tool_settings = context.scene.tool_settings
        if context.mode == 'EDIT_GPENCIL':
            return tool_settings.gpencil_selectmode_edit == 'SEGMENT'
        elif context.mode == 'SCULPT_GPENCIL':
            return tool_settings.use_gpencil_select_mask_segment
        elif context.mode == 'VERTEX_GPENCIL':
            return tool_settings.use_gpencil_vertex_select_mask_segment
        else:
            return False

    @ToolDef.from_fn
    def bend():
        return dict(
            idname="builtin.bend",
            label="Bend",
            icon="ops.gpencil.edit_bend",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def select():
        def draw_settings(context, layout, _tool):
            if _defs_gpencil_edit.is_segment(context):
                layout.prop(context.tool_settings.gpencil_sculpt,
                            "intersection_threshold")
        return dict(
            idname="builtin.select",
            label="Tweak",
            icon="ops.generic.select",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def box_select():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.select_box")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            if _defs_gpencil_edit.is_segment(context):
                layout.prop(context.tool_settings.gpencil_sculpt,
                            "intersection_threshold")
        return dict(
            idname="builtin.select_box",
            label="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso_select():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.select_lasso")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            if _defs_gpencil_edit.is_segment(context):
                layout.prop(context.tool_settings.gpencil_sculpt,
                            "intersection_threshold")
        return dict(
            idname="builtin.select_lasso",
            label="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle_select():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("gpencil.select_circle")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            layout.prop(props, "radius")
            if _defs_gpencil_edit.is_segment(context):
                layout.prop(context.tool_settings.gpencil_sculpt,
                            "intersection_threshold")

        def draw_cursor(_context, tool, xy):
            from gpu_extras.presets import draw_circle_2d
            props = tool.operator_properties("gpencil.select_circle")
            radius = props.radius
            draw_circle_2d(xy, (1.0,) * 4, radius, segments=32)

        return dict(
            idname="builtin.select_circle",
            label="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
            draw_cursor=draw_cursor,
        )

    @ToolDef.from_fn
    def radius():
        return dict(
            idname="builtin.radius",
            label="Radius",
            description=(
                "Expand or contract the radius of the selected points"
            ),
            icon="ops.gpencil.radius",

            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def shear():
        return dict(
            idname="builtin.shear",
            label="Shear",
            icon="ops.gpencil.edit_shear",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def tosphere():
        return dict(
            idname="builtin.to_sphere",
            label="To Sphere",
            icon="ops.transform.tosphere",
            widget=None,
            keymap=(),
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            idname="builtin.extrude",
            label="Extrude",
            icon="ops.gpencil.extrude_move",
            widget="VIEW3D_GGT_xform_extrude",
            keymap=(),
            draw_settings=_template_widget.VIEW3D_GGT_xform_extrude.draw_settings,
        )

    @ToolDef.from_fn
    def transform_fill():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("gpencil.transform_fill")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", expand=True)

        return dict(
            idname="builtin.transform_fill",
            label="Transform Fill",
            icon="ops.gpencil.transform_fill",
            cursor='DEFAULT',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def interpolate():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("gpencil.interpolate")
            layout.prop(props, "layers")
            layout.prop(props, "interpolate_selected_only")
            layout.prop(props, "exclude_breakdowns")
            layout.prop(props, "flip")
            layout.prop(props, "smooth_factor")
            layout.prop(props, "smooth_steps")

        return dict(
            idname="builtin.interpolate",
            label="Interpolate",
            icon="ops.pose.breakdowner",
            cursor='DEFAULT',
            widget=None,
            keymap=(),
            draw_settings=draw_settings,
        )


class _defs_gpencil_sculpt:

    @staticmethod
    def poll_select_mask(context):
        if context is None:
            return True
        ob = context.active_object
        tool_settings = context.scene.tool_settings
        return (
            ob is not None and
            ob.type == 'GPENCIL' and (
                tool_settings.use_gpencil_select_mask_point or
                tool_settings.use_gpencil_select_mask_stroke or
                tool_settings.use_gpencil_select_mask_segment
            )
        )

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="ops.gpencil.sculpt_",
            type=bpy.types.Brush,
            attr="gpencil_sculpt_tool",
            tooldef_keywords=dict(
                operator="gpencil.sculpt_paint",
            ),
        )


class _defs_gpencil_weight:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="ops.gpencil.sculpt_",
            type=bpy.types.Brush,
            attr="gpencil_weight_tool",
            tooldef_keywords=dict(
                operator="gpencil.weight_paint",
            ),
        )


class _defs_curves_sculpt:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="ops.curves.sculpt_",
            type=bpy.types.Brush,
            attr="curves_sculpt_tool",
            icon_map={
                # Use the generic icon for selection painting.
                "ops.curves.sculpt_selection_paint": "ops.generic.select_paint",
            },
        )


class _defs_gpencil_vertex:

    @staticmethod
    def poll_select_mask(context):
        if context is None:
            return True
        ob = context.active_object
        tool_settings = context.scene.tool_settings
        return (
            ob is not None and
            ob.type == 'GPENCIL' and (
                tool_settings.use_gpencil_vertex_select_mask_point or
                tool_settings.use_gpencil_vertex_select_mask_stroke or
                tool_settings.use_gpencil_vertex_select_mask_segment
            )
        )

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            idname_prefix="builtin_brush.",
            icon_prefix="brush.paint_vertex.",
            type=bpy.types.Brush,
            attr="gpencil_vertex_tool",
            cursor='DOT',
            tooldef_keywords=dict(
                operator="gpencil.vertex_paint",
            ),
        )


class _defs_node_select:

    @ToolDef.from_fn
    def select():
        return dict(
            idname="builtin.select",
            label="Tweak",
            icon="ops.generic.select",
            widget=None,
            keymap="Node Tool: Tweak",
        )

    @ToolDef.from_fn
    def box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("node.select_box")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_box",
            label="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap="Node Tool: Select Box",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("node.select_lasso")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_lasso",
            label="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap="Node Tool: Select Lasso",
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("node.select_circle")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
            layout.prop(props, "radius")

        def draw_cursor(_context, tool, xy):
            from gpu_extras.presets import draw_circle_2d
            props = tool.operator_properties("node.select_circle")
            radius = props.radius
            draw_circle_2d(xy, (1.0,) * 4, radius, segments=32)

        return dict(
            idname="builtin.select_circle",
            label="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap="Node Tool: Select Circle",
            draw_settings=draw_settings,
            draw_cursor=draw_cursor,
        )


class _defs_node_edit:

    @ToolDef.from_fn
    def links_cut():
        return dict(
            idname="builtin.links_cut",
            label="Links Cut",
            icon="ops.node.links_cut",
            widget=None,
            keymap="Node Tool: Links Cut",
            options={'KEYMAP_FALLBACK'},
        )


class _defs_sequencer_generic:

    @ToolDef.from_fn
    def cursor():
        return dict(
            idname="builtin.cursor",
            label="Cursor",
            description=(
                "Set the cursor location, drag to transform"
            ),
            icon="ops.generic.cursor",
            keymap="Sequencer Tool: Cursor",
        )

    @ToolDef.from_fn
    def blade():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sequencer.split")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "type", expand=True)
        return dict(
            idname="builtin.blade",
            label="Blade",
            icon="ops.sequencer.blade",
            cursor='CROSSHAIR',
            widget=None,
            keymap="Sequencer Tool: Blade",
            draw_settings=draw_settings,
            options={'KEYMAP_FALLBACK'},
        )

    @ToolDef.from_fn
    def sample():
        return dict(
            idname="builtin.sample",
            label="Sample",
            description=(
                "Sample pixel values under the cursor"
            ),
            icon="ops.paint.weight_sample",  # XXX, needs own icon.
            keymap="Sequencer Tool: Sample",
        )

    @ToolDef.from_fn
    def translate():
        return dict(
            idname="builtin.move",
            label="Move",
            icon="ops.transform.translate",
            widget="SEQUENCER_GGT_gizmo2d_translate",
            operator="transform.translate",
            keymap="Sequencer Tool: Move",
        )

    @ToolDef.from_fn
    def rotate():
        return dict(
            idname="builtin.rotate",
            label="Rotate",
            icon="ops.transform.rotate",
            widget="SEQUENCER_GGT_gizmo2d_rotate",
            operator="transform.rotate",
            keymap="Sequencer Tool: Rotate",
        )

    @ToolDef.from_fn
    def scale():
        return dict(
            idname="builtin.scale",
            label="Scale",
            icon="ops.transform.resize",
            widget="SEQUENCER_GGT_gizmo2d_resize",
            operator="transform.resize",
            keymap="Sequencer Tool: Scale",
        )

    @ToolDef.from_fn
    def transform():
        return dict(
            idname="builtin.transform",
            label="Transform",
            description=(
                "Supports any combination of grab, rotate, and scale at once"
            ),
            icon="ops.transform.transform",
            widget="SEQUENCER_GGT_gizmo2d",
            # No keymap default action, only for gizmo!
        )


class _defs_sequencer_select:
    @ToolDef.from_fn
    def select():
        return dict(
            idname="builtin.select",
            label="Tweak",
            icon="ops.generic.select",
            widget=None,
            keymap="Sequencer Tool: Tweak",
        )

    @ToolDef.from_fn
    def box():
        def draw_settings(_context, layout, tool):
            props = tool.operator_properties("sequencer.select_box")
            row = layout.row()
            row.use_property_split = False
            row.prop(props, "mode", text="", expand=True, icon_only=True)
        return dict(
            idname="builtin.select_box",
            label="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap="Sequencer Tool: Select Box",
            draw_settings=draw_settings,
        )


class IMAGE_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the `ToolSelectPanelHelper` API.
    keymap_prefix = "Image Editor Tool:"

    # Default group to use as a fallback.
    tool_fallback_id = "builtin.select"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            if context.space_data is None:
                mode = 'VIEW'
            else:
                mode = context.space_data.mode
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # Private tool lists for convenient reuse in `_tools`.

    _tools_transform = (
        _defs_image_uv_transform.translate,
        _defs_image_uv_transform.rotate,
        _defs_image_uv_transform.scale,
        _defs_image_uv_transform.transform,
    )

    _tools_select = (
        (
            _defs_image_uv_select.select,
            _defs_image_uv_select.box,
            _defs_image_uv_select.circle,
            _defs_image_uv_select.lasso,
        ),
    )

    _tools_annotate = (
        (
            _defs_annotate.scribble,
            _defs_annotate.line,
            _defs_annotate.poly,
            _defs_annotate.eraser,
        ),
    )

    # Private tools dictionary, store data to implement `tools_all` & `tools_from_context`.
    # The keys match image spaces modes: `context.space_data.mode`.
    # The values represent the tools, see `ToolSelectPanelHelper` for details.
    _tools = {
        None: [
            # for all modes
        ],
        'VIEW': [
            _defs_image_generic.sample,
            *_tools_annotate,
        ],
        'UV': [
            *_tools_select,
            _defs_image_generic.cursor,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            None,
            _defs_image_uv_edit.rip_region,
            None,
            lambda context: (
                _defs_image_uv_sculpt.generate_from_brushes(context)
                if _defs_image_generic.poll_uvedit(context)
                else ()
            ),
        ],
        'MASK': [
            None,
        ],
        'PAINT': [
            _defs_texture_paint.generate_from_brushes,
            None,
            *_tools_annotate,
        ],
    }


class NODE_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the `ToolSelectPanelHelper` API.
    keymap_prefix = "Node Editor Tool:"

    # Default group to use as a fallback.
    tool_fallback_id = "builtin.select"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            if context.space_data is None:
                mode = None
            else:
                mode = context.space_data.tree_type
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # Private tool lists for convenient reuse in `_tools`.

    _tools_select = (
        (
            _defs_node_select.select,
            _defs_node_select.box,
            _defs_node_select.lasso,
            _defs_node_select.circle,
        ),
    )

    _tools_annotate = (
        (
            _defs_annotate.scribble,
            _defs_annotate.line,
            _defs_annotate.poly,
            _defs_annotate.eraser,
        ),
    )

    # Private tools dictionary, store data to implement `tools_all` & `tools_from_context`.
    # The keys is always `None` since nodes don't use use modes to access different tools.
    # The values represent the tools, see `ToolSelectPanelHelper` for details.
    _tools = {
        None: [
            *_tools_select,
            None,
            *_tools_annotate,
            None,
            _defs_node_edit.links_cut,
        ],
    }


class VIEW3D_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the `ToolSelectPanelHelper` API.
    keymap_prefix = "3D View Tool:"

    # Default group to use as a fallback.
    tool_fallback_id = "builtin.select"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            mode = context.mode
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # Private tool lists for convenient reuse in `_tools`.

    _tools_transform = (
        _defs_transform.translate,
        _defs_transform.rotate,
        (
            _defs_transform.scale,
            _defs_transform.scale_cage,
        ),
        _defs_transform.transform,
    )

    _tools_select = (
        (
            _defs_view3d_select.select,
            _defs_view3d_select.box,
            _defs_view3d_select.circle,
            _defs_view3d_select.lasso,
        ),
    )

    _tools_annotate = (
        (
            _defs_annotate.scribble,
            _defs_annotate.line,
            _defs_annotate.poly,
            _defs_annotate.eraser,
        ),
    )

    _tools_gpencil_select = (
        (
            _defs_gpencil_edit.select,
            _defs_gpencil_edit.box_select,
            _defs_gpencil_edit.circle_select,
            _defs_gpencil_edit.lasso_select,
        ),
    )

    _tools_view3d_add = (
        _defs_view3d_add.cube_add,
        _defs_view3d_add.cone_add,
        _defs_view3d_add.cylinder_add,
        _defs_view3d_add.uv_sphere_add,
        _defs_view3d_add.ico_sphere_add,
    )

    _tools_default = (
        *_tools_select,
        _defs_view3d_generic.cursor,
        None,
        *_tools_transform,
        None,
        *_tools_annotate,
        _defs_view3d_generic.ruler,
    )

    # Private tools dictionary, store data to implement `tools_all` & `tools_from_context`.
    # The keys match object-modes from: `context.mode`.
    # The values represent the tools, see `ToolSelectPanelHelper` for details.
    _tools = {
        None: [
            # Don't use this! because of paint modes.
            # _defs_view3d_generic.cursor,
            # End group.
        ],
        'OBJECT': [
            *_tools_default,
            None,
            _tools_view3d_add,
        ],
        'POSE': [
            *_tools_default,
            None,
            (
                _defs_pose.breakdown,
                _defs_pose.push,
                _defs_pose.relax,
            ),
        ],
        'EDIT_ARMATURE': [
            *_tools_default,
            None,
            _defs_edit_armature.roll,
            (
                _defs_edit_armature.bone_size,
                _defs_edit_armature.bone_envelope,
            ),
            None,
            (
                _defs_edit_armature.extrude,
                _defs_edit_armature.extrude_cursor,
            ),
            _defs_transform.shear,
        ],
        'EDIT_MESH': [
            *_tools_default,

            None,
            _tools_view3d_add,
            None,
            (
                _defs_edit_mesh.extrude,
                _defs_edit_mesh.extrude_manifold,
                _defs_edit_mesh.extrude_normals,
                _defs_edit_mesh.extrude_individual,
                _defs_edit_mesh.extrude_cursor,
            ),
            _defs_edit_mesh.inset,
            _defs_edit_mesh.bevel,
            (
                _defs_edit_mesh.loopcut_slide,
                _defs_edit_mesh.offset_edge_loops_slide,
            ),
            (
                _defs_edit_mesh.knife,
                _defs_edit_mesh.bisect,
            ),
            _defs_edit_mesh.poly_build,
            (
                _defs_edit_mesh.spin,
                _defs_edit_mesh.spin_duplicate,
            ),
            (
                _defs_edit_mesh.vertex_smooth,
                _defs_edit_mesh.vertex_randomize,
            ),
            (
                _defs_edit_mesh.edge_slide,
                _defs_edit_mesh.vert_slide,
            ),
            (
                _defs_edit_mesh.shrink_fatten,
                _defs_edit_mesh.push_pull,
            ),
            (
                _defs_transform.shear,
                _defs_edit_mesh.tosphere,
            ),
            (
                _defs_edit_mesh.rip_region,
                _defs_edit_mesh.rip_edge,
            ),
        ],
        'EDIT_CURVE': [
            *_tools_default,
            None,
            _defs_edit_curve.draw,
            _defs_edit_curve.pen,
            (
                _defs_edit_curve.extrude,
                _defs_edit_curve.extrude_cursor,
            ),
            None,
            _defs_edit_curve.curve_radius,
            _defs_edit_curve.tilt,
            None,
            _defs_transform.shear,
            _defs_edit_curve.curve_vertex_randomize,
        ],
        'EDIT_CURVES': [
            *_tools_default,
        ],
        'EDIT_SURFACE': [
            *_tools_default,
            None,
            _defs_transform.shear,
        ],
        'EDIT_METABALL': [
            *_tools_default,
            None,
            _defs_transform.shear,
        ],
        'EDIT_LATTICE': [
            *_tools_default,
            None,
            _defs_transform.shear,
        ],
        'EDIT_TEXT': [
            _defs_edit_text.select_text,
            _defs_view3d_generic.cursor,
            None,
            *_tools_annotate,
            _defs_view3d_generic.ruler,
        ],
        'PARTICLE': [
            *_tools_select,
            _defs_view3d_generic.cursor,
            None,
            _defs_particle.generate_from_brushes,
        ],
        'SCULPT': [
            _defs_sculpt.generate_from_brushes,
            None,
            (
                _defs_sculpt.mask_border,
                _defs_sculpt.mask_lasso,
                _defs_sculpt.mask_line,
            ),
            _defs_sculpt.hide_border,
            (
                _defs_sculpt.face_set_box,
                _defs_sculpt.face_set_lasso,
            ),
            (
                _defs_sculpt.trim_box,
                _defs_sculpt.trim_lasso,
            ),
            _defs_sculpt.project_line,
            None,
            _defs_sculpt.mesh_filter,
            _defs_sculpt.cloth_filter,
            _defs_sculpt.color_filter,
            None,
            _defs_sculpt.face_set_edit,
            _defs_sculpt.mask_by_color,
            None,
            _defs_transform.translate,
            _defs_transform.rotate,
            _defs_transform.scale,
            _defs_transform.transform,
            None,
            *_tools_annotate,
        ],
        'PAINT_TEXTURE': [
            _defs_texture_paint.generate_from_brushes,
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_select
                if _defs_texture_paint.poll_select_mask(context)
                else ()
            ),
            *_tools_annotate,
        ],
        'PAINT_VERTEX': [
            _defs_vertex_paint.generate_from_brushes,
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_select
                if _defs_vertex_paint.poll_select_mask(context)
                else ()
            ),
            *_tools_annotate,
        ],
        'PAINT_WEIGHT': [
            _defs_weight_paint.generate_from_brushes,
            _defs_weight_paint.gradient,
            None,
            (
                _defs_weight_paint.sample_weight,
                _defs_weight_paint.sample_weight_group,
            ),
            None,
            lambda context: (
                (
                    _defs_view3d_generic.cursor,
                    None,
                    *VIEW3D_PT_tools_active._tools_transform,
                )
                if context is None or context.pose_object
                else ()
            ),
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_select
                if _defs_weight_paint.poll_select_mask(context)
                else ()
            ),
            *_tools_annotate,
        ],
        'PAINT_GPENCIL': [
            _defs_view3d_generic.cursor,
            None,
            _defs_gpencil_paint.generate_from_brushes,
            _defs_gpencil_paint.cutter,
            None,
            _defs_gpencil_paint.eyedropper,
            None,
            _defs_gpencil_paint.line,
            _defs_gpencil_paint.polyline,
            _defs_gpencil_paint.arc,
            _defs_gpencil_paint.curve,
            _defs_gpencil_paint.box,
            _defs_gpencil_paint.circle,
            None,
            _defs_gpencil_paint.interpolate,
            None,
            *_tools_annotate,
        ],
        'EDIT_GPENCIL': [
            *_tools_gpencil_select,
            _defs_view3d_generic.cursor,
            None,
            *_tools_transform,
            None,
            _defs_gpencil_edit.extrude,
            _defs_gpencil_edit.radius,
            _defs_gpencil_edit.bend,
            (
                _defs_gpencil_edit.shear,
                _defs_gpencil_edit.tosphere,
            ),
            _defs_gpencil_edit.transform_fill,
            None,
            _defs_gpencil_edit.interpolate,
            None,
            *_tools_annotate,
        ],
        'SCULPT_GPENCIL': [
            _defs_gpencil_sculpt.generate_from_brushes,
            None,
            *_tools_annotate,
            lambda context: (
                VIEW3D_PT_tools_active._tools_gpencil_select
                if _defs_gpencil_sculpt.poll_select_mask(context)
                else ()
            ),
        ],
        'WEIGHT_GPENCIL': [
            _defs_gpencil_weight.generate_from_brushes,
            None,
            *_tools_annotate,
        ],
        'VERTEX_GPENCIL': [
            _defs_gpencil_vertex.generate_from_brushes,
            None,
            *_tools_annotate,
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_gpencil_select
                if _defs_gpencil_vertex.poll_select_mask(context)
                else ()
            ),
        ],
        'SCULPT_CURVES': [
            _defs_curves_sculpt.generate_from_brushes,
            None,
            *_tools_annotate,
        ],
    }


class SEQUENCER_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the `ToolSelectPanelHelper` API.
    keymap_prefix = "Sequence Editor Tool:"

    # Default group to use as a fallback.
    tool_fallback_id = "builtin.select"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            if context.space_data:
                mode = context.space_data.view_type
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # Private tool lists for convenient reuse in `_tools`.

    _tools_select = (
        (
            _defs_sequencer_select.select,
            _defs_sequencer_select.box,
        ),
    )
    _tools_annotate = (
        (
            _defs_annotate.scribble,
            _defs_annotate.line,
            _defs_annotate.poly,
            _defs_annotate.eraser,
        ),
    )

    # Private tools dictionary, store data to implement `tools_all` & `tools_from_context`.
    # The keys match sequence editors view type: `context.space_data.view_type`.
    # The values represent the tools, see `ToolSelectPanelHelper` for details.
    _tools = {
        None: [
        ],
        'PREVIEW': [
            *_tools_select,
            _defs_sequencer_generic.cursor,
            None,
            _defs_sequencer_generic.translate,
            _defs_sequencer_generic.rotate,
            _defs_sequencer_generic.scale,
            _defs_sequencer_generic.transform,
            None,
            _defs_sequencer_generic.sample,
            *_tools_annotate,
        ],
        'SEQUENCER': [
            *_tools_select,
            _defs_sequencer_generic.blade,
        ],
        'SEQUENCER_PREVIEW': [
            *_tools_select,
            None,
            *_tools_annotate,
            None,
            _defs_sequencer_generic.blade,
        ],
    }


classes = (
    IMAGE_PT_tools_active,
    NODE_PT_tools_active,
    VIEW3D_PT_tools_active,
    SEQUENCER_PT_tools_active,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
