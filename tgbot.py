import re
import requests
import asyncio
import os
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties

API_TOKEN =("7554455567:AAGt4JS2-B19iZdKNyFsic7inIK9XjyOXLI")
CHAT_ID = 966229619

ITEMS_TO_CHECK = [
    "Charm%20%7C%20Die-cast%20AK?filter=",
    "Charm%20%7C%20Baby%20Karat%20CT",
    "Charm%20%7C%20Baby%20Karat%20T",
    "Charm%20%7C%20Semi-Precious"
]

def parse(name):
    response = requests.get(f"https://steamcommunity.com/market/listings/730/{name}")
    name_id_match = re.search(r"Market_LoadOrderSpread\( (?P<item_id>\d+) \)", response.text)
    if not name_id_match:
        raise ValueError("Не удалось получить item_nameid")

    name_id = name_id_match.group("item_id")

    response = requests.get(
        f"https://steamcommunity.com/market/itemordershistogram?country=RU&language=russian&currency=5&item_nameid={name_id}&two_factor=0"
    ).json()

    highest_buy_order = int(response["highest_buy_order"]) / 100
    lowest_sell_order = int(response["lowest_sell_order"]) / 100

    return highest_buy_order, lowest_sell_order, response["buy_order_graph"], response["sell_order_graph"]

def get_template_ids(name):
    url = f"https://steamcommunity.com/market/listings/730/{name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    matches = re.findall(r'Charm Template: (\d+)', response.text)

    seen = set()
    ordered_ids = []
    for m in matches:
        if m not in seen:
            ordered_ids.append(m)
            seen.add(m)
    return ordered_ids

def match_ids_to_prices(template_ids, sell_graph):
    lines = []
    for i in range(min(len(template_ids), len(sell_graph))):
        tid = template_ids[i]
        if int(tid) > 66000:
            price, quantity, _ = sell_graph[i]
            lines.append(f"{tid:<10} {price:<10.2f} {int(quantity):<10}")
    return "\n".join(lines)

async def send_steam_data(bot, name):
    try:
        buy_price, sell_price, buy_graph, sell_graph = parse(name)
        template_ids = get_template_ids(name)
        filtered_info = match_ids_to_prices(template_ids, sell_graph)

        if not filtered_info:
            print(f"{name} — шаблонов > 66000 не найдено")
            return

        message = (
            f"https://steamcommunity.com/market/listings/730/{name}\n"
            f"Самая высокая цена покупки: {buy_price:.2f} руб.\n"
            f"Самая низкая цена продажи: {sell_price:.2f} руб.\n\n"
            f"Charm Template ID и цены (ID > 66000):\n"
            f"{filtered_info}"
        )

        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)

    except Exception as e:
        print(f"Ошибка при обработке {name}: {e}")

async def check_all_items_once(bot):
    for item in ITEMS_TO_CHECK:
        await send_steam_data(bot, item)

async def main():
    session = AiohttpSession()
    bot = Bot(token=API_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await check_all_items_once(bot)

if __name__ == "__main__":
    asyncio.run(main())
