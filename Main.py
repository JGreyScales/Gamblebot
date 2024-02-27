# Known bugs
# When a user is elimated they are not removed from the game list until the game has completed

# Due to async "thread" cycling, we do not need to worry about thread safe memory or process access
# Written by JGreyScales
# Contributers:
# 
# ------------------------- #

import disnake, os, json, random, asyncio, signal
from enum import Enum
from dotenv import load_dotenv
from disnake.ext import commands
from Config.helpers import helpers

# Reminder to windows users that file system may not work as intended.
# There is plans to peform this modifcation automatically to ensure the easiest dev environment possible
if os.name == "nt": print("please note that you may need to change all '/' with open commands to: " + '\\' + '\\' + "\nexample being within function: 'balance'")
else: print("Current filesystem is configured for linux (Ubuntu)")

load_dotenv()

Idticker = 1

rooms = {
}

# game definements

# bot definement
intents = disnake.Intents.all()
client = commands.InteractionBot(intents=intents)


async def garbageCollectionOnClosure():
    for guild in rooms:
        for guildroom in rooms[guild]:
            await rooms[guild][guildroom]["hostMessage"].delete()
            await rooms[guild][guildroom]["gameChannel"].delete()
    exit(1)

def closureHandle(signum, frame):
    # we do not need these in memory and they are required for the signal to function
    del signum, frame
    # set the function to "return" the uncaught task never retrieved, but do not store it to memory as this is an expected error
    asyncio.gather(garbageCollectionOnClosure(), return_exceptions=True)
    # Begin the async task and prepare garbage collection
    asyncio.create_task(garbageCollectionOnClosure())

# Begin an async signal to watch for ctrl+_ commands and handle them
signal.signal(signal.SIGINT, closureHandle)

 # ------------------------- #

# ------------------------- #
#  take a guild ID and an optional assignable ID
# generate or verify if the ID is valid.
# if the ID is not valid; generate a new valid ID and return
def genID(guild, *id) -> int:
    # test to see if a value has been assigned already
    try:
        id = id[0]
    except(IndexError):
        #  if no value is assigned, pull value from the IDTicker
        global Idticker
        id = Idticker
    global rooms
    try:
        for key in list(rooms[guild].keys()):
            if key == id:
                id = genID(guild, id + 1)
                Idticker = id + 1
                return id 
    except:
        return 1
        
    Idticker = id + 1
    return id


#  store the information from the INIT game func into the dict
def storeRoom(funcInfo, gameInfo, guild) -> bool:
    global rooms

    gameInfo["gameObject"] = funcInfo[0]
    gameInfo["gameChannel"] = funcInfo[2]
    gameInfo["hostMessage"] = funcInfo[3]

    try:
        rooms[guild][funcInfo[1]] = gameInfo
    except(KeyError):   
        rooms[guild] = {}
        rooms[guild][funcInfo[1]] = gameInfo

    return True if funcInfo[4] == True else False

#  store game types
class Games(str, Enum):
    RussianRoullete = 0
# ------------------------- #


# ------------------------- #
@client.slash_command()
async def help(ctx: disnake.ApplicationCommandInteraction):
    
    games = "\n\t".join([k for k in Games.__dict__ if not k.startswith('_')])
    # Make this nice with an embed eventually
    await ctx.send(content=("Use /start_game to create a room and begin gambling\nUse /Join and provide the room ID to join an active game\nCurrent games that can be played:\n\t" + games), ephemeral=True)

#  start the game
@client.slash_command()
async def start_game(ctx: disnake.ApplicationCommandInteraction,
                     selected_game: Games,
                    #  Positive integer greater than 0
                     entry_fee: commands.Range[int, 1, ...]):
    
    gameInfo = {
        "selectedGame" : selected_game,
        "players": [ctx.author.id],
    }
    global rooms
    author: disnake.user = ctx.author
    guildID = ctx.guild.id
    inRoom = helpers.locateRoom(rooms, guildID, author.id, True)
    deductStatus = helpers.deductBalance(ctx.guild_id, ctx.author, entry_fee)
    if inRoom == False:
        if deductStatus == True:
            assignedID = genID(ctx.guild_id)
            try:
                returnObject = await helpers.initGame(assignedID, selected_game, ctx.author.id, ctx.guild_id, client, entry_fee)
            except:
                await verifySetup(client, ctx.guild)
                returnObject = await helpers.initGame(assignedID, selected_game, ctx.author.id, ctx.guild_id, client, entry_fee)
            finally:
                returnStatus = storeRoom(returnObject, gameInfo, ctx.guild_id)

            await ctx.send("Room Successfully created", ephemeral=True)
        else:
            await ctx.send("You do not have enough credits for this entry fee", ephemeral=True)
    # This else catches if the player is already in a room
    else:
        await ctx.send("You are already in a room in this guild, unable to start", ephemeral=True)



