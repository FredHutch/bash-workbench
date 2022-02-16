import npyscreen
import wb_tui

class WorkbenchApp(npyscreen.NPSAppManaged):
    def onStart(self):
        # Primary display is a tree view of collections and datasets
        self.registerForm(
            "MAIN",
            wb_tui.forms.DatasetExplorer()
        )
