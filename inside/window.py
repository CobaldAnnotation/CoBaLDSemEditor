import os
import pickle
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import pyqtSlot
from functools import partial
from inside.reader import Conllu, Wrapper
from inside.dialogues import SaveWarning

SEMSLOTS = pickle.load(open('inside/semslots.bin', 'rb'))
SEMCLASS = pickle.load(open('inside/semclasses.bin', 'rb'))

SEMSLOTVARS = QtWidgets.QCompleter(SEMSLOTS)
SEMCLASSVARS = QtWidgets.QCompleter(SEMCLASS)

SEMSLOTS = set(SEMSLOTS)
SEMCLASS = set(SEMCLASS)

WITHFEATS = '  ID  FORM                     LEMMA                    UPOS  FEATURES                                                                      HEAD  DEPREL         DEPS    '
NOFEATS = '  ID  FORM                     LEMMA                    UPOS  HEAD  DEPREL         DEPS    '

class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.nomorph = True # check morphofeats
        self.data = Conllu() #Wrapper() # empty
        self.filepath = None #path to open conll
        self.sentnumber = 1 # a number for go to button

        self.initUI()
        self.loadsavedsettings()

    def initUI(self):
        # global settings
        self.settings = QtCore.QSettings('CoBaLD', 'CoBaLD Editor') 
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))
        self.resize(self.settings.value("size", QtCore.QSize(1920, 1080))) 
        self.move(self.settings.value("pos", QtCore.QPoint(100, 100))) 
        self.setWindowTitle("CoBaLD Editor")

        # font load
        fontId = QtGui.QFontDatabase.addApplicationFont("inside/design/cour.ttf")
        if fontId < 0:
            print('font not loaded')
        families = QtGui.QFontDatabase.applicationFontFamilies(fontId)
        self.fontsize = 9
        self.monospacefont = QtGui.QFont(families[0], self.fontsize)
        fontId = QtGui.QFontDatabase.addApplicationFont("inside/design/A_STB.ttf")
        if fontId < 0:
            print('font not loaded')
        families = QtGui.QFontDatabase.applicationFontFamilies(fontId)
        self.sentencefont = QtGui.QFont(families[0], 12)

        # create Menu and Toolbar
        self.createActions()
        self.createMenuBar()
        self.createToolBars()

        # main widget
        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)

        # Status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("color: #0a516d; border-top: 1px solid black;")

        # main layout
        self.grid = QtWidgets.QVBoxLayout()
        wid.setLayout(self.grid)

        # Widgets to main layout
        self.numberwid = QtWidgets.QLabel('Sentence №')
        self.numberwid.setFont(self.sentencefont)

        self.textwid = QtWidgets.QPlainTextEdit('Text')
        # self.textwid.setMaximumWidth(1920)
        self.textwid.setMaximumHeight(60)
        self.textwid.setReadOnly(True)
        self.textwid.setStyleSheet("color: #0a516d; border-bottom: 1px solid black;")

        self.translheader = QtWidgets.QLabel('Translation')
        self.translheader.setFont(self.sentencefont)
        self.translwid = QtWidgets.QPlainTextEdit('Translation')
        # self.translwid.setMaximumWidth(1920)
        self.translwid.setReadOnly(True)
        self.translwid.setMaximumHeight(60)
        self.translwid.setStyleSheet("color: #0a516d; border-bottom: 1px solid black;")

        # create column headers

        self.headercolgrid = QtWidgets.QHBoxLayout()
        self.headercols = QtWidgets.QLabel(NOFEATS)
        self.headercols.setFont(self.monospacefont)
        self.headersemslot = QtWidgets.QLabel('SEMSLOT')
        self.headersemslot.setFont(self.monospacefont)
        self.headersemclass = QtWidgets.QLabel('SEMCLASS')
        self.headersemclass.setFont(self.monospacefont)
        self.headercolgrid.addWidget(self.headercols)
        self.headercolgrid.addWidget(self.headersemslot)
        self.headercolgrid.addWidget(self.headersemclass)

        # token widget with layout
        self.tokenwidget = QtWidgets.QWidget()
        self.scrollArea = QtWidgets.QScrollArea(wid)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.tokenwidget)
        # self.scrollArea.setMaximumWidth(1920)
        self.tokens = QtWidgets.QVBoxLayout(self.tokenwidget)

        # compile layout with widgets
        self.grid.addWidget(self.numberwid)
        self.grid.addWidget(self.textwid)
        self.grid.addWidget(self.translheader)
        self.grid.addWidget(self.translwid)
        self.grid.addLayout(self.headercolgrid)
        self.grid.addWidget(self.scrollArea)

    def createActions(self):
        """Actions: Open, Save, Save As and Close. 
        Font size actions are underimplemented - not sure if we need them"""
        self.openAction = QtWidgets.QAction('&Open')
        self.openAction.setText('&Open')
        self.openAction.setShortcut(QtGui.QKeySequence.Open)
        self.openAction.triggered.connect(self.openFile)
        self.openAction.setIcon(QtGui.QIcon('inside/design/openfile.png'))

        self.saveAction = QtWidgets.QAction('&Save')
        self.saveAction.setText('&Save')
        self.saveAction.setShortcut(QtGui.QKeySequence.Save)
        self.saveAction.triggered.connect(self.saveFile)
        self.saveAction.setIcon(QtGui.QIcon('inside/design/save.png'))

        self.saveAsAction = QtWidgets.QAction('&Save As...')
        self.saveAsAction.setText('&Save As...')
        self.saveAsAction.setShortcut(QtGui.QKeySequence('Ctrl+Shift+S'))
        self.saveAsAction.triggered.connect(self.saveNewFile)
        self.saveAsAction.setIcon(QtGui.QIcon('inside/design/saveas.png'))

        self.closeAction = QtWidgets.QAction('&Close')
        self.closeAction.setText('&Close')
        self.closeAction.setShortcut(QtGui.QKeySequence('Ctrl+W'))
        self.closeAction.triggered.connect(self.closeFile)
        self.closeAction.setIcon(QtGui.QIcon('inside/design/close.png')) 

        self.nextAction = QtWidgets.QAction('&Next')
        self.nextAction.setText('&Next')
        self.nextAction.setShortcut(QtGui.QKeySequence('Shift+Enter'))
        self.nextAction.triggered.connect(self.nextsent)
        self.nextAction.setIcon(QtGui.QIcon('inside/design/next.png'))

        self.prevAction = QtWidgets.QAction('&Previous')
        self.prevAction.setText('&Previous')
        self.prevAction.setShortcut(QtGui.QKeySequence('Shift+Backspace'))
        self.prevAction.triggered.connect(self.prevsent)
        self.prevAction.setIcon(QtGui.QIcon('inside/design/prev.png'))

        # may need to use
        self.numberloadAction = QtWidgets.QAction('&Go to')
        self.numberloadAction.setText('&Go to')
        self.numberloadAction.triggered.connect(self.gotosent)
        self.numberloadAction.setIcon(QtGui.QIcon('inside/design/goto.png'))

        self.sizepAction = QtWidgets.QAction('&Font size +')
        self.sizepAction.setText('&Font size +')
        self.sizepAction.setShortcut(QtGui.QKeySequence.ZoomIn)
        self.sizepAction.triggered.connect(self.fontsizeplus)

        self.sizemAction = QtWidgets.QAction('&Font size -')
        self.sizemAction.setText('&Font size -')
        self.sizemAction.setShortcut(QtGui.QKeySequence.ZoomOut)
        self.sizemAction.triggered.connect(self.fontsizeminus)

    def createMenuBar(self):
        """Menu Bar for File"""
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.closeAction)

    def createToolBars(self):
        """Toolbar for navigation"""
        # create widgets for toolbar
        if not self.data.ready:
            # if file not open
            self.gotonumber = QtWidgets.QSpinBox()
            self.gotonumber.setMinimum(0)
            self.gotonumber.setMaximum(0)
        else:
            self.gotonumber = QtWidgets.QSpinBox()
            self.gotonumber.setMinimum(1)
            self.gotonumber.setMaximum(len(self.data))
        self.gotonumber.setFixedWidth(60)
        self.gotonumber.valueChanged.connect(self.gotosentgetnumber) # immediately loads sent - may change
        self.datalength = QtWidgets.QLabel('') # number of sents in file
        self.morphcheck = QtWidgets.QCheckBox('Show morphological features')
        self.morphcheck.stateChanged.connect(self.morphload)

        # create toolbar and add widgets
        MoveToolBar = self.addToolBar("Navigate")
        MoveToolBar.addAction(self.prevAction)
        MoveToolBar.addAction(self.nextAction)
        MoveToolBar.addAction(self.numberloadAction)
        MoveToolBar.addWidget(self.gotonumber)
        MoveToolBar.addWidget(self.datalength)
        MoveToolBar.addWidget(self.morphcheck)

    def prevsent(self):
        """Move to previous sentence"""
        if not self.data.ready:
            return
        if self.data.current != 1: # if current sent is 1, can't move back
            attempt = self.savesent(self.data.current)
            if attempt:
                return
            self.data.current -= 1 
            self.loadsenttogui(self.data.current)

    def nextsent(self):
        """Move to next sentence"""
        if not self.data.ready:
            return
        if self.data.current < len(self.data): # if current sent is last, can't move forward
            attempt = self.savesent(self.data.current)
            if attempt:
                return
            self.data.current += 1
            self.loadsenttogui(self.data.current)

    def gotosentgetnumber(self, sentkey):
        self.sentnumber = sentkey

    def gotosent(self):
        """Jump to sentence by number"""
        if not self.data.ready:
            return
        if self.sentnumber <= len(self.data): # probably useless
            attempt = self.savesent(self.data.current)
            if attempt:
                return
            self.data.current = self.sentnumber
            self.loadsenttogui(self.data.current)

    def morphload(self, checked):
        """Show/hide morphofeats"""
        if checked:
            self.nomorph = False 
            self.headercols.setText(WITHFEATS)
        else:
            self.nomorph = True
            self.headercols.setText(NOFEATS)
        if not self.data.ready: # otherwise we crash
            return
        self.loadsenttogui(self.data.current)

    def loadsenttogui(self, sentkey):
        """Loading sentence to interface"""
        self.gotonumber.setValue(sentkey)
        self.numberwid.setText(f'Sentence № {sentkey}')
        self.textwid.setPlainText(self.data.data[sentkey].text)
        self.translwid.setPlainText(self.data.data[sentkey].translation)
        if self.tokens.count(): # if self.tokens widget is not empty we must clear it
            self.clearLayout(self.tokens)
        # filling self.tokens with new token widgets
        for token in self.data.data[sentkey].tokens:
            tokenlayout = QtWidgets.QHBoxLayout() # a horisontal layout for a token
            # add morphosyntax
            if self.nomorph:
                tokenms = QtWidgets.QLabel(token.nomorphosyntax)
            else:
                tokenms = QtWidgets.QLabel(token.morphosyntax)
            tokenms.setFont(self.monospacefont)
            # add semantics
            tokensemslot = QtWidgets.QLineEdit(token.semslot)
            tokensemslot.setCompleter(SEMSLOTVARS)
            tokensemclass = QtWidgets.QLineEdit(token.semclass)
            tokensemclass.setCompleter(SEMCLASSVARS)

            tokenlayout.addWidget(tokenms)
            tokenlayout.addWidget(tokensemslot)
            tokenlayout.addWidget(tokensemclass)
            self.tokens.addLayout(tokenlayout)
        self.tokens.addStretch() # no spacing
        self.tokens.update()
        self.grid.update()

    def savesent(self, sentkey):
        """Save sentence to Conllu data"""
        for i in range(self.tokens.count() - 1): # last element is stretcher, thus -1
            tokenlayout = self.tokens.itemAt(i) # get current token layout, i must coincide with sentence token indexes
            try:
                # -2 = semslot, -1 = semclass (might just write 1 and 2 respectively)
                semslot = tokenlayout.itemAt(tokenlayout.count() - 2).widget().text()
                semclass = tokenlayout.itemAt(tokenlayout.count() - 1).widget().text()
                if semslot not in SEMSLOTS:
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic slot: {semslot}')
                    return 'INCORRECT'
                if semclass not in SEMCLASS:
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic class: {semclass}')
                    return 'INCORRECT'
                self.data.data[sentkey].tokens[i].semslot = semslot
                self.data.data[sentkey].tokens[i].semclass = semclass
            except IndexError: # for testing purposes, normally shouldn't occur
                print('Self tokens count', self.tokens.count(), 'total tokens', len(self.data.data[sentkey].tokens), i)
                print(self.data.data[sentkey].text)
                raise

    def clearLayout(self, layout):
        """Clear tokens from layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item is not None:
                    if type(item) != QtWidgets.QSpacerItem: # don't need really
                        while item.count():
                            subitem = item.takeAt(0)
                            widget = subitem.widget()
                            if widget is not None:
                                widget.setParent(None)
                    layout.removeItem(item)
                    del item # may be redundant
        
    def openFile(self):
        """Open file function: gets filename"""
        filename = QtWidgets.QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                               "", "CONLL-U files (*.conllu);;All Files (*)")
        filepath = filename[0]
        if filepath and filepath.endswith('conllu'): # check if we open a conllu
            self.loadFile(filepath)
        else:
            QtWidgets.QMessageBox.about(self, 'Error', 'File cannot be opened!')

    def loadFile(self, filepath):
        """Load file - used in open and in loadsaved"""
        filename = os.path.splitext(os.path.basename(filepath))[0]
        new = Conllu() #filler
        res = new.read(filepath) # we must try to read the file and get possible errors
        if res == 'BAD':
            QtWidgets.QMessageBox.about(self, 'Error', 'File unreadable! Something wrong with tokens')
            return
        if res == 'EMPTY':
            QtWidgets.QMessageBox.about(self, 'Error', 'No sentences found in file! May be corrupt')
            return
        # if everything is okay
        self.filepath = filepath
        self.setWindowTitle(f"CoBaLD Editor - {filename}")
        self.data = new
        # go to settings
        self.gotonumber.setMinimum(1)
        self.gotonumber.setMaximum(len(self.data))
        self.datalength.setText(f"  of {len(self.data)}  ")

        self.statusBar.showMessage('File loaded', 3000)
        self.loadsenttogui(self.data.current) # show sent

    def saveFile(self):
        """Save existing file to hard drive - actually re-writes the whole file"""
        savewarn = SaveWarning(filename=os.path.splitext(os.path.basename(self.filepath))[0])
        if savewarn.exec():
            attempt = self.savesent(self.data.current)
            if attempt:
                return # save currently open sent to Conllu data
            self.data.save(self.filepath)
            self.statusBar.showMessage('File saved', 3000)

    def saveNewFile(self):
        """Save to new file - conllu extension only"""
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save file", '', "CONLL-U (*.conllu)")
        if filename:
            attempt = self.savesent(self.data.current)
            if attempt:
                return # save currently open sent to Conllu data
            self.data.save(filename[0])
            # change current settings to new file
            self.filepath = filename[0]
            self.setWindowTitle(f"CoBaLD Editor - {os.path.splitext(os.path.basename(self.filepath))[0]}")
            self.statusBar.showMessage('File saved', 3000)

    def closeFile(self):
        """Close current file and empty settings"""
        self.data = Conllu()
        self.textwid.setPlainText('Text')
        self.translwid.setPlainText('Translation')
        self.datalength.setText('')
        self.clearLayout(self.tokens)
        self.tokens.update()
        self.filepath = None 

    def fontsizeplus(self):
        '''increase font size'''
        self.fontsize += 1

    def fontsizeminus(self):
        '''decrease font size'''
        self.fontsize -= 1

    def loadsavedsettings(self):
        """Load from saved settings"""
        if os.path.exists('inside/settings.bin'):
            settings = pickle.load(open('inside/settings.bin', 'rb'))
            # morphofeats on/off
            self.nomorph = settings['nomorph']
            if not self.nomorph:
                self.morphcheck.setChecked(True)
            # try to open file
            if settings['lastfile'] and os.path.exists(settings['lastfile']):
                self.loadFile(settings['lastfile'])
                self.data.current = settings['lastcurrent']
                if self.data:
                    self.loadsenttogui(self.data.current)
                else:
                    self.filepath = None

    def closeEvent(self, e):
        """Close app and save settings"""
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        settings = {'lastfile': self.filepath, 'lastcurrent': self.data.current, 'nomorph': self.nomorph}
        pickle.dump(settings, open('inside/settings.bin', 'wb'))
        e.accept()