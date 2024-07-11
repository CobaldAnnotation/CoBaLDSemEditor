import os
import re
import pickle
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import pyqtSlot
from inside.reader import Conllu, Token
from inside.utils import RestoreWarning, StoreCommand, CustomQLineEdit, CorrectFieldWarning, AddRemoveTokenWindow, DeleteWarning
from googletrans import Translator

# Things for checking and auto-completion of fields
SEMSLOTS = pickle.load(open('inside/semslots.bin', 'rb'))
SEMCLASS = pickle.load(open('inside/semclasses.bin', 'rb'))
DEPRELS = pickle.load(open('inside/deprel.bin', 'rb'))
FEATS = pickle.load(open('inside/feats.bin', 'rb'))
POSLIST = pickle.load(open('inside/upos.bin', 'rb'))

SEMSLOTVARS = QtWidgets.QCompleter(SEMSLOTS)
SEMCLASSVARS = QtWidgets.QCompleter(SEMCLASS)
DEPRELCOMPL = QtWidgets.QCompleter(DEPRELS)
POSCOMPL = QtWidgets.QCompleter(POSLIST)

SEMSLOTS = set(SEMSLOTS)
SEMCLASS = set(SEMCLASS)

# Stupid lazy me
WITHFEATS = '  ID  FORM               LEMMA                   UPOS  FEATURES                                                      HEAD DEPREL       DEPS           '
NOFEATS = '  ID  FORM               LEMMA                   UPOS  HEAD DEPREL      DEPS            '

# Can add new languages for translation support
LANGS = {'Hungarian': 'hu', 'Serbian': 'sr', 'Russian': 'ru', 'English': 'en', 'Turkish': 'tr', 'Czech': 'cs', 'Bulgarian': 'bg'}

