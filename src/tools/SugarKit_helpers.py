import bpy
# from mathutils import Matrix
# from uuid import uuid1 as uuid
from types import SimpleNamespace  # SimpleNamespace(**dict)
import platform
import math


# / Use list() to duplicate bpy collection [array] to python list
# / Use dict() to duplicate bpy struct {object} to python dict
# / Use SimpleNamespace() istead of dict {object} to get key's value by dot syntax


# Log


def C(*args):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(
                    override, text=''.join(str(a) for a in args), type="OUTPUT")


def CD(bpy_dict, tabs=0):
    if not bpy_dict:
        return
    C('  ' * tabs, bpy_dict)
    for attrKey in dir(bpy_dict):
        C('  ' + '  ' * tabs, attrKey, ': ', getattr(bpy_dict, attrKey))
    if not tabs:
        C()


def CL(bpy_col, inDetail=False, nameContains=''):
    if not bpy_col:
        return
    C(bpy_col)
    for item in list(bpy_col):
        if not nameContains or (nameContains and item.name and nameContains.lower() in item.name.lower()):
            CD(item, 1) if inDetail else C('  ', item)
    C()


# Keymap


def findIn(arr, cb):
    # call: findIn(['A', 'B', 'C'], lambda it: it == 'B')
    for item in arr:
        if cb(item):
            return item
    return None


addonKeymaps = []


def addAddonKeymapItem(
    keymapName,
    operatorData,
    hotkey,
    setKmiProps=None,
    disableOld=False,
    disableOldExactProps=None,
):
    wmkcs = bpy.context.window_manager.keyconfigs
    km, kmi = newKeymapItem(
        keyconfig=wmkcs.addon,
        keymapName=keymapName,
        operatorData=operatorData,
        hotkey=parseHotkeyStringInput(hotkey),
        setKmiProps=setKmiProps,
        disableOld=parseHotkeyStringInput(disableOld),
        disableOldExactProps=parseHotkeyStringInput(disableOldExactProps),
    )
    addonKeymaps.append((km, kmi))


def removeAddonKeymapItems():
    for km, kmi in addonKeymaps:
        km.keymap_items.remove(kmi)
    addonKeymaps.clear()


def addActiveKeymapItem(
    keymapName,
    operatorData,
    hotkey,
    setKmiProps=None,
    disableOld=False,
    disableOldExactProps=None
):
    wmkcs = bpy.context.window_manager.keyconfigs
    newKeymapItem(
        keyconfig=wmkcs.active,
        keymapName=keymapName,
        operatorData=operatorData,
        hotkey=parseHotkeyStringInput(hotkey),
        setKmiProps=setKmiProps,
        disableOld=parseHotkeyStringInput(disableOld),
        disableOldExactProps=parseHotkeyStringInput(disableOldExactProps)
    )


def disableActiveKeymapItem(
    keymapName,
    operatorData,
    hotkey=None
):
    wmkcs = bpy.context.window_manager.keyconfigs
    disableKeymapItem(
        wmkcs.active,
        keymapName,
        operatorData,
        parseHotkeyStringInput(hotkey)
    )


def addUserKeymapItem(
    keymapName,
    operatorData,
    hotkey,
    setKmiProps=None,
    disableOld=False,
    disableOldExactProps=None
):
    wmkcs = bpy.context.window_manager.keyconfigs
    newKeymapItem(
        keyconfig=wmkcs.user,
        keymapName=keymapName,
        operatorData=operatorData,
        hotkey=parseHotkeyStringInput(hotkey),
        setKmiProps=setKmiProps,
        disableOld=parseHotkeyStringInput(disableOld),
        disableOldExactProps=parseHotkeyStringInput(disableOldExactProps)
    )


