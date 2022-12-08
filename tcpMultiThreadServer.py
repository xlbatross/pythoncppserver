from tcpMultiThreadServerClass import TCPMultiThreadServer
from threading import Thread
import cv2
import numpy as np
import time

# 생성된 쓰레드에서 반복적으로 처리할 함수
# 클라이언트에서 데이터가 수신되면 서버는 요청을 처리하고 처리 결과 데이터에 따라 특정 클라이언트에 데이터를 송신한다 .
def handler(server : TCPMultiThreadServer, cSock):
    while True:
        data = server.receive(cSock)
        if type(data) != np.ndarray:
            cv2.destroyWindow("receive")
            break
        cv2.imshow("receive", data)
        cv2.waitKey(1)
        # processData = server.processData(cSock=cSock, data=data)
        # server.send(cSock=cSock, data=processData)

server = TCPMultiThreadServer(port = 2500, listener = 100) # TCPMultiThreadServer 서버 객체 생성

# 무한 루프
# 서버는 항상 클라이언트 연결을 대기한다
while True:
    print("waiting for connection...")
    clientSock, addr = server.accept() # 서버에 연결된 클라이언트가 존재하면 클라이언트에 연결된 소켓과 클라이언트의 어드레스를 반환한다.
    cThread = Thread(target=handler, args=(server, clientSock)) # 연결된 클라이언트에 대한 쓰레드 생성
    cThread.daemon = True # 생성된 쓰레드의 데몬 여부를 True로 한다. (데몬 스레드 = 메인 스레드가 종료되면 즉시 종료되는 스레드)
    cThread.start() # 쓰레드 시작
    print(server.client)