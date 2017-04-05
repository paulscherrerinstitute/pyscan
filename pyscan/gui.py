from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QDialog, QPushButton, QProgressBar, QGridLayout, QLabel


class SubPanelContents(QDialog):
    def __init__(self, parent=None):
        super(SubPanelContents, self).__init__(parent)
        self.exitbutton = QPushButton('Abort measurement')
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.connect(self.exitbutton, SIGNAL("ex"), self.vis)
        self.appearing = 1

        self.connect(self.exitbutton, SIGNAL("pb"), self.updatePB)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.abortScan = 0
        self.connect(self.exitbutton, SIGNAL("clicked()"), self.abort)

    def abort(self):
        self.abortScan = 1

    def updatePB(self):
        self.pbar.setValue(self.Progress)

    def vis(self):
        pass


class SubPanel(QDialog):
    def __init__(self, parent=None):
        super(SubPanel, self).__init__(parent)
        self.exitbutton = QPushButton('Abort measurement')

        self.connect(self.exitbutton, SIGNAL("ex"), self.vis)
        self.appearing = 1

        self.connect(self.exitbutton, SIGNAL("pb"), self.updatePB)
        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)

        self.abortScan = 0
        self.connect(self.exitbutton, SIGNAL("clicked()"), self.abort)

        layout = QGridLayout()
        layout.addWidget(self.pbar, 0, 0)

        layout.addWidget(self.exitbutton, 1, 0)
        layout.addWidget(QLabel("Don't close this window but use the button above to abort the measurement."), 2, 0)

        self.setLayout(layout)

        self.setWindowTitle("pyScan progress")

    def abort(self):
        self.abortScan = 1

    def updatePB(self):
        self.pbar.setValue(self.Progress)

    def vis(self):
        if self.appearing == 0:
            self.setVisible(False)
        else:
            self.setVisible(True)


class DummyClass:
    def __init__(self):
        self.Progress = 1  # For Thomas!!