def editUserKeymapItem(
    keymapName,
    operatorData,
    hotkey,
    oldHotkey=None,
    oldHotkeyExactProps=None,
):
    wmkcs = bpy.context.window_manager.keyconfigs
    idName, properties = parseOperatorData(operatorData)

    if oldHotkey == None:
        kmi = wmkcs.user.keymaps[keymapName].keymap_items.find_from_operator(
            idName)
    elif type(oldHotkey) is str or type(oldHotkey) is dict:
        kmi = findKeymapItem(
            wmkcs.user, keymapName, idName, parseHotkeyStringInput(oldHotkey))
    elif oldHotkeyExactProps != None:
        kmi = findKeymapItem(
            wmkcs.user, keymapName, operatorData, parseHotkeyStringInput(oldHotkey))

    editKemapItemHotkey(kmi, parseHotkeyStringInput(hotkey))


KEYMAP_NAME_SPACES = {"3D View": "VIEW_3D", "Image": "IMAGE_EDITOR", "Node Editor": "NODE_EDITOR",
                      "SequencerCommon": "SEQUENCE_EDITOR", "Clip": "CLIP_EDITOR", "Dopesheet": "DOPESHEET_EDITOR",
                      "Graph Editor": "GRAPH_EDITOR", "NLA Editor": "NLA_EDITOR", "Text": "TEXT_EDITOR",
                      "Console": "CONSOLE", "Info": "INFO", "Outliner": "OUTLINER", "File Browser": "FILE_BROWSER"}
MODIFIERS = ['any', 'shift', 'ctrl', 'alt', 'cmd', 'repeat']
INPUT_VALUES = ['ANY', 'PRESS', 'RELEASE', 'CLICK',
                'DOUBLE_CLICK', 'CLICK_DRAG', 'NOTHING']


def parseHotkeyStringInput(hotkey):  # 'A shift ctrl CLICK' -> {'A': ['shift', 'ctrl', 'CLICK']} \
    if type(hotkey) is str and len(hotkey.split()):
        hotkeySplit = hotkey.split()
        if len(hotkeySplit) == 1:
            return hotkey
        else:
            return {hotkeySplit.pop(0): hotkeySplit}
    else:
        return hotkey


def parseKeymapNameSpace(keymapName):
    name = keymapName
    if keymapName in list(KEYMAP_NAME_SPACES.keys()):
        space = KEYMAP_NAME_SPACES[keymapName]
    else:
        space = 'EMPTY'
    return name, space


def parseOperatorData(operatorData):
    if type(operatorData) is dict:
        idName = list(operatorData.keys())[0]
        properties = operatorData[idName]
    else:
        idName = operatorData
        properties = None
    return idName, properties


def parseKeyBinding(hotkey):
    if type(hotkey) is dict:
        key = list(hotkey.keys())[0]
        modifiers = hotkey[key]
        keyModifier = findIn(
            modifiers, lambda it: it not in MODIFIERS and it not in INPUT_VALUES)
        inputValue = findIn(modifiers, lambda it: it in INPUT_VALUES)
        repeat = findIn(modifiers, lambda it: it == 'repeat')
    else:
        key = hotkey
        modifiers = []
        keyModifier = None
        inputValue = None
        repeat = None
    return key, modifiers, keyModifier, inputValue, repeat


def newKeymapItem(
    keyconfig,
    keymapName,
    operatorData,  # 'id/propvalue' | {[id]: {prop1: 1, ...}}
    hotkey,  # 'key' | {[key]: ['shift', 'ctrl', 'alt', 'X', 'CLICK']}
    setKmiProps=None,  # def - for non-default operators or enum props set by value
    disableOld=False,  # True - one that found by find_from_operator() | hotkey
    disableOldExactProps=None,  # hotkey
):
    kmName, space = parseKeymapNameSpace(keymapName)
    idName, properties = parseOperatorData(operatorData)
    key, modifiers, keyModifier, inputValue, repeat = parseKeyBinding(hotkey)

    km = keyconfig.keymaps.new(name=kmName, space_type=space) if (
        keyconfig.name == 'Blender addon') else keyconfig.keymaps[kmName]

    if disableOld == True:
        kmi = km.keymap_items.find_from_operator(idName)
        if kmi:
            kmi.active = False
    elif type(disableOld) is str or type(disableOld) is dict:
        disableKeymapItem(
            keyconfig,
            kmName,
            idName,
            hotkey=disableOld,
        )
    elif disableOldExactProps != None:
        disableKeymapItem(
            keyconfig,
            kmName,
            operatorData,
            hotkey=disableOldExactProps,
        )

    newMethod = getattr(
        km.keymap_items, 'new' if not km.is_modal else 'new_modal')

    if 'any' in modifiers:
        kmi = newMethod(
            idName,
            key,
            inputValue if inputValue else 'PRESS',
            any=True,
            key_modifier=keyModifier if keyModifier else 'NONE',
            repeat=True if repeat else False
        )
    else:
        kmi = newMethod(
            idName,
            key,
            inputValue if inputValue else 'PRESS',
            shift='shift' in modifiers,
            ctrl='ctrl' in modifiers,
            alt='alt' in modifiers,
            oskey='cmd' in modifiers,
            key_modifier=keyModifier if keyModifier else 'NONE',
            repeat=True if repeat else False
        )

    if properties and type(properties) is dict:
        for k, v in properties.items():
            kmi.properties[k] = v

    if setKmiProps:
        try:
            setKmiProps(kmi)
        except Exception as er:
            pass

    return (km, kmi)


