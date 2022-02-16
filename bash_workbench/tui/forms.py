import npyscreen

class DatasetExplorer(npyscreen.Form):
    def create(self):
        self.tree = self.add(
            npyscreen.MLTreeMultiSelect,
            name = "Text:",
            value= "Hellow World!"
        )

        treedata = npyscreen.NPSTreeData(
            content="root",
            selectable=True,
            ignoreRoot=False
        )
        c1 = treedata.newChild(
            content="Child 1",
            selectable=True,
            selected=False
        )

        self.tree.values = treedata

    def afterEditing(self):
        self.parentApp.setNextForm(None)