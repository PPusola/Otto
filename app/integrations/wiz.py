from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pywizlight import PilotBuilder, discovery, wizlight


NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "purple": (128, 0, 255),
    "pink": (255, 64, 160),
    "orange": (255, 128, 0),
}


@dataclass
class WizDevice:
    name: str
    ip: str


class WizController:
    def __init__(self, broadcast_space: str = "192.168.1.255") -> None:
        self.broadcast_space = broadcast_space
        self.devices: dict[str, WizDevice] = {}

    async def discover(self) -> dict[str, Any]:
        bulbs = await discovery.discover_lights(broadcast_space=self.broadcast_space)
        found = []
        for bulb in bulbs:
            ip = bulb.ip
            name = f"wiz-{ip.replace('.', '-')}"
            self.devices[name.lower()] = WizDevice(name=name, ip=ip)
            found.append({"name": name, "ip": ip})
        return {"lights": found}

    def configure(self, mapping: dict[str, str]) -> None:
        for name, ip in mapping.items():
            self.devices[name.lower()] = WizDevice(name=name, ip=ip)

    async def turn_on(self, name_or_group: str) -> dict[str, Any]:
        light = self._light(name_or_group)
        await light.turn_on()
        return {"light": name_or_group, "on": True}

    async def turn_off(self, name_or_group: str) -> dict[str, Any]:
        light = self._light(name_or_group)
        await light.turn_off()
        return {"light": name_or_group, "on": False}

    async def set_brightness(self, name_or_group: str, percent: int) -> dict[str, Any]:
        if percent < 0 or percent > 100:
            raise ValueError("WiZ brightness percent must be between 0 and 100")
        light = self._light(name_or_group)
        await light.turn_on(PilotBuilder(brightness=percent))
        return {"light": name_or_group, "brightness": percent}

    async def set_color(self, name_or_group: str, color: str) -> dict[str, Any]:
        light = self._light(name_or_group)
        normalized = color.strip().lower()
        if normalized.startswith("kelvin:"):
            kelvin = int(normalized.split(":", 1)[1])
            await light.turn_on(PilotBuilder(colortemp=kelvin))
            return {"light": name_or_group, "kelvin": kelvin}
        if normalized in {"warm white", "warm"}:
            await light.turn_on(PilotBuilder(colortemp=2700))
            return {"light": name_or_group, "kelvin": 2700}
        if normalized in {"cool white", "cool"}:
            await light.turn_on(PilotBuilder(colortemp=6500))
            return {"light": name_or_group, "kelvin": 6500}
        rgb = NAMED_COLORS.get(normalized)
        if not rgb:
            raise ValueError(f"Unsupported WiZ color {color!r}")
        await light.turn_on(PilotBuilder(rgb=rgb))
        return {"light": name_or_group, "rgb": rgb}

    def _light(self, name_or_group: str) -> wizlight:
        device = self.devices.get(name_or_group.strip().lower())
        if not device:
            raise RuntimeError(f"Unknown WiZ light {name_or_group!r}. Run discovery or add it to config.")
        return wizlight(device.ip)
