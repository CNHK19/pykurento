
class JsonRpcConstants():

    JSON_RPC_VERSION = "2.0"
    JSON_RPC_PROPERTY = "jsonrpc"
    PARAMS_PROPERTY = "params"
    ID_PROPERTY = "id"
    RESULT_PROPERTY = "result"
    ERROR_PROPERTY = "error"
    DATA_PROPERTY = "data"
    METHOD_PROPERTY = "method"
    SESSION_ID_PROPERTY = "sessionId"
    METHOD_START = "start"
    METHOD_TERMINATE = "terminate"
    METHOD_POLL = "poll"
    METHOD_EXECUTE = "execute"
    METHOD_CONNECT = "connect"
    METHOD_PING = "ping"
    METHOD_CLOSE = "closeSession"
    PONG_PAYLOAD = "value"
    PONG = "pong"
    EVENT_SESSION_TERMINATED = "sessionTerminated"
    EVENT_SESSION_ERROR = "sessionError"
    RECONNECTION_ERROR = "reconnection error"
    RECONNECTION_SUCCESSFUL = "reconnection successful"
    ERROR_NO_ERROR = 0
    ERROR_APPLICATION_TERMINATION = 1
    ERROR_INVALID_PARAM = -32602
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_REQUEST = -32600
    ERROR_PARSE_ERROR = -32700
    ERROR_INTERNAL_ERROR = -32603
    ERROR_SERVER_ERROR = -32000