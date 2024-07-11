from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QUndoCommand, QLineEdit, QWidget, QPushButton, QHBoxLayout
from PyQt5 import QtGui, QtCore

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

class DeleteWarning(QDialog):
    """Window for warning about deleting non-null int-indexed tokens"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CoBaLD Editor")
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        message = QLabel(f"Are you sure you want to delete this token? It cannot be undone!")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class CorrectFieldWarning(QDialog):
    """Window for warning about possibly incorrect fields"""
    def __init__(self, category, text):
        super().__init__()
        self.setWindowTitle(category)
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        message = QLabel(f"Please confirm this annotation is correct: {text}")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class StoreCommand(QUndoCommand):
    """For undo/redo purposes: restores initial text"""
    def __init__(self, field, text):
        QUndoCommand.__init__(self)
        self.field = field
        self.text = text

    def undo(self):
        self.field.setText(self.field.init_text)
     
    def redo(self):
        self.field.setText(self.text)

class CustomQLineEdit(QLineEdit):
    """Stores initial text for undo/redo"""
    def __init__(self, parent):
        super().__init__(parent)
        self.init_text = self.text()

class AddRemoveTokenWindow(QWidget):
    '''A Window for getting the token index from user'''
    choice = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Enter token index')
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))
        self.liner = QLineEdit(self)
        self.button = QPushButton("&Default")
        self.button.setText('OK')
        self.button.clicked.connect(self.ok)
        self.button.setDefault(True)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.liner)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def ok(self):
        self.choice.emit(self.liner.text())
        self.close()