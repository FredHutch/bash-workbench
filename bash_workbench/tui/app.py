import npyscreen
import bash_workbench as wb

class WorkbenchApp(npyscreen.NPSAppManaged):
    def onStart(self):
        # Primary display is a tree view of collections and datasets
        self.registerForm(
            "MAIN",
            wb.tui.forms.DatasetExplorer()
        )
