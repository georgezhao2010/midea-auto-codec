import lupa
import logging
import threading
import json

_LOGGER = logging.getLogger(__name__)


class LuaRuntime:
    def __init__(self, file):
        self._runtimes = lupa.LuaRuntime()
        string = f'dofile("{file}")'
        self._runtimes.execute(string)
        self._lock = threading.Lock()
        self._json_to_data = self._runtimes.eval("function(param) return jsonToData(param) end")
        self._data_to_json = self._runtimes.eval("function(param) return dataToJson(param) end")

    def json_to_data(self, json):
        with self._lock:
            result = self._json_to_data(json)
        return result

    def data_to_json(self, data):
        with self._lock:
            result = self._data_to_json(data)
        return result


class MideaCodec(LuaRuntime):
    def __init__(self, file, sn=None, sub_type=None):
        super().__init__(file)
        self._sn = sn
        self._sub_type = sub_type

    def _build_base_dict(self):
        device_info ={}
        if self._sn is not None:
            device_info["deviceSN"] = self._sn
        if self._sub_type is not None:
            device_info["deviceSN"] = self._sub_type
        base_dict = {
            "deviceinfo": device_info
        }
        return base_dict

    def build_query(self, append=None):
        query_dict = self._build_base_dict()
        query_dict["query"] = {} if append is None else append
        json_str = json.dumps(query_dict)
        result = self.json_to_data(json_str)
        return result

    def build_control(self, append=None):
        query_dict = self._build_base_dict()
        query_dict["control"] = {} if append is None else append
        json_str = json.dumps(query_dict)
        result = self.json_to_data(json_str)
        return result

    def build_status(self, append=None):
        query_dict = self._build_base_dict()
        query_dict["status"] = {} if append is None else append
        json_str = json.dumps(query_dict)
        result = self.json_to_data(json_str)
        return result

    def decode_status(self, data: str):
        data_dict = self._build_base_dict()
        data_dict["msg"] = {
            "data": data
        }
        json_str = json.dumps(data_dict)
        result = self.data_to_json(json_str)
        status = json.loads(result)
        return status.get("status")