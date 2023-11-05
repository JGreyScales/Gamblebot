import disnake
class RussianRoullete:
    def __init__(self, id: int, players: list, owner: int, entryFee: int) -> None:
        self.id = id
        self.players = players
        self.roomID = 0
        self.ownerID = owner       
        self.entryFee = entryFee
    
    def assist_eliminatePlayer(self, playerID) -> bool:
        # run the code, if no errors return true
        return True
    
    def startRound(self, message: disnake.Message, room: dict) -> bool:
        print("ran")
        return True
