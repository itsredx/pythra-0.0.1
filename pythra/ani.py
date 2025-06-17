from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cut-Out Square with Rounded Corners</title>
  <style>
    .box {
      width: 200px;
      height: 200px;
      background: linear-gradient(45deg, #4ADEDE, #7873f5);
      margin: 40px auto;
      display: block;
      /* Adjust cutSize% and radius% as needed */
      clip-path: path('
        M 20% 0
        L 90% 0
        A 10% 10% 0 0 1 100% 10%
        L 100% 90%
        A 10% 10% 0 0 1 90% 100%
        L 10% 100%
        A 10% 10% 0 0 1 0 90%
        L 0 20%
        L 20% 0
        Z
      ');
    }
  </style>
</head>
<body>
  <div class="box"></div>
</body>
</html>
"""
"""
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
