import http.server
import socketserver
import threading
import time



class AssetServer(threading.Thread):
    """
    A class to serve static files from a given directory over HTTP.

    This class extends `threading.Thread` to run a simple HTTP server on a separate thread.
    It serves files from the specified directory and listens on a specified port.
    
    Attributes:
        directory (str): The directory from which files will be served.
        port (int): The port number to listen on (default is 8000).
        server (socketserver.TCPServer or None): The HTTP server instance (initialized when the server starts).

    Methods:
        run():
            Starts the HTTP server on a separate thread, serving files from the specified directory.
        
        stop():
            Stops the HTTP server if it's running.
    """
    def __init__(self, directory, port=8000):
        """
        Initializes the AssetServer with the given directory and port.

        Args:
            directory (str): The directory to serve files from.
            port (int, optional): The port to listen on. Default is 8000.
        """
        super().__init__()
        self.directory = directory
        self.port = port
        self.server = None

    def run(self):
        """
        Starts the HTTP server to serve static files from the specified directory.

        This method is executed when the thread is started. It creates an HTTP server that listens
        on the specified port and serves files from the given directory.
        """
        handler = http.server.SimpleHTTPRequestHandler
        handler.directory = self.directory
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            self.server = httpd
            httpd.serve_forever()

    def stop(self):
        """
        Stops the HTTP server if it is running.

        This method safely shuts down the server by calling the `shutdown()` method.
        """
        if self.server:
            self.server.shutdown()




