import socket
import pickle
import numpy as np
import cv2
import json
import base64

class TCPMultiThreadServer:
    def __init__(self, port : int = 2500, listener : int = 600):
        self.connected = False # 서버가 클라이언트와 연결되었는지를 판단하는 변수
        self.client : dict[tuple, list[socket.socket, str]] = {} # 현재 서버에 연결된 클라이언트 정보를 담는 변수
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 소켓 생성
        self.sock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다. 
        self.sock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

    # 접속 종료로 인한 클라이언트 정보 정리
    def disconnect(self, cAddr : tuple):
        if cAddr in self.client: # 접속을 끊은 클라이언트의 정보가 client 인스턴스 변수에 존재한다면.
            del self.client[cAddr] # 클라이언트 정보 삭제
        if len(self.client) == 0: # 만약 서버에 연결된 클라이언트가 없다면
            self.connected = False # 서버와 연결된 클라이언트가 없는 상태임을 저장한다.
        print(self.client)
    
    # 클라이언트 연결
    def accept(self):
        cSock, cAddr = self.sock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
        self.connected = True # 서버가 클라이언트와 연결된 상태임을 저장한다.
        self.client[cAddr] = [cSock, ""] # client 인스턴스 변수에 클라이언트의 어드레스를 키값으로 하여 소켓과 해당 클라이언트에 로그인한 아이디를 저장한다.
        # 지금은 서버로 접속만 했기 때문에 아이디 부분은 빈 부분이다.
        return cSock, cAddr # 클라이언트와 연결된 소켓과 클리이언트의 어드레스 반환

    # 모든 클라이언트에 데이터 송신
    def sendAllClient(self, data):
        if self.connected: # 현재 서버가 클라이언트에 연결된 상태라면
            for client in self.client.values(): # 연결된 모든 클라이언트에
                client[0].sendall(pickle.dumps(data)) # 바이트 바이너리로 변환한 데이터를 송신한다
            return True
        else:
            return False
    
    # 특정 클라이언트들에 데이터 송신
    def sendReceiver(self, data):
        if self.connected: # 현재 서버가 클라이언트에 연결된 상태라면
            for receiver in data.receiver: # 송신할 데이터에 보관된 클라이언트들에게
                self.client[receiver][0].sendall(pickle.dumps(data)) # 바이트 바이너리로 변환한 데이터를 송신한다
            return True
        else:
            return False

    # 단일 클라이언트에 데이터 송신
    def sendClient(self, cSock : socket.socket, data):
        if self.connected: # 현재 서버가 클라이언트에 연결된 상태라면
            cSock.sendall(pickle.dumps(data)) # 해당 클라이언트에 연결된 소켓에 바이트 바이너리로 변환한 데이터를 송신한다
            return True
        else:
            return False

    # 데이터 송신
    # 데이터 송신은 이 메소드를 통해서만 전달된다.
    # def send(self, cSock : socket.socket, data):
    #     self.sendClient(cSock=cSock, data=data) # 단일 클라이언트에 데이터 송신

    def send(self, cSock : socket.socket, data : bytes):
        if self.connected:
            cSock.sendall(len(data).to_bytes(4, "little"))
            cSock.sendall(data)
            return True
        else:
            return False

    # 데이터 수신
    def receive(self, rSock : socket.socket = None):
        cAddr = rSock.getpeername() # 데이터를 수신할 클라이언트의 어드레스
        try:
            # 헤더를 받는다.
            packet = rSock.recv(4)
            if not packet: # 수신한 데이터가 없으면
                raise # 오류 발생
            dataSize = int.from_bytes(packet, "little")

            headerBytes = bytearray()
            while len(headerBytes) < dataSize:
                packetSize = 1024 if len(headerBytes) + 1024 < dataSize else dataSize - len(headerBytes)
                packet = rSock.recv(packetSize) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생
                headerBytes.extend(packet)
            ######

            # 실제 데이터를 받는다.
            packet : bytes = rSock.recv(4)
            if not packet: # 수신한 데이터가 없으면
                raise # 오류 발생
            dataSize = int.from_bytes(packet, "little")

            dataBytes = bytearray()
            while len(dataBytes) < dataSize:
                packetSize = 4096 if len(dataBytes) + 4096 < dataSize else dataSize - len(dataBytes)
                packet = rSock.recv(packetSize) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생
                dataBytes.extend(packet)
        
            return (headerBytes, dataBytes)
        except Exception as e:
            rSock.close() # 클라이언트와 연결된 소켓을 닫고
            self.disconnect(cAddr) # 해당 클라이언트의 정보를 해제한다.
            print(e.with_traceback())
            return None
    
    # 요청 데이터 처리
    # 클라이언트에서 수신받은 요청 데이터의 타입을 구분하여 처리하고
    # 처리된 데이터를 반환하는 함수
    def processData(self, cSock : socket.socket, headerBytes : bytearray, dataBytes : bytearray):
        dataType = int.from_bytes(headerBytes[0:4], "little")
        if dataType == 1:
            height = int.from_bytes(headerBytes[4:8], "little")
            width = int.from_bytes(headerBytes[8:12], "little")
            channels = int.from_bytes(headerBytes[12:16], "little")
            img = np.ndarray(shape=(height, width, channels), buffer=dataBytes, dtype=np.uint8)
        return headerBytes, dataBytes

