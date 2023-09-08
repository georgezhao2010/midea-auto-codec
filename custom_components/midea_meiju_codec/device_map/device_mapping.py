from homeassistant.const import *
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.climate import (
    HVACMode,
    PRESET_NONE,
    PRESET_ECO,
    PRESET_COMFORT,
    PRESET_SLEEP,
    PRESET_BOOST,
    SWING_OFF,
    SWING_BOTH,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)

DEVICE_MAPPING = {
    "0xAC": {
        "default": {
            "manufacturer": "美的",
            "queries": [{}, {"query_type": "prevent_straight_wind"}],
            "centralized": ["power", "temperature", "small_temperature", "mode", "eco", "comfort_power_save",
                            "comfort_sleep", "strong_wind", "wind_swing_lr", "wind_swing_lr", "wind_speed",
                            "ptc", "dry"],
            "entities": {
                Platform.CLIMATE: {
                    "thermostat": {
                        "name": "Thermostat",
                        "power": "power",
                        "target_temperature": ["temperature", "small_temperature"],
                        "hvac_modes": {
                            HVACMode.OFF: {"power": "off"},
                            HVACMode.HEAT: {"power": "on", "mode": "heat"},
                            HVACMode.COOL: {"power": "on", "mode": "cool"},
                            HVACMode.AUTO: {"power": "on", "mode": "auto"},
                            HVACMode.DRY: {"power": "on", "mode": "dry"},
                            HVACMode.FAN_ONLY: {"power": "on", "mode": "fan"}
                        },
                        "preset_modes": {
                            PRESET_NONE: {
                                "eco": "off",
                                "comfort_power_save": "off",
                                "comfort_sleep": "off",
                                "strong_wind": "off"
                            },
                            PRESET_ECO: {"eco": "on"},
                            PRESET_COMFORT: {"comfort_power_save": "on"},
                            PRESET_SLEEP: {"comfort_sleep": "on"},
                            PRESET_BOOST: {"strong_wind": "on"}
                        },
                        "swing_modes": {
                            SWING_OFF: {"wind_swing_lr": "off", "wind_swing_ud": "off"},
                            SWING_BOTH: {"wind_swing_lr": "on", "wind_swing_ud": "on"},
                            SWING_HORIZONTAL: {"wind_swing_lr": "on", "wind_swing_ud": "off"},
                            SWING_VERTICAL: {"wind_swing_lr": "off", "wind_swing_ud": "on"},
                        },
                        "fan_modes": {
                            "silent": {"wind_speed": 20},
                            FAN_LOW: {"wind_speed": 40},
                            FAN_MEDIUM: {"wind_speed": 60},
                            FAN_HIGH: {"wind_speed": 80},
                            "full": {"wind_speed": 100},
                            FAN_AUTO: {"wind_speed": 102}
                        },
                        "current_temperature": "indoor_temperature",
                        "aux_heat": "ptc",
                        "min_temp": 17,
                        "max_temp": 30,
                        "temperature_unit": TEMP_CELSIUS,
                        "precision": PRECISION_HALVES,
                    }
                },
                Platform.SWITCH: {
                    "dry": {
                        "name": "Dry",
                        "device_class": SwitchDeviceClass.SWITCH,
                    },
                    "prevent_straight_wind": {
                        "binary_rationale": [1, 2]
                    }
                },
                Platform.SENSOR: {
                    "indoor_temperature": {
                        "name": "室内温度",
                        "device_class": SensorDeviceClass.TEMPERATURE,
                        "unit": TEMP_CELSIUS,
                        "state_class": SensorStateClass.MEASUREMENT
                    },
                    "outdoor_temperature": {
                        "name": "室外机温度",
                        "device_class": SensorDeviceClass.TEMPERATURE,
                        "unit": TEMP_CELSIUS,
                        "state_class": SensorStateClass.MEASUREMENT
                    },
                },
                Platform.BINARY_SENSOR: {
                    "power": {}
                }
            }
        }
    },
}
