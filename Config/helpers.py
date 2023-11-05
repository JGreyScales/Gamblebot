import disnake, json, disnake.utils
from disnake.ext import commands
from Games.RRclass import RussianRoullete as RR
class helpers:
       

    # create the text room and set permissions
    async def createRoom(guild, catergory, ownerID, givenID, ownerName):

        hostChannel = await guild.fetch_channel(catergory)
        gameChannel = await hostChannel.create_text_channel(f"{givenID}-{ownerName}'s room", position=1)
        await gameChannel.set_permissions(guild.default_role, view_channel=False)
        await gameChannel.set_permissions(ownerName, view_channel=True, send_messages=True)

        return gameChannel

    # init a game from scratch
    async def initGame(givenID, selected_game, ownerID, guild, disnakeClient, entryFee) -> list:

        gameObject = False
        # really silly method but I don't forsee alot of games being added
        # If many games are added I will rework the "game detection" system
        # for now just assign each game type an ID and run a if-else to find the ID
        # or use a switch statement; really doesn't matter to me
        if selected_game == "0":
            gameObject = RR(givenID, [], ownerID, entryFee)
            gameName = "Russian Roullete"

        # load config info and load assets
        configInfo = json.load(open(f"Config\\Guilds\\{guild}.json", "r"))
        guild = await disnakeClient.fetch_guild(guild)
        hostChannel = await guild.fetch_channel(configInfo["roomChannel"])
        ownerName = await guild.fetch_member(ownerID)

        # create room
        gameChannel = await helpers.createRoom(guild, configInfo["Catergory"], ownerID, givenID, ownerName)

        # make this all fancy with an embed eventually
        await hostChannel.send(f"Room:{givenID}\nopen for game:{gameName}\nby:{ownerName}\nStatus:Open\nEntryFee:{entryFee}")       

        #  send end user avalible functions inside of the game channel
        await gameChannel.send("To run these commands type !<function name>")
        commands = await gameChannel.send("\n".join([method for method in dir(gameObject) if method.startswith('__') == False and (method in gameObject.__dict__.keys()) == False and method[0:7] != "assist_"]))
        await commands.pin()

        # GameObject
        # MessageID for Host
        # game Channel ID
        # Init Status
        return [gameObject, givenID, gameChannel, True]
    


    # locate the RoomID of an active game from the owners ID
    # This is done this way because DISNAKE FUCKING BROKEY
    # but also because the owner can add users from any channel
    def locateRoom(rooms, guildID, authorID, *args):
        if args[0] == True:
            # if the locate room is in player seek mode
            for roomID in rooms[guildID].keys():
                if authorID in (rooms[guildID][roomID]["players"]):
                    return roomID
                else: continue
        else:
            for roomID in rooms[guildID].keys():
                if (rooms[guildID][roomID]["players"][0]) == authorID:
                    return roomID
                else: continue
        return False

    # add a player to an active room by setting permissions
    async def addPlayer(gameChannel, player) -> bool:
        await gameChannel.set_permissions(player, view_channel=True, send_messages=True)
        return True

    # compares the player in questions balance & the deductable amount to ensure the user does not go into the negative
    # If the user passes this check; deduct the balance from the player and return true; allowing them to entry the room
    def deductBalance(guildID: int, player: disnake.User, deductable: int) -> bool:
        configInfo = json.load(open(f"Config\\Guilds\\{guildID}.json", "r"))
        # Write a check ensuring the player does infact exist in the database
        # Due to logic there shouldn't be a likely reason why the player does not exist
        # But if for some reason they join the server and this is the first command they run; error can happen
        playerBalance = configInfo["economy"][str(player.id)]
        if playerBalance - deductable >= 0:
            configInfo["economy"][str(player.id)] = playerBalance - deductable
            with open(f"Config\\Guilds\\{guildID}.json", "w") as file:
                        json.dump(configInfo, file, indent=4)
            return True
        else:
             return False
    

    def increaseBalance(guildID: int, user: disnake.User, amount: int) -> bool:
        configInfo = json.load(open(f"Config\\Guilds\\{guildID}.json", "r"))
        # attempt easy += amount operator, if failure due to key error- manually set balance to increase amount thus creating new user in database
        try:
            configInfo["economy"][str(user.id)] += amount
        except(KeyError):
            configInfo["economy"][str(user.id)] = amount
        with open(f"Config\\Guilds\\{guildID}.json", "w") as file:
                    json.dump(configInfo, file, indent=4)
        return True
