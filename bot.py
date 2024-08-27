import discord
from discord.ext import commands
import logging
import json
import re
import markov

logging.basicConfig(level=logging.DEBUG,
                    format="[%(levelname)s][%(asctime)s] %(message)s"
                    )
logger = logging.getLogger()



with open("config.json", "r") as f:
    config = json.load(f)


intents = discord.Intents.default()
intents.message_content = True


client = commands.Bot(command_prefix=config["command_prefix"], intents=intents) #discord.Client(intents=intents)
client.message_count = 0

def set_blacklist():
    with open("blacklist.json", "r") as f:
        client.__setattr__("blacklist", json.load(f))

def set_config():
    with open("config.json", "r") as f:
        client.__setattr__("config", json.load(f))

set_blacklist()
set_config()
model = markov.Model()

def blacklisted(chat):
    chat = chat.lower()
    for phrase in client.blacklist["full_phrases"]:
        if phrase in chat:
            logger.debug(f"Chat contained blacklisted phrase '{phrase}': {chat}")
            return True
    
    for regex in client.blacklist["regex"]:
        if re.search(regex, chat):
            logger.debug(f"Chat contained blacklisted pattern '{regex}': {chat}")
            return True

    chat_words = chat.split()
    for word in client.blacklist["words"]:
        if word in chat_words:
            logger.debug(f"Chat contained blacklisted word '{word}': {chat}")
            return True
    
    return False


async def process_message(message, with_commands = True):
    if    message.author == client.user \
       or message.author.id in client.config["ignored_users"] \
       or message.author.bot \
       or message.channel.id in client.config["ignored_channels"]:
        return
    text = message.content

    if text.startswith(client.config["command_prefix"]):
        if with_commands:
            await client.process_commands(message)
        return

    if blacklisted(text):
        return 

    for att in message.attachments:
        text = text + " " + str(att)

    model.process_data(text)


def is_admin(ctx):
    return ctx.author.id in client.config["admins"]

def is_in_valid_commands(ctx):
    return ctx.channel.id in client.config["command_channel"] or not client.config["require_command_channel"]


def edit_blacklist(action, field, value):
    with open(config["blacklist_file"], "r") as f:
        working_blacklist = json.load(f)

    if action == "add":
        try:
            working_blacklist[field].append(value)
            ret = f"Successfully added '{value}' to '{field}'"
        except KeyError:
            return f"'{field}' is not a field in blacklist"
    elif action == "remove":
        try:
            working_blacklist[field].remove(value)
            ret = f"Successfully removed '{value}' from '{field}'"
        except KeyError:
            return f"'{field}' is not a field in blacklist"
        except ValueError:
            return f"'{value}' is not in field '{field}' of blacklist"
    else:
        return f"Cannot {action} in blacklist"
    
    with open(config["blacklist_file"], "w+") as f:
        json.dump(working_blacklist, f, indent=2)
    
    set_blacklist()
    return "Successfully updated blacklist"

def edit_config(action, field, value):
    ADD_REMOVE_ABLES = ["admins", "ignored_channels", "ignored_users", "command_channel", "scan_cats"]
    MUTABLE = ["autosend", "command_channel",
                "cooldown", "admins", "ignored_users", "scan_cats"
                "admins", "min_length", "max_length", "maxchars", 
                "ignored_channels"]
    NUMERICALS = ["cooldown", "autosend", "min_length", "max_length", "ignored_users", "admins"]
    with open("config.json", "r") as f:
        working_config = json.load(f)

    if action != "set" and field not in ADD_REMOVE_ABLES:
        return f"Cannot {action} the field '{field}', please set instead"
    
    if action == "set" and field in ADD_REMOVE_ABLES:
        return f"Cannot set the field '{field}', please add or remove"
    
    if field not in MUTABLE:
        return f"Cannot change field '{field}', only {MUTABLE}"

    if field in NUMERICALS:
        try:
            value = int(value)
        except ValueError:
            return f"Field '{field}' accepts only numbers, not '{value}'"

    if action == "set":
        working_config[field] = value
        ret = f"Successfully set '{field}' to '{value}'"

    elif action == "add":
        if field in working_config:
            working_config[field].append(value)
            ret = f"Successfully added '{value}' to '{field}'"
        else:
            return f"'{field}' is not in config"
    
    elif action == "remove":
        try:
            working_config[field].remove(value)
            ret = f"Successfully removed '{value}' from '{field}'"
        except ValueError:
            return f"'{value}' is not in '{field}'"
    
    with open("config.json", "w+") as f:
        json.dump(working_config, f, indent=2)
    set_config()
    return "Successfully updated config"

@client.command()
@discord.ext.commands.cooldown(1, client.config["cooldown"])
@commands.check(is_in_valid_commands)
async def chain(ctx):
    chain = model.generate_chain(min_length = client.config["min_length"], max_length=config["max_length"])
    logger.info(f"Made a chain: {chain}")
    await ctx.send(chain)
    client.message_count -= 1


@client.command(name="blacklist")
@commands.check(is_admin)
async def reblacklist(ctx, action, field, value):
    output = edit_blacklist(action, field, value)
    await ctx.send(output)

@client.command(name="config")
@commands.check(is_admin)
async def reconfig(ctx, action, field, value):
    output = edit_config(action, field, value)
    await ctx.send(output)

@client.command()
@commands.check(is_admin)
async def reset(ctx):
    global model
    model = markov.Model()
    await ctx.send("Reset the model")
    
@client.event
async def on_ready():
    logging.info(f'We have logged in as {client.user}')
    guild = client.get_guild(config["active_server"])
    count = 0
    for text_chan in guild.text_channels:
        if text_chan.id in client.config["ignored_channels"]:
            continue
        if (text_chan.category_id == None or text_chan.category_id in client.config["scan_cats"]):
            async for message in text_chan.history(limit = 50):
                await process_message(message, with_commands=False)
                count += 1

    logging.info(f"Pre-processed {count} messages")


@client.event
async def on_raw_message_delete(delete_event):
    model.subtract_full_string(delete_event.cached_message.content)

@client.event
async def on_message(message):
    logging.debug(f"{message.author}: {message.content}")

    await process_message(message)
    client.message_count += 1
    if client.message_count > client.config["autosend"]:
        client.message_count = 0
        chain = model.generate_chain(min_length = client.config["min_length"], max_length=config["max_length"])
        await message.channel.send(chain)
    
client.run(config["token"])
