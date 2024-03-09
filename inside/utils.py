from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QUndoCommand, QLineEdit
from PyQt5 import QtGui

class RestoreWarning(QDialog):
    """Window for warning about resetting annotation"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CoBaLD Editor")
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        message = QLabel(f"Are you sure you want to reset annotation? It cannot be undone!")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class StoreCommand(QUndoCommand):
    def __init__(self, field, text):
        QUndoCommand.__init__(self)
        self.field = field
        self.text = text

    def undo(self):
        self.field.setText(self.field.init_text)
     
    def redo(self):
        self.field.setText(self.text)

class CustomQLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_text = self.text()