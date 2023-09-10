from homeassistant.components.fan import FanEntity, FanEntityFeature
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
from .core.logger import MideaLogger


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES][device_id].get(CONF_DEVICE)
    manufacturer = hass.data[DOMAIN][DEVICES][device_id].get("manufacturer")
    rationale = hass.data[DOMAIN][DEVICES][device_id].get("rationale")
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.FAN)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaFanEntity(device, manufacturer, rationale, entity_key, config))
    async_add_entities(devs)


class MideaFanEntity(MideaEntity, FanEntity):
    def __init__(self, device, manufacturer, rationale, entity_key, config):
        super().__init__(device, manufacturer, rationale, entity_key, config)
        self._key_power = self._config.get("power")
        self._key_preset_modes = self._config.get("preset_modes")
        self._key_speeds = self._config.get("speeds")
        self._key_oscillate = self._config.get("oscillate")
        self._key_directions = self._config.get("directions")
        self._attr_speed_count = len(self._key_speeds) if self._key_speeds else 0

    @property
    def supported_features(self):
        features = 0
        if self._key_preset_modes is not None and len(self._key_preset_modes) > 0:
            features |= FanEntityFeature.PRESET_MODE
        if self._key_speeds is not None and len(self._key_speeds) > 0:
            features |= FanEntityFeature.SET_SPEED
        if self._key_oscillate is not None:
            features |= FanEntityFeature.OSCILLATE
        if self._key_directions is not None and len(self._key_directions) > 0:
            features |= FanEntityFeature.DIRECTION
        return features

    @property
    def is_on(self) -> bool:
        return self._get_status_on_off(self._key_power)

    @property
    def preset_modes(self):
        return list(self._key_preset_modes.keys())

    @property
    def preset_mode(self):
        return self._dict_get_selected(self._key_preset_modes)

    @property
    def percentage(self):
        index = self._list_get_selected(self._key_speeds)
        if index is None:
            return None
        return round((index + 1) * 100 / self._attr_speed_count)

    @property
    def oscillating(self):
        return self._get_status_on_off(self._key_oscillate)

    def turn_on(
            self,
            percentage: int | None = None,
            preset_mode: str | None = None,
            **kwargs,
    ):
        if preset_mode is not None:
            new_status = self._key_preset_modes.get(preset_mode)
        else:
            new_status = {}
        if percentage is not None:
            index = round(percentage * self._attr_speed_count / 100) - 1
            new_status.update(self._key_speeds[index])
        new_status[self._key_power] = self._rationale[1]
        self._device.set_attributes(new_status)

    def turn_off(self):
        self._set_status_on_off(self._key_power, False)

    def set_percentage(self, percentage: int):
        index = round(percentage * self._attr_speed_count / 100)
        if 0 < index < len(self._key_speeds):
            new_status = self._key_speeds[index - 1]
            self._device.set_attributes(new_status)

    def set_preset_mode(self, preset_mode: str):
        new_status = self._key_preset_modes.get(preset_mode)
        self._device.set_attributes(new_status)

    def oscillate(self, oscillating: bool):
        if self.oscillating != oscillating:
            self._set_status_on_off(self._key_oscillate, oscillating)

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            pass
