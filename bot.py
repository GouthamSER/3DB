import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media, Media2, Media3, choose_mediaDB, db as clientDB
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR, LOG_CHANNEL, SECONDDB_URI, THIRDDB_URI
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types

# for prevent stoping the bot after 1 week
logging.getLogger("asyncio").setLevel(logging.CRITICAL -1)

# peer id invaild fixxx
from pyrogram import utils as pyroutils
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

from plugins.webcode import bot_run
from os import environ
from aiohttp import web as webserver

PORT_CODE = environ.get("PORT", "8080")

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="my_bot",  # Replace "my_bot" with your desired session name
            session_name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        await Media2.ensure_indexes()
        await Media3.ensure_indexes()
        
        # Choose the appropriate DB based on available space
        stats = await clientDB.command('dbStats')
        free_dbSize = round(512 - ((stats['dataSize'] / (1024 * 1024)) + (stats['indexSize'] / (1024 * 1024))), 2)
        
        if SECONDDB_URI and free_dbSize < 10:
            # Check free space in SECONDDB
            second_db_client = ClientDB(SECONDDB_URI)
            second_db_stats = await second_db_client.command('dbStats')
            second_free_dbSize = round(512 - ((second_db_stats['dataSize'] / (1024 * 1024)) + 
                                              (second_db_stats['indexSize'] / (1024 * 1024))), 2)
                                              
            if THIRDDB_URI and second_free_dbSize < 10:
                tempDict["indexDB"] = THIRDDB_URI
                logging.info(f"Both Primary and Secondary DBs have less than 10MB free. Using Third DB.")
            elif not THIRDDB_URI:
                logging.error("Third DB URI missing!\n\nAdd THIRDDB_URI now!\n\nExiting...")
                exit()
            else:
                tempDict["indexDB"] = SECONDDB_URI
                logging.info(f"Primary DB is low on space. Using Secondary DB with {second_free_dbSize} MB free.")
        
        elif SECONDDB_URI is None and THIRDDB_URI is not None and free_dbSize < 10:
            tempDict["indexDB"] = THIRDDB_URI
            logging.info(f"Primary DB is low on space, and Secondary DB is unavailable. Using Third DB.")
        
        elif SECONDDB_URI is None and THIRDDB_URI is None:
            logging.error("Both Secondary and Third DB URIs are missing! Exiting...")
            exit()
        
        else:
            logging.info(f"Primary DB has enough space ({free_dbSize}MB). Using it for data storage.")
        
        await choose_mediaDB()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started as {me.username}.")
        logging.info(LOG_STR)
        await self.send_message(chat_id=LOG_CHANNEL, text="Restart Successfully ✓\nKuttu Bot 2 💫")
        print("Og Eva Re-editeD ⚡\n3db Gooyz beTa testings")

        client = webserver.AppRunner(await bot_run())
        await client.setup()
        bind_address = "0.0.0.0"
        await webserver.TCPSite(client, bind_address, PORT_CODE).start()

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
