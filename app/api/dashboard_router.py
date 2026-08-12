# app/api/dashboard_router.py – Dashboard API
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.device_loader import load_devices
from app.config.settings import settings
from app.infrastructure.mqtt_client import MqttClient
from app.infrastructure.status_cache import StatusCache
from app.infrastructure.midea_client import MideaClient
from app.infrastructure.miio_client import MiioClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _extract_value(data: dict, path: str):
    """Extrahiert einen Wert aus verschachteltem Dict über Punkt-Pfad (z.B. 'SonoffSC.Temperature')."""
    keys = path.split(".")
    val = data
    for key in keys:
        if isinstance(val, dict):
            val = val.get(key)
        else:
            return None
    return val


async def _esphome_status(ip: str, endpoint: str, unit: str | None = None) -> dict:
    """Holt Status von ESPHome per HTTP."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://{ip}/{endpoint}")
            data = resp.json()
            value = data.get("value", data.get("state"))
            return {"temperature": value, "unit": unit or ""}
    except Exception as e:
        logger.debug("ESPHome %s nicht erreichbar: %s", ip, e)
        return {}


async def _shelly_status(ip: str, channel: str, device_type: str) -> dict:
    """Holt den aktuellen Status eines Shelly-Geräts per HTTP."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            if device_type == "roller":
                resp = await client.get(f"http://{ip}/roller/{channel}")
                data = resp.json()
                return {"position": data.get("current_pos")}
            elif device_type == "dimmer":
                resp = await client.get(f"http://{ip}/light/{channel}")
                data = resp.json()
                is_on = data.get("ison", False)
                return {"state": "ON" if is_on else "OFF", "brightness": data.get("brightness")}
            else:
                resp = await client.get(f"http://{ip}/relay/{channel}")
                data = resp.json()
                is_on = data.get("ison", False)
                return {"state": "ON" if is_on else "OFF"}
    except Exception as e:
        logger.debug("Shelly %s nicht erreichbar: %s", ip, e)
        return {}


async def _midea_status(device) -> dict:
    """Holt Status der Midea/Comfee Klimaanlage."""
    try:
        status = await MideaClient.get_status(device)
        if not status:
            return {}
        power_on = status.get("power_state", False)
        op_mode = status.get("operational_mode", 1)
        mode_map = {1: "auto", 2: "cool", 3: "dry", 4: "heat", 5: "fan"}
        system_mode = mode_map.get(op_mode, "auto")
        if not power_on:
            system_mode = "off"
        return {
            "state": "ON" if power_on else "OFF",
            "current_heating_setpoint": status.get("target_temperature"),
            "local_temperature": status.get("indoor_temperature"),
            "system_mode": system_mode,
            "heating": "ON" if power_on else "OFF",
        }
    except Exception as e:
        logger.debug("Midea %s nicht erreichbar: %s", device.ip, e)
        return {}


async def _miio_status(device) -> dict:
    """Holt Status des Xiaomi Luftreinigers."""
    try:
        status = await MiioClient.get_status(device)
        if not status:
            return {}
        power_on = status.get("power_state", False)
        return {
            "state": "ON" if power_on else "OFF",
            "mode": status.get("mode", "unknown"),
            "aqi": status.get("aqi"),
        }
    except Exception as e:
        logger.debug("MiIO %s nicht erreichbar: %s", device.ip, e)
        return {}


@router.get("/devices")
async def get_devices():
    """Liefert alle Geräte mit aktuellem Status."""
    import asyncio
    devices = load_devices()
    cache = StatusCache.get()
    result = []

    # Shelly + ESPHome + Midea + MiIO Status parallel abfragen
    http_tasks = {}
    for d in devices:
        if d.protocol == "shelly" and d.ip:
            http_tasks[d.id] = _shelly_status(d.ip, d.channel, d.type)
        elif d.protocol == "esphome" and d.ip and d.endpoint_status:
            http_tasks[d.id] = _esphome_status(d.ip, d.endpoint_status, d.unit)
        elif d.protocol == "midea":
            http_tasks[d.id] = _midea_status(d)
        elif d.protocol == "miio":
            http_tasks[d.id] = _miio_status(d)

    http_results = {}
    if http_tasks:
        results = await asyncio.gather(*http_tasks.values(), return_exceptions=True)
        for device_id, res in zip(http_tasks.keys(), results):
            http_results[device_id] = res if isinstance(res, dict) else {}

    for d in devices:
        # MQTT-Cache für z2m Geräte
        state_data = cache.get_state(d.id, d.topic_id)
        # HTTP-Status überschreibt (Shelly + ESPHome)
        if d.id in http_results:
            state_data = {**state_data, **http_results[d.id]}

        device_info = {
            "id": d.id,
            "name": d.name,
            "ip": d.ip,
            "type": d.type,
            "category": d.category,
            "channel": d.channel,
            "protocol": d.protocol,
            "hardware": d.hardware,
            "unit": d.unit or "°C",
            "status": f"{d.protocol} · {d.hardware}",
        }

        # Typ-spezifische Werte extrahieren
        if d.type == "sensor":
            temp = state_data.get("temperature")
            # value_path: z.B. "SonoffSC.Temperature" für verschachtelte Payloads
            if temp is None and d.value_path:
                temp = _extract_value(state_data, d.value_path)
            device_info["temperature"] = temp
            device_info["last_seen"] = state_data.get("last_seen") or state_data.get("Time")
        elif d.type == "thermostat":
            device_info["temperature"] = state_data.get("occupied_heating_setpoint",
                                          state_data.get("current_heating_setpoint"))
            device_info["current_temp"] = state_data.get("local_temperature")
            device_info["system_mode"] = state_data.get("system_mode", "off")
            device_info["heating"] = state_data.get("heating", "OFF")
            device_info["state"] = state_data.get("state")
            device_info["last_seen"] = state_data.get("last_seen")
        elif d.type in ("switch", "dimmer", "light"):
            raw_state = state_data.get("state", "")
            # value_path für verschachtelte Payloads (z.B. Tasmota "POWER")
            if not raw_state and d.value_path:
                raw_state = str(_extract_value(state_data, d.value_path) or "")
            device_info["state"] = "ON" if raw_state == "ON" else "OFF" if raw_state else None
            if d.type in ("dimmer", "light"):
                device_info["brightness"] = state_data.get("brightness")
        elif d.type == "purifier":
            device_info["state"] = state_data.get("state")
            device_info["mode"] = state_data.get("mode", "unknown")
            device_info["aqi"] = state_data.get("aqi")
        elif d.type == "roller":
            device_info["position"] = state_data.get("position")

        result.append(device_info)

    return result