def disableKeymapItem(
    keyconfig,
    keymapName,  # '*' - in all keymaps
    operatorData,  # '*' - with any id | '*...' - with any id including ... | \
                   # 'id' - with id with any props | {[id]: False} - with id only without props
    hotkey=None,
):
    if keymapName != '*':
        # Compare only in passed keymap
        try:
            km = keyconfig.keymaps[keymapName]
        except Exception as er:
            km = None
        if km and km.keymap_items:
            for kmi in km.keymap_items:
                if compareKeymapItem(kmi, operatorData, hotkey, isModal=km.is_modal):
                    kmi.active = False
    else:
        # Compare in all keymaps
        for km in keyconfig.keymaps:
            for kmi in km.keymap_items:
                if compareKeymapItem(kmi, operatorData, hotkey, isModal=km.is_modal):
                    kmi.active = False


def compareKeymapItem(kmi, operatorData, hotkey, isModal):
    isOpSame = compareKmiWithOperator(kmi, operatorData, isModal)
    isKeySame = compareKmiWithHotkey(kmi, hotkey)
    return isOpSame and isKeySame


def compareKmiWithOperator(kmi, operatorData, isModal, log=False):
    if type(operatorData) is str:
        if operatorData == '*':
            return True
        elif operatorData.startswith('*'):
            return True if operatorData[1:] in kmi.idname else False

    idName, properties = parseOperatorData(operatorData)

    if not isModal:
        if idName != kmi.idname:
            return False

        compareProps = False if type(operatorData) is str else True

        if compareProps:
            if (properties and not kmi.properties) or (not properties and kmi.properties):
                return False
            elif properties and kmi.properties:
                if (len(properties.items()) != len(kmi.properties.items())):
                    return False
                else:
                    # Compare props one by one
                    for k, v in kmi.properties.items():
                        if (k not in properties) or (properties[k] != v):
                            return False
    elif isModal:
        if idName != kmi.propvalue:
            return False

    return True


def compareKmiWithHotkey(kmi, hotkey, log=False):
    if not hotkey:
        return True

    key, modifiers, keyModifier, inputValue, repeat = parseKeyBinding(hotkey)
    different = []

    if kmi.type != key:
        different.append('type')
    if (kmi.shift and 'shift' not in modifiers) or ('shift' in modifiers and not kmi.shift):
        different.append('shift')
    if (kmi.ctrl and 'ctrl' not in modifiers) or ('ctrl' in modifiers and not kmi.ctrl):
        different.append('ctrl')
    if (kmi.alt and 'alt' not in modifiers) or ('alt' in modifiers and not kmi.alt):
        different.append('alt')
    if (kmi.oskey and 'cmd' not in modifiers) or ('cmd' in modifiers and not kmi.oskey):
        different.append('cmd')
    if (kmi.any and 'any' not in modifiers) or ('any' in modifiers and not kmi.any):
        different.append('any')
    if kmi.key_modifier != 'NONE' and kmi.key_modifier != keyModifier:
        different.append('keymod')
    if kmi.value != (inputValue if inputValue else 'PRESS'):
        different.append('value')

    return True if not len(different) else False


