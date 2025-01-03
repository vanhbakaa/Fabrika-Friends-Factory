import json
import os
import glob
import asyncio
import argparse
import sys
from itertools import cycle
from urllib.parse import unquote
import traceback 
from aiofile import AIOFile
from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper, run_tapper1
from bot.core.query import run_query_tapper, run_query_tapper1
from bot.core.registrator import register_sessions
from ..core.agents import generate_random_user_agent

start_text = """

Select an action:

    1. Run clicker (Session)
    2. Create session
    3. Run clicker (Query)
"""

global tg_clients


def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names

def fetch_username(query):
    try:
        fetch_data = unquote(query).split("user=")[1].split("&chat_instance=")[0]
        json_data = json.loads(fetch_data)
        return json_data['username']
    except:
        try:
            fetch_data = unquote(query).split("user=")[1].split("&auth_date=")[0]
            json_data = json.loads(fetch_data)
            return json_data['username']
        except:
            try:
                fetch_data = unquote(unquote(query)).split("user=")[1].split("&auth_date=")[0]
                json_data = json.loads(fetch_data)
                return json_data['username']
            except:
                logger.warning(f"Invaild query: {query}")
                return ""


async def get_user_agent(session_name):
    async with AIOFile("user_agents.json", "r") as file:
        content = await file.read()
        user_agents = json.loads(content)

    if session_name not in list(user_agents.keys()):
        logger.info(f"{session_name} | Doesn't have user agent, Creating...")
        ua = generate_random_user_agent(device_type="android", browser_type="chrome")
        user_agents.update({session_name: ua})
        async with AIOFile("user_agents.json", "w") as file:
            content = json.dumps(user_agents, indent=4)
            await file.write(content)
        return ua
    else:
        logger.info(f"{session_name} | Loading user agent from cache...")
        return user_agents[session_name]


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    parser.add_argument("-m", "--multithread", type=str, help="Enable multi-threading")

    logger.info(
        f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies"
    )

    action = parser.parse_args().action
    ans = parser.parse_args().multithread

    if not os.path.exists("user_agents.json"):
        with open("user_agents.json", "w") as file:
            file.write("{}")
        logger.info("User agents file created successfully")

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2", "3"]:
                logger.warning("Action must be 1, 2 or 3")
            else:
                action = int(action)
                break

    if action == 2:
        await register_sessions()
    elif action == 1:
        if ans is None:
            while True:
                ans = input("> Do you want to run the bot with multi-thread? (y/n) ")
                if ans not in ["y", "n"]:
                    logger.warning("Answer must be y or n")
                else:
                    break

        if ans == "y":
            tg_clients = await get_tg_clients()

            await run_tasks(tg_clients=tg_clients)
        else:
            tg_clients = await get_tg_clients()
            proxies = get_proxies()
            await run_tapper1(tg_clients=tg_clients, proxies=proxies)
    elif action == 3:
        ans = None
        while True:
            ans = input("> Do you want to run the bot with multi-thread? (y/n) ")
            if ans not in ["y", "n"]:
                logger.warning("Answer must be y or n")
            else:
                break
        if ans == "y":
            with open("data.txt", "r") as f:
                query_ids = [line.strip() for line in f.readlines()]
            # proxies = get_proxies()
            await run_tasks_query(query_ids)
        else:
            with open("data.txt", "r") as f:
                query_ids = [line.strip() for line in f.readlines()]
            proxies = get_proxies()

            await run_query_tapper1(query_ids, proxies)


async def run_tasks_query(query_ids: list[str]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    account_name = [i for i in range(len(query_ids) + 10)]
    name_cycle = cycle(account_name)
    tasks = [
        asyncio.create_task(
            run_query_tapper(
                query=query,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                ua=await get_user_agent(fetch_username(query)),
            )
        )
        for query in query_ids
    ]

    await asyncio.gather(*tasks)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                ua=await get_user_agent(tg_client.name),
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)
