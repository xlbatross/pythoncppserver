import socket
import cv2
from dataheader import *
from db import DB


class TCPMultiThreadServer:
    def __init__(self, port : int = 2500, listener : int = 600):
        self.db = DB()
        self.connected = False # 서버가 클라이언트와 연결되었는지를 판단하는 변수
        
        self.clients : dict[socket.socket, list[str, socket.socket, int, int]] = {} # 현재 서버에 연결된 클라이언트 정보를 담는 변수
        # ex) {클라이언트 소켓, ["아이디", 방장 소켓, 눈깜박임 체크 카운트 = 0, 다른 방향 체크 카운트 = 0]}

        self.roomList : dict[socket.socket, tuple[str, list[socket.socket]]] = {} # 현재 생성된 방의 정보를 담는 변수. 
        print(self.roomList)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 서버 소켓 생성
        self.sock.bind(('', port)) # 서버 소켓에 어드레스(IP가 빈칸일 경우 자기 자신(127.0.0.1)로 인식한다. + 포트번호)를 지정한다. 
        self.sock.listen(listener) # 서버 소켓을 연결 요청 대기 상태로 한다.

    # 접속 종료로 인한 클라이언트 정보 정리
    def disconnect(self, cSock: socket.socket):
        if cSock in self.roomList:
            self.send(cSock, ResDisjoinRoom("", isProfessorOut=True))
        if cSock in self.clients: # 접속을 끊은 클라이언트의 정보가 client 인스턴스 변수에 존재한다면.
            if not self.clients[cSock][1] is None:
                self.send(cSock, ResDisjoinRoom(cSock.getpeername()[0] + " " + str(cSock.getpeername()[1]), isProfessorOut=False))
            del self.clients[cSock] # 클라이언트 정보 삭제
        if len(self.clients) == 0: # 만약 서버에 연결된 클라이언트가 없다면
            self.connected = False # 서버와 연결된 클라이언트가 없는 상태임을 저장한다.
        cSock.close() # 클라이언트와 연결된 소켓을 닫고
        print(self.clients)
        print(self.roomList)
    
    # 클라이언트 연결
    def accept(self):
        cSock, cAddr = self.sock.accept() # 클라이언트와 연결이 된다면 클라이언트와 연결된 소켓과 클라이언트의 어드레스(IP와 포트번호)를 반환한다.
        self.connected = True # 서버가 클라이언트와 연결된 상태임을 저장한다.
        self.clients[cSock] = ["", None, 0, 0]
        # client 인스턴스 변수에 클라이언트 소켓를 키값으로 하여 소켓과 해당 클라이언트에 로그인한 아이디를 저장한다.
        # 지금은 서버로 접속만 했기 때문에 아이디 부분은 빈 부분이다.
        # 아이디 부분 옆은 접속한 방의 방장의 소켓이다. 지금은 아직 방에 들어가지 않았으니 None이다.
        return cSock, cAddr # 클라이언트와 연결된 소켓과 클리이언트의 어드레스 반환

    def sendByteData(self, cSock : socket.socket, data : bytearray):
        cSock.sendall(len(data).to_bytes(4, "little"))
        cSock.sendall(data)

    def sendData(self, cSock : socket.socket, response : Response):
        self.sendByteData(cSock, response.headerBytes)
        for dataByte in response.dataBytesList:
            self.sendByteData(cSock, dataByte)
    
    def send(self, cSock : socket.socket, response : Response):
        if type(response) in [ResRoomList, ResRoomList2, ResMakeRoom, ResLogin, ResSignUp]:
            self.sendData(cSock, response)
        elif type(response) == ResEnterRoom:
            self.sendData(cSock, response)
            if response.isEnter:
                hostSocket = self.clients[cSock][1]
                resJoinRoom = ResJoinRoom(cSock.getpeername()[0] + " " + str(cSock.getpeername()[1]))
                for roomMemberSock in self.roomList[hostSocket][1]:
                    self.sendData(roomMemberSock, resJoinRoom)
                self.sendData(hostSocket, resJoinRoom)
        elif ResImage in type(response).mro():
            if response.number == 0:
                for roomMemberSock in self.roomList[cSock][1]:
                    self.sendData(roomMemberSock, response)
            elif response.number > 0:
                hostSocket = self.clients[cSock][1]
                self.sendData(hostSocket, response)
        elif type(response) == ResDisjoinRoom:
            if response.isProfessorOut:
                for roomMemberSock in self.roomList[cSock][1]:
                    self.clients[roomMemberSock][1] = None
                    self.sendData(roomMemberSock, response)
                del self.roomList[cSock]
            else:
                hostSocket = self.clients[cSock][1]
                self.clients[cSock][1] = None
                self.roomList[hostSocket][1].remove(cSock)
                for roomMemberSock in self.roomList[hostSocket][1]:
                    self.sendData(roomMemberSock, response)
                self.sendData(hostSocket, response)
        elif type(response) == ResChat:
            hostSocket = cSock if cSock in self.roomList else self.clients[cSock][1]
            for roomMemberSock in self.roomList[hostSocket][1]:
                self.sendData(roomMemberSock, response)
            self.sendData(hostSocket, response)
        
    # 데이터 실제 수신
    def receiveData(self, rSock : socket.socket = None):
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
            self.disconnect(rSock) # 해당 클라이언트의 정보를 해제한다.
            # print(e.with_traceback())
            return None

    def receive(self, rSock : socket.socket = None):
        headerBytes = self.receiveData(rSock)
        if headerBytes is None:
            return (None, None)
        receiveCount = int.from_bytes(headerBytes[0:4], "little")
        dataBytesList = list()
        for i in range(receiveCount):
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
    
        request = Request(headerBytes=headerBytes)

        print()
        print(cSock.getpeername())
        print(request.receiveCount)
        print(request.type)
        print(request.totalDataSize)

        receiveTotalSize = 0
        for dataBytes in dataBytesList:
            receiveTotalSize += len(dataBytes)

        print(receiveTotalSize)

        if request.totalDataSize != receiveTotalSize:
            return None

        if request.type == RequestType.image.value: # reqImage
            print("request Image")
            reqImage = ReqImage(request, dataBytesList)
            image = cv2.cvtColor(reqImage.img, cv2.COLOR_BGR2RGB)
            number = -1
            if cSock in self.roomList:
                return ResProImage(image, 0)
            elif not self.clients[cSock][1] is None:
                hostSock = self.clients[cSock][1]
                number = self.roomList[hostSock][1].index(cSock) + 1

                # To improve performance
                image.flags.writeable = False
                # get the result
                results = face_mesh.process(image)
                # To improve performance
                image.flags.writeable = True

                img_h, img_w, img_c = image.shape
                face_3d = []
                face_2d = []

                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    for idx in [33, 263, 1, 61, 291, 199]:
                        lm = face_landmarks.landmark[idx]
                        x, y = int(lm.x * img_w), int(lm.y * img_h)
                        # get the 2d coordinates
                        face_2d.append([x, y])
                        # get the 3d coodinates
                        face_3d.append([x, y, lm.z])

                    # Convert it to the NumPy Array
                    face_2d = np.array(face_2d, dtype=np.float64)
                    # Convert it to the NumPy Array
                    face_3d = np.array(face_3d, dtype=np.float64)
                    # the camera matrix
                    focal_length = 1 * img_w

                    cam_matrix = np.array([ [focal_length, 0, img_h / 2],
                                            [0, focal_length, img_w / 2],
                                            [0, 0, 1]])
                    
                    # The Distance Matrix
                    dist_matrix = np.zeros((4, 1), dtype=np.float64)

                    # Solve Pnp
                    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

                    # Get rotational matrix
                    rmat, jac = cv2.Rodrigues(rot_vec)

                    # Get angels
                    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

                    # get the y rotation degree
                    x = angles[0] * 360
                    y = angles[1] * 360
                    z = angles[2] * 360

                    # See Where the user's head tiliing

                    if y < -10:
                        text = "looking left"
                        self.clients[cSock][3] += 1
                    elif y > 10:
                        text = "looking right"
                        self.clients[cSock][3] += 1
                    elif x < -5:
                        text = "looking down"
                        self.clients[cSock][3] += 1
                    elif x > 15:
                        text = "looking up"
                        self.clients[cSock][3] += 1
                    else:
                        text = "Forward"
                        self.clients[cSock][3] = 0
                    
                    if self.clients[cSock][3] >= 150:
                        cv2.putText(image, f"alert!", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if number == 1:
                    return ResFirstImage(image, number)
                elif number == 2:
                    return ResSecondImage(image, number)
                elif number == 3:
                    return ResThirdImage(image, number)
                elif number == 4:
                    return ResForthImage(image, number)
        elif request.type == RequestType.roomList.value: # reqRoomList
            print("request Room list")
            return ResRoomList2(self.roomList)
        elif request.type == RequestType.makeRoom.value: # reqMakeRoom
            print("request Make room")
            reqMakeRoom = ReqMakeRoom(request, dataBytesList)
            isMake = False
            if not cSock in self.roomList:
                self.roomList[cSock] = (reqMakeRoom.roomName, [])
                isMake = True
            return ResMakeRoom(isMake)
        elif request.type == RequestType.enterRoom.value:
            print("request Enter room")
            reqEnterRoom = ReqEnterRoom(request, dataBytesList)
            hostAddress = (reqEnterRoom.ip, reqEnterRoom.port)
            isEnter = False
            for proSock in self.roomList:
                if hostAddress == proSock.getpeername() and cSock.getpeername() != proSock.getpeername() and self.clients[cSock][1] is None and len(self.roomList[proSock][1]) < 1:
                    self.clients[cSock][1] = proSock
                    self.roomList[proSock][1].append(cSock)
                    isEnter = True
                    break
            return ResEnterRoom(isEnter)
        elif request.type == RequestType.leaveRoom.value:
            print("request leave room")
            isProfessorOut = (True if cSock in self.roomList else False)
            return  ResDisjoinRoom(cSock.getpeername()[0] + " " + str(cSock.getpeername()[1]), isProfessorOut=isProfessorOut)
        elif request.type == RequestType.login.value:
            print("request Login")
            reqLogin = ReqLogin(request, dataBytesList)
            ment,name = self.db.login(reqLogin.num,reqLogin.pw)
            if name!="":
                self.clients[cSock][0] = name
            return ResLogin(ment=ment,name=name)
        elif request.type == RequestType.signUp.value:
            print("request SignUp")
            reqSignUp = ReqSignUp(request, dataBytesList)
            isSuccessed, ment = self.db.signUp(reqSignUp.name, reqSignUp.num, reqSignUp.pw, reqSignUp.cate)
            return ResSignUp(isSuccessed=isSuccessed, ment=ment)
        #가히
        elif request.type == RequestType.chat.value:
            print("request chat")
            if cSock in self.roomList or not self.clients[cSock][1] is None:
                reqChat = ReqChat(request, dataBytesList)
                print(reqChat.text)
                name = self.clients[cSock][0] 
                text = reqChat.text
                print(name)
                return ResChat(name,text)
            