from tcpClientClass import TCPClient
from threading import Thread
import sys
import cv2

def send(client : TCPClient):
    msg = input()
    client.sendData(msg)
    print(f"client : {msg}")

def sendImage(client : TCPClient):
    pass

def receive(client : TCPClient):
    msg = client.receiveMessage()
    print(f"server : {msg}")

if __name__ == "__main__":
    client = TCPClient()
    if not client.connect():
        sys.exit()
    
    capture = cv2.VideoCapture(0)
    
    # sendThread = Thread(target=send, args=(client,))
    # receiveThread = Thread(target=receive, args=(client,))

    # sendThread.start()
    # receiveThread.start()

    # sendThread.join()
    # receiveThread.join()