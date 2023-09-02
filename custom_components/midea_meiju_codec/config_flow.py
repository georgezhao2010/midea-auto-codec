import voluptuous as vol
import logging
import os
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant import config_entries
from homeassistant.const import (
    CONF_TYPE,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DEVICE,
    CONF_PORT,
    CONF_MODEL,
    CONF_IP_ADDRESS,
    CONF_DEVICE_ID,
    CONF_PROTOCOL,
    CONF_TOKEN,
    CONF_NAME

)
from .core.cloud import MeijuCloudExtend
from .core.discover import discover
from .core.device import MiedaDevice
from .const import (
    DOMAIN,
    STORAGE_PATH,
    CONF_ACCOUNT,
    CONF_HOME,
    CONF_KEY
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    _session = None
    _cloud = None
    _current_home = None
    _device_list = {}

    def _get_configured_account(self):
        for entry in self._async_current_entries():
            if entry.data.get(CONF_TYPE) == CONF_ACCOUNT:
                return entry.data.get(CONF_USERNAME), entry.data.get(CONF_PASSWORD)
        return None, None

    def _device_configured(self, device_id):
        for entry in self._async_current_entries():
            if device_id == entry.data.get(CONF_DEVICE_ID):
                return True
        return False

    async def async_step_user(self, user_input=None, error=None):
        username, password = self._get_configured_account()
        if username is not None and password is not None:
            if self._session is None:
                self._session = async_create_clientsession(self.hass)
            if self._cloud is None:
                self._cloud = MeijuCloudExtend(self._session, username, password)
            if await self._cloud.login():
                return await self.async_step_home()
        if user_input is not None:
            return self.async_create_entry(
                title=f"{user_input[CONF_USERNAME]}",
                data={
                    CONF_TYPE: CONF_ACCOUNT,
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD]
                })
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str
            }),
            errors={"base": error} if error else None
        )

    async def async_step_home(self, user_input=None, error=None):
        if user_input is not None:
            self._current_home = user_input[CONF_HOME]
            return await self.async_step_device()
        homes = await self._cloud.get_homegroups()
        home_list = {}
        for home in homes:
            home_list[int(home.get("homegroupId"))] = home.get("name")
        return self.async_show_form(
            step_id="home",
            data_schema=vol.Schema({
                vol.Required(CONF_HOME, default=list(home_list.keys())[0]):
                    vol.In(home_list),
            }),
            errors={"base": error} if error else None
        )

    async def async_step_device(self, user_input=None, error=None):
        if user_input is not None:
            # 下载lua
            # 本地尝试连接设备
            device = self._device_list[user_input[CONF_DEVICE]]
            if not device.get("online"):
                return await self.async_step_device(error="offline_error")
            discover_devices = discover([device["type"]])
            _LOGGER.debug(discover_devices)
            if discover_devices is None or len(discover_devices) == 0:
                return await self.async_step_device(error="discover_failed")
            current_device = discover_devices.get(user_input[CONF_DEVICE])
            if current_device is None:
                return await self.async_step_device(error="discover_failed")
            os.makedirs(self.hass.config.path(STORAGE_PATH), exist_ok=True)
            path = self.hass.config.path(STORAGE_PATH)
            file = await self._cloud.get_lua(device["sn"], device["type"], path, device["enterprise_code"])
            if file is None:
                return await self.async_step_device(error="download_lua_failed")
            use_token = None
            use_key = None
            connected = False
            if current_device.get("protocol") == 3:
                for byte_order_big in [False, True]:
                    token, key = await self._cloud.get_token(user_input[CONF_DEVICE], byte_order_big=byte_order_big)
                    if token and key:
                        dm = MiedaDevice(
                            name=device.get("name"),
                            device_id=user_input[CONF_DEVICE],
                            device_type=current_device.get(CONF_TYPE),
                            ip_address=current_device.get(CONF_IP_ADDRESS),
                            port=current_device.get(CONF_PORT),
                            token=token,
                            key=key,
                            protocol=3,
                            model=device.get(CONF_MODEL),
                            lua_file=None
                        )
                        if dm.connect():
                            use_token = token
                            use_key = key
                            connected = True
                    else:
                        return await self.async_step_device(error="cant_get_token")
            else:
                dm = MiedaDevice(
                    name=device.get("name"),
                    device_id=user_input[CONF_DEVICE],
                    device_type=current_device.get(CONF_TYPE),
                    ip_address=current_device.get(CONF_IP_ADDRESS),
                    port=current_device.get(CONF_PORT),
                    token=use_token,
                    key=use_key,
                    protocol=2,
                    model=device.get(CONF_MODEL),
                    lua_file=None
                )
                if dm.connect():
                    connected = True

            if not connected:
                return await self.async_step_device(error="connect_error")
            return self.async_create_entry(
                title=device.get("name"),
                data={
                    CONF_NAME: device.get("name"),
                    CONF_DEVICE_ID: user_input[CONF_DEVICE],
                    CONF_TYPE: current_device.get("type"),
                    CONF_PROTOCOL: current_device.get("protocol"),
                    CONF_IP_ADDRESS: current_device.get("ip_address"),
                    CONF_PORT: current_device.get("port"),
                    CONF_MODEL: device.get("model"),
                    CONF_TOKEN: use_token,
                    CONF_KEY: use_key,
                    "lua_file": file,
                    "sn": device.get("sn"),
                    "sn8": device.get("sn8"),
                })
        devices = await self._cloud.get_devices(self._current_home)
        self._device_list = {}
        device_list = {}
        for device in devices:
            if not self._device_configured(int(device.get("applianceCode"))):
                self._device_list[int(device.get("applianceCode"))] = {
                    "name": device.get("name"),
                    "type": int(device.get("type"), 16),
                    "sn8": device.get("sn8"),
                    "sn": device.get("sn"),
                    "model": device.get("productModel"),
                    "enterprise_code": device.get("enterpriseCode"),
                    "online": device.get("onlineStatus") == "1"
                }
                device_list[int(device.get("applianceCode"))] = \
                    f"{device.get('name')} ({'在线' if device.get('onlineStatus') == '1' else '离线'})"

        if len(self._device_list) == 0:
            return await self.async_step_device(error="no_new_devices")
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE, default=list(device_list.keys())[0]):
                    vol.In(device_list),
            }),
            errors={"base": error} if error else None
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        pass