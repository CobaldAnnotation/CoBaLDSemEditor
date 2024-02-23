from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel
from PyQt5 import QtGui

class SaveWarning(QDialog):
    """Window for warning about re-writing current file"""
    def __init__(self, filename):
        super().__init__()

        self.setWindowTitle("CoBaLD Editor")
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(f"Are you sure you want to rewrite {filename}.conllu?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)