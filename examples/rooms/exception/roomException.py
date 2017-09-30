

class Code():
    GENERIC_ERROR_CODE=999
    TRANSPORT_ERROR_CODE=803
    TRANSPORT_RESPONSE_ERROR_CODE=802
    TRANSPORT_REQUEST_ERROR_CODE=801

    MEDIA_MUTE_ERROR_CODE=307
    MEDIA_NOT_A_WEB_ENDPOINT_ERROR_CODE=306
    MEDIA_RTP_ENDPOINT_ERROR_CODE=305
    MEDIA_WEBRTC_ENDPOINT_ERROR_CODE=304
    MEDIA_ENDPOINT_ERROR_CODE=303
    MEDIA_SDP_ERROR_CODE=302
    MEDIA_GENERIC_ERROR_CODE=301

    ROOM_CANNOT_BE_CREATED_ERROR_CODE=204
    ROOM_CLOSED_ERROR_CODE=203
    ROOM_NOT_FOUND_ERROR_CODE=202
    ROOM_GENERIC_ERROR_CODE=201
    USER_NOT_STREAMING_ERROR_CODE=105
    EXISTING_USER_IN_ROOM_ERROR_CODE=104
    USER_CLOSED_ERROR_CODE=103
    USER_NOT_FOUND_ERROR_CODE=102
    USER_GENERIC_ERROR_CODE=101

class RoomException(Exception):

    def __init__(self, code, message):
        self.serialVersionUID = 1
        if not code:
            self.code = Code.GENERIC_ERROR_CODE
        else:
            self.code =code
        self.message = message

    def getCode(self):
        return self.code

    def getCodeValue(self):
        return self.code.getValue()

    def toString(self):
        return "Code: " + self.getCodeValue() + " " + self.message



