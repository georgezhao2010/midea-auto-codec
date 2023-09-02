import logging
import os
import base64
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    Platform,
    CONF_TYPE,
    CONF_PORT,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_DEVICE_ID,
    CONF_PROTOCOL,
    CONF_TOKEN,
    CONF_NAME
)
from .core.device import MiedaDevice
from .const import (
    DOMAIN,
    DEVICES,
    CONF_KEY,
    CONF_ACCOUNT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, hass_config: dict):
    hass.data.setdefault(DOMAIN, {})
    cjson = os.getcwd() + "/cjson.lua"
    bit = os.getcwd() + "/bit.lua"
    if not os.path.exists(cjson):
        from .const import CJSON_LUA
        cjson_lua = base64.b64decode(CJSON_LUA.encode("utf-8")).decode("utf-8")
        with open(cjson, "wt") as fp:
            fp.write(cjson_lua)
    if not os.path.exists(bit):
        from .const import BIT_LUA
        bit_lua = base64.b64decode(BIT_LUA.encode("utf-8")).decode("utf-8")
        with open(bit, "wt") as fp:
            fp.write(bit_lua)
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry):
    device_type = config_entry.data.get(CONF_TYPE)
    if device_type == CONF_ACCOUNT:
        return True
    name = config_entry.data.get(CONF_NAME)
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device_type = config_entry.data.get(CONF_TYPE)
    token = config_entry.data.get(CONF_TOKEN)
    key = config_entry.data.get(CONF_KEY)
    ip_address = config_entry.options.get(CONF_IP_ADDRESS, None)
    if not ip_address:
        ip_address = config_entry.data.get(CONF_IP_ADDRESS)
    port = config_entry.data.get(CONF_PORT)
    model = config_entry.data.get(CONF_MODEL)
    protocol = config_entry.data.get(CONF_PROTOCOL)
    lua_file = config_entry.data.get("lua_file")
    _LOGGER.error(f"lua_file = {lua_file}")
    if protocol == 3 and (key is None or key is None):
        _LOGGER.error("For V3 devices, the key and the token is required.")
        return False
    device = MiedaDevice(
        name=name,
        device_id=device_id,
        device_type=device_type,
        ip_address=ip_address,
        port=port,
        token=token,
        key=key,
        protocol=protocol,
        model=model,
        lua_file=lua_file,
    )
    if device:
        device.open()
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        if DEVICES not in hass.data[DOMAIN]:
            hass.data[DOMAIN][DEVICES] = {}
        hass.data[DOMAIN][DEVICES][device_id] = device
        for platform in [Platform.BINARY_SENSOR]:
            hass.async_create_task(hass.config_entries.async_forward_entry_setup(
                config_entry, platform))
        #config_entry.add_update_listener(update_listener)
        return True
    return False