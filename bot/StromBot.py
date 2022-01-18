import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class StromBot(sc2.BotAI):

    upgrade_map = {}
    async def on_step(self, iteration):
        forges = self.structures(UnitTypeId.FORGE).ready
        cybers = self.structures(UnitTypeId.CYBERNETICSCORE).ready
        #councils = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready

        if iteration == 0:
                await self.chat_send("(protoss)(glhf)(protoss)")
        #If they kill our only base left, attach with everything as a last ditch effort
        if not self.townhalls.ready:
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])

        await self.chrono_boost()

        await self.distribute_workers()

        await self.build_workers()

        await self.warp_pylons()

        await self.take_gas()

        await self.expand()

        await self.warp_gateway()
        #We probably want to put a condition on this at some point
        #Actually we probably want to shift to making this a more general army function which just starts with zealots
        await self.warp_zealots()

        #In this iteration of the bot we are only going to use one cyber
        if (self.structures(UnitTypeId.CYBERNETICSCORE).amount < 1):
            await self.warp_cyber()
        
        if self.structures(UnitTypeId.CYBERNETICSCORE).amount > 0:
            await self.warp_twilight()

        if self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.amount == 1:
            await self.get_charge()

        if self.structures(UnitTypeId.FORGE).amount < 3:
            await self.warp_forge()

        if (forges.amount >= 1):
            for f in forges:
                if f.is_idle:
                    await self.forge_upgrade(f)

        if (cybers.amount > 0):
            for c in cybers:
                if c.is_idle:
                    await self.cyber_upgrade(c)
        '''
        We need to start thinking about a function for attacking with our army
        '''

    async def build_workers(self):

        if self.workers.amount < self.townhalls.amount*22 and self.workers.amount < 66:
            for nexus in self.townhalls.idle:
                if(self.supply_left > 2 or (self.supply_left > 1 and self.already_pending(PYLON))):
                    nexus.train(UnitTypeId.PROBE)

    async def warp_pylons(self):
        nexuses = self.structures(UnitTypeId.NEXUS).ready
        #First check:
        #Do we have less than 5 supply left, and are we not currently building a pylon
        if self.supply_left < 5 and not self.already_pending(PYLON):
            if nexuses.exists:
                if self.supply_cap == 15:
                    if self.can_afford(PYLON):
                        await self.build(PYLON, near=self.main_base_ramp.protoss_wall_pylon)
                elif self.supply_cap < 39:
                    await self.build(PYLON, near=self.main_base_ramp.protoss_wall_pylon.towards(nexuses.first, 10))
                else:
                    await self.build(PYLON, near=nexuses.random.position.towards(self.game_info.map_center, 8))
        elif (self.structures(UnitTypeId.GATEWAY).ready.amount == 1 and
            self.structures(UnitTypeId.FORGE).amount == 1 and
            self.structures(UnitTypeId.PYLON).amount < 2 and
            self.can_afford(UnitTypeId.PYLON)
            ):
                await self.build(PYLON, near=self.main_base_ramp.protoss_wall_pylon.towards(nexuses.first, 10))
    
    #
    async def take_gas(self):
            for nexus in self.townhalls.ready:
                vespene_geysers = self.vespene_geyser.closer_than(15, nexus)
                for vg in vespene_geysers:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break
                    if self.workers.amount > self.townhalls.ready.amount * 21:
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
        #NOTE: WE NEVER WANT MORE GATEWAYS THAN UNITS WHICH COME FROM THE GATEWAY
        #Here we are getting a count of all the units that come from the gateway
        gw_units = (self.units(UnitTypeId.ZEALOT).amount + self.units(UnitTypeId.STALKER).amount + self.units(UnitTypeId.SENTRY).amount +
        self.units(UnitTypeId.ADEPT).amount + self.units(UnitTypeId.HIGHTEMPLAR).amount + self.units(UnitTypeId.DARKTEMPLAR).amount)

        #The most basic check we can make is:
        #Do we have minerals to make a gateway, and are we waiting to make our first?
        #Next we want to make sure that we never make more
        if(self.can_afford(UnitTypeId.GATEWAY)):
            #If we have no gateways, then make a gateway
            #This is like the most basic thing here
            if self.structures(UnitTypeId.GATEWAY).amount < 1:
                await self.build(UnitTypeId.GATEWAY, near=pylons.first.position.towards(self.structures(UnitTypeId.NEXUS).first, 8))
            #Here we check if we have less than 4 gates AND 
            #Do we have more units than we have gateways
            #We don't want to be spending minerals on buildings before we have units
            elif (self.structures(UnitTypeId.GATEWAY).amount < 4 and
            self.structures(UnitTypeId.WARPGATE).amount < 4 and 
            gw_units > self.structures(UnitTypeId.GATEWAY).amount and 
            self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.amount > 0):
                #The first check is:
                #Do we have exactly 1 pylon, 
                #less than 2 gateways
                # and we are not currently warping in a new gateway
                #This gateway will go near our only pylon
                if(pylons.amount == 1 and
                not self.already_pending(UnitTypeId.GATEWAY) and
                self.structures(UnitTypeId.GATEWAY).ready.amount < 2
                ):
                    await self.build(UnitTypeId.GATEWAY, near=pylons.first.position.towards(self.structures(UnitTypeId.NEXUS).first, 8))
                #So if we have more than 1 pylon
                #We want to build this gateway near the last pylon built
                elif pylons.ready.amount > 2:
                    await self.build(UnitTypeId.GATEWAY, near=pylons[1].position.towards(self.structures(UnitTypeId.NEXUS).first, 8))
    #Here we warp in our cybernetics cores
    async def warp_cyber(self):
        pylons = self.structures(UnitTypeId.PYLON)
        #This condition checks the following:
        #Can we afford a cybernetics core
        #
        if (self.can_afford(UnitTypeId.CYBERNETICSCORE) and
        pylons.ready.amount-1 > self.structures(UnitTypeId.CYBERNETICSCORE).amount and
        self.structures(UnitTypeId.GATEWAY).ready.amount > 0 and
        self.structures(UnitTypeId.FORGE).ready.amount > 0 and
        not self.already_pending(UnitTypeId.CYBERNETICSCORE)
        ):
            await self.build(UnitTypeId.CYBERNETICSCORE, near=pylons[-1].position.towards(self.structures(UnitTypeId.FORGE).first, 1))
    
    async def warp_twilight(self):
        pylons = self.structures(UnitTypeId.PYLON)

        if(self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and 
        self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount == 0 and 
        not self.already_pending(UnitTypeId.TWILIGHTCOUNCIL)):
            await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=pylons[-1].position.towards(self.structures(UnitTypeId.FORGE).first, 1))

    async def get_charge(self):
        if (UpgradeId.CHARGE not in self.game_data.upgrades and 
        self.can_afford(UpgradeId.CHARGE)):
            self.research(UpgradeId.CHARGE)

    async def warp_forge(self):
        pylons = self.structures(UnitTypeId.PYLON)
        gates = self.structures(UnitTypeId.GATEWAY)
        forges = self.structures(UnitTypeId.FORGE)
        if (self.minerals > 149):
            if ((pylons.ready.amount > self.structures(UnitTypeId.FORGE).amount) and
            gates.amount >= 1 and
            (gates.amount > forges.amount)):
                await self.build(UnitTypeId.FORGE, near=pylons[-1].position.towards(gates[-1], 4))

    async def warp_zealots(self):
        #First we want to check if we have gates to warp in warp_zealots
        if self.structures(UnitTypeId.GATEWAY).amount >= 1:
            if self.can_afford(UnitTypeId.ZEALOT):
                #Now we will make a list of gateways
                gates = self.structures(UnitTypeId.GATEWAY).ready
                for g in gates.idle:
                    g.train(UnitTypeId.ZEALOT)

    async def chrono_boost(self):
        #The first check we make is:
        #Can we chrono a gateway, then can we chrono a nexus
        nexuses = self.structures(UnitTypeId.NEXUS)
        gates = self.structures(UnitTypeId.GATEWAY)

        for g in gates:
            if(not g.is_idle and
            not g.has_buff(BuffId.CHRONOBOOSTENERGYCOST)):
                for n in nexuses:
                    n(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, g)

        for n in nexuses:
            if (not n.is_idle and
            not n.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and
            self.structures(UnitTypeId.PYLON).ready.amount >= 1 and 
            gates.amount < 1):
                n(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, n)

    async def forge_upgrade(self, forge):

        if UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)

        if UpgradeId.PROTOSSSHIELDSLEVEL1 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSSHIELDSLEVEL1)

        if UpgradeId.PROTOSSGROUNDARMORSLEVEL1 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)

        if UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2)

        if UpgradeId.PROTOSSSHIELDSLEVEL2 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSSHIELDSLEVEL2)

        if UpgradeId.PROTOSSGROUNDARMORSLEVEL2 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL2)

        if UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3)
        
        if UpgradeId.PROTOSSSHIELDSLEVEL3 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSSHIELDSLEVEL3)
        
        if UpgradeId.PROTOSSGROUNDARMORSLEVEL3 not in self.game_data.upgrades:
            forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL3)

    async def cyber_upgrade(self, cyber):
        if UpgradeId.WARPGATERESEARCH not in self.game_data.upgrades:
            cyber.research(UpgradeId.WARPGATERESEARCH)

def main():

    sc2.run_game(maps.get("AcropolisLE"), [Bot(Race.Protoss, StromBot()), Computer(Race.Terran, Difficulty.Easy)], realtime=False)

if __name__ == '__main__':
    main()
