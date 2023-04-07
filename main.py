import asyncio
import os
import random
import subprocess

import pyautogui
from blinker import Device, ButtonWidget, NumberWidget
from blinker.voice_assistant import VAType, VoiceAssistant

os.environ["AUTH_KEY"] = '2c19e8b1f0e2'
device = Device(os.environ["AUTH_KEY"], mi_type=VAType.LIGHT)

voice_assistant = VoiceAssistant(VAType.LIGHT)

btn_shutdown = ButtonWidget('btn-shutdown')
btn_mute = ButtonWidget('btn-mute')
num_volume = NumberWidget('num-volume')
num_brightness = NumberWidget('num-brightness')

device.addVoiceAssistant(voice_assistant)
device.addWidget(btn_shutdown)
device.addWidget(btn_mute)
device.addWidget(num_volume)
device.addWidget(num_brightness)


async def set_volume(msg):
    print(f"received volume: {msg}")


async def set_brightness(msg):
    print(f"received brightness: {msg}")


async def mute(msg):
    print(f"received mute: {msg}")
    pyautogui.press("mute")
    await num_volume.value(0).update()


async def shutdown(msg):
    print(f"received shutdown: {msg}")
    await asyncio.sleep(1)
    # await device.sendMessage({"": "Shutting down"}, None)
    subprocess.run(["shutdown", "-h", "now"])


async def heartbeat_func(msg):
    print(f"received heartbeat: {msg}")
    x = random.randint(0, 100)
    await num_volume.value(x).update()
    await num_brightness.value(x).update()


async def ready_func():
    # 获取设备配置信息
    print(vars(device.config))


async def echo(msg):
    print(f"received voice message: {vars(msg)}")


btn_mute.func = mute
btn_shutdown.func = shutdown
num_volume.func = set_volume
num_brightness.func = set_brightness
device.heartbeat_callable = heartbeat_func
device.ready_callable = ready_func

voice_assistant.state_query_callable = echo
voice_assistant.power_change_callable = echo
voice_assistant.brightness_change_callable = echo
voice_assistant.mode_change_callable = echo
voice_assistant.color_change_callable = echo
voice_assistant.colortemp_change_callable = echo


if __name__ == '__main__':
    device.run()
