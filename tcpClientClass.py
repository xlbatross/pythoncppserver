import socket
import pickle  ##텍스트 이외의 자료형 파일 저장하기 위한 것
import numpy as np

class TCPClient:
    def __init__(self, serverIp : str = '127.0.0.1', serverPort : int = 2500): # 서버 IP와 포트 번호는 현재 강의실의 내 자리의 IP주소와 포트번호를 기본으로 지정했다.
        self.serverIp = serverIp # 연결할 서버의 IP 주소
        self.serverPort = serverPort # 연결할 서버의 포트 번호
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 클라이언트 소켓 생성
        self.packetSize = 1024
    
    # 소켓을 닫는 함수
    def disconnect(self):
        self.sock.close()

    # 서버 연결
    def connect(self):
        try:
            self.sock.connect((self.serverIp, self.serverPort)) # 서버의 어드레스를 통해 서버 연결
            return True # True 반환
        except socket.error: # 연결에 실패했을 경우
            return False # False 반환
    
    # 데이터 수신
    def receive(self):
        try:
            receiveBytes = bytearray()  #1바이트 단위의 값을 연속적으로 저장하는 시퀀스 자료형, 요소 변경 가능
            while True:
                packet = self.sock.recv(self.packetSize) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생   #raise : 에러 발생시키고 싶은곳에 작성?
                receiveBytes.extend(packet)
                if len(packet) < self.packetSize:
                    break
            data = pickle.loads(receiveBytes) # 수신한 데이터를 바이트 바이너리에서 클래스 객체로 변환
            return data # 변환한 데이터를 반환
        except socket.error: # 오류가 발생했을 경우
            self.disconnect() # 소켓을 닫는다
            return None

    # 문자 수신
    def receiveMessage(self):
        try:
            receiveBytes = bytearray()  #1바이트 단위의 값을 연속적으로 저장하는 시퀀스 자료형, 요소 변경 가능
            while True:
                packet = self.sock.recv(1024) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생   #raise : 에러 발생시키고 싶은곳에 작성?
                receiveBytes.extend(packet)
                if len(packet) < 1024:
                    break
            print(receiveBytes)
            data = receiveBytes.decode() # 수신한 데이터를 바이트 바이너리에서 클래스 객체로 변환
            return data # 변환한 데이터를 반환
        except socket.error: # 오류가 발생했을 경우
            self.disconnect() # 소켓을 닫는다
            return None
    
    # 데이터 송신
    def send(self, data):
        try:
            self.sock.sendall(pickle.dumps(data)) # 클래스 객체를 바이트 바이너리 데이터로 변환하여 서버로 송신
            return True
        except socket.error:
            self.disconnect()
            return False

    def dataToHeaderByteArray(self, data):
        packetCount : int = 0
        dataType : str = ""
        encodeData : bytes
        returnByteArray = bytearray()
        if type(data) == str:
            encodeData = str(data).encode()
            dataType = "string"
        elif type(data) == np.ndarray:
            encodeData = np.ndarray(data).tobytes()
            dataType = "image"
        if encodeData:
            packetCount = len(encodeData) // self.packetSize + (0 if len(encodeData) % self.packetSize == 0 else 1)
        if packetCount > 0 and dataType != "":
            returnByteArray.extend(("packetCount:" + str(packetCount) + "|dataType:" + dataType + "|").encode())
            returnByteArray.extend(bytearray(self.packetSize - len(returnByteArray)))
            returnByteArray.extend(encodeData)
        return returnByteArray

    # 데이터 송신
    def sendData(self, data):
        try:
            self.sock.sendall(self.dataToHeaderByteArray(data)) # 클래스 객체를 바이트 바이너리 데이터로 변환하여 서버로 송신
            return True
        except socket.error:
            self.disconnect()
            return False
    
    # 클라이언트의 어드레스 반환
    def address(self):
        return self.sock.getsockname()        
        