#  add players to a pre-existing room
@client.slash_command()
async def join(ctx: disnake.ApplicationCommandInteraction,
                    room_id: int):



    global rooms
    author: disnake.user = ctx.author
    guildID = ctx.guild.id
    inRoom = helpers.locateRoom(rooms, guildID, author.id, True)
    # if the value returns anything but false; the user is in a room inside that guild
    if inRoom == False:
        # Check to ensure that the game is not active
        # Active games game the gamestate of True
        if rooms[guildID][room_id]["gameObject"].gameState != True:
            deductStatus = helpers.deductBalance(guildID, author, rooms[guildID][room_id]["gameObject"].entryFee)
            if deductStatus == True:
                permissionSet = (await helpers.addPlayer(rooms[guildID][room_id]["gameChannel"], author))
                if (permissionSet == True):
                    activePlayers = rooms[guildID][room_id]["players"]
                    activePlayers.append(author.id)
                    rooms[guildID][room_id]["players"] = activePlayers
                    await ctx.send("Room joined successfully", ephemeral=True)

            # This else catches if the player does not have enough money to participate
            else:
                await ctx.send("You do not have enough balance to enter this room", ephemeral=True)
        # this else catches if the room is already active
        else:
            await ctx.send("The game is already started, you cannot join", ephemeral=True)
    # This else catches if the player is already in a room
    else:
        await ctx.send("You are already in a room in this guild, unable to join", ephemeral=True)

# ------------------------- #

@client.slash_command()
async def balance(ctx: disnake.ApplicationCommandInteraction):
        configInfo = json.load(open(f"Config/Guilds/{ctx.guild.id}.json", "r"))
        balance = configInfo["economy"][str(ctx.author.id)]

        await ctx.send(f"You current have {balance} credits", ephemeral=True)


# ------------------------- #
#  ensure the discord server has valid channels that accord to the configuration file
async def verifySetup(client, guild):
                channelID = 0
                categoryID = 0
                for category in guild.by_category():
                    if str(category[0]) == "GambleBot":
                        for channel in category[1]:
                            if channel.name == "rooms":
                                channelID = channel.id
                                break
                        else:
                            # create text channel
                            channel = await category[0].create_text_channel("rooms")
                            await channel.set_permissions(guild.default_role,send_messages=False,add_reactions=False,embed_links=False,attach_files=False,create_instant_invite=False,create_public_threads=False,use_application_commands=False)
                            channelID = channel.id
                        categoryID = category[0].id
                        break
                # create category
                else:
                    category = await guild.create_category("GambleBot", reason="Required channel for GambleBot", position=0)
                    await category.set_permissions(guild.default_role,send_messages=False,add_reactions=False,embed_links=False,attach_files=False,create_instant_invite=False,create_public_threads=False,use_application_commands=False)
                    channel = await category.create_text_channel("rooms")
                    channelID = channel.id


                    # Bug with category ID causes fatal error on initial setup and creation; not iterable, return object is "GambleBot"
                    categoryID = category[0].id
                    

                config = {
                    "roomChannel":channelID,
                    "category":categoryID,
                    "economy":{
                        guild.owner.id:0
                    }
                }

                with open(f"Config/Guilds/{guild.id}.json", "w+") as file:
                    json.dump(config, file, indent=4)



@client.event
async def on_ready():
    for guild in client.guilds:
        try:   
            open(f"Config/Guilds/{guild.id}.json", "r")
        except(FileNotFoundError):
            await verifySetup(client, guild)
    print("bot booted")
    loop = asyncio.get_event_loop()
    print("Init of room watcher thread beginning")
    task = loop.create_task(checkCurrentRooms())

async def checkCurrentRooms():
    global rooms
    print("room watcher began")
    while True:
        try:
            for guild in rooms:
                for guildroom in rooms[guild]:
                    try:
                    # if the game has gone live remove the message from avalible rooms
                        if rooms[guild][guildroom]["gameObject"].gameState == True:
                            await rooms[guild][guildroom]["hostMessage"].delete()
                    # if the game has finished, delete it from rooms storage, and delete the channel
                        elif rooms[guild][guildroom]["gameObject"].gameState == 2:
                            try:
                                await rooms[guild][guildroom]["hostMessage"].delete()
                            finally:
                                await rooms[guild][guildroom]["gameChannel"].delete()
                                del rooms[guild][guildroom]

                    except Exception as e:
                        print(e)
        except RuntimeError:
            pass
        # Reset the id ticket back to zero every 20 seconds.
        # The Id room gen should be able to handle this properly
        global Idticker
        Idticker = 1
        await asyncio.sleep(20)


# ------------------------- #

# ------------------------- #
@client.event
async def on_message(message: disnake.Message):
    try:
        if message.content[0] == "!":
            global rooms
            roomID = helpers.locateRoom(rooms, message.guild.id, message.author.id, True)
            if roomID != False:
                try:
                    method = getattr(rooms[message.guild.id][roomID]["gameObject"], message.content[1::])
                    returnStatus = await method(message, rooms[message.guild.id][roomID])
                    try:
                        if returnStatus[2] == True:
                            # pay the winner
                            helpers.increaseBalance(message.guild.id, await message.guild.fetch_member(returnStatus[0]), returnStatus[1])
                    except:
                        pass
                except:
                    pass
                # write a statement saying invalid command
        elif message.author.bot != True:
            helpers.increaseBalance(message.guild.id, message.author, random.randint(1, 5))
    except(IndexError):
        pass

try:
    client.run(os.getenv("token"))

except(SystemExit):
    print("Exit Handled")