class Window(QtWidgets.QMainWindow):
    """
    Main window class
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.nomorph = True # check morphofeats - if True, show them in GUI
        self.data = Conllu() # must create an empty conllu instance, will be replaced later
        self.filepath = None # path to open project
        self.sentnumber = 1 # a number for go to button
        self.translator = Translator()

        self.initUI()
        self.onload = True # some костыль
        self.loadsavedsettings()

    def initUI(self):
        # global settings
        self.settings = QtCore.QSettings('CoBaLD', 'CoBaLD Editor') 
        self.setWindowIcon(QtGui.QIcon('inside/design/main.png'))
        self.resize(self.settings.value("size", QtCore.QSize(1920, 1080))) 
        self.move(self.settings.value("pos", QtCore.QPoint(100, 100))) 
        self.setWindowTitle("CoBaLD Editor")

        # font load - can cause troubles on Ubuntu
        fontId = QtGui.QFontDatabase.addApplicationFont("inside/design/cour.ttf")
        if fontId < 0:
            print('font not loaded')
        families = QtGui.QFontDatabase.applicationFontFamilies(fontId)
        self.fontsize = 9
        self.monospacefont = QtGui.QFont(families[0], self.fontsize)
        fontId = QtGui.QFontDatabase.addApplicationFont("inside/design/A_STB.ttf")
        if fontId < 0:
            print('font not loaded')
            self.sentencefont = None 
        else:
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
        if self.sentencefont:
            self.numberwid.setFont(self.sentencefont)

        self.textwid = QtWidgets.QPlainTextEdit('Text')
        self.textwid.setMaximumHeight(60)
        self.textwid.setReadOnly(True)
        self.textwid.setStyleSheet("color: #0a516d; border-bottom: 1px solid black;")

        self.translheader = QtWidgets.QLabel('Translation')
        if self.sentencefont:
            self.translheader.setFont(self.sentencefont)
        self.translwid = QtWidgets.QPlainTextEdit('Translation')
        self.translwid.setReadOnly(True)
        self.translwid.setMaximumHeight(60)
        self.translwid.setStyleSheet("color: #0a516d; border-bottom: 1px solid black;")

        # create column headers
        self.headercolgrid = QtWidgets.QHBoxLayout()
        self.createcolumnheaders()

        # token widget with layout
        self.tokenwidget = QtWidgets.QWidget()
        self.scrollArea = QtWidgets.QScrollArea(wid)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.tokenwidget)
        self.tokens = QtWidgets.QVBoxLayout(self.tokenwidget)

        # comment window
        self.commentTitle = QtWidgets.QLabel('Comments')
        if self.sentencefont:
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

    def createcolumnheaders(self):
        # create column headers
        self.idxform = QtWidgets.QLabel("  ID\tFORM")
        self.idxform.setFixedWidth(300)
        self.lemmaheader = QtWidgets.QLabel("LEMMA")
        self.lemmaheader.setFixedWidth(300)
        self.uposheader = QtWidgets.QLabel("UPOS")
        self.uposheader.setFixedWidth(75)
        if not self.nomorph:
            self.featsheader = QtWidgets.QLabel("FEATS")
        self.headheader = QtWidgets.QLabel("HEAD")
        self.headheader.setFixedWidth(50)
        self.deprelheader = QtWidgets.QLabel("DEPREL")
        self.deprelheader.setFixedWidth(150)
        self.depsheader = QtWidgets.QLabel("DEPS")
        self.depsheader.setFixedWidth(200)
        self.headersemslot = QtWidgets.QLabel('SEMSLOT')
        self.headersemslot.setFont(self.monospacefont)
        self.headersemclass = QtWidgets.QLabel('SEMCLASS')
        self.headersemclass.setFont(self.monospacefont)
        self.headercolgrid.addWidget(self.idxform)
        self.headercolgrid.addWidget(self.lemmaheader)
        self.headercolgrid.addWidget(self.uposheader)
        if not self.nomorph:
            self.headercolgrid.addWidget(self.featsheader)
        self.headercolgrid.addWidget(self.headheader)
        self.headercolgrid.addWidget(self.deprelheader)
        self.headercolgrid.addWidget(self.depsheader)
        self.headercolgrid.addWidget(self.headersemslot)
        self.headercolgrid.addWidget(self.headersemclass)

    def createActions(self):
        """
        Actions: New project, Open project, Import conllu,
        Export conllu, Save project, Save as, Close
        Undo, redo, navigation, translation
        """
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

        self.nextuncheckedAction = QtWidgets.QAction('&First unchecked')
        self.nextuncheckedAction.setText('&First Unchecked')
        self.nextuncheckedAction.triggered.connect(self.nextuncheckedsent)
        self.nextuncheckedAction.setIcon(QtGui.QIcon('inside/design/nextunch.png'))

        self.prevAction = QtWidgets.QAction('&Previous')
        self.prevAction.setText('&Previous')
        self.prevAction.setShortcut(QtGui.QKeySequence('Shift+Backspace'))
        self.prevAction.triggered.connect(self.prevsent)
        self.prevAction.setIcon(QtGui.QIcon('inside/design/prev.png'))

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

        self.addtoken = QtWidgets.QAction('&Add token at...')
        self.addtoken.setText('&Add token at...')
        self.addtoken.triggered.connect(self.addtokenat)

        self.removetoken = QtWidgets.QAction('&Remove token...')
        self.removetoken.setText('&Remove token...')
        self.removetoken.triggered.connect(self.deltoken)

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
        self.gotonumber.valueChanged.connect(self.gotosentgetnumber)
        self.gotonumber.editingFinished.connect(self.gotoOnEnter)
        self.datalength = QtWidgets.QLabel() # number of sents in file
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
        MoveToolBar.addAction(self.nextuncheckedAction)
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
        """Get google translations"""
        if self.data.hastranslations: # not to overwrite existing translations in original conllu
            return
        try:
            trans = self.translator.translate(self.textwid.toPlainText(), src=self.srclang.currentText(), dest=self.destlang.currentText())
            self.translwid.setPlainText(trans.text)
            self.data.data[self.data.current].translation = trans.text
        except Exception:
            QtWidgets.QMessageBox.about(self, 'Error', "Google Translate doesn't respond")
            return
    
    def addtokenat(self):
        """Get index to add a token at it"""
        self.tokenindexwindow = AddRemoveTokenWindow()
        self.tokenindexwindow.show()
        # received index, adding
        self.tokenindexwindow.choice.connect(self.receive_index_foradd)

    def deltoken(self):
        """
        Get index to remove a token with that index: 
        if there are two tokens with the same index, 
        the first one will be deleted
        """
        self.tokenindexwindow = AddRemoveTokenWindow()
        self.tokenindexwindow.show()
        self.tokenindexwindow.choice.connect(self.receive_index_fordel) 

    @pyqtSlot(str)
    def receive_index_fordel(self, choice):
        """Delete token with chosen index"""
        if not ('.' in choice or choice.isdigit()):
            # We check what was entered - only 1.1 or 1 types allowed
            QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect index: {choice}')
            return
        # we find the needed token - iterating because idxs don't necessarily coincide with python list indexes
        # we need i index in order to re-numerate the rest of the tokens later
        for i, token in enumerate(self.data.data[self.data.current].tokens):
            if token.idx == choice:
                # if we try to delete a normal token with no . in index 
                # then maybe it's not what we want
                if '.' not in choice and token.form != '#NULL':
                    msg = DeleteWarning()
                    if not msg.exec():
                        return
                # otherwise delete
                del self.data.data[self.data.current].tokens[i]
                # if it's not 1.1 type token, then we have to re-numerate indexes and heads 
                if choice.isdigit():
                    # i - 1 states that we don't need to re-numerate anything before our deleted token
                    # -1 means step direction
                    self.renumerate(i - 1, -1)
                break
        self.loadsenttogui(self.data.current)

    @pyqtSlot(str)
    def receive_index_foradd(self, choice):
        """
        Add new token at a chosen index
        """
        if not ('.' in choice or choice.isdigit()):
            # We check what was entered - only 1.1 or 1 types allowed
            QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect index: {choice}')
            return
        # create new empty token, we only fill index and form as they can't be corrected
        # we presume that one would only create a #NULL token
        # although there is an option to create a token with int-index... oops
        newtoken = Token('\t'.join('_' * 12))
        newtoken.idx = choice
        newtoken.form = '#NULL'
        choice = float(choice)
        hyphen = False # a костыль for cases when we try to add a token right before \d-\d type
        for i, token in enumerate(self.data.data[self.data.current].tokens):
            if '-' in token.idx: 
                continue
            if float(token.idx) > choice:
                # if we add a \d.\d type token - position should be after \d token
                if i > 0 and round(choice) != choice:
                    self.data.data[self.data.current].tokens.insert(i, newtoken)
                # if we add an int-indexed token - position should be before idx token
                elif i > 0 and round(choice) == choice:
                    if '-' in self.data.data[self.data.current].tokens[i - 1].idx:
                        self.data.data[self.data.current].tokens.insert(i - 2, newtoken)
                        hyphen = True
                    else:
                        self.data.data[self.data.current].tokens.insert(i - 1, newtoken)
                else:
                    # probably wouldn't happen, but in case if we want to add a 0.1 token
                    self.data.data[self.data.current].tokens = [newtoken] + self.data.data[self.data.current].tokens
                break
        # if we add an int-indexed token, we have to re-numerate damn everything
        if round(choice) == choice:
            if hyphen:
                self.renumerate(i - 2, 1)
            else:
                self.renumerate(i - 1, 1)
        self.loadsenttogui(self.data.current)

    def renumerate(self, i, step):
        """
        Re-numerate method: re-numerates indexes and calls a method to re-numerate heads
        """
        # we choose if we deleted or added: the direction should change accordingly in order to re-numerate correctly
        if step < 0:
            r = range(i + 1, len(self.data.data[self.data.current].tokens))
        else:
            r = range(len(self.data.data[self.data.current].tokens) - 1, i, -1)
        for j in r:
            # just for shortening reasons
            token = self.data.data[self.data.current].tokens[j]
            # if we have a \d.\d token
            if '.' in token.idx:
                old = token.idx
                token.idx = str(float(token.idx) + step)
                self.renumerateheads(old, token.idx)
            # if we have a \d-\d token
            elif '-' in token.idx:
                left, right = token.idx.split('-')
                left = int(left) + step
                right = int(right) + step
                token.idx = f"{left}-{right}"
            # if we have a normal int-indexed token
            else:
                old = token.idx
                token.idx = str(int(token.idx) + step)
                self.renumerateheads(old, token.idx)

    def renumerateheads(self, idx, newidx):
        """
        Method to re-numerate heads both in head and deps columns
        """
        for token in self.data.data[self.data.current].tokens:
            if token.head == idx:
                token.head = newidx 
            if idx in re.findall('(\d+|\d+\.\d+):', token.deps):
                # a possible break for cases like idx == 1, we may replace 11:
                # but probably won't happen
                token.deps = token.deps.replace(f"{idx}:", f"{newidx}:")

    def setcheckedsent(self, checked):
        """Mark sent as checked"""
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

    def nextuncheckedsent(self):
        """Move to the first unchecked sent by searching through data"""
        if not self.data.ready:
            return
        for key, sent in self.data.data.items():
            if not sent.checked:
                attempt = self.savesent(self.data.current)
                if attempt:
                    return
                self.data.current = key 
                break
        self.loadsenttogui(self.data.current)

    def gotosentgetnumber(self, sentkey):
        """Just to get sentnumber from qspinbox"""
        self.sentnumber = sentkey

    @pyqtSlot()
    def gotoOnEnter(self):
        """Works on enter, sends us to the sentence with the number in the qspinbox"""
        print(self.gotonumber.value())
        self.gotosent()

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
        if not self.onload:
            self.savesent(self.data.current)
        else:
            self.onload = False
        if checked:
            self.nomorph = False 
            for i in reversed(range(self.headercolgrid.count())): 
                self.headercolgrid.itemAt(i).widget().setParent(None)
            self.createcolumnheaders()
            # self.headercols.setText(WITHFEATS)
        else:
            self.nomorph = True
            for i in reversed(range(self.headercolgrid.count())): 
                self.headercolgrid.itemAt(i).widget().setParent(None)
            self.createcolumnheaders()
            # self.headercols.setText(NOFEATS)
        if not self.data.ready: # otherwise we crash
            return
        self.loadsenttogui(self.data.current)

    def loadsenttogui(self, sentkey):
        """Loading sentence to interface"""
        self.gotonumber.setValue(sentkey) # update qspinbox
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
            # morphosyntax widgets
            tokeninfo = QtWidgets.QLabel(f"{token.idx}\t{token.form}")
            # add context menu to add\remove tokens
            tokeninfo.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
            tokeninfo.addAction(self.addtoken)
            tokeninfo.addAction(self.removetoken)
            tokeninfo.setFixedWidth(300)
            tokenlemma = CustomQLineEdit(token.lemma)
            tokenlemma.setFixedWidth(300)
            tokenlemma.editingFinished.connect(self.storeFieldText)
            tokenpos = CustomQLineEdit(token.upos)
            tokenpos.setFixedWidth(75)
            tokenpos.setCompleter(POSCOMPL)
            tokenpos.editingFinished.connect(self.storeFieldText)
            tokenfeats = CustomQLineEdit(token.feats)
            # tokenfeats.setFixedWidth(800)
            tokenfeats.editingFinished.connect(self.storeFieldText)
            tokenhead = CustomQLineEdit(token.head)
            tokenhead.setFixedWidth(50)
            tokenhead.editingFinished.connect(self.storeFieldText)
            tokendeprel = CustomQLineEdit(token.deprel)
            tokendeprel.setFixedWidth(150)
            tokendeprel.setCompleter(DEPRELCOMPL)
            tokendeprel.editingFinished.connect(self.storeFieldText)
            tokendeps = CustomQLineEdit(token.deps)
            tokendeps.setFixedWidth(200)
            tokendeps.editingFinished.connect(self.storeFieldText)
            # add semantics
            tokensemslot = CustomQLineEdit(token.semslot)
            tokensemslot.editingFinished.connect(self.storeFieldText)
            tokensemslot.setCompleter(SEMSLOTVARS)
            tokensemclass = CustomQLineEdit(token.semclass)
            tokensemclass.editingFinished.connect(self.storeFieldText)
            tokensemclass.setCompleter(SEMCLASSVARS)

            # tokenlayout.addWidget(tokenms)
            tokenlayout.addWidget(tokeninfo)
            tokenlayout.addWidget(tokenlemma)
            tokenlayout.addWidget(tokenpos)
            if not self.nomorph:
                tokenlayout.addWidget(tokenfeats)
            tokenlayout.addWidget(tokenhead)
            tokenlayout.addWidget(tokendeprel)
            tokenlayout.addWidget(tokendeps)
            tokenlayout.addWidget(tokensemslot)
            tokenlayout.addWidget(tokensemclass)
            self.tokens.addLayout(tokenlayout)
        self.tokens.addStretch() # no spacing
        self.tokens.update()
        self.grid.update()
        self.commentArea.setPlainText(self.data.data[sentkey].comment)
        self.undoStack.clear() # empty undo stack

    def savesent(self, sentkey):
        """Save sentence to Conllu data"""
        for i in range(self.tokens.count() - 1): # last element is stretcher, thus -1
            tokenlayout = self.tokens.itemAt(i) # get current token layout, i must coincide with sentence token indexes
            try:
                # get all fields
                # -1 = semclass, -2 = semslot, -3 = deps, -4 = deprel, -5 = tokenhead
                semclass = tokenlayout.itemAt(tokenlayout.count() - 1).widget().text()
                semslot = tokenlayout.itemAt(tokenlayout.count() - 2).widget().text()
                deps = tokenlayout.itemAt(tokenlayout.count() - 3).widget().text()
                deprel = tokenlayout.itemAt(tokenlayout.count() - 4).widget().text()
                head = tokenlayout.itemAt(tokenlayout.count() - 5).widget().text()
                if self.nomorph: # -6 = pos, -7 = lemma
                    upos = tokenlayout.itemAt(tokenlayout.count() - 6).widget().text()
                    lemma = tokenlayout.itemAt(tokenlayout.count() - 7).widget().text()
                else: # -6 = feats, -7 = pos, -8 = lemma
                    feats = tokenlayout.itemAt(tokenlayout.count() - 6).widget().text()
                    upos = tokenlayout.itemAt(tokenlayout.count() - 7).widget().text()
                    lemma = tokenlayout.itemAt(tokenlayout.count() - 8).widget().text()

                # check the fields for correctness
                if semclass not in SEMCLASS:
                    tokenlayout.itemAt(tokenlayout.count() - 1).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                    QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 1).widget().setStyleSheet(""))
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic class: {semclass}')
                    return f'!!!{semclass}'
                if semslot not in SEMSLOTS:
                    tokenlayout.itemAt(tokenlayout.count() - 2).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                    QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 2).widget().setStyleSheet(""))
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect semantic slot: {semslot}')
                    return f'!!!{semslot}'
                # deprel
                if deprel not in DEPRELS and deprel != '_':
                    # we allow to save deprels not existing in our list - just in case
                    msg = CorrectFieldWarning('Dependency relation:', deprel)
                    if not msg.exec():
                        tokenlayout.itemAt(tokenlayout.count() - 4).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                        QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 4).widget().setStyleSheet(""))
                        return f"!!!{deprel}"
                # head checks
                if not head.isdigit() and head != '_':
                    tokenlayout.itemAt(tokenlayout.count() - 5).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                    QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 5).widget().setStyleSheet(""))
                    QtWidgets.QMessageBox.about(self, 'Error', f'Incorrect head: {head}')
                    return f'!!!{head}'
                if head != '_' and int(head) > int(self.data.data[sentkey].tokens[-1].idx):
                    tokenlayout.itemAt(tokenlayout.count() - 5).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                    QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 5).widget().setStyleSheet(""))
                    QtWidgets.QMessageBox.about(self, 'Error', f'Head out of sentence boundaries: {head}')
                    return f'!!!{head}'
                # check feats
                if not self.nomorph:
                    featlist = re.findall(r"(?i)([a-z\[\]]+)=", feats)
                    if set(featlist) - FEATS:
                        # we allow to save feats not existing in our list - just in case
                        msg = CorrectFieldWarning('Grammatical info:', feats)
                        if not msg.exec():
                            tokenlayout.itemAt(tokenlayout.count() - 6).widget().setStyleSheet("background-color: rgb(245, 66, 87)")
                            QtCore.QTimer.singleShot(2000, lambda: tokenlayout.itemAt(tokenlayout.count() - 6).widget().setStyleSheet(""))
                            return f"!!!{feats}"
                # save to conllu instance
                self.data.data[sentkey].tokens[i].semclass = semclass
                self.data.data[sentkey].tokens[i].semslot = semslot
                self.data.data[sentkey].tokens[i].deps = deps
                self.data.data[sentkey].tokens[i].deprel = deprel 
                self.data.data[sentkey].tokens[i].head = head
                if not self.nomorph:
                    self.data.data[sentkey].tokens[i].feats = feats 
                self.data.data[sentkey].tokens[i].upos = upos 
                self.data.data[sentkey].tokens[i].lemma = lemma
            except IndexError: # for testing purposes, normally shouldn't occur
                print('Self tokens count', self.tokens.count(), 'total tokens', len(self.data.data[sentkey].tokens), i)
                print(self.data.data[sentkey].text)
                raise
        self.data.data[sentkey].comment = self.commentArea.toPlainText()

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
            filename = os.path.splitext(os.path.basename(filepath))[0]
            self.setWindowTitle(f"CoBaLD Editor - {filename}")
            QtWidgets.QMessageBox.about(self, 'New project', 'Now we must import a .conllu')
            self.importConll()

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
        """Import conllu file - gets called automatically on new project"""
        if not self.filepath:
            QtWidgets.QMessageBox.about(self, 'Error', 'Create project first!')
            return
        filename = QtWidgets.QFileDialog.getOpenFileName(None, "QFileDialog.getOpenFileName()",
                                               "", "CONLL-U Files (*.conllu)")
        filepath = filename[0]
        if not filepath:
            return
        if filepath and filepath.endswith('conllu'):
            self.data = Conllu()
            attempt = self.data.read(filepath)
            if attempt == 'BAD':
                QtWidgets.QMessageBox.about(self, 'Error', 'Something is wrong with the tokens!')
            elif attempt == 'EMPTY':
                QtWidgets.QMessageBox.about(self, 'Error', 'File seems to be empty!')
            else:
                self.statusBar.showMessage('CONLL-U loaded', 3000)
                self.loadsenttogui(self.data.current)
                if self.data.ready:
                    self.gotonumber.setMinimum(1)
                    self.gotonumber.setMaximum(len(self.data))
                    self.datalength.setText(f"  of {len(self.data)}  ")
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
        """Export conllu, obviously"""
        if not self.data.ready:
            QtWidgets.QMessageBox.about(self, 'Warning', 'No data to export!')
            return
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export CONLL-U", '', "CONLL-U files (*.conllu)")
        if filename[0]:
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
        self.setWindowTitle("CoBaLD Editor")

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
        """For undo/redo purposes"""
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