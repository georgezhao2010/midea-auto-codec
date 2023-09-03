import logging
from homeassistant.const import (
    CONF_DEVICE_ID,
    STATE_ON,
    STATE_OFF
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from .midea_entities import MideaEntity
from .const import (
    DOMAIN,
    DEVICES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    binary_sensors = []
    sensor = MideaDeviceStatusSensor(device, "status")
    binary_sensors.append(sensor)
    async_add_entities(binary_sensors)


class MideaDeviceStatusSensor(MideaEntity):
    @property
    def device_class(self):
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def state(self):
        return STATE_ON if self._device.connected else STATE_OFF

    @property
    def name(self):
        return f"{self._device_name} Status"

    @property
    def icon(self):
        return "mdi:devices"

    @property
    def is_on(self):
        return self.state == STATE_ON

    @property
    def available(self):
        return True

    @property
    def extra_state_attributes(self) -> dict:
        return self._device.attributes

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            pass
