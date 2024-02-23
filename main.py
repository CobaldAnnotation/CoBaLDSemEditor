import sys
import PyQt5.QtWidgets as QtWidgets
from PyQt5 import QtGui
from inside.window import Window

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = Window()

    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()