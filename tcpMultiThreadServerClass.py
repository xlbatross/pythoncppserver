import socket
import cv2
from dataheader import *


class TCPMultiThreadServer:
    def __init__(self, port : int = 2500, listener : int = 600):
        self.connected = False # 서버가 클라이언트와 연결되었는지를 판단하는 변수
        self.clients : dict[tuple[str, int], list[socket.socket, str]] = {} # 현재 서버에 연결된 클라이언트 정보를 담는 변수

        self.roomList : dict[tuple[str, int], tuple[str, list[tuple[str, int]]]] = {} # 현재 생성된 방의 정보를 담는 변수. 
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트 

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 소켓 생성
        self.sock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다. 
        self.sock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

    # 접속 종료로 인한 클라이언트 정보 정리
    def disconnect(self, cAddr : tuple):
        if cAddr in self.roomList:
            del self.roomList[cAddr]
        if cAddr in self.clients: # 접속을 끊은 클라이언트의 정보가 client 인스턴스 변수에 존재한다면.
            del self.clients[cAddr] # 클라이언트 정보 삭제
        if len(self.clients) == 0: # 만약 서버에 연결된 클라이언트가 없다면
            self.connected = False # 서버와 연결된 클라이언트가 없는 상태임을 저장한다.
        print(self.clients)
    
    # 클라이언트 연결
    def accept(self):
        cSock, cAddr = self.sock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
        self.connected = True # 서버가 클라이언트와 연결된 상태임을 저장한다.
        self.clients[cAddr] = [cSock, ""] # client 인스턴스 변수에 클라이언트의 어드레스를 키값으로 하여 소켓과 해당 클라이언트에 로그인한 아이디를 저장한다.
        # 지금은 서버로 접속만 했기 때문에 아이디 부분은 빈 부분이다.
        return cSock, cAddr # 클라이언트와 연결된 소켓과 클리이언트의 어드레스 반환

    def sendData(self, cSock : socket.socket, data : bytearray):
        if self.connected:
            cSock.sendall(len(data).to_bytes(4, "little"))
            cSock.sendall(data)
            return True
        else:
            return False

    def send(self, cSock : socket.socket, response):
        self.sendData(cSock, response.headerBytes)
        for dataByte in response.dataBytesList:
            self.sendData(cSock, dataByte)
        
    # 데이터 실제 수신
    def receiveData(self, rSock : socket.socket = None):
        cAddr = rSock.getpeername() # 데이터를 수신할 클라이언트의 어드레스
        try:
            packet = rSock.recv(4)
            if not packet: # 수신한 데이터가 없으면
                raise # 오류 발생
            dataSize = int.from_bytes(packet, "little")

            receiveBytes = bytearray()
            while len(receiveBytes) < dataSize:
                packetSize = 1024 if len(receiveBytes) + 1024 < dataSize else dataSize - len(receiveBytes)
                packet = rSock.recv(packetSize) # 서버로부터 데이터를 수신받는다.
                if not packet: # 수신한 데이터가 없으면
                    raise # 오류 발생
                receiveBytes.extend(packet)
            return receiveBytes
        except Exception as e:
            rSock.close() # 클라이언트와 연결된 소켓을 닫고
            self.disconnect(cAddr) # 해당 클라이언트의 정보를 해제한다.
            print(e.with_traceback())
            return None

    def receive(self, rSock : socket.socket = None):
        headerBytes = self.receiveData(rSock)
        if headerBytes is None:
            return (None, None)
        dataCount = int.from_bytes(headerBytes[0:4], "little")
        dataBytesList = list()
        for i in range(dataCount):
            receiveBytes = self.receiveData(rSock)
            if receiveBytes is None:
                return (None, None)
            dataBytesList.append(receiveBytes)
        return (headerBytes, dataBytesList)
    
    # 요청 데이터 처리
    # 클라이언트에서 수신받은 요청 데이터의 타입을 구분하여 처리하고
    # 처리된 데이터를 반환하는 함수
    def processData(self, cSock : socket.socket, headerBytes : bytearray, dataBytesList : list[bytearray], 
        mp_face_mesh, face_mesh, mp_drawing, mp_drawing_styles):
        cAddr = cSock.getpeername()
        requestType = int.from_bytes(headerBytes[4:8], "little")
        print(int.from_bytes(headerBytes[0:4], "little"))
        print(int.from_bytes(headerBytes[4:8], "little"))
        print(int.from_bytes(headerBytes[8:12], "little"))

        if requestType == RequestType.image.value: # reqImage
            reqImage = ReqImage(headerBytes, dataBytesList)

            image = cv2.cvtColor(reqImage.img, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image)

            # Draw the face mesh annotations on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_tesselation_style())
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_contours_style())
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_iris_connections_style())
            cv2.imshow(str(cSock.getpeername()), image)
            cv2.waitKey(1)
            return ResImage(reqImage=reqImage, imageByteData=image.tobytes())
        elif requestType == RequestType.roomList.value: # reqRoomList
            print("request Room list")
            return ResRoomList(self.roomList)
        elif requestType == RequestType.makeRoom.value: # reqMakeRoom
            print("request Make room")
            isMake = False
            reqMakeRoom = ReqMakeRoom(headerBytes, dataBytesList)
            if not cAddr in self.roomList:
                self.roomList[cAddr] = (reqMakeRoom.roomName, [])
                isMake = True
            return ResMakeRoom(isMake)
        elif requestType == RequestType.enterRoom.value:
            print("request Enter room")
            reqEnterRoom = ReqEnterRoom(headerBytes, dataBytesList)
            print(reqEnterRoom.ip)
            print(reqEnterRoom.port)


