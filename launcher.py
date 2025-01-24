from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, BodyLabel, DisplayLabel, LineEdit ,LargeTitleLabel, PushButton
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        setFont(self.label, 28)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # 必须给子界面设置全局唯一的对象名
        self.setObjectName(text.replace(' ', '-'))

class start_pyquick(QFrame):
    def start(self):
        print("Button clicked")
    def __init__(self, text: str,parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QVBoxLayout(self)

        self.filepath=LineEdit(self)
        self.filepath.setFixedSize(500,30)

        self.start_botton = PushButton("Start pyquick", self)
        self.start_botton.clicked.connect(self.start)

        self.hBoxLayout.addWidget(self.filepath, 1, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.start_botton, 2, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))

class Window(FluentWindow):
    def __init__(self):
        super().__init__()
        # 创建子界面，实际使用时将 Widget 换成自己的子界面
        self.homeInterface = start_pyquick("Start pyquick", self)
        self.settingInterface = Widget("Settings", self)
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'start')
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

    def initWindow(self):

        self.setWindowIcon(QIcon('pyquick.ico'))
        self.setWindowTitle('Launcher')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
