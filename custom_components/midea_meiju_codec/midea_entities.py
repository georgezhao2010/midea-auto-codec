from homeassistant.helpers.entity import Entity
from .const import DOMAIN


class MideaEntity(Entity):
    def __init__(self, device, entity_key: str):
        self._device = device
        self._device.register_update(self.update_state)
        self._entity_key = entity_key
        self._unique_id = f"{DOMAIN}.{self._device.device_id}_{entity_key}"
        self.entity_id = self._unique_id
        self._device_name = self._device.device_name

    @property
    def device(self):
        return self._device

    @property
    def device_info(self):
        return {
            "manufacturer": "Midea",
            "model": f"{self._device.model} ({self._device.sn8})",
            "identifiers": {(DOMAIN, self._device.device_id)},
            "name": self._device_name
        }

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        return self._device.get_attribute(self._entity_key)

    @property
    def available(self):
        return self._device.connected

    def update_state(self, status):
        if self._entity_key in status or "connected" in status:
            try:
                self.schedule_update_ha_state()
            except Exception as e:
                pass