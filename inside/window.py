import os
import pickle
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import pyqtSlot
from functools import partial
from inside.reader import Conllu
from inside.utils import SaveWarning, RestoreWarning, StoreCommand, CustomQLineEdit
from googletrans import Translator

SEMSLOTS = pickle.load(open('inside/semslots.bin', 'rb'))
SEMCLASS = pickle.load(open('inside/semclasses.bin', 'rb'))

SEMSLOTVARS = QtWidgets.QCompleter(SEMSLOTS)
SEMCLASSVARS = QtWidgets.QCompleter(SEMCLASS)

SEMSLOTS = set(SEMSLOTS)
SEMCLASS = set(SEMCLASS)

WITHFEATS = '  ID  FORM                     LEMMA                    UPOS  FEATURES                                                                      HEAD  DEPREL         DEPS    '
NOFEATS = '  ID  FORM                     LEMMA                    UPOS  HEAD  DEPREL         DEPS    '

LANGS = {'Hungarian': 'hu', 'Serbian': 'sr', 'Russian': 'ru', 'English': 'en', 'Turkish': 'tr', 'Czech': 'cs'}

class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.nomorph = True # check morphofeats
        self.data = Conllu() #Wrapper() # empty
        self.filepath = None #path to open project
        self.sentnumber = 1 # a number for go to button
        self.translator = Translator()

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
        self.undoStack = QtWidgets.QUndoStack()
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

        # comment window
        self.commentTitle = QtWidgets.QLabel('Comments')
        self.commentTitle.setFont(self.sentencefont)
        self.commentArea = QtWidgets.QPlainTextEdit()
        self.commentArea.setMaximumHeight(120)

        # compile layout with widgets
        self.grid.addWidget(self.numberwid)
        self.grid.addWidget(self.textwid)
        self.grid.addWidget(self.translheader)
        self.grid.addWidget(self.translwid)
        self.grid.addLayout(self.headercolgrid)
        self.grid.addWidget(self.scrollArea)
        self.grid.addWidget(self.commentTitle)
        self.grid.addWidget(self.commentArea)

    def createActions(self):
        """Actions: Open, Save, Save As and Close. 
        Font size actions are underimplemented - not sure if we need them"""
        self.newAction = QtWidgets.QAction('&New Project')
        self.newAction.setText('&New Project')
        self.newAction.setShortcut(QtGui.QKeySequence.New)
        self.newAction.triggered.connect(self.newProject)
        self.newAction.setIcon(QtGui.QIcon('inside/design/new.png'))

        self.openAction = QtWidgets.QAction('&Open')
        self.openAction.setText('&Open')
        self.openAction.setShortcut(QtGui.QKeySequence.Open)
        self.openAction.triggered.connect(self.openFile)
        self.openAction.setIcon(QtGui.QIcon('inside/design/openfile.png'))

        self.importAction = QtWidgets.QAction('&Import CONLL-U')
        self.importAction.setText('&Import CONLL-U')
        self.importAction.triggered.connect(self.importConll)
        self.importAction.setIcon(QtGui.QIcon('inside/design/import.png'))

        self.exportAction = QtWidgets.QAction('&Export CONLL-U')
        self.exportAction.setText('&Export CONLL-U')
        self.exportAction.triggered.connect(self.exportConll)
        self.exportAction.setIcon(QtGui.QIcon('inside/design/export.png'))

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

        self.undoAction = self.undoStack.createUndoAction(self, self.tr("&Undo"))
        self.undoAction.setShortcut(QtGui.QKeySequence.Undo)
        self.undoAction.setIcon(QtGui.QIcon('inside/design/undo.png'))
        self.redoAction = self.undoStack.createRedoAction(self, self.tr("&Redo"))
        self.redoAction.setShortcut(QtGui.QKeySequence.Redo)
        self.redoAction.setIcon(QtGui.QIcon('inside/design/redo.png'))

        self.restoreAction = QtWidgets.QAction('&Reset Sentence')
        self.restoreAction.setText('&Reset Sentence')
        self.restoreAction.triggered.connect(self.restoresent)
        self.restoreAction.setIcon(QtGui.QIcon('inside/design/restore.png'))

        self.translAction = QtWidgets.QAction('&Make Translation')
        self.translAction.setText('&Make Translation')
        self.translAction.triggered.connect(self.translate)
        self.translAction.setIcon(QtGui.QIcon('inside/design/translate.png'))

    def createMenuBar(self):
        """Menu Bar for File"""
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.importAction)
        fileMenu.addAction(self.exportAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.closeAction)
        editMenu = menuBar.addMenu('&Edit')
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)

    def createToolBars(self):
        """Toolbar for navigation"""
        # create widgets for toolbars
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
        self.srclang = QtWidgets.QComboBox()
        self.srclang.insertItems(1, list(LANGS.keys()))
        self.transldir = QtWidgets.QLabel('Label')
        self.transldir.setPixmap(QtGui.QPixmap("inside/design/transdir.png"))
        self.transldir.resize(32, 32)
        self.destlang = QtWidgets.QComboBox()
        self.destlang.insertItems(1, list(LANGS.keys()))
        self.destlang.setCurrentIndex(3)
        self.checkedsent = QtWidgets.QCheckBox('Checked')
        self.checkedsent.stateChanged.connect(self.setcheckedsent)

        # create toolbars and add widgets
        UndoRedoBar = self.addToolBar("Edit")
        UndoRedoBar.addAction(self.undoAction)
        UndoRedoBar.addAction(self.redoAction)
        UndoRedoBar.addAction(self.restoreAction)
        UndoRedoBar.addWidget(self.checkedsent)

        MoveToolBar = self.addToolBar("Navigate")
        MoveToolBar.addAction(self.prevAction)
        MoveToolBar.addAction(self.nextAction)
        MoveToolBar.addAction(self.numberloadAction)
        MoveToolBar.addWidget(self.gotonumber)
        MoveToolBar.addWidget(self.datalength)

        ViewToolBar = self.addToolBar("View")
        ViewToolBar.addWidget(self.morphcheck)
        ViewToolBar.addWidget(self.srclang)
        ViewToolBar.addWidget(self.transldir)
        ViewToolBar.addWidget(self.destlang)
        ViewToolBar.addAction(self.translAction)

    def translate(self):
        if self.data.hastranslations:
            return
        try:
            trans = self.translator.translate(self.textwid.toPlainText(), src=self.srclang.currentText(), dest=self.destlang.currentText())
            self.translwid.setPlainText(trans.text)
            self.data.data[self.data.current].translation = trans.text
        except Exception:
            QtWidgets.QMessageBox.about(self, 'Error', "Google Translate doesn't respond")
            return
    
    def setcheckedsent(self, checked):
        "Mark sent as checked"
        if checked and len(self.data) > 0:
            self.data.data[self.data.current].checked = True 
        elif len(self.data) > 0:
            self.data.data[self.data.current].checked = False

    def restoresent(self):
        """Restore initial markup"""
        if not self.data.ready:
            return   
        warn = RestoreWarning()
        if warn.exec():
            self.loadsenttogui(self.data.current)

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
        if self.data.data[sentkey].checked:
            self.checkedsent.setChecked(True)
        else:
            self.checkedsent.setChecked(False)
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
            tokensemslot = CustomQLineEdit(token.semslot)
            tokensemslot.editingFinished.connect(self.storeFieldText)
            tokensemslot.setCompleter(SEMSLOTVARS)
            tokensemclass = CustomQLineEdit(token.semclass)
            tokensemclass.editingFinished.connect(self.storeFieldText)
            tokensemclass.setCompleter(SEMCLASSVARS)

            tokenlayout.addWidget(tokenms)
            tokenlayout.addWidget(tokensemslot)
            tokenlayout.addWidget(tokensemclass)
            self.tokens.addLayout(tokenlayout)
        self.tokens.addStretch() # no spacing
        self.tokens.update()
        self.grid.update()
        self.commentArea.setPlainText(self.data.data[sentkey].comment)

    def savesent(self, sentkey):
        """Save sentence to Conllu data"""
        for i in range(self.tokens.count() - 1): # last element is stretcher, thus -1
            tokenlayout = self.tokens.itemAt(i) # get current token layout, i must coincide with sentence token indexes
            try:
                # -2 = semslot, -1 = semclass (might just write 1 and 2 respectively)
                semslot = tokenlayout.itemAt(tokenlayout.count() - 2).widget().text()
                semclass = tokenlayout.itemAt(tokenlayout.count() - 1).widget().text()
                if semslot not in SEMSLOTS:
                    tokenlayout.itemAt(tokenlayout.count() - 2).widget().setText('INCORRECT')
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic slot: {semslot}')
                    return f'!!!{semslot}'
                if semclass not in SEMCLASS:
                    tokenlayout.itemAt(tokenlayout.count() - 1).widget().setText('INCORRECT')
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic class: {semclass}')
                    return f'!!!{semclass}'
                self.data.data[sentkey].tokens[i].semslot = semslot
                self.data.data[sentkey].tokens[i].semclass = semclass
            except IndexError: # for testing purposes, normally shouldn't occur
                print('Self tokens count', self.tokens.count(), 'total tokens', len(self.data.data[sentkey].tokens), i)
                print(self.data.data[sentkey].text)
                raise
        self.data.data[sentkey].comment = self.commentArea.toPlainText()
        self.undoStack.clear() # empty undo stack

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
        
    def newProject(self):
        """Create new empty project"""
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "New file", '', "CoBaLD Files (*.cobald)")
        if filename:
            filepath = filename[0]
            self.filepath = filepath 
            self.data = Conllu()
            self.sentnumber = 1

    def openFile(self):
        """Open file function: gets filename"""
        filename = QtWidgets.QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                               "", "CoBaLD Files (*.cobald)")
        filepath = filename[0]
        if not filepath:
            return
        if filepath and filepath.endswith('cobald'): # check if we open a cobald project
            self.loadFile(filepath)
        else:
            QtWidgets.QMessageBox.about(self, 'Error', 'File cannot be opened!')

    def loadFile(self, filepath):
        """Load project file - used in open and in loadsaved"""
        self.data.load(filepath)
        self.filepath = filepath
        filename = os.path.splitext(os.path.basename(filepath))[0]
        self.setWindowTitle(f"CoBaLD Editor - {filename}")
        # go to settings
        if self.data.ready:
            self.gotonumber.setMinimum(1)
            self.gotonumber.setMaximum(len(self.data))
            self.datalength.setText(f"  of {len(self.data)}  ")
            self.loadsenttogui(self.data.current) # show sent

        self.statusBar.showMessage('Project loaded', 3000)

    def importConll(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                               "", "CONLL-U Files (*.conllu)")
        filepath = filename[0]
        if not filepath:
            return
        if filepath and filepath.endswith('conllu'):
            attempt = self.data.read(filepath)
            if attempt == 'BAD':
                QtWidgets.QMessageBox.about(self, 'Error', 'Something is wrong with the tokens!')
            elif attempt == 'EMPTY':
                QtWidgets.QMessageBox.about(self, 'Error', 'File seems to be empty!')
            else:
                self.statusBar.showMessage('CONLL-U loaded', 3000)
                self.loadsenttogui(self.data.current)
        else:
            QtWidgets.QMessageBox.about(self, 'Error', 'File cannot be opened!')

    def saveFile(self):
        """Save existing project to hard drive"""
        attempt = self.savesent(self.data.current)
        if attempt:
            return # save currently open sent to Conllu data
        self.data.save(self.filepath)
        self.statusBar.showMessage('Project saved', 3000)

    def saveNewFile(self):
        """Save to new file - conllu extension only"""
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save file", '', "CoBaLD Files (*.cobald)")
        if filename:
            attempt = self.savesent(self.data.current)
            if attempt:
                return # save currently open sent to Conllu data
            self.data.save(filename[0])
            # change current settings to new file
            self.filepath = filename[0]
            self.setWindowTitle(f"CoBaLD Editor - {os.path.splitext(os.path.basename(self.filepath))[0]}")
            self.statusBar.showMessage('Project saved', 3000)

    def exportConll(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export CONLL-U", '', "CONLL-U files (*.conllu)")
        if filename:
            self.data.write_conllu(filename[0])
        self.statusBar.showMessage('CONLL-U exported', 3000)

    def closeFile(self):
        """Close current file and empty settings"""
        self.data = Conllu()
        self.textwid.setPlainText('Text')
        self.translwid.setPlainText('Translation')
        self.datalength.setText('')
        self.clearLayout(self.tokens)
        self.tokens.update()
        self.filepath = None 
        self.checkedsent.setChecked(False)

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
                self.data.current = settings['lastcurrent']
                self.loadFile(settings['lastfile'])
            if settings.get('srclang') and settings.get('destlang'):
                self.srclang.setCurrentText(settings['srclang'])
                self.destlang.setCurrentText(settings['destlang'])

    def storeFieldText(self):
        command = StoreCommand(self.sender(), self.sender().text())
        self.undoStack.push(command)

    def closeEvent(self, e):
        """Close app and save settings"""
        self.data.save(self.filepath)
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        settings = {'lastfile': self.filepath, 'lastcurrent': self.data.current, 'nomorph': self.nomorph, 'srclang': self.srclang.currentText(), 'destlang': self.destlang.currentText()}
        pickle.dump(settings, open('inside/settings.bin', 'wb'))
        e.accept()