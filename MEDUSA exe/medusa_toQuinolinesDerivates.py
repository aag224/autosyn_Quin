#from rich_click import group

from matterlab_hotplates import IKAHotplate
from matterlab_pumps import JKemPump
from matterlab_valves import JKemNewValve
from pathlib import Path
from typing import Union, Dict, Optional
import json
from math import ceil
import time
from datetime import datetime

class BaseProcedures(object):
    def __init__(self):
        self._load_ports_settings()
        self._initialize_pump()
        self._initialize_valve()
        self._initialize_hotplate()
        #self._syringe_content = {"pump_port": "N2"}

    def _load_ports_settings(self):
        with open(Path.cwd().parent.parent / 'data' / 'ports_settings.json') as f:
            self.ports_settings = json.load(f)

    def _initialize_pump(self):
        self.pump1 = JKemPump('COM3', 1, ports=self.ports_settings["pump1_ports"])
        self.pump2 = JKemPump('COM3', 2, ports=self.ports_settings["pump2_ports"]) 
        self.pump4 = JKemPump('COM3', 4, ports=self.ports_settings["pump4_ports"]) 
        self.pump5 = JKemPump('COM3', 5, ports=self.ports_settings["pump5_ports"]) 
        self.pump6 = JKemPump('COM3', 6, ports=self.ports_settings["pump6_ports"]) 
        

    def _initialize_valve(self):
        self.valve = []
        for i in range(1, len(self.ports_settings["valve_ports"])+1):
            valve = JKemNewValve(com_port = 'COM5',                   
                                  valve_num = i,
                                  ports = self.ports_settings["valve_ports"][i-1]
                                  )
            self.valve.append(valve)

    def _initialize_hotplate(self):
        self.hotplate = IKAHotplate(com_port ='COM9')                

    def _build_fluid_connection(self,
                                zone: Dict
                                ):
            if "_group_1" in zone["pump_port"]:
                pump_port = self.pump1.switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 1 port {zone['pump_port']} at {pump_port}\n")
                if "valve_port" in zone:
                    if zone['valve_port'] in self.valve[0].ports:
                        valve_port = self.valve[0].switch_port(port=zone['valve_port'])
                        print(f"Fluid connection built for \n"
                              f"Valve 1 port {zone['valve_port']} at {valve_port}")
                    elif zone['valve_port'] in self.valve[1].ports:
                        edge_port = self.valve[0].switch_port(port="edge1")
                        valve_port = self.valve[1].switch_port(port=zone['valve_port'])
                        print(f"Fluid connection built for \n"
                              f"Valve 2 port {zone['valve_port']} at {valve_port}")

            elif "_group_2" in zone['pump_port']:
                pump_port = self.pump2.switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 2 port {zone['pump_port']} at {pump_port}\n")
                if "valve_port" in zone:
                    if zone['valve_port'] in self.valve[2].ports:
                        valve_port = self.valve[2].switch_port(port=zone['valve_port'])
                        print(f"Fluid connection built for \n"
                              f"Valve 3 port {zone['valve_port']} at {valve_port}")
                    elif zone['valve_port'] in self.valve[3].ports:
                        edge_port = self.valve[2].switch_port(port="edge2")
                        valve_port = self.valve[3].switch_port(port=zone['valve_port'])
                        print(f"Fluid connection built for \n"
                              f"Valve 4 port {zone['valve_port']} at {valve_port}")

            elif "_group_4" in zone['pump_port']:
                pump_port = self.pump4.switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 4 port {zone['pump_port']} at {pump_port}\n")

            elif "_group_5" in zone['pump_port']:
                pump_port = self.pump5.switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 5 port {zone['pump_port']} at {pump_port}\n")
                
            elif "_group_6" in zone['pump_port']:
                pump_port = self.pump6.switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 6 port {zone['pump_port']} at {pump_port}\n")
                
    def _add_step(self, task: str, **params):
        self.reaction_steps[str(len(self.reaction_steps) + 1)] = {"task": task, "parameters": params}

    def transfer_compound(self,
                          target_zone: Dict,
                          quantity: float,
                          specification: str = "liquid",
                          source_zone: Dict = None,
                          compound: Union[str, None] = None,
                          delay: int = 0,
                          **kwargs
                          ):
        if source_zone is None:
            source_zone = self.get_compound_location(compound)

        self._syringe_content: Dict = source_zone
        if "_group_1" in source_zone["pump_port"]:
            self.pump = self.pump1
        elif "_group_2" in source_zone["pump_port"]:
            self.pump = self.pump2
        elif "_group_4" in source_zone["pump_port"]:
            self.pump = self.pump4
        elif "_group_5" in source_zone["pump_port"]:
            self.pump = self.pump5
        elif "_group_6" in source_zone["pump_port"]:
            self.pump = self.pump6

        if specification == "gas":
            speed = 2.0
            self._build_fluid_connection(zone=source_zone)
            self.pump.draw(volume = quantity, speed= speed)
            time.sleep(delay)
            self._build_fluid_connection(zone = target_zone)
            self.pump.dispense_all(speed = speed)
        else:
            if "speed" in kwargs:
                speed = kwargs["speed"]
            else:
                speed = 0.5
            self._build_fluid_connection(zone=source_zone)
            self.pump.draw(volume=quantity, speed=speed)
            time.sleep(delay)
            self._build_fluid_connection(zone=target_zone)
            self.pump.dispense_all(speed=speed)

    def schlenk_cycle(self,
                      zones: list[Dict],
                      waste: Dict,
                      num_cycles: int,
                      delay: int = 1,
                      **kwargs):
        for zone in zones:
            for i in range (0, num_cycles):
                self.transfer_compound(target_zone = waste,
                                       quantity = 10.0,
                                       source_zone = zone,
                                       delay = delay,
                                       **kwargs
                                       )
                print(f"Schlenk cycle on zone {zone} cycle {i+1} done.")

    @property
    def syringe_content(self):
        return self._syringe_content

    def rinse_syringe(self,
                      source_zone: Dict,
                      waste: Dict,
                      quantity: float = 0.5,
                      iterations: int = 3,
                      delay: int = 2,
                      **kwargs):
        for i in range(0, iterations):
            self.transfer_compound(
                                   target_zone=waste,
                                   quantity = quantity,
                                   source_zone=source_zone,
                                   delay = delay,
                                   **kwargs
                                   )
        print(f"Syringe has been rinsed with solution at zone {source_zone}.")

    def add_solution(self,
                     target_zone: Dict,
                     quantity: float,
                     source_zone: Dict,
                     source_N2: Dict,
                     waste: Dict,
                     purge_N2: int = 2,
                     delay: int = 2,
                     rinse: bool = True,
                     **kwargs
                     ):
        if rinse:
            if (self.syringe_content != source_zone) \
                    and (self.syringe_content != source_N2):
                self.rinse_syringe(source_zone, waste=waste)

        self.transfer_compound(target_zone = target_zone,
                               quantity=quantity,
                               source_zone=source_zone,
                               delay = delay,
                               **kwargs)
        print(f"{quantity} mL solution from zone {source_zone} transferred to {target_zone}.")

        for i in range(0, purge_N2):
            self.transfer_compound(specification='gas',
                                   target_zone=target_zone,
                                   quantity=2.0,
                                   source_zone=source_N2,
                                   )
            print(f"Tubing to {target_zone} flushed with 2 mL N2 for {i+1} times")

        self._syringe_content = source_zone

    def make_solution(self, zone: Dict,
                      quantity: float,
                      mix_iterations: int = 5,
                      source_solvent = Dict,
                      waste = Dict,
                      delay: int = 2,
                      **kwargs):
        transfer_iterations = ceil(quantity / 10.0)
        quantity_per_iteration = quantity / transfer_iterations

        for j in range (0, transfer_iterations):
            self.add_solution(target_zone=zone,
                              quantity=quantity_per_iteration,
                              source_zone=source_solvent,
                              waste = waste,
                              purge_N2=0,
                              delay = delay,
                              **kwargs
                              )
        print(f"{quantity} mL {source_solvent.keys()} added to stock solution zone {zone}.")

        self._syringe_content = zone

        for k in range(0, mix_iterations):
            self.add_solution(target_zone=zone,
                              quantity=10.0,
                              source_zone=zone,
                              waste = waste,
                              purge_N2=2,
                              delay = delay,
                              **kwargs
                              )
        self.add_solution(target_zone=zone,
                          quantity=1,
                          source_zone=zone,
                          waste = waste,
                          purge_N2=0,
                          **kwargs
                          )
        print(f"Solution at {zone} has been made with {quantity} mL of Dioxane.")

        self._syringe_content = zone

    def heat_and_stir(self,
                      reaction_time: float,
                      temp: float,
                      rpm: int,
                      **kwargs):
        self.hotplate.rpm = int(rpm)
        self.hotplate.temp = temp
        print(f"Stir at {rpm} and heat at {temp} start.")
        time.sleep(reaction_time*3600)
        self.hotplate.stand_by()
        print("Heat and stir stopped.")

