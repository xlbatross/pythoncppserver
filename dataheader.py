from enum import Enum
import numpy as np

class RequestType(Enum):
    image = 1
    roomList = 2
    makeRoom = 3
    enterRoom = 4

class ResponseType(Enum):
    image = 1
    roomList = 2
    makeRoom = 3
    enterRoom = 4
    joinRoom = 5

class DataType(Enum):
    String = 0
    IntNumber = 1
    OpenCVImage = 2

####
class Request:
    def __init__(self, headerBytes : bytearray):
        self.headerBytes = headerBytes
        self.receiveCount = int.from_bytes(headerBytes[0:4], "little")
        self.type = int.from_bytes(headerBytes[4:8], "little")
        self.dataSize = int.from_bytes(headerBytes[8:12], "little")

class ReqImage(Request):
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=headerBytes)
        self.img = np.ndarray(shape=(240, 320, 3), buffer=dataBytesList[0], dtype=np.uint8)

class ReqMakeRoom(Request):
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=headerBytes)
        self.roomName = dataBytesList[0].decode()

class ReqEnterRoom(Request):
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=headerBytes)
        self.ip = dataBytesList[0].decode()
        self.port = int.from_bytes(dataBytesList[1], "little")
####
class Response:
    def __init__(self):
        self.headerBytes : bytearray = bytearray()
        self.dataBytesList : list[bytearray] = list()

class ResImage(Response):
    def __init__(self, img : np.ndarray, number : int):
        super().__init__()
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.image.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # dataSize
        self.headerBytes.extend(DataType.OpenCVImage.value.to_bytes(4, "little"))
        self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
        self.dataBytesList.append(img.tobytes())
        self.dataBytesList.append(number.to_bytes(4, "little"))

class ResRoomList(Response):
    def __init__(self, roomList : dict[tuple[str, int], tuple[str, list[tuple[str, int]]]]):
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트
        super().__init__()
        self.headerBytes.extend((len(roomList) * 4).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.roomList.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(4).to_bytes(4, "little")) # dataSize / 방장 IP 길이, 방장 포트 번호 길이, 방 이름 길이, 방안의 사람 수 길이
        for key in roomList:
            # 방장 IP
            self.headerBytes.extend(DataType.String.value.to_bytes(4, "little"))
            self.dataBytesList.append(key[0].encode())
            # 방장 포트 번호
            self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
            self.dataBytesList.append(key[1].to_bytes(4, "little"))
            # 방 이름
            self.headerBytes.extend(DataType.String.value.to_bytes(4, "little"))
            self.dataBytesList.append(roomList[key][0].encode())
            # 방 안 사람 수
            self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
            self.dataBytesList.append(len(roomList[key][1]).to_bytes(4, "little"))

class ResMakeRoom(Response):
    def __init__(self, isMake : bool):
        super().__init__()
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.makeRoom.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # dataSize
        self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
        self.dataBytesList.append(isMake.to_bytes(4, "little"))

class ResEnterRoom(Response):
    def __init__(self, isEnter : bool):
        super().__init__()
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.enterRoom.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # dataSize
        self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
        self.dataBytesList.append(isEnter.to_bytes(4, "little"))

class ResJoinRoom(Response):
    def __init__(self, name : str, isProfessor : bool):
        super().__init__()
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # receiveCount
        self.headerBytes.extend(ResponseType.joinRoom.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(2).to_bytes(4, "little")) # dataSize
        self.headerBytes.extend(DataType.String.value.to_bytes(4, "little"))
        self.headerBytes.extend(DataType.IntNumber.value.to_bytes(4, "little"))
        self.dataBytesList.append(name.encode())
        self.dataBytesList.append(isProfessor.to_bytes(4, "little"))