@router.get("/debug/cache")
async def debug_cache():
    """Zeigt den rohen MQTT-Cache (nur für Entwicklung)."""
    cache = StatusCache.get()
    return cache._cache


class ControlRequest(BaseModel):
    device_id: str
    action: str
    value: str | int | float


@router.post("/control")
async def control_device(req: ControlRequest):
    """Steuert ein Gerät über HTTP (Shelly) oder MQTT (z2m/generic)."""
    devices = load_devices()
    device = next((d for d in devices if d.id == req.device_id), None)

    if not device:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")

    mqtt = MqttClient.get()

    if req.action == "power":
        state = "on" if req.value == "ON" else "off"
        if device.protocol == "shelly":
            async with httpx.AsyncClient(timeout=5.0) as client:
                if device.type == "dimmer":
                    await client.get(f"http://{device.ip}/light/{device.channel}?turn={state}")
                else:
                    await client.get(f"http://{device.ip}/relay/{device.channel}?turn={state}")
        elif device.protocol == "esphome":
            endpoint = device.endpoint_on if req.value == "ON" else device.endpoint_off
            if endpoint:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(f"http://{device.ip}/{endpoint}")
        elif device.protocol == "z2m":
            mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{device.mqtt_name}/set", {"state": req.value})
        elif device.protocol == "mqtt":
            mqtt.publish(device.topic, req.value)
        elif device.protocol == "midea":
            try:
                await MideaClient.set_power(device, req.value == "ON")
            except Exception as e:
                logger.error("Midea Power fehlgeschlagen: %s", e)
                raise HTTPException(status_code=503, detail="Klimaanlage nicht erreichbar")
        elif device.protocol == "miio":
            try:
                await MiioClient.set_power(device, req.value == "ON")
            except Exception as e:
                logger.error("MiIO Power fehlgeschlagen: %s", e)
                raise HTTPException(status_code=503, detail="Luftreiniger nicht erreichbar")

    elif req.action == "brightness":
        if device.protocol == "shelly":
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"http://{device.ip}/light/{device.channel}?turn=on&brightness={int(req.value)}")
        elif device.protocol == "z2m":
            mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{device.mqtt_name}/set", {"brightness": int(req.value)})

    elif req.action == "position":
        if device.protocol == "shelly":
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"http://{device.ip}/roller/{device.channel}?go=to_pos&roller_pos={int(req.value)}")
        elif device.protocol == "z2m":
            mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{device.mqtt_name}/set", {"position": int(req.value)})

    elif req.action == "roller_cmd":
        if device.protocol == "shelly":
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"http://{device.ip}/roller/{device.channel}?go={req.value}")

    elif req.action == "temperature":
        if device.protocol == "z2m":
            mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{device.mqtt_name}/set", {"current_heating_setpoint": float(req.value)})
        elif device.protocol == "midea":
            try:
                await MideaClient.set_temperature(device, float(req.value))
            except Exception as e:
                logger.error("Midea Temperatur fehlgeschlagen: %s", e)
                raise HTTPException(status_code=503, detail="Klimaanlage nicht erreichbar")

    elif req.action == "system_mode":
        if device.protocol == "z2m":
            mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{device.mqtt_name}/set", {"system_mode": str(req.value)})
        elif device.protocol == "midea":
            try:
                await MideaClient.set_mode(device, str(req.value))
            except Exception as e:
                logger.error("Midea Modus fehlgeschlagen: %s", e)
                raise HTTPException(status_code=503, detail="Klimaanlage nicht erreichbar")

    elif req.action == "purifier_mode":
        if device.protocol == "miio":
            try:
                await MiioClient.set_mode(device, str(req.value))
            except Exception as e:
                logger.error("MiIO Modus fehlgeschlagen: %s", e)
                raise HTTPException(status_code=503, detail="Luftreiniger nicht erreichbar")

    else:
        raise HTTPException(status_code=400, detail=f"Unbekannte Aktion: {req.action}")

    logger.info("Control: %s [%s] → %s = %s", device.name, device.protocol, req.action, req.value)

    # Cache sofort aktualisieren (nicht auf MQTT-Antwort warten)
    cache = StatusCache.get()
    cached = cache.get_state(device.id, device.topic_id)
    if req.action == "temperature":
        cached["current_heating_setpoint"] = float(req.value)
    elif req.action == "system_mode":
        cached["system_mode"] = str(req.value)
    elif req.action == "power":
        cached["state"] = str(req.value)
    if cached:
        key = device.topic_id or device.id
        cache._cache[key] = cached

    return {"ok": True, "device": device.id, "action": req.action, "value": req.value}
