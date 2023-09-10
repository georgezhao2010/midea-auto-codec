from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_DEVICE,
    CONF_ENTITIES,
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
    rationale = hass.data[DOMAIN][DEVICES][device_id].get("rationale")
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.SELECT)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaSelectEntity(device, manufacturer, rationale, entity_key, config))
    async_add_entities(devs)


class MideaSelectEntity(MideaEntity, SelectEntity):
    def __init__(self, device, manufacturer, rationale, entity_key, config):
        super().__init__(device, manufacturer, rationale, entity_key, config)
        self._key_options = self._config.get("options")

    @property
    def options(self):
        return list(self._key_options.keys())

    @property
    def current_option(self):
        return self._dict_get_selected(self._key_options)

    def select_option(self, option: str):
        new_status = self._key_options.get(option)
        self._device.set_attributes(new_status)

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            pass

