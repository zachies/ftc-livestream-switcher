class Payload(object):
    def __init__(self, number: int, shortName: str, field: int):
        self.number = number
        self.shortName = shortName
        self.field = field

class ScoringResponse(object):
    def __init__(self, updateTime: int, updateType: str, payload: Payload):
        self.updateTime = updateTime
        self.updateType = updateType
        self.payload = payload