class Reaction(BaseProcedures):
    def __init__(self):
        super().__init__()

    def generate_experiment_One_details(self, num_reactions: int, temp = 65, reaction_time = 24):
        self.available_reaction_zones = []
        self.available_1wash_zones = []
        self.available_2wash_zones = []
        if num_reactions > 15:
            raise ValueError("You can't run more than 15 reactions with this setup.")
    
        for i in range(0, num_reactions):
            self.available_reaction_zones.append({"pump_port": "reaction_group_1",
                                                "valve_port": f"reaction1_{i}"})
        for w in range(1, (num_reactions//2)+1):
            self.available_1wash_zones.append({"pump_port":f"wash{w}_group_4"})

        for w in range(1, (num_reactions//2)+1):
            self.available_2wash_zones.append({"pump_port":f"wash{w}_group_5"})
        
        self.reaction_steps = {
            "1": {
                "task": "schlenk_cycle",
                "parameters": {
                    "specification": "gas",
                    "zones":  self.available_reaction_zones,
                    "waste": {"pump_port": "waste_group_1"},
                    "num_cycles": 5,
                    "delay": 1
                }
            },
            "2":{
                "task": "rinse_syringe",
                "parameters": {
                    "specification": "liquid",
                    "source_zone": {"pump_port": "THF_group_1"},
                    "waste": {"pump_port": "waste_group_1"},
                    "quantity": 1,
                    "iteration": 3,
                    "delay": 1.0
                }
            },
        }
        for j in range(0, num_reactions):
            #  self.reaction_steps[f"{j*2+5}"]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone =  self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "Br-Quinoline_group_1"},
                    source_N2 = {"pump_port": "N2_group_1"},
                    waste = {"pump_port": "waste_group_1"},
                    purge_N2 = 2, 
                    delay = 10.0,
                    rinse = False
            )
        for j in range(0, num_reactions):
            # self.reaction_steps[f"{j*2+6}"]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone =  self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "Boronic_acid_group_1"},
                    source_N2 = {"pump_port": "N2_group_1"},
                    waste ={"pump_port": "waste_group_1"},
                    purge_N2 = 2,
                    delay = 10.0,
                    rinse = False
            )
        for j in range(0, num_reactions):
            # self.reaction_steps[f"{j*2+7}]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone = self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "Pd_XPhos_G2_group_1"},
                    source_N2 = {"pump_port": "N2_group_1"},
                    waste = {"pump_port": "waste_group_1"},
                    purge_N2 = 2,
                    delay = 10.0,
                    rinse = False
            )
        for j in range(0, num_reactions):
            # self.reaction_steps[f"{j * 2 + 8}"]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone =  self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "K3PO4_group_1"},
                    source_N2 = {"pump_port": "N2_group_1"},
                    waste = {"pump_port": "waste_group_1"},
                    purge_N2 = 2,
                    delay = 10.0,
                    rinse = False
            )
        self._add_step("heat_and_stir",
                specification = "none",
                reaction_time = reaction_time,
                temp = temp,
                rpm = 800
        )
        if num_reactions//2 > 3:
                    raise ValueError("The number of reactions is too high for the available wash zones. Please reduce the number of reactions to 6 or less.")
        
        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification = "liquid",
                        target_zone = self.available_1wash_zones[j],
                        quantity = 0.75,
                        source_zone = {"pump_port": "NaCl_aq_group_4"},
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse = True
            )
        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification =  "liquid",
                        target_zone =  self.available_2wash_zones[j],
                        quantity = 0.75,
                        source_zone = {"pump_port": "NaCl_aq_group_5"},
                        source_N2 = {"pump_port": "N2_group_5"},
                        waste = {"pump_port": "waste_group_5"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse = True
            )
        self._add_step("heat_and_stir",
                specification = "none",
                reaction_time = 0.08333,
                temp = 0,
                rpm = 800
        )
        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification = "liquid",
                        target_zone =  {"pump_port": "waste_group_4"},
                        quantity = 0.75,
                        source_zone = self.available_1wash_zones[j],
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse = True
            )
        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification = "liquid",
                        target_zone = {"pump_port": "waste_group_5"},
                        quantity = 0.75,
                        source_zone = self.available_2wash_zones[j],
                        source_N2 = {"pump_port": "N2_group_5"},
                        waste = {"pump_port": "waste_group_5"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse = True
            )
        with open(Path.cwd().parent.parent/'data'/'experimentOne_plan.json', 'w') as f:
            json.dump(self.reaction_steps, f, indent=2)

    def generate_experiment_Two_details(self, num_reactions: int, temp = 0, reaction_time = 2):
        self.available_reaction_zones = []
        self.available_1wash_zones = []
        self.available_2wash_zones = []
        if num_reactions > 15:
            raise ValueError("You can't run more than 15 reactions with this setup.")
        for i in range(0, num_reactions):
            self.available_reaction_zones.append({"pump_port": "reaction_group_2",
                                                "valve_port": f"reaction2_{i}"}
                                                )
        for w in range(1, (num_reactions//2)+1):
            self.available_1wash_zones.append({"pump_port":f"wash{w}_group_4"})

        for w in range(1, (num_reactions//2)+1):
            self.available_2wash_zones.append({"pump_port":f"wash{w}_group_5"})
        
        self.reaction_steps = {
            "1": {
                "task": "schlenk_cycle",
                "parameters": {
                    "specification": "gas",
                    "zones":  self.available_reaction_zones,
                    "waste": {"pump_port": "waste_group_2"},
                    "num_cycles": 5,
                    "delay": 1
                }
            },
            "2":{
                "task": "rinse_syringe",
                "parameters": {
                    "specification": "liquid",
                    "source_zone": {"pump_port": "THF_group_2"},
                    "waste": {"pump_port": "waste_group_2"},
                    "quantity": 1,
                    "iteration": 3,
                    "delay": 1.0
                }
            }
        }
        for j in range(0, num_reactions):
            #  self.reaction_steps[f"{j*2+5}"]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone = self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "Malonitrile_group_2"},
                    source_N2 = {"pump_port": "N2_group_2"},
                    waste = {"pump_port": "waste_group_2"},
                    purge_N2 = 2,
                    delay = 10.0,
                    rinse = False
            )
        for j in range(0, num_reactions):
            # self.reaction_steps[f"{j*2+6}"]
            self._add_step("add_solution",
                    specification = "liquid",
                    target_zone = self.available_reaction_zones[j],
                    quantity = 0.75,
                    source_zone = {"pump_port": "NaHCO3_group_2"},
                    source_N2 = {"pump_port": "N2_group_2"},
                    waste = {"pump_port": "waste_group_2"},
                    purge_N2 = 2,
                    delay = 10.0,
                    rinse = False
            )
        self._add_step("heat_and_stir",
                specification = "none",
                reaction_time = reaction_time,
                temp = temp,
                rpm = 800
        )
        if num_reactions//2 > 3:
            raise ValueError("The number of reactions is too high for the available wash zones. Please reduce the number of reactions to 6 or less.")

        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification = "liquid",
                        target_zone = self.available_1wash_zones[j],
                        quantity = 0.75,
                        source_zone = {"pump_port": "NaCl_aq_group_4"},
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse =  True
            )
            for j in range(0, num_reactions//2):
                self._add_step("add_solution",
                            specification = "liquid",
                            target_zone =  self.available_2wash_zones[j],
                            quantity = 0.75,
                            source_zone = {"pump_port": "NaCl_aq_group_5"},
                            source_N2 = {"pump_port": "N2_group_5"},
                            waste = {"pump_port": "waste_group_5"},
                            purge_N2 = 2,
                            delay = 10.0,
                            rinse = True
                )
        self._add_step("heat_and_stir",
                specification =  "none",
                reaction_time = 0.08333,
                temp = 0,
                rpm = 800
        )
        for j in range(0, num_reactions//2):
            self._add_step("add_solution",
                        specification = "liquid",
                        target_zone =  {"pump_port": "waste_group_4"},
                        quantity = 0.75,
                        source_zone = self.available_1wash_zones[j],
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 10.0,
                        rinse = True
            )
            for j in range(0, num_reactions//2):
                self._add_step("add_solution",
                            specification = "liquid",
                            target_zone =   {"pump_port": "waste_group_5"},
                            quantity = 0.75,
                            source_zone = self.available_2wash_zones[j],
                            source_N2 ={"pump_port": "N2_group_5"},
                            waste = {"pump_port": "waste_group_5"},
                            purge_N2 = 2,
                            delay = 10.0,
                            rinse = True
                )
        with open(Path.cwd().parent.parent / 'data' / 'experimentTwo_plan.json', 'w') as f:
            json.dump(self.reaction_steps, f, indent=2)

    def generate_rinse_details(self, num_reactions: int, group: int=1, solvent: str = "THF", iterations: int = 3):
        self.available_reaction_zones = []

        for i in range(0, num_reactions):
            self.available_reaction_One_zones.append({"pump_port": "reaction_group_1",
                                                "valve_port": f"reaction1_{i}"})
        for i in range(0, num_reactions):
            self.available_reaction_Two_zones.append({"pump_port": "reaction_group_2",
                                                "valve_port": f"reaction2_{i}"}
                                                )
        solvent = solvent or f"THF_group_{group}"
        waste   = {"pump_port": f"waste_group_{group}"}
        n2      = {"pump_port": f"N2_group_{group}"}
        for i in range(num_reactions):
            vial = {"pump_port": f"reaction_group_{group}",
                    "valve_port": f"reaction{group}_{i}"}
            self._add_step("add_solution",
                        specification="liquid",
                        source_zone={"pump_port": solvent}, target_zone=vial,
                        source_N2=n2, waste=waste,
                        quantity=1, purge_N2=2, delay=2.0, rinse=False)
            self._add_step("add_solution",
                        specification="liquid",
                        source_zone=vial, target_zone=waste,
                        source_N2=n2, waste=waste,
                        quantity=1, purge_N2=2, delay=2.0, rinse=True)

        for i in range(num_reactions):
            self._add_step("add_solution",
                            specification="gas",
                            source_zone=n2,
                            target_zone={"pump_port": f"reaction_group_{group}",
                                        "valve_port": f"reaction{group}_{i}"},
                            source_N2=n2, waste=waste,
                            quantity=5, purge_N2=0, delay=1.0, rinse=False)

            with open(Path.cwd().parent.parent/'data'/f'experiment_syringe_group_{group}.json', 'w') as f:
                json.dump(self.reaction_steps, f, indent=2)

    def run_reaction(self, reaction: Dict):
        if reaction["task"] == "schlenk_cycle":
            self.schlenk_cycle(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
        elif reaction["task"] == "rinse_syringe":
            self.rinse_syringe(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
        elif reaction["task"] == "make_solution":
            self.make_solution(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
            input("Press Enter to continue")
        elif reaction["task"] == "add_solution":
            self.add_solution(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
        elif reaction["task"] == "heat_and_stir":
            self.heat_and_stir(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))

    def run_reactions(self, rxn_steps: Dict = None):
        if rxn_steps is None:
            rxn_steps = self.reaction_steps
        for i in range(0, len(rxn_steps)):
            self.run_reaction(rxn_steps[f"{i + 1}"])