import asyncio
import json
import os
import subprocess
import time
from typing import Optional

from miservice.miaccount import MiAccount
from miservice.minaservice import MiNAService
from aiohttp import ClientSession

GET_CONVERSATION = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
HARDWARE = "S12"
# micli list to get MI_DID, needed in miio service
MI_DID = os.environ["MI_DID"]
# get by mina service device list, needed in cookies to get conversation
DEVICE_ID = os.environ["DEVICE_ID"]


async def main():
    print("Waiting for commands")
    session = ClientSession()
    account = MiAccount(
        session,
        os.environ["MI_USER"],
        os.environ["MI_PASS"],
    )

    await account.login("micoapi")

    session.cookie_jar.update_cookies({"deviceId": DEVICE_ID})
    mina_service = MiNAService(account)

    last_timestamp = int(time.time() * 1000)
    while True:
        try:
            question = await poll(session, last_timestamp)
        except Exception as e:
            print(f"poll error: {e!r}")
        else:
            if question:
                last_timestamp = question.get("time")
                query = question.get("query", "").strip()
                print(f"got query: {query}")
                await handle_command(query, mina_service)
        await asyncio.sleep(3)


async def poll(session: ClientSession, last_timestamp: int) -> Optional[dict]:
    url = GET_CONVERSATION.format(hardware=HARDWARE, timestamp=int(time.time() * 1000))
    resp = await session.get(url)
    try:
        data = await resp.json()
    except Exception as e:
        print(f"get conversation failed: {e!r}")
        return None

    d = json.loads(data["data"])
    records = d.get("records")
    if not records:
        return None
    if records[0].get("time") > last_timestamp:
        return records[0]
    return None


async def handle_command(command: str, mina_service: MiNAService):
    if "关电脑" in command or "关机" in command or "shutdown" in command:
        await mina_service.player_pause(DEVICE_ID)
        await mina_service.text_to_speech(DEVICE_ID, "正在关机中...")
        await asyncio.sleep(1)
        subprocess.run(["shutdown", "/h"])


if __name__ == '__main__':
    asyncio.run(main())
