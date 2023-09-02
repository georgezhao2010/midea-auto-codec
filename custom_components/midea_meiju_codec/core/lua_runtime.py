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
    def __init__(self, file):
        super().__init__(file)

    def build_query(self, append=None):
        json_str = '{"deviceinfo":{"deviceSubType":1},"query":{}}'
        result = self.json_to_data(json_str)
        return result

    def decode_status(self, data):
        data = '{"deviceinfo": {"deviceSubType":1},"msg":{"data": "' + data + '"}}'
        result = self.data_to_json(data)
        status = json.loads(result)
        return status.get("status")