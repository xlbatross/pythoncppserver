import socket
import selectors
from dataheader import *
from db import DB
import cv2
import mediapipe as mp

HOST = ''
PORT = 2500

db = DB()
sel = selectors.DefaultSelector()  # 최적의 Selector를 생성한다.

clients : dict[socket.socket, list[str, socket.socket]] = {} # 현재 서버에 연결된 클라이언트 정보를 담는 변수
roomList : dict[socket.socket, tuple[str, list[socket.socket]]] = {} # 현재 생성된 방의 정보를 담는 변수. 

def accept_client(sock : socket.socket, ):
    """ 서버 소켓에 클라이언트가 접속하면 호출된다. """
    conn, addr = sock.accept()
    clients[conn] = ["", None]
    sel.register(conn, selectors.EVENT_READ, listenClient)  # 클라이언트 소켓을 등록한다.

# 접속 종료로 인한 클라이언트 정보 정리
def disconnect(conn : socket.socket):
    if conn in roomList:
        send(conn, ResDisjoinRoom("", isProfessorOut=True))
        del roomList[conn]
    if conn in clients: # 접속을 끊은 클라이언트의 정보가 client 인스턴스 변수에 존재한다면.
        if not clients[conn][1] is None:
            send(conn, ResDisjoinRoom(conn.getpeername()[0] + " " + str(conn.getpeername()[1]), isProfessorOut=False))
        del clients[conn] # 클라이언트 정보 삭제
    sel.unregister(conn)
    conn.close() # 클라이언트와 연결된 소켓을 닫는다.
    print(clients)
    print(roomList)

# 데이터 실제 수신
def receiveData(conn : socket.socket):
    try:
        packet = conn.recv(4)
        if not packet: # 수신한 데이터가 없으면
            raise # 오류 발생
        dataSize = int.from_bytes(packet, "little")

        receiveBytes = bytearray()
        while len(receiveBytes) < dataSize:
            packetSize = 1024 if len(receiveBytes) + 1024 < dataSize else dataSize - len(receiveBytes)
            packet = conn.recv(packetSize) # 서버로부터 데이터를 수신받는다.
            if not packet: # 수신한 데이터가 없으면
                raise # 오류 발생
            receiveBytes.extend(packet)
        return receiveBytes
    except Exception as e:
        disconnect(conn) # 해당 클라이언트의 정보를 해제한다.
        # print(e.with_traceback())
        return None

def receive(conn : socket.socket):
    headerBytes = receiveData(conn)
    if headerBytes is None:
        return (None, None)
    receiveCount = int.from_bytes(headerBytes[0:4], "little")
    dataBytesList = list()
    for i in range(receiveCount):
        receiveBytes = receiveData(conn)
        if receiveBytes is None:
            return (None, None)
        dataBytesList.append(receiveBytes)
    return (headerBytes, dataBytesList)

def sendByteData(conn : socket.socket, data : bytearray):
    conn.sendall(len(data).to_bytes(4, "little"))
    conn.sendall(data)

def sendData(conn : socket.socket, response : Response):
    sendByteData(conn, response.headerBytes)
    for dataByte in response.dataBytesList:
        sendByteData(conn, dataByte)

def send(conn : socket.socket, response : Response):
    if type(response) in [ResRoomList, ResRoomList2, ResMakeRoom, ResLogin, ResSignUp, ResChat]:
        sendData(conn, response)
    elif type(response) == ResEnterRoom:
        sendData(conn, response)
        if response.isEnter:
            proSock = clients[conn][1]
            resJoinRoom = ResJoinRoom(conn.getpeername()[0] + " " + str(conn.getpeername()[1]))
            for stuSock in roomList[proSock][1]:
                sendData(stuSock, resJoinRoom)
            sendData(proSock, resJoinRoom)
    elif type(response) == ResImage:
        if response.number == 0:
            for stuSock in roomList[proSock][1]:
                sendData(stuSock, response)
        elif response.number > 0:
            proSock = clients[conn][1]
            sendData(proSock, response)
    elif type(response) == ResDisjoinRoom:
        if response.isProfessorOut:
            for stuSock in roomList[conn][1]:
                clients[stuSock][1] = None
                sendData(stuSock, response)
        else:
            proSock = clients[conn][1]
            clients[conn][1] = None
            roomList[proSock][1].remove(conn)
            for stuSock in roomList[conn][1]:
                sendData(stuSock, response)
            sendData(proSock, response)

