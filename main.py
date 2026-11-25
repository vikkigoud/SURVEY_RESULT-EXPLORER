import sys
import random
from pathlib import Path
from datetime import date, timedelta

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.core.models import SurveyRecord
from app.core.storage import Storage
from app.ui.main_window import MainWindow
app = QApplication(sys.argv)
from PySide6.QtWidgets import QApplication