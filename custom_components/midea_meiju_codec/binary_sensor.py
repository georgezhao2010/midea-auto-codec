from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass
)
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_DEVICE,
    CONF_ENTITIES
)
from .const import (
    DOMAIN,
    DEVICES
)
from .midea_entities import MideaBinaryBaseEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES][device_id].get(CONF_DEVICE)
    manufacturer = hass.data[DOMAIN][DEVICES][device_id].get("manufacturer")
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.BINARY_SENSOR)
    devs = [MideaDeviceStatusSensorEntity(device, manufacturer,"Status", {})]
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaBinarySensorEntity(device, manufacturer, entity_key, config))
    async_add_entities(devs)


class MideaDeviceStatusSensorEntity(MideaBinaryBaseEntity, BinarySensorEntity):

    @property
    def device_class(self):
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def icon(self):
        return "mdi:devices"

    @property
    def is_on(self):
        return self._device.connected

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


class MideaBinarySensorEntity(MideaBinaryBaseEntity, BinarySensorEntity):
    pass
