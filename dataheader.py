from enum import Enum

class RequestType(Enum):
    image = 1
    roomList = 2

class ResponseType(Enum):
    image = 1
    roomList = 2

####
class reqHeader:
    def __init__(self, headerBytes : bytearray):
        self.dataCount = int.from_bytes(headerBytes[0:4])
        self.type = int.from_bytes(headerBytes[4:8])
        self.attrSize = int.from_bytes(headerBytes[8:12])

class reqImage(reqHeader):
    def __init__(self, headerBytes : bytearray):
        super().__init__(headerBytes=headerBytes)
        self.height = int.from_bytes(headerBytes[12:16])
        self.width = int.from_bytes(headerBytes[16:24])
        self.channels = int.from_bytes(headerBytes[24:32])

####
class resRoomList:
    def __init__(self, roomList : dict[tuple[str, int], list[tuple[str, int]]]):
        # 키는 방장 클라이언트의 어드레스(IP와 포트 번호), 밸류는 방에 존재하는 인원의 어드레스의 리스트
        self.byteArray = bytearray()
        self.byteArray.extend(len(roomList).to_bytes(4, "little")) # datacount
        self.byteArray.extend(int(ResponseType.roomList).to_bytes(4, "little")) # response type
        self.byteArray.extend(int(4).to_bytes(4, "little")) # attrSize / 방장 IP 길이, 방장 포트 번호 길이, 방 이름 길이, 방안의 사람 수 길이
        
        for key in roomList:
            self.byteArray.extend(key[0].)
            for address in roomList[key]:
