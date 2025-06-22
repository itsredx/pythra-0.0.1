from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        html_content = """
        <!DOCTYPE html>
        <html lang="en"><head><meta charset="UTF-8"><title>SimpleBar in QWebEngine</title>
          <link rel="stylesheet" href="https://unpkg.com/simplebar@latest/dist/simplebar.css" />
          <style>
            .my-scroll-container { max-height:200px; border:1px solid #ccc; margin:16px; }
            .my-scroll-container .simplebar-track.simplebar-vertical {
              background: rgba(0, 0, 128, 0.1);
            }
            .my-scroll-container .simplebar-scrollbar:before {
              background-color: #2196F3;
              border-radius: 4px;
            }
            .my-scroll-container .simplebar-scrollbar:hover:before {
              background-color: #1976D2;
            }
            .my-scroll-container .simplebar-scrollbar {
              transition: none !important;
            }
            .my-scroll-container .simplebar-scrollbar:before {
              opacity: 1 !important;
            }
            .my-scroll-container .simplebar-scrollbar { width: 10px !important; }
          </style>
        </head><body>
          <h1>SimpleBar in PySide6</h1>
          <div id="scroll-area" class="my-scroll-container" data-simplebar>
            <ul>
              """ + "\n".join(f"<li>Item {i}</li>" for i in range(1, 51)) + """
            </ul>
          </div>
          <script src="https://unpkg.com/simplebar@latest/dist/simplebar.min.js"></script>
          <script>
            new SimpleBar(document.getElementById('scroll-area'), {
              autoHide: false,
              scrollbarMinSize: 20
            });
          </script>
        </body></html>
        """
        self.web_view.setHtml(html_content)
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