def findKeymapItem(
    keyconfig,
    keymapName,
    operatorData,
    hotkey
):
    try:
        km = keyconfig.keymaps[keymapName]
    except Exception as er:
        km = None
    if km and km.keymap_items:
        for kmi in km.keymap_items:
            if compareKeymapItem(kmi, operatorData, hotkey, isModal=km.is_modal):
                return kmi


def editKemapItemHotkey(kmi, hotkey):
    if not kmi:
        return

    key, modifiers, keyModifier, inputValue, repeat = parseKeyBinding(hotkey)

    kmi.type = key
    if 'any' in modifiers:
        kmi.shift = False
        kmi.ctrl = False
        kmi.alt = False
        kmi.oskey = False
        kmi.any = True
    else:
        kmi.shift = 'shift' in modifiers
        kmi.ctrl = 'ctrl' in modifiers
        kmi.alt = 'alt' in modifiers
        kmi.oskey = 'cmd' in modifiers
    kmi.key_modifier = keyModifier if keyModifier else kmi.key_modifier
    kmi.value = inputValue if inputValue else kmi.value
    kmi.repeat = repeat if repeat != None else kmi.repeat


# Sculpt trim curve modal:
def getKeymapFromContext(context, name, keyconfigName="active"):
    wmkcs = context.window_manager.keyconfigs
    if keyconfigName == "active":
        return wmkcs.active.keymaps[name]
    elif keyconfigName == "user":
        return wmkcs.user.keymaps[name]  # == wmkcs['Blender user'].keymaps[name] \
    elif keyconfigName == 'addon':
        return wmkcs.addon.keymaps[name]  # == wmkcs['Blender addon'].keymaps[name] \
    elif keyconfigName == 'default':
        return wmkcs.default.keymaps[name]  # == wmkcs['Blender'].keymaps[name] \
    else:
        try:
            return wmkcs[keyconfigName].keymaps[name]
        except Exception as er:
            return None


def disableActiveKeymapItems(keymap):
    disabledKeymapItemsIds = []
    if keymap and keymap.keymap_items:
        for kmi in keymap.keymap_items:
            if kmi.active:
                kmi.active = False
                disabledKeymapItemsIds.append(kmi.id)
    return disabledKeymapItemsIds


def removeActiveKeymapItems(keymap):
    if keymap and keymap.keymap_items:
        for kmi in list(keymap.keymap_items):
            if kmi.active:
                keymap.keymap_items.remove(kmi)


def unableDisabledKeymapItems(keymap, disabledKeymapItemsIds):
    if keymap and keymap.keymap_items:
        for kmi in keymap.keymap_items:
            if kmi.id in disabledKeymapItemsIds:
                kmi.active = True
        disabledKeymapItemsIds.clear()


# Keyconf builder:
def restoreDefaultKeymaps():
    wmkcs = bpy.context.window_manager.keyconfigs
    # Restore keymaps to default to avoid future collision bugs
    for dkm in wmkcs.default.keymaps:
        dkm.restore_to_default()


def buildNewActiveKeyconfig(name):
    wmkcs = bpy.context.window_manager.keyconfigs
    # Get old keyconfig
    try:
        kc = wmkcs[name.replace(" ", "_")]
    except Exception as er:
        kc = None
    # Remove old keyconfig if exists
    if kc:
        wmkcs.active = kc
        bpy.ops.wm.keyconfig_preset_add(remove_active=True)
    # Create new keyconfig
    bpy.ops.wm.keyconfig_preset_add(name=name)  # and set active
    kc = wmkcs.active
    # Copy all keymaps and keymap items from default keyconfig
    for dkm in wmkcs.default.keymaps:
        km = kc.keymaps.new(
            name=dkm.name,
            space_type=dkm.space_type,
            region_type=dkm.region_type,
            modal=dkm.is_modal
        )
        for kmi in dkm.keymap_items:
            km.keymap_items.new_from_item(kmi)
    return kc


