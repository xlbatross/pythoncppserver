from enum import Enum
import numpy as np
import socket

class RequestType(Enum):
    image = 1
    roomList = 2
    makeRoom = 3
    enterRoom = 4
    leaveRoom = 5
    login = 6
    signUp = 7
    chat = 8 #가히

class ResponseType(Enum):
    image = 1
    roomList = 2
    makeRoom = 3
    enterRoom = 4
    joinRoom = 5
    disjoinRoom = 6
    login = 7
    signUp = 8
    proImage = 9
    firstImage = 10
    secondImage = 11
    thirdImage = 12
    forthImage = 13
    chat = 14 #가히

####
class Request:
    def __init__(self, headerBytes : bytearray):
        self.headerBytes = headerBytes
        self.receiveCount = int.from_bytes(headerBytes[0:4], "little")
        self.type = int.from_bytes(headerBytes[4:8], "little")
        self.totalDataSize = int.from_bytes(headerBytes[8:12], "little")

class ReqImage(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.img = np.ndarray(shape=(360, 480, 3), buffer=dataBytesList[0], dtype=np.uint8)

class ReqMakeRoom(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.roomName = dataBytesList[0].decode()

class ReqEnterRoom(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.ip = dataBytesList[0].decode()
        self.port = int.from_bytes(dataBytesList[1], "little")

class ReqLogin(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.num = dataBytesList[0].decode()
        self.pw = dataBytesList[1].decode()

class ReqSignUp(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.name = dataBytesList[0].decode()
        self.num = dataBytesList[1].decode()
        self.pw = dataBytesList[2].decode()
        self.cate = dataBytesList[3].decode()

#가히
class ReqChat(Request):
    def __init__(self, request : Request, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=request.headerBytes)
        self.text = dataBytesList[0].decode()

####
class Response:
    def __init__(self):
        self.headerBytes : bytearray = bytearray()
        self.dataBytesList : list[bytearray] = list()
    
    def totalDataSize(self):
        totalDataSize = 0
        for dataBytes in self.dataBytesList:
            totalDataSize += len(dataBytes)
        return totalDataSize

class ResImage(Response):
    def __init__(self, img : np.ndarray, number : int, imageTypeValue : int):
        super().__init__()
        self.number = number
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(imageTypeValue.to_bytes(4, "little")) # response type
        self.dataBytesList.append(img.tobytes())
        self.dataBytesList.append(number.to_bytes(4, "little"))
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResRoomList(Response):
    def __init__(self, roomList : dict[tuple[str, int], tuple[str, list[tuple[str, int]]]]):
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트
        super().__init__()
        self.headerBytes.extend((len(roomList) * 4).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.roomList.value.to_bytes(4, "little")) # response type

        for key in roomList:
            # 방장 IP
            self.dataBytesList.append(key[0].encode())
            # 방장 포트 번호
            self.dataBytesList.append(key[1].to_bytes(4, "little"))
            # 방 이름
            self.dataBytesList.append(roomList[key][0].encode())
            # 방 안 사람 수
            self.dataBytesList.append(len(roomList[key][1]).to_bytes(4, "little"))

        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResRoomList2(Response):
    def __init__(self, roomList : dict[socket.socket, tuple[str, list[socket.socket]]]):
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트
        super().__init__()
        print(roomList)
        self.headerBytes.extend((len(roomList) * 4).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.roomList.value.to_bytes(4, "little")) # response type

        for key in roomList:
            # 방장 IP
            self.dataBytesList.append(key.getpeername()[0].encode())
            # 방장 포트 번호
            self.dataBytesList.append(key.getpeername()[1].to_bytes(4, "little"))
            # 방 이름
            self.dataBytesList.append(roomList[key][0].encode())
            # 방 안 사람 수
            self.dataBytesList.append(len(roomList[key][1]).to_bytes(4, "little"))

        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResMakeRoom(Response):
    def __init__(self, isMake : bool):
        super().__init__()
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.makeRoom.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(isMake.to_bytes(4, "little"))
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResEnterRoom(Response):
    def __init__(self, isEnter : bool):
        super().__init__()
        self.isEnter = isEnter
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.enterRoom.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(isEnter.to_bytes(4, "little"))
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResJoinRoom(Response):
    def __init__(self, name : str):
        super().__init__()
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.joinRoom.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(name.encode())
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResDisjoinRoom(Response):
    def __init__(self, name : str, isProfessorOut : bool):
        super().__init__()
        self.isProfessorOut = isProfessorOut
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.disjoinRoom.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(name.encode())
        self.dataBytesList.append(isProfessorOut.to_bytes(4, "little"))
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResLogin(Response):
    def __init__(self, ment : str, name : str):
        super().__init__()
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.login.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(ment.encode())
        self.dataBytesList.append(name.encode())
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResSignUp(Response):
    def __init__(self, isSuccessed : bool, ment : str):
        super().__init__()
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.signUp.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(isSuccessed.to_bytes(4, "little"))
        self.dataBytesList.append(ment.encode())
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize

class ResProImage(ResImage):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__(img, number, ResponseType.proImage.value)

class ResFirstImage(ResImage):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__(img, number, ResponseType.firstImage.value)

class ResSecondImage(ResImage):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__(img, number, ResponseType.secondImage.value)

class ResThirdImage(ResImage):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__(img, number, ResponseType.thirdImage.value)

class ResForthImage(ResImage):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__(img, number, ResponseType.forthImage.value)

#가히
class ResChat(Response):
    def __init__(self, name : str, text : str):
        super().__init__()
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.chat.value.to_bytes(4, "little")) # response type
        self.dataBytesList.append(name.encode())
        self.dataBytesList.append(text.encode())
        self.headerBytes.extend(self.totalDataSize().to_bytes(4, "little")) # totalDataSize