from homeassistant.components.switch import SwitchEntity
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_DEVICE,
    CONF_ENTITIES,
    STATE_ON,
    STATE_OFF
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
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.SWITCH)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaSwitchEntity(device, manufacturer, entity_key, config))
    async_add_entities(devs)


class MideaSwitchEntity(MideaBinaryBaseEntity, SwitchEntity):

    def turn_on(self):
        self._device.set_attribute(attribute=self._entity_key, value=self._binary_rationale[1])

    def turn_off(self):
        self._device.set_attribute(attribute=self._entity_key, value=self._binary_rationale[0])
