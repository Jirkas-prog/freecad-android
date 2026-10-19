# SPDX-License-Identifier: GPL-3.0-only
"""Install the bundled, pinned FusionFlow modules into this app's private FreeCAD profile."""
import os,sys,shutil,traceback
from pathlib import Path
import FreeCAD as App,FreeCADGui as Gui

try:
    base=Path('/fusionflow')
    mods=Path(App.getUserAppDataDir())/'Mod'
    mods.mkdir(parents=True,exist_ok=True)
    for name in ('FusionFlow','freecad-fusion','OpenTheme'):
        shutil.copytree(base/name,mods/name,dirs_exist_ok=True)
        sys.path.insert(0,str(mods/name))
    Gui.activateWorkbench('PartDesignWorkbench')
    from freecad_fusion import commands,navicube_drag
    commands.register()
    # QCursor.setPos has no physical cursor to recenter on WebAssembly. Keep
    # native face/edge cube clicks and use the viewport's normal touch navigation.
    from fusionflow_setup import configure
    prefs=App.ParamGet('User parameter:BaseApp/Preferences/Mod/FusionFlow')
    if not prefs.GetBool('Configured',False):configure()
    import fusionflow_ui
    fusionflow_ui.install()
    from PySide import QtCore, QtGui, QtWidgets
    # A tablet may alternate between fingers and an attached mouse/trackpad.
    # Store the chosen navigation mode in this app's private FreeCAD profile.
    def set_input_mode(mode):
        style='Gui::GestureNavigationStyle' if mode=='Touch' else 'Gui::RevitNavigationStyle'
        prefs.SetString('AndroidInputMode',mode)
        App.ParamGet('User parameter:BaseApp/Preferences/View').SetString('NavigationStyle',style)
        for name in App.listDocuments():
            gui_doc=Gui.getDocument(name)
            if gui_doc and gui_doc.ActiveView:gui_doc.ActiveView.setNavigationType(style)
        App.saveParameter()
    design=Gui.getMainWindow().findChild(QtWidgets.QToolButton,'DesignButton')
    if design and not getattr(design,'_android_input_menu',None):
        menu=design.menu().addMenu('Input')
        group=QtGui.QActionGroup(menu);group.setExclusive(True)
        for label,mode in [('Touch / pen','Touch'),('Mouse / trackpad','Mouse')]:
            action=menu.addAction(label);action.setCheckable(True);group.addAction(action)
            action.setChecked(prefs.GetString('AndroidInputMode','Touch')==mode)
            action.triggered.connect(lambda checked=False,m=mode:set_input_mode(m))
        design._android_input_menu=menu
    set_input_mode(prefs.GetString('AndroidInputMode','Touch'))
    # External add-on installation and executable FEM solvers are not packaged.
    # The normal modelling workbenches and bundled FusionFlow remain available.
    class OfflineAddonManager:
        def GetResources(self):return {'MenuText':'Add-on Manager (offline edition)'}
        def IsActive(self):return False
        def Activated(self):pass
    Gui.addCommand('Std_AddonMgr',OfflineAddonManager())
    App.ParamGet('User parameter:BaseApp/Preferences/Mod/Start').SetBool('ShowOnStartup',False)
    for area in Gui.getMainWindow().findChildren(QtWidgets.QMdiArea):
        for subwindow in area.subWindowList():
            if subwindow.widget().metaObject().className()=='StartGui::StartView':subwindow.close()
    for dock in Gui.getMainWindow().findChildren(QtWidgets.QDockWidget):
        if dock.objectName() in ('Python console','Report view'):dock.hide()
    Path('/fusionflow-ready.json').write_text('{"ready":true}',encoding='utf-8')
    App.Console.PrintMessage('FusionFlow is ready in the local Android runtime.\n')
except Exception:
    Path('/fusionflow-ready.json').write_text(__import__('json').dumps({'ready':False,'error':traceback.format_exc()}),encoding='utf-8')
    traceback.print_exc()
