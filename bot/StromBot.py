import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class StromBot(sc2.BotAI):
    pylon_list = []
    async def on_step(self, iteration):

        if iteration == 0:
                await self.chat_send("(protoss)(glhf)(protoss)")

        await self.distribute_workers()

        await self.build_workers()

        await self.warp_pylons()

        await self.take_gas()

        await self.expand()

        await self.warp_gateway()

        #In this iteration of the bot we are only going to use one cyber
        if self.structures(UnitTypeId.CYBERNETICSCORE).amount < 1:
            await self.warp_cyber()

        if self.structures(UnitTypeId.FORGE).amount < 3:
            await self.warp_forge()

    async def build_workers(self):

        if self.workers.amount < self.townhalls.amount*22:
            for nexus in self.townhalls.idle:
                if(self.supply_left > 2 or (self.supply_left > 1 and self.already_pending(PYLON))):
                    nexus.train(UnitTypeId.PROBE)

    async def warp_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.structures(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.supply_cap == 15:
                    if self.can_afford(PYLON):
                        await self.build(PYLON, near=self.main_base_ramp.protoss_wall_pylon)
                elif self.supply_cap < 39:
                    await self.build(PYLON, near=self.main_base_ramp.protoss_wall_pylon.towards(nexuses.first))
                else:
                    await self.build(PYLON, near=nexuses.random.position.towards(self.game_info.map_center, 8))
                    '''for pylon in self.structures(UnitTypeId.PYLON):
                        if pylon not in self.pylon_list:
                            self.pylon_list.append(pylon)'''

    async def take_gas(self):
            for nexus in self.townhalls.ready:
                vespene_geysers = self.vespene_geyser.closer_than(15, nexus)
                for vg in vespene_geysers:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break
                    if self.workers.amount > 21:
                        if((not self.gas_buildings or
                            not self.gas_buildings.closer_than(1, vg)) and
                            not self.already_pending(UnitTypeId.ASSIMILATOR)
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
        #Here we make a list of pylons so that we can reference some certain ones
        pylons = self.structures(UnitTypeId.PYLON)
        if(self.can_afford(UnitTypeId.GATEWAY) and
        self.structures(UnitTypeId.GATEWAY).amount < 4):
            if(pylons.amount == 1 and
            not self.already_pending(UnitTypeId.GATEWAY) and
            self.structures(UnitTypeId.GATEWAY).ready.amount < 2
            ):
                await self.build(UnitTypeId.GATEWAY, near=pylons.first.position.towards(self.structures(UnitTypeId.NEXUS).first, 8))
            elif pylons.ready.amount > 1:
                await self.build(UnitTypeId.GATEWAY, near=pylons[-1].position.towards(self.structures(UnitTypeId.NEXUS).first, 8))

def main():

    sc2.run_game(maps.get("AcropolisLE"), [Bot(Race.Protoss, StromBot()), Computer(Race.Terran, Difficulty.Easy)], realtime=False)

if __name__ == '__main__':
    main()
