import sc2 
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class StromBot(sc2.BotAI):
    def __init__(self):
        self.bases = 1
    
    async def on_step(self, iteration):
        
        if iteration == 0:
                await self.chat_send("(protoss)(glhf)(protoss)")

        await self.distribute_workers()
        
        await self.build_workers()

        await self.warp_pylons()

        await self.take_gas()

        await self.expand() 
        
        await self.warp_gateway()

    async def build_workers(self):
        
        if self.workers.amount < self.townhalls.amount*22:
            for nexus in self.townhalls.idle:
                nexus.train(UnitTypeId.PROBE)
                    
        
    async def warp_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.structures(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    async def take_gas(self):
            for nexus in self.townhalls.ready:
                vespene_geysers = self.vespene_geyser.closer_than(15, nexus)
                for vg in vespene_geysers:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break
                    if(not self.gas_buildings or 
                        not self.gas_buildings.closer_than(1, vg)
                        ):
                        worker.build(UnitTypeId.ASSIMILATOR, vg)
                        worker.stop(queue=True)

    async def expand(self):
            if( 
                self.can_afford(NEXUS) and 
                (self.workers.amount / self.structures(UnitTypeId.NEXUS).amount > 21) and 
                not self.already_pending(NEXUS)
            ):
                await self.expand_now()               
    
    async def warp_gateway(self):
        pass
    
def main():
    
    sc2.run_game(maps.get("AcropolisLE"), [Bot(Race.Protoss, StromBot()), Computer(Race.Terran, Difficulty.Easy)], realtime=False)

if __name__ == '__main__':
    main()