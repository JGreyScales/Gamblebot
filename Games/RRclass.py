import disnake, random, math
from Config.helpers import helpers
class RussianRoullete:
    def __init__(self, id: int, players: list, owner: int, entryFee: int) -> None:
        self.id = id
        self.players = players
        self.players.append(owner)
        self.roomID = 0
        self.ownerID = owner       
        self.entryFee = entryFee
        self.bulletChamber = 0
        self.currentIndex = 0
        self.multiplier = 1

        # gameState is a required field
        self.gameState = False
    
    async def assist_nextPlayer(self, message: disnake.Message, room: dict) -> bool:
        self.currentIndex += 1
        # if the current index is greater then the amount of players
        if self.currentIndex > len(self.players)-1:
            self.currentIndex = 0

        # if only one player is left, award them and close the game
        if len(self.players) == 1:
            await room["gameChannel"].send(f"Congrats, you have won. Your payout is {math.floor((self.entryFee * self.multiplier) / 1.8)}")
            self.gameState = False
            # Write code to add balance to the end user
            return [self.players[0], math.floor((self.entryFee * self.multiplier) / 1.8), True]
        else:
            await room["gameChannel"].send(f"It is currently {await message.guild.fetch_member(self.players[self.currentIndex])}'s turn")
            return False
            
    async def fire(self, message: disnake.Message, room: dict) -> bool:
        print(self.gameState)
        if self.gameState == True:
            if self.bulletChamber == self.currentIndex + 1:
                await room["gameChannel"].set_permissions(message.author, view_channel=False, send_messages=False)
                self.players.pop(self.currentIndex)
                await room["gameChannel"].send(f"user {message.author} has been eliminated")

                # Send message saying that this user has been eliminated

            returnValue = await RussianRoullete.assist_nextPlayer(self, message, room)
            # finally, run code deciding if the player has won, or who the next player is

            if returnValue == True:
                return True
            
    async def spinBarrel(self, message: disnake.Message, room: dict) -> bool:
        if self.gameState == True:
            self.bulletChamber = random.randint(1, len(room["players"]))
            returnStatus = await RussianRoullete.assist_nextPlayer(self, message, room)
            if returnStatus == False:
                await room["gameChannel"].send(f"The barrel has been spun")

    
    async def startGame(self, message: disnake.Message, room: dict):
        # If the game is not currently active, run the setup commands
        if self.gameState != True and str(message.author.id) == str(self.ownerID):
            self.bulletChamber = random.randint(1, len(room["players"]))
            self.gameState = True
            self.players = list(room["players"])
            self.currentIndex = random.randint(0, len(room["players"]))
            self.multiplier = len(self.players)
            text = (f"""Game started, Please use !fire to commence future rounds until this room is completed\nEach player can use !spinBarrel once to randomly spin the barrel and pass it to the next person\nIt is currently {await message.guild.fetch_member(self.players[self.currentIndex])}'s turn""")
            await room["gameChannel"].send(text)