from homeassistant.components.climate import *
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_DEVICE,
)
from .const import (
    DOMAIN,
    DEVICES
)
from .core.logger import MideaLogger
from .midea_entities import MideaEntity, Rationale


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES][device_id].get(CONF_DEVICE)
    manufacturer = hass.data[DOMAIN][DEVICES][device_id].get("manufacturer")
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.CLIMATE)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaClimateEntity(device, manufacturer, entity_key, config))
    async_add_entities(devs)


class MideaClimateEntity(MideaEntity, ClimateEntity):
    def __init__(self, device, manufacturer, entity_key, config):
        super().__init__(device, manufacturer, entity_key, config)
        self._key_power = self._config.get("power")
        self._key_hvac_modes = self._config.get("hvac_modes")
        self._key_preset_modes = self._config.get("preset_modes")
        self._key_aux_heat = self._config.get("aux_heat")
        self._key_swing_modes = self._config.get("swing_modes")
        self._key_fan_modes = self._config.get("fan_modes")
        self._key_current_temperature_low = self._config.get("current_temperature_low")
        self._key_min_temp = self._config.get("min_temp")
        self._key_max_temp = self._config.get("max_temp")
        self._key_target_temperature = self._config.get("target_temperature")
        self._attr_temperature_unit = self._config.get("temperature_unit")
        self._attr_precision = self._config.get("precision")

    @property
    def state(self):
        return self.hvac_mode

    @property
    def supported_features(self):
        features = 0
        if self._key_target_temperature is not None:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self._key_preset_modes is not None:
            features |= ClimateEntityFeature.PRESET_MODE
        if self._key_aux_heat is not None:
            features |= ClimateEntityFeature.AUX_HEAT
        if self._key_swing_modes is not None:
            features |= ClimateEntityFeature.SWING_MODE
        if self._key_fan_modes is not None:
            features |= ClimateEntityFeature.FAN_MODE
        return features

    @property
    def current_temperature(self):
        return self._device.get_attribute("indoor_temperature")

    @property
    def target_temperature(self):
        if isinstance(self._key_target_temperature, list):
            temp_int = self._device.get_attribute(self._key_target_temperature[0])
            tem_dec = self._device.get_attribute(self._key_target_temperature[1])
            if temp_int is not None and tem_dec is not None:
                return temp_int + tem_dec
            return None
        else:
            return self._device.get_attribute(self._key_target_temperature)

    @property
    def min_temp(self):
        if isinstance(self._key_min_temp, str):
            return float(self._device.get_attribute(self._key_min_temp))
        else:
            return float(self._key_min_temp)

    @property
    def max_temp(self):
        if isinstance(self._key_max_temp, str):
            return float(self._device.get_attribute(self._key_max_temp))
        else:
            return float(self._key_max_temp)

    @property
    def target_temperature_low(self):
        return self.min_temp

    @property
    def target_temperature_high(self):
        return self.max_temp

    @property
    def preset_modes(self):
        return list(self._key_preset_modes.keys())

    @property
    def preset_mode(self):
        return self.get_mode(self._key_preset_modes)

    @property
    def fan_modes(self):
        return list(self._key_fan_modes.keys())

    @property
    def fan_mode(self):
        return self.get_mode(self._key_fan_modes, Rationale.LESS)

    @property
    def swing_modes(self):
        return list(self._key_swing_modes.keys())

    @property
    def swing_mode(self):
        return self.get_mode(self._key_swing_modes)

    @property
    def is_on(self) -> bool:
        return self.hvac_mode != HVACMode.OFF

    @property
    def hvac_mode(self):
        return self.get_mode(self._key_hvac_modes)

    @property
    def hvac_modes(self):
        return list(self._key_hvac_modes.keys())

    @property
    def is_aux_heat(self):
        return self._device.get_attribute(self._key_aux_heat) == "on"

    def turn_on(self):
        self._device.set_attribute(attribute=self._key_power, value="on")

    def turn_off(self):
        self._device.set_attribute(attribute=self._key_power, value="off")

    def set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE not in kwargs:
            return
        temperature = kwargs.get(ATTR_TEMPERATURE)
        temp_int, temp_dec = divmod(temperature, 1)
        temp_int = int(temp_int)
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        if hvac_mode is not None:
            new_status = self._key_hvac_modes.get(hvac_mode)
        else:
            new_status = {}
        if isinstance(self._key_target_temperature, list):
            new_status[self._key_target_temperature[0]] = temp_int
            new_status[self._key_target_temperature[1]] = temp_dec
        else:
            new_status[self._key_target_temperature] = temperature
        MideaLogger.error(new_status)
        self._device.set_attributes(new_status)

    def set_fan_mode(self, fan_mode: str):
        new_statis = self._key_fan_modes.get(fan_mode)
        self._device.set_attributes(new_statis)

    def set_preset_mode(self, preset_mode: str):
        new_statis = self._key_preset_modes.get(preset_mode)
        self._device.set_attributes(new_statis)

    def set_hvac_mode(self, hvac_mode: str):
        new_status = self._key_hvac_modes.get(hvac_mode)
        self._device.set_attributes(new_status)

    def set_swing_mode(self, swing_mode: str):
        new_status = self._key_swing_modes.get(swing_mode)
        self._device.set_attributes(new_status)

    def turn_aux_heat_on(self) -> None:
        self._device.set_attribute(attr=self._key_aux_heat, value="on")

    def turn_aux_heat_off(self) -> None:
        self._device.set_attribute(attr=self._key_aux_heat, value="off")

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            pass
