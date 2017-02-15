from server import flaskServer
from core import case

if __name__ == "__main__":
    case.initialize_case_db()
    flaskServer.start()
