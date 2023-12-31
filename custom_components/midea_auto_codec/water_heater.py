from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.const import (
    Platform,
    CONF_DEVICE_ID,
    CONF_DEVICE,
    CONF_ENTITIES,
    ATTR_TEMPERATURE
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
    entities = hass.data[DOMAIN][DEVICES][device_id].get(CONF_ENTITIES).get(Platform.WATER_HEATER)
    devs = []
    if entities is not None:
        for entity_key, config in entities.items():
            devs.append(MideaWaterHeaterEntityEntity(device, manufacturer, rationale, entity_key, config))
    async_add_entities(devs)


class MideaWaterHeaterEntityEntity(MideaEntity, WaterHeaterEntity):
    def __init__(self, device, manufacturer, rationale, entity_key, config):
        super().__init__(device, manufacturer, rationale, entity_key, config)
        self._key_power = self._config.get("power")
        self._key_operation_list = self._config.get("operation_list")
        self._key_min_temp = self._config.get("min_temp")
        self._key_max_temp = self._config.get("max_temp")
        self._key_current_temperature = self._config.get("current_temperature")
        self._key_target_temperature = self._config.get("target_temperature")
        self._attr_temperature_unit = self._config.get("temperature_unit")
        self._attr_precision = self._config.get("precision")

    @property
    def supported_features(self):
        features = 0
        if self._key_target_temperature is not None:
            features |= WaterHeaterEntityFeature.TARGET_TEMPERATURE
        if self._key_operation_list is not None:
            features |= WaterHeaterEntityFeature.OPERATION_MODE
        return features

    @property
    def operation_list(self):
        return list(self._key_operation_list.keys())

    @property
    def current_operation(self):
        return self._dict_get_selected(self._key_operation_list)

    @property
    def current_temperature(self):
        return self._device.get_attribute(self._key_current_temperature)

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
    def is_on(self) -> bool:
        return self._get_status_on_off(self._key_power)

    def turn_on(self):
        self._set_status_on_off(self._key_power, True)

    def turn_off(self):
        self._set_status_on_off(self._key_power, False)

    def set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE not in kwargs:
            return
        temperature = kwargs.get(ATTR_TEMPERATURE)
        temp_int, temp_dec = divmod(temperature, 1)
        temp_int = int(temp_int)
        new_status = {}
        if isinstance(self._key_target_temperature, list):
            new_status[self._key_target_temperature[0]] = temp_int
            new_status[self._key_target_temperature[1]] = temp_dec
        else:
            new_status[self._key_target_temperature] = temperature
        self._device.set_attributes(new_status)

    def set_operation_mode(self, operation_mode: str) -> None:
        new_status = self._key_operation_list.get(operation_mode)
        self._device.set_attributes(new_status)

    def update_state(self, status):
        try:
            self.schedule_update_ha_state()
        except Exception as e:
            pass

