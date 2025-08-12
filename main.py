# AI Network Sniffer - Punkt startowy aplikacji

import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    """Punkt wejścia aplikacji - uruchamia główne okno GUI.
    
    Returns:
        Kod wyjścia aplikacji PyQt5
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())