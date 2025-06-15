from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

html = """
<!DOCTYPE html>
<html>
<head>
<style>
body {
  background: #111;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
}
.gradient-border {
  padding: 4px;
  border-radius: 16px;
  background: linear-gradient(45deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4);
  background-size: 300% 300%;
  animation: moveGradient 4s linear infinite;
}
.content {
  background: #111;
  border-radius: 12px;
  padding: 2rem 4rem;
  color: white;
}
@keyframes moveGradient {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}
</style>
</head>
<body>
  <div class="gradient-border">
    <div class="content">Animated Border</div>
  </div>
</body>
</html>
"""

app = QApplication([])
view = QWebEngineView()
view.setHtml(html)
view.show()
app.exec()
