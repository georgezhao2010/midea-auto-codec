import threading
import socket
import time
from enum import IntEnum
from .security import LocalSecurity, MSGTYPE_HANDSHAKE_REQUEST, MSGTYPE_ENCRYPTED_REQUEST
from .packet_builder import PacketBuilder
from .lua_runtime import MideaCodec
from .logger import MideaLogger


class AuthException(Exception):
    pass


class ResponseException(Exception):
    pass


class RefreshFailed(Exception):
    pass


class ParseMessageResult(IntEnum):
    SUCCESS = 0
    PADDING = 1
    ERROR = 99


class MiedaDevice(threading.Thread):
    def __init__(self,
                 name: str,
                 device_id: int,
                 device_type: int,
                 ip_address: str,
                 port: int,
                 token: str | None,
                 key: str | None,
                 protocol: int,
                 model: str | None,
                 subtype: int | None,
                 sn: str | None,
                 sn8: str | None,
                 lua_file: str | None):
        threading.Thread.__init__(self)
        self._socket = None
        self._ip_address = ip_address
        self._port = port
        self._security = LocalSecurity()
        self._token = bytes.fromhex(token) if token else None
        self._key = bytes.fromhex(key) if key else None
        self._buffer = b""
        self._device_name = name
        self._device_id = device_id
        self._device_type = device_type
        self._protocol = protocol
        self._model = model
        self._updates = []
        self._is_run = False
        self._subtype = subtype
        self._sn = sn
        self._sn8 = sn8
        self._attributes = {
            "device_type": "T0x%02X" % device_type,
            "sn": sn,
            "sn8": sn8,
            "subtype": subtype
        }
        self._refresh_interval = 30
        self._heartbeat_interval = 10
        self._connected = False
        self._queries = [{}]
        self._centralized = []
        self._lua_runtime = MideaCodec(lua_file, sn=sn, subtype=subtype) if lua_file is not None else None

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_type(self):
        return self._device_type

    @property
    def model(self):
        return self._model

    @property
    def sn(self):
        return self._sn

    @property
    def sn8(self):
        return self._sn8

    @property
    def subtype(self):
        return self._subtype

    @property
    def attributes(self):
        return self._attributes

    @property
    def connected(self):
        return self._connected

    def set_refresh_interval(self, refresh_interval):
        self._refresh_interval = refresh_interval

    @property
    def queries(self):
        return self._queries

    @queries.setter
    def queries(self, queries: list):
        self._queries = queries

    @property
    def centralized(self):
        return self._centralized

    @centralized.setter
    def centralized(self, centralized: list):
        self._centralized = centralized

    def get_attribute(self, attribute):
        return self._attributes.get(attribute)

    def set_attribute(self, attribute, value):
        if attribute in self._attributes.keys():
            new_status = {}
            for attr in self._centralized:
                new_status[attr] = self._attributes.get(attr)
            new_status[attribute] = value
            if set_cmd := self._lua_runtime.build_control(new_status):
                self.build_send(set_cmd)

    def set_attributes(self, attributes):
        new_status = {}
        for attr in self._centralized:
            new_status[attr] = self._attributes.get(attr)
        has_new = False
        for attribute, value in attributes.items():
            if attribute in self._attributes.keys():
                has_new = True
                new_status[attribute] = value
        if has_new:
            if set_cmd := self._lua_runtime.build_control(new_status):
                self.build_send(set_cmd)

    @staticmethod
    def fetch_v2_message(msg):
        result = []
        while len(msg) > 0:
            factual_msg_len = len(msg)
            if factual_msg_len < 6:
                break
            alleged_msg_len = msg[4] + (msg[5] << 8)
            if factual_msg_len >= alleged_msg_len:
                result.append(msg[:alleged_msg_len])
                msg = msg[alleged_msg_len:]
            else:
                break
        return result, msg

    def connect(self, refresh=False):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10)
            MideaLogger.debug(f"Connecting to {self._ip_address}:{self._port}", self._device_id)
            self._socket.connect((self._ip_address, self._port))
            MideaLogger.debug(f"Connected", self._device_id)
            if self._protocol == 3:
                self.authenticate()
            MideaLogger.debug(f"Authentication success", self._device_id)
            self.device_connected(True)
            if refresh:
                self.refresh_status()
            return True
        except socket.timeout:
            MideaLogger.debug(f"Connection timed out", self._device_id)
        except socket.error:
            MideaLogger.debug(f"Connection error", self._device_id)
        except AuthException:
            MideaLogger.debug(f"Authentication failed", self._device_id)
        except ResponseException:
            MideaLogger.debug(f"Unexpected response received", self._device_id)
        except RefreshFailed:
            MideaLogger.debug(f"Refresh status is timed out", self._device_id)
        except Exception as e:
            MideaLogger.error(f"Unknown error: {e.__traceback__.tb_frame.f_globals['__file__']}, "
                              f"{e.__traceback__.tb_lineno}, {repr(e)}")
        self.device_connected(False)
        return False

    def authenticate(self):
        request = self._security.encode_8370(
            self._token, MSGTYPE_HANDSHAKE_REQUEST)
        MideaLogger.debug(f"Handshaking")
        self._socket.send(request)
        response = self._socket.recv(512)
        if len(response) < 20:
            raise AuthException()
        response = response[8: 72]
        self._security.tcp_key(response, self._key)

    def send_message(self, data):
        if self._protocol == 3:
            self.send_message_v3(data, msg_type=MSGTYPE_ENCRYPTED_REQUEST)
        else:
            self.send_message_v2(data)

    def send_message_v2(self, data):
        if self._socket is not None:
            self._socket.send(data)
        else:
            MideaLogger.debug(f"Send failure, device disconnected, data: {data.hex()}")

    def send_message_v3(self, data, msg_type=MSGTYPE_ENCRYPTED_REQUEST):
        data = self._security.encode_8370(data, msg_type)
        self.send_message_v2(data)

    def build_send(self, cmd):
        MideaLogger.debug(f"Sending: {cmd}")
        bytes_cmd = bytes.fromhex(cmd)
        msg = PacketBuilder(self._device_id, bytes_cmd).finalize()
        self.send_message(msg)

    def refresh_status(self):
        for query in self._queries:
            if query_cmd := self._lua_runtime.build_query(query):
                self.build_send(query_cmd)

    def parse_message(self, msg):
        if self._protocol == 3:
            messages, self._buffer = self._security.decode_8370(self._buffer + msg)
        else:
            messages, self._buffer = self.fetch_v2_message(self._buffer + msg)
        if len(messages) == 0:
            return ParseMessageResult.PADDING
        for message in messages:
            if message == b"ERROR":
                return ParseMessageResult.ERROR
            payload_len = message[4] + (message[5] << 8) - 56
            payload_type = message[2] + (message[3] << 8)
            if payload_type in [0x1001, 0x0001]:
                # Heartbeat detected
                pass
            elif len(message) > 56:
                cryptographic = message[40:-16]
                if payload_len % 16 == 0:
                    decrypted = self._security.aes_decrypt(cryptographic)
                    MideaLogger.debug(f"Received: {decrypted.hex()}")
                    # 这就是最终消息
                    if status := self._lua_runtime.decode_status(decrypted.hex()):
                        MideaLogger.debug(f"Decoded: {status}")
                        new_status = {}
                        for single in status.keys():
                            value = status.get(single)
                            if single not in self._attributes or self._attributes[single] != value:
                                self._attributes[single] = value
                                new_status[single] = value
                        if len(new_status) > 0:
                            self.update_all(new_status)
        return ParseMessageResult.SUCCESS

    def send_heartbeat(self):
        msg = PacketBuilder(self._device_id, bytearray([0x00])).finalize(msg_type=0)
        self.send_message(msg)

    def device_connected(self, connected=True):
        self._connected = connected
        status = {"connected": connected}
        self.update_all(status)

    def register_update(self, update):
        self._updates.append(update)

    def update_all(self, status):
        MideaLogger.debug(f"Status update: {status}")
        for update in self._updates:
            update(status)

    def open(self):
        if not self._is_run:
            self._is_run = True
            threading.Thread.start(self)

    def close(self):
        if self._is_run:
            self._is_run = False
            self._lua_runtime = None
            self.close_socket()

    def close_socket(self):
        self._buffer = b""
        if self._socket:
            self._socket.close()
            self._socket = None

    def set_ip_address(self, ip_address):
        MideaLogger.debug(f"Update IP address to {ip_address}")
        self._ip_address = ip_address
        self.close_socket()

    def run(self):
        while self._is_run:
            while self._socket is None:
                if self.connect(refresh=True) is False:
                    if not self._is_run:
                        return
                    self.close_socket()
                    time.sleep(5)
            timeout_counter = 0
            start = time.time()
            previous_refresh = start
            previous_heartbeat = start
            self._socket.settimeout(1)
            while True:
                try:
                    now = time.time()
                    if now - previous_refresh >= self._refresh_interval:
                        self.refresh_status()
                        previous_refresh = now
                    if now - previous_heartbeat >= self._heartbeat_interval:
                        self.send_heartbeat()
                        previous_heartbeat = now
                    msg = self._socket.recv(512)
                    msg_len = len(msg)
                    if msg_len == 0:
                        raise socket.error("Connection closed by peer")
                    result = self.parse_message(msg)
                    if result == ParseMessageResult.ERROR:
                        MideaLogger.debug(f"Message 'ERROR' received")
                        self.close_socket()
                        break
                    elif result == ParseMessageResult.SUCCESS:
                        timeout_counter = 0
                except socket.timeout:
                    timeout_counter = timeout_counter + 1
                    if timeout_counter >= 120:
                        MideaLogger.debug(f"Heartbeat timed out")
                        self.close_socket()
                        break
                except socket.error as e:
                    MideaLogger.debug(f"Socket error {repr(e)}")
                    self.close_socket()
                    break
                except Exception as e:
                    MideaLogger.error(f"Unknown error :{e.__traceback__.tb_frame.f_globals['__file__']}, "
                                      f"{e.__traceback__.tb_lineno}, {repr(e)}")
                    self.close_socket()
                    break