def disableMacOsKeyBindingsInKeyconfig(
    keyconfig,
    excludes=[]
):
    if (platform.system() != 'Darwin'):
        return

    shift = '⇧'
    ctrl = '⌃'
    alt = '⌥'
    cmd = '⌘'
    parsedExcludes = []

    for excludesString in excludes:
        es = excludesString
        es = es.replace('shift', shift)
        es = es.replace('ctrl', ctrl)
        es = es.replace('alt', alt)
        es = es.replace('cmd', cmd)
        parsedExcludes.append(es)

    if keyconfig and keyconfig.keymaps:
        for km in keyconfig.keymaps:
            if km.keymap_items:
                for kmi in km.keymap_items:
                    if kmi.active and kmi.map_type in ['KEYBOARD', 'MOUSE']:
                        kmiString = kmi.to_string()
                        if kmi.oskey and cmd in kmiString:
                            if kmiString not in parsedExcludes:
                                kmi.active = False


def clearAllInactiveKeymapItemsInKeyconfig(keyconfig):
    if keyconfig and keyconfig.keymaps:
        for km in keyconfig.keymaps:
            if km and km.keymap_items:
                for kmi in list(km.keymap_items):
                    if not kmi.active:
                        km.keymap_items.remove(kmi)


def saveAndExportKeyconfig(filename):
    bpy.ops.wm.save_userpref()
    path = bpy.utils.user_resource('SCRIPTS', path="presets")
    filepath = bpy.path.native_pathsep(path + '/keyconfig/' + filename)
    bpy.ops.preferences.keyconfig_export(filepath=filepath, all=True)


def clearAndSaveKeyconfig(keyconfig, filename):
    clearAllInactiveKeymapItemsInKeyconfig(keyconfig)
    saveAndExportKeyconfig(filename)

# Kit


def simplenamespace(bpy_dict):
    obj = SimpleNamespace()
    for attrKey in dir(bpy_dict):
        if not attrKey.startswith("__"):
            setattr(obj, attrKey, getattr(bpy_dict, attrKey))
    return obj


def appendNewActMatToObject(obj, diffuseColor=(1.0, 1.0, 1.0, 1.0), matSlot=None):
    newMat = bpy.data.materials.new("Material")
    newMat.diffuse_color = diffuseColor
    if not matSlot:
        obj.data.materials.append(newMat)
    else:
        matSlot.material = newMat
    obj.active_material = newMat
    return newMat


def getObjectUsersOfMat(mat, col):
    # From https://blender.stackexchange.com/a/19021/179841
    users = []
    for obj in col:
        if isinstance(obj.data, bpy.types.Mesh) and mat.name in obj.data.materials:
            users.append(obj)
    return users


def applyObjectTransformsWithContext(context, obj, transforms=['location', 'rotation', 'scale']):
    with context.temp_override(selected_editable_objects=[obj]):
        bpy.ops.object.transform_apply(
            location='location' in transforms, rotation='rotation' in transforms, scale='scale' in transforms)


def getOutlinerActivatedObjectsFromContext(context):
    selected_ids = context.selected_ids
    return [sel for sel in selected_ids if sel.rna_type.name != 'Collection']


def selectUnhideAllInGroup(group):
    for obj in bpy.data.objects:
        if obj.users_collection == group:
            obj.hide_set(False)
            obj.select_set(True)


def getObjectModeFromContextMode(contextMode):
    if contextMode == 'OBJECT' or 'PENCIL' in contextMode:
        return 'OBJECT'
    elif contextMode.startswith("EDIT"):
        return 'EDIT'
    elif contextMode.startswith("SCULPT"):
        return 'SCULPT'
    elif contextMode.startswith("PAINT"):
        modeParts = contextMode.split('_')
        return modeParts[1] + '_' + modeParts[0]
    else:
        return 'OBJECT'


def setActiveObjectInContext(context, obj, delPrev=False, mode="", tool=""):
    if not obj:
        return

    if not delPrev:
        context.active_object.select_set(False)
    else:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.delete()
    obj.select_set(True)
    context.view_layer.objects.active = obj

    if mode:
        bpy.ops.object.mode_set(mode=mode)

    if tool:
        toolName = "builtin." + tool
        bpy.ops.wm.tool_set_by_id(name=toolName)


