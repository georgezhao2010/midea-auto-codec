from homeassistant.components.sensor import SensorEntity
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
from .midea_entities import MideaEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES][device_id].get(CONF_DEVICE)
    manufacturer = hass.data[DOMAIN][DEVICES][device_id].get("manufacturer")
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.SENSOR)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaSensorEntity(device, manufacturer, entity_key, config))
    async_add_entities(devs)


class MideaSensorEntity(MideaEntity, SensorEntity):

    @property
    def state(self):
        return self._device.get_attribute(self._entity_key)
