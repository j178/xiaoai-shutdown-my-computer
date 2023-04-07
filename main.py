import asyncio
import os
import subprocess

from blinker import Device, ButtonWidget, NumberWidget
from blinker.voice_assistant import VAType, VoiceAssistant, DataMessage, PowerMessage, ModeMessage, ColorTempMessage
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

speakers = AudioUtilities.GetSpeakers()
interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

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
    vol = msg["num-volume"]
    volume.SetMasterVolumeLevelScalar(vol / 100, None)
    await num_volume.value(vol).update()


# TODO control brightness
async def set_brightness(msg):
    print(f"received brightness: {msg}")


async def mute(msg):
    print(f"received mute: {msg}")
    if msg["btn-mute"] == "off":
        volume.SetMute(False, None)
        await btn_mute.turn("off").update()
    else:
        volume.SetMute(True, None)
        await btn_mute.turn("on").update()


async def shutdown(msg):
    print(f"received shutdown: {msg}")
    await btn_shutdown.turn("off").update()
    await asyncio.sleep(1)
    subprocess.run(["shutdown", "/h"])


async def heartbeat_func(msg):
    print(f"received heartbeat: {msg}")
    muted = volume.GetMute()
    vol = int(volume.GetMasterVolumeLevelScalar() * 100)
    await btn_mute.turn("on" if muted else "off").update()
    await btn_shutdown.turn("on").update()
    await num_volume.value(vol).update()
    await num_brightness.value(0).update()


async def ready_func():
    # 获取设备配置信息
    print(vars(device.config))


btn_mute.func = mute
btn_shutdown.func = shutdown
num_volume.func = set_volume
num_brightness.func = set_brightness
device.heartbeat_callable = heartbeat_func
device.ready_callable = ready_func

# https://diandeng.tech/doc/xiaoai
# 将这台电脑模拟为一个台灯，可以用小爱同学控制开关、调节模式、控制色温

# 1. 将模式调节用来控制静音
# "小爱同学，将 PC 设为日光模式"
MODE_UNMUTE = 0
# "小爱同学，将 PC 设为月光模式"
MODE_MUTE = 1


# 2. 将色温调节用来控制音量，色温范围为 1000-10000
# "小爱同学，将 PC 的色温调节到 2000"

def volume_to_color_temp(value: int) -> int:
    return int((value - 0) * (10000 - 1000) / (100 - 0) + 1000)


def color_temp_to_volume(value: int) -> int:
    return int((value - 1000) * (100 - 0) / (10000 - 1000) + 0)


async def voice_query_state(msg: DataMessage):
    print(f"received voice query: {vars(msg)}")
    match msg.data:
        case 'state':
            await msg.power('on')
        case 'mode':
            muted = volume.GetMute()
            await msg.mode(MODE_MUTE if muted else MODE_UNMUTE)
        case 'bright':
            pass
        case 'colTemp':
            vol = int(volume.GetMasterVolumeLevelScalar() * 100)
            col_temp = volume_to_color_temp(vol)
            await msg.colorTemp(col_temp)
    # await msg.update()


async def voice_echo(msg):
    print(f"received voice message: {vars(msg)}")
    await msg.update()


async def voice_shutdown(msg: PowerMessage):
    print(f"received shutdown message: {vars(msg)}")
    await msg.power('off')
    await msg.update()
    await asyncio.sleep(1)
    subprocess.run(["shutdown", "/h"])


async def voice_mute_unmute(msg: ModeMessage):
    print(f"received mute_unmute message: {vars(msg)}")
    if msg.data['mode'] == MODE_MUTE:
        volume.SetMute(True, None)
        await msg.mode(MODE_MUTE)
    else:
        volume.SetMute(False, None)
        await msg.mode(MODE_UNMUTE)
    await msg.update()


async def voice_volume(msg: ColorTempMessage):
    print(f"received volume message: {vars(msg)}")
    col_temp = msg.data["colTemp"]
    vol = color_temp_to_volume(col_temp)
    volume.SetMasterVolumeLevelScalar(vol / 100, None)
    await msg.colorTemp(col_temp)
    await msg.update()


voice_assistant.state_query_callable = voice_query_state
voice_assistant.power_change_callable = voice_shutdown
voice_assistant.mode_change_callable = voice_mute_unmute
voice_assistant.colortemp_change_callable = voice_volume
voice_assistant.brightness_change_callable = voice_echo
voice_assistant.color_change_callable = voice_echo

if __name__ == '__main__':
    device.run()
