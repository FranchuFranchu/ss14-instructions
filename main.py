import os
from math import lcm, gcd
from itertools import chain
from pathlib import Path
from yaml import SafeLoader, load
from attrdict import AttrDict
import yaml
import re
BASE_DIR = Path(os.environ["SS14_PATH"])

def type_constructor(loader, node):
	if type(node) == yaml.nodes.MappingNode:
		return loader.construct_mapping(node)
	return {}
	
def get_loader():
	loader = SafeLoader
	s = "StopPiloting DamageTypeTrigger SpillTileReaction CableTerminalNode SpawnPrototypeAtContainer ContainerEmpty ReagentThreshold WashCreamPieReaction PopupEveryone BuildComputer AddToSolutionReaction TritiumFireReaction GibBehavior SetAnchor DeleteEntity FadeBehaviour DeadMobState WeekdayInMonth PlantAdjustNutrition CombatMode ExplodeBehavior BuildMachine SpriteStateChange Computus PlantAdjustHealth DisarmAction DoActsBehavior ColorCycleBehaviour DayOfYear FlammableTileReaction RaiseEvent AirlockBolted DoorWelded MachineDeconstructedEvent PortablePipeNode IncompatibleConditionsRequirement RobustHarvest GhostBoo ToggleInternalsAction ContainerNotEmpty ElectrocutionNode ScreamAction PlantAdjustPests SetStackCount AnyConditions ChineseNewYear CleanTileReaction CableNode DumpCanisterBehavior DeleteEntitiesInContainer DebugToggle SpillBehavior PhysShapeCircle PulseBehaviour KillRandomPersonCondition MovespeedModifier GiveItemOnHolidaySpecial SpillIfPuddlePresentTileReaction PipeNode EmptyAllContainersBehaviour GiveItemSpell PlantAdjustWeeds PlantAdjustMutationLevel WirePanel ToggleLightAction ChangeConstructionNodeBehavior EntityAnchored DebugTargetEntity FridayThirteenth LungBehavior EmptyOrWindowValidInTile SatiateHunger PlantAdjustMutationMod NormalMobState PlantDiethylamine CriticalMobState AllConditions SpawnPrototype MachineFrameRegenerateProgress StopBeingPulled StealCondition ExtinguishTileReaction ExtinguishReaction FlammableReaction TileNotBlocked OrganType StayAliveCondition ContainerSlot PlantAdjustToxins CableTerminalPortNode AdjacentNode TabletopChessSetup SpawnEntitiesBehavior VisualizerDataInt WaterVaporReaction AddComponentSpecial RandomizeBehaviour TileType SpriteChange DebugTargetPoint SnapToGrid SmokeAreaReactionEffect PhysShapeAabb PlaySoundBehavior ToiletLidClosed TraitorRequirement Custom MachineFrameComplete DieCondition PlantAdjustWater EmptyAllContainers RemoveCuffs WallmountCondition ComponentInTile ToggleMagbootsAction ExplosionReactionEffect DestroyEntity HealthChange PortPipeNode SatiateThirst FoamAreaReactionEffect DebugInstant PlasmaFireReaction AddContainer TabletopParchisSetup ConditionalAction ResistFire Unbuckle PlantAffectGrowth CableDeviceNode NoWindowsInTile DamageTrigger StopPulling"
	for i in s.split(" "):
		SafeLoader.add_constructor("!type:"+i, type_constructor)
		
	return loader

s = list()
for i in (BASE_DIR / "Resources/Prototypes/Recipes/Reactions").glob("**/*"):
	if i.is_file():
		#s |= set(re.findall(r'!type:(.+?)\b', i.open().read()))
		with i.open() as f:
			L = load(f, Loader=get_loader())
			if type(L) == list:
				s.extend(L)

direct_ingredient_mapping = {}
indirect_ingredient_mapping = {}

for i in s:
	i = AttrDict(i)
	if i.type == 'reaction':
		if not i.get("products"):
			continue
		main_id = i.id
		product_amount = list(i.products.values())[0]
		map_obj = {}
		for k, v in i.reactants.items():
			if not v.get("catalyst"):
				map_obj[k] = v["amount"] / product_amount
			else:
				map_obj[k] = 0
		direct_ingredient_mapping[main_id] = map_obj
def find_ingredients(k):
	v = direct_ingredient_mapping.get(k)
	if v is None:
		return {k: 1}
	s = {}
	for k, v in v.items():
		s |= { tk: tv * v for tk, tv in find_ingredients(k).items() }
		
	return s
	
for k, v in direct_ingredient_mapping.items():
	indirect_ingredient_mapping[k] = find_ingredients(k)

from json import dumps

d = {}

for chemical, recipe in indirect_ingredient_mapping.items():
	factors = []
	for k, v in recipe.items():
		if v:
			factors.append(1 / v)
	
	multiply_by = []
	for i in factors:
		if i % 1:
			factor = 1
			for factor in range(1, 1000):
				if not round(factor * (i % 1), 4) % 1:
					multiply_by.append(factor)
					break
	
	lcm_ = lcm(*multiply_by)
	
	factors = [int(round((1 / v) * lcm_, 4)) for v in filter(lambda v: v != 0, recipe.values())]
	
	gcd_ = gcd(*factors)
	#print(factors, gcd_)
	
	new_values = {k: int(round((1 / v) * lcm_, 4)) / gcd_ if v != 0 else 0 for k, v in recipe.items()}
	#print(str(sum(new_values.values())) + "u " + chemical, new_values)
	
	d[chemical] = new_values
	
print(dumps(d))
	