def createCurveAndEditInContext(context, name="Curve", inFront=False, tool='draw'):
    curveData = bpy.data.curves.new('Curve', type='CURVE')
    curveData.dimensions = '3D'
    curve = bpy.data.objects.new(name, curveData)
    curve.show_in_front = True if inFront else False
    context.collection.objects.link(curve)

    setActiveObjectInContext(context, curve, mode='EDIT', tool=tool)

    return curve


def setModalTextInContext(context, headerText=None, statusText=None):
    try:
        context.area.header_text_set(text=headerText)
    except Exception as er:
        pass
    try:
        context.workspace.status_text_set(text=statusText)
    except Exception as er:
        pass


def findBpyObjectByName(name, col=None):
    col = bpy.data.objects if col == None else col
    for obj in col:
        if obj.name == name:
            return obj
    return None


def getCurvePointsAll(curve):
    points = []
    for spline in curve.data.splines:
        for point in spline.bezier_points:
            points.append(point)
    return points


def getCurveActivePoint(curve, returnIfActiveLeftOrRight=False):
    for spline in curve.data.splines:
        for point in spline.bezier_points:
            if point.select_control_point:
                return point
            elif returnIfActiveLeftOrRight and (point.select_left_handle or point.select_right_handle):
                return point
    return None


def selectWholeBezierPoint(point, select=True):
    if point:
        point.select_control_point = select
        point.select_left_handle = select
        point.select_right_handle = select


def setCurveCyclic(curve, doCycle):
    for s in curve.data.splines:
        s.use_cyclic_u = doCycle


def moveObjectModifierAtTheEnd(obj, mod):
    modIdx = -1
    if obj.modifiers:
        for i, m in enumerate(obj.modifiers):
            if m.name == mod.name:
                modIdx = i
    if modIdx == -1 or modIdx == len(obj.modifiers) - 1:
        return
    obj.modifiers.move(modIdx, len(obj.modifiers) - 1)


def addTimerForContext(context, time=0.3):
    return context.window_manager.event_timer_add(
        time, window=context.window)


def removeTimerFromContext(context, timer):
    return context.window_manager.event_timer_remove(
        timer) and None if timer else None


def getActiveBrushTextureInContext(context):
    try:
        if context.mode == 'SCULPT':
            return context.tool_settings.sculpt.brush.texture
        elif context.mode == 'PAINT_VERTEX':
            return context.tool_settings.vertex_paint.brush.texture
        elif context.mode == 'PAINT_WEIGHT':
            return context.tool_settings.weight_paint.brush.texture
        elif context.mode == 'PAINT_TEXTURE':
            return context.tool_settings.image_paint.brush.texture
    except Exception as er:
        return None


def setActiveBrushTextureImageInContext(context, image):
    try:
        if context.mode == 'SCULPT':
            context.tool_settings.sculpt.brush.texture.image = image
        elif context.mode == 'PAINT_VERTEX':
            context.tool_settings.vertex_paint.brush.texture.image = image
        elif context.mode == 'PAINT_WEIGHT':
            context.tool_settings.weight_paint.brush.texture.image = image
        elif context.mode == 'PAINT_TEXTURE':
            context.tool_settings.image_paint.brush.texture.image = image
    except Exception as er:
        pass


def createUvTransformer(angle, origin=(0, 0), offset=(0, 0), scale=(1, 1)):
    cos_theta, sin_theta = math.cos(angle), math.sin(angle)
    x0, y0 = origin
    offset_x, offset_y = offset
    scale_x, scale_y = scale

    def xform(point):
        x = (point[0] - x0) * scale_x + offset_x
        y = (point[1] - y0) * scale_y + offset_y
        return (x * cos_theta - y * sin_theta + x0,
                x * sin_theta + y * cos_theta + y0)
    return xform


def isToolSelect(tool):
    return tool in [
        'builtin.select', 'builtin.select_box', 'builtin.select_circle', 'builtin.select_lasso']
