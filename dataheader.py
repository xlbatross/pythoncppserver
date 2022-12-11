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

####
class Request:
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        self.headerBytes = headerBytes
        self.dataBytesList = dataBytesList
        self.dataCount = int.from_bytes(headerBytes[0:4], "little")
        self.type = int.from_bytes(headerBytes[4:8], "little")
        self.attrSize = int.from_bytes(headerBytes[8:12], "little")

class ReqImage(Request):
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=headerBytes, dataBytesList=dataBytesList)
        self.height = int.from_bytes(headerBytes[12:16], "little")
        self.width = int.from_bytes(headerBytes[16:20], "little")
        self.channels = int.from_bytes(headerBytes[20:24], "little")
        self.img = np.ndarray(shape=(self.height, self.width, self.channels), buffer=self.dataBytesList[0], dtype=np.uint8)

class ReqMakeRoom(Request):
    def __init__(self, headerBytes : bytearray, dataBytesList : list[bytearray]):
        super().__init__(headerBytes=headerBytes, dataBytesList=dataBytesList)
        self.roomName = dataBytesList[0].decode()
####
class Response:
    def __init__(self):
        self.headerBytes : bytearray = bytearray()
        self.dataBytesList : list[bytearray] = list()

class ResImage(Response):
    def __init__(self, reqImage : ReqImage, imageByteData : bytearray):
        super().__init__()
        self.headerBytes.extend(reqImage.headerBytes)
        self.dataBytesList.append(imageByteData)

class ResRoomList(Response):
    def __init__(self, roomList : dict[tuple[str, int], tuple[str, list[tuple[str, int]]]]):
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트
        super().__init__()
        self.headerBytes.extend(len(roomList).to_bytes(4, "little")) # datacount
        self.headerBytes.extend(ResponseType.roomList.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(4).to_bytes(4, "little")) # attrSize / 방장 IP 길이, 방장 포트 번호 길이, 방 이름 길이, 방안의 사람 수 길이
        for key in roomList:
            dataBytes = bytearray()

            # 방장 IP
            ipBytes = key[0].encode()
            self.headerBytes.extend(len(ipBytes).to_bytes(4, "little"))
            dataBytes.extend(ipBytes)
            # 방장 포트 번호
            self.headerBytes.extend(int(4).to_bytes(4, "little"))
            dataBytes.extend(key[1].to_bytes(4, "little"))
            # 방 이름
            roomNameBytes = roomList[key][0].encode()
            self.headerBytes.extend(len(roomNameBytes).to_bytes(4, "little"))
            dataBytes.extend(roomNameBytes)
            # 방 안 사람 수
            self.headerBytes.extend(int(4).to_bytes(4, "little"))
            dataBytes.extend(len(roomList[key][1]).to_bytes(4, "little"))

            self.dataBytesList.append(dataBytes)

class ResMakeRoom(Response):
    def __init__(self, isMake : bool):
        super().__init__()
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # datacount
        self.headerBytes.extend(ResponseType.makeRoom.value.to_bytes(4, "little")) # response type
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # attrSize
        self.headerBytes.extend(int(1).to_bytes(4, "little")) # data length  
        self.dataBytesList.append(isMake.to_bytes(1, "little"))