# 요청 데이터 처리
# 클라이언트에서 수신받은 요청 데이터의 타입을 구분하여 처리하고
# 처리된 데이터를 반환하는 함수
def processData(conn : socket.socket, headerBytes : bytearray, dataBytesList : list[bytearray], 
    mp_face_mesh, face_mesh, mp_drawing, mp_drawing_styles):
    
    request = Request(headerBytes=headerBytes)

    print()
    print(conn.getpeername())
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
        if conn in roomList:
            return ResProImage(image, 0)
        elif not clients[conn][1] is None:
            proSock = clients[conn][1]
            number = roomList[proSock][1].index(conn) + 1

            results = face_mesh.process(image)

            # Draw the face mesh annotations on the image.
            image.flags.writeable = True
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
            # cv2.imshow(str(cSock.getpeername()), image)
            # cv2.waitKey(1)
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
        return ResRoomList2(roomList)
    elif request.type == RequestType.makeRoom.value: # reqMakeRoom
        print("request Make room")
        reqMakeRoom = ReqMakeRoom(request, dataBytesList)
        isMake = False
        if not conn in roomList:
            roomList[conn] = (reqMakeRoom.roomName, [])
            isMake = True
        return ResMakeRoom(isMake)
    elif request.type == RequestType.enterRoom.value:
        print("request Enter room")
        reqEnterRoom = ReqEnterRoom(request, dataBytesList)
        hostAddress = (reqEnterRoom.ip, reqEnterRoom.port)
        isEnter = False
        for proSock in roomList:
            if hostAddress == proSock.getpeername() and conn.getpeername() != proSock.getpeername() and clients[conn][1] is None and len(roomList[conn][1]) < 4:
                clients[conn][1] = proSock
                roomList[proSock][1].append(conn)
                isEnter = True
                break
        return ResEnterRoom(isEnter)
    elif request.type == RequestType.leaveRoom.value:
        print("request leave room")
        isProfessorOut = (True if conn in roomList else False)
        return  ResDisjoinRoom(conn.getpeername()[0] + " " + str(conn.getpeername()[1]), isProfessorOut=isProfessorOut)
    elif request.type == RequestType.login.value:
        print("request Login")
        reqLogin = ReqLogin(request, dataBytesList)
        ment, name = db.login(reqLogin.num,reqLogin.pw)
        return ResLogin(ment=ment, name=name)
    elif request.type == RequestType.signUp.value:
        print("request SignUp")
        reqSignUp = ReqSignUp(request, dataBytesList)
        isSuccessed, ment = db.signUp(reqSignUp.name, reqSignUp.num, reqSignUp.pw, reqSignUp.cate)
        return ResSignUp(isSuccessed=isSuccessed, ment=ment)
    #가히
    elif request.type == RequestType.chat.value:
        print("request chat")
        text = ReqChat(request, dataBytesList)
        return ReqChat(text=text)

def listenClient(conn : socket.socket, mp_face_mesh, face_mesh, mp_drawing, mp_drawing_styles):
    headerBytes, dataBytesList = receive(conn)
    if headerBytes is None and dataBytesList is None:
        return
    response = processData(
        conn=conn, headerBytes=headerBytes, dataBytesList=dataBytesList, 
        mp_face_mesh=mp_face_mesh, 
        face_mesh=face_mesh,
        mp_drawing=mp_drawing,
        mp_drawing_styles = mp_drawing_styles
    )
    print(response)
    if not response is None:
        send(conn, response)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print('서버가 시작되었습니다.')
    sel.register(server, selectors.EVENT_READ, accept_client)  # 서버 소켓을 등록한다.

    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_face_mesh = mp.solutions.face_mesh

    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
        while True:
            events = sel.select()  # 클라이언트의 접속 또는 접속된 클라이언트의 데이터 요청을 감시
            for key, mask in events:
                callback = key.data  # 실행할 함수
                if key.fileobj == server:
                    callback(key.fileobj)
                else:
                    callback(key.fileobj, mp_face_mesh, face_mesh, mp_drawing, mp_drawing_styles)  # 이벤트가 발생한 소켓을 인수로 실행할 함수를 실행한다.
