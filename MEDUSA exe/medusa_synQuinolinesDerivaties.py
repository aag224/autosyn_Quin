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
        self._initialize_valve()
        self._initialize_pump()
        self._initialize_hotplate()
        self._syringe_content = {"pump_port":"N2"}
        self.GROUPS = {
            "_group_1": ("pump1", "valve1"),
            "_group_2": ("pump2", "valve2"),
            "_group_4": ("pump3", "valve3"),
        }

    def _load_ports_settings(self):
        with open(Path.cwd().parent.parent /'data' / 'ports_settings2.json') as f:
            self.ports_settings = json.load(f)
        self.pump_cfg: Dict[str, Dict] = self.ports_settings["pumps"]
        self.valve_cfg: Dict[str, Dict] = self.ports_settings["valves"]

    def _initialize_pump(self):
        self.pumps = {}
        for pump_id, cfs in self.pump_cfg.items():
            self.pumps[pump_id] = JKemPump(com_port=cfs["com_port"],
                                               address=cfs['address'],
                                               ports=cfs['ports'])

    def _initialize_valve(self):
        self.valves = {}
        for valve_id, cfs in self.valve_cfg.items():
            self.valves[valve_id] = JKemNewValve(com_port=cfs["com_port"],
                                                    valve_num=cfs["valve_num"],
                                                    ports=cfs["ports"])

    def _initialize_hotplate(self):
        self.hotplate1 = IKAHotplate(com_port='COM7')
        self.hotplate2 = IKAHotplate(com_port='COM9')
        self.hotplate3 = IKAHotplate(com_port='COM6')

        self.hotplates = {
            "hotplate1": self.hotplate1,
            "hotplate2": self.hotplate2,
            "hotplate3": self.hotplate3
        }

    def _build_fluid_connection(self,
                                zone: Dict
                                ):
        if "pump_port" in zone:
            if "_group_1" in zone["pump_port"]:
                pump_port = self.pumps["pump1"].switch_port(port=zone['pump_port'])  
                print(f"Fluid connection built for \n"
                    f"Pump 1 port {zone['pump_port']} at {pump_port}\n")
            elif "_group_2" in zone["pump_port"]:
                pump_port = self.pumps["pump2"].switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 2 port {zone['pump_port']} at {pump_port}\n")
            elif "_group_4" in zone["pump_port"]:
                pump_port = self.pumps["pump4"].switch_port(port=zone['pump_port'])
                print(f"Fluid connection built for \n"
                      f"Pump 4 port {zone['pump_port']} at {pump_port}\n")
        elif "valve_port" in zone:
            if "_group_1" in zone["valve_port"]: 
                valve_port = self.valves["valve1"].switch_port(
                        port=zone['valve_port'])  
                self.pumps["pump1"].switch_port(port="reaction_group_1")
                print(f"Fluid connection built for \n"
                          f"Valve 1 port {zone['valve_port']} at {valve_port}")
            elif "_group_2" in zone["valve_port"]:
                valve_port = self.valves["valve2"].switch_port(port=zone['valve_port'])
                self.pumps["pump2"].switch_port(port="reaction_group_2")
                print(f"Fluid connection built for \n"
                      f"Valve 2 port {zone['valve_port']} at {valve_port}")
            elif "_group_4" in zone["valve_port"]:
                valve_port = self.valves["valve3"].switch_port(port=zone['valve_port'])
                self.pumps["pump4"].switch_port(port="reaction_group_4")
                print(f"Fluid connection built for \n"
                      f"Valve 3 port {zone['valve_port']} at {valve_port}")

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
        if 'pump_port' in source_zone:
            if "_group_1" in source_zone['pump_port']:
                self.pump = self.pumps['pump1']
            elif "_group_2" in source_zone['pump_port']:
                self.pump = self.pumps["pump2"]
            elif "_group_4" in source_zone['pump_port']:
                self.pump = self.pumps["pump4"]
        elif 'valve_port' in source_zone:
            if "_group_1" in source_zone['valve_port']:
                self.pump = self.pumps['pump1']
            elif "_group_2" in source_zone['valve_port']:
                self.pump = self.pumps["pump2"]
            elif "_group_4" in source_zone['valve_port']:
                self.pump = self.pumps["pump4"]
        else:
            raise ValueError("No pump or valve valid selected")

        if specification == "gas":
            speed = 2.0
            self._build_fluid_connection(zone=source_zone)
            self.pump.draw(volume=quantity, speed=speed)
            time.sleep(delay)
            self._build_fluid_connection(zone=target_zone)
            self.pump.dispense_all(speed=speed)
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
            for i in range(0, num_cycles):
                self.transfer_compound(target_zone=waste,
                                       quantity=10.0,
                                       source_zone=zone,
                                       delay=delay,
                                       **kwargs
                                       )
                print(f"Schlenk cycle on zone {zone} cycle {i + 1} done.")

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
                quantity=quantity,
                source_zone=source_zone,
                delay=delay,
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
                     rinse: bool = False,
                     sleep: int = 0,
                     **kwargs
                     ):
        """
        if rinse:
            if (self.syringe_content != source_zone) \
                    and (self.syringe_content != source_N2):
                self.rinse_syringe(source_zone, waste=waste)
                """
        self.transfer_compound(target_zone=target_zone,
                               quantity=quantity,
                               source_zone=source_zone,
                               delay=delay,
                               **kwargs)
        print(f"{quantity} mL solution from zone {source_zone} transferred to {target_zone}.")

        for i in range(0, purge_N2):
            self.transfer_compound(specification='gas',
                                   target_zone=target_zone,
                                   quantity=2.0,
                                   source_zone=source_N2,
                                   )
            print(f"Tubing to {target_zone} flushed with 2 mL N2 for {i + 1} times")
        time.sleep(sleep * 3600)

        self._syringe_content = source_zone

    def make_solution(self, zone: Dict,
                      quantity: float,
                      mix_iterations: int = 5,
                      source_solvent=Dict,
                      waste=Dict,
                      delay: int = 2,
                      **kwargs):
        transfer_iterations = ceil(quantity / 10.0)
        quantity_per_iteration = quantity / transfer_iterations

        for j in range(0, transfer_iterations):
            self.add_solution(target_zone=zone,
                              quantity=quantity_per_iteration,
                              source_zone=source_solvent,
                              waste=waste,
                              purge_N2=0,
                              delay=delay,
                              **kwargs
                              )
        print(f"{quantity} mL {source_solvent.keys()} added to stock solution zone {zone}.")

        self._syringe_content = zone

        for k in range(0, mix_iterations):
            self.add_solution(target_zone=zone,
                              quantity=10.0,
                              source_zone=zone,
                              waste=waste,
                              purge_N2=2,
                              delay=delay,
                              **kwargs
                              )
        self.add_solution(target_zone=zone,
                          quantity=1,
                          source_zone=zone,
                          waste=waste,
                          purge_N2=0,
                          **kwargs
                          )
        print(f"Solution at {zone} has been made with {quantity} mL of Dioxane.")

        self._syringe_content = zone

    def heat_and_stir(self,
                      reaction_time: float,
                      temp: float,
                      rpm: int,
                      hotplate: str,
                      **kwargs):
        self.hotplates[hotplate].rpm = int(rpm)
        self.hotplates[hotplate].temp = temp
        print(f"Stir at {rpm} and heat at {temp} start.")
        time.sleep(reaction_time * 3600)
        self.hotplates[hotplate].stand_by()
        print("Heat and stir stopped.")

    def heat_and_stir_ON(self,
                         temp: float,
                         rpm: int,
                         hotplate: str,
                         sleep: int = 0,
                         **kwargs):
        self.hotplates[hotplate].rpm = int(rpm)
        self.hotplates[hotplate].temp = temp
        print(f"Stir at {rpm} and heat at {temp} start.")
        if sleep != 0:
            time.sleep(sleep)
        
    def heat_and_stir_OFF(self,
                         temp: float,
                         rpm: int,
                         hotplate: str,
                         sleep: int = 0,
                         **kwargs):
        self.hotplates[hotplate].stand_by()
        print(f"Stir and heat ended.")
        if sleep != 0:
            time.sleep(sleep)

class Reaction(BaseProcedures):
    def __init__(self):
        super().__init__()

    def generate_experiment_One_details(self, num_reactions: int, temp=65):
        self.available_reaction_zones_group1 = []
        self.available_reaction_zones_group2 = []
        self.available_reaction_zones_group4 = []
        self.available_1wash_zones_group4 = []
        if num_reactions > 6:
            raise ValueError("You can't run more than 6 reactions with this setup.")

        for i in range(0, num_reactions):
            self.available_reaction_zones_group1.append({"valve_port": f"reaction_{i + 1}_group_1", })
            self.available_reaction_zones_group2.append({"valve_port": f"reaction_{i + 1}_group_2", })
            self.available_reaction_zones_group4.append({"valve_port": f"reaction_{i + 1}_group_4"})
            self.available_1wash_zones_group4.append({"valve_port": f"reaction_{i + 1}_group_4"})

        self.reaction_steps = {
            "1": {
                "task": "schlenk_cycle",
                "parameters": {
                    "specification": "gas",
                    "zones": self.available_reaction_zones_group1,
                    "waste": {"pump_port": "waste_group_1"},
                    "num_cycles": 2,
                    "delay": 1
                }
            },
            "2": {
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
        for j in range(0, 2):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group1[j],
                           quantity=0.75,
                           source_zone={"pump_port": "Boronic_acid_1_group_1"},
                           source_N2={"pump_port": "N2_group_1"},
                           waste={"pump_port": "waste_group_1"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )

        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_1"},
                       waste={"pump_port": "waste_group_1"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )

        for j in range(2, 4):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group1[j],
                           quantity=0.75,
                           source_zone={"pump_port": "Boronic_acid_2_group_1"},
                           source_N2={"pump_port": "N2_group_1"},
                           waste={"pump_port": "waste_group_1"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )

        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_1"},
                       waste={"pump_port": "waste_group_1"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )

        for j in range(4, 6):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group1[j],
                           quantity=0.75,
                           source_zone={"pump_port": "Boronic_acid_3_group_1"},
                           source_N2={"pump_port": "N2_group_1"},
                           waste={"pump_port": "waste_group_1"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )

        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_1"},
                       waste={"pump_port": "waste_group_1"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )

        for j in range(0, num_reactions):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group1[j],
                           quantity=0.75,
                           source_zone={"pump_port": "Br-Quinoline_group_1"},
                           source_N2={"pump_port": "N2_group_1"},
                           waste={"pump_port": "waste_group_1"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )

        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_1"},
                       waste={"pump_port": "waste_group_1"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )

        for j in range(0, num_reactions):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group2[j],
                           quantity=0.75,
                           source_zone={"pump_port": "Pd_XPhos_G2_group_2"},
                           source_N2={"pump_port": "N2_group_2"},
                           waste={"pump_port": "waste_group_2"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        for j in range(0, num_reactions):
            self._add_step("add_solution",
                           specification="liquid",
                           target_zone=self.available_reaction_zones_group2[j],
                           quantity=0.75,
                           source_zone={"pump_port": "K3PO4_group_2"},
                           source_N2={"pump_port": "N2_group_2"},
                           waste={"pump_port": "waste_group_2"},
                           purge_N2=2,
                           delay=7.0,
                           rinse=False
                           )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        self._add_step("heat_and_stir_ON",
                       temp=temp,
                       rpm=800,
                       hotplate="hotplate3"
                       )
        self._add_step("heat_and_stir_ON",
                       temp=temp,
                       rpm=800,
                       hotplate="hotplate2"
                       )
        self._add_step("heat_and_stir_ON",
                       temp=temp,
                       rpm=800,
                       hotplate="hotplate1",
                       wait=0.033
                       )
        self._add_step("heat_and_stir_OFF",
                       hotplate="hotplate1",
                       wait=0.5
                       )
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group2[0],
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone={"pump_port":"Malononitrile_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group2[0],
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone={"pump_port": "Indandione_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=True
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        self._add_step("heat_and_stir_ON",
                       temp=0,
                       rpm=800,
                       hotplate="hotplate1",
                       wait=1 # CAMBIARRRRR!!!!!
                       )
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate1",
                       )
        # Remove aqueous solution reaction 1
        self._add_step("add_solution",
                        specification = "liquid",
                        target_zone = {"pump_port": "waste_group_4"},
                        quantity = 0.75, # ----->  Verificar este volumen!!!
                        source_zone = self.available_1wash_zones_group4[0],
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 7.0,
                        rinse = False
                    )
        # Wash with NaCl aq
        self._add_step("add_solution",
                        specification = "liquid",
                        target_zone = self.available_1wash_zones_group4[0],
                        quantity = 0.75,
                        source_zone = {"pump_port": "NaCl_aq_group_4"},
                        source_N2 = {"pump_port": "N2_group_4"},
                        waste = {"pump_port": "waste_group_4"},
                        purge_N2 = 2,
                        delay = 7.0,
                        rinse = False
                    )
        # Remove aqueous phase
        self._add_step("add_solution",
                                specification = "liquid",
                                target_zone = {"pump_port": "waste_group_4"},
                                quantity = 0.75,
                                source_zone = self.available_1wash_zones_group4[0],
                                source_N2 = {"pump_port": "N2_group_4"},
                                waste = {"pump_port": "waste_group_4"},
                                purge_N2 = 2,
                                delay = 7.0,
                                rinse = True
                    )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[0],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[0],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[0],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Turn ON the hotplate 1
        self._add_step("heat_and_stir_ON",
                       temp=temp,
                       rpm=800,
                       hotplate="hotplate1",
                       sleep = 0.66
                       )#  --------------------> 40 min wait
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       sleep=0.33)
        # Turn OFF hotplate 1
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate1",
                       wait=0.5
                       ) # -------> 30 min
        # Remove aqueous solution reaction 2
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone=self.available_1wash_zones_group4[1],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Wash with NaCl aq
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_1wash_zones_group4[1],
                       quantity=0.75,
                       source_zone={"pump_port": "NaCl_aq_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Remove aqueous phase
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,
                       source_zone=self.available_1wash_zones_group4[1],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[1],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[1],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[1],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       sleep=9.5) # ------> 10 hrs
        # Turn OFF hotplate 2
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate2",
                       wait=0.5
                       )  # -------> 30 min
        # Add Malonitrile to reaction 3
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"valve_port": "reaction_3_group_2"},
                       quantity=0.75,
                       source_zone={"pump_port": "Malononitrile_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        # Add Indandione to reaction 4
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"valve_port": "reaction_4_group_2"},
                       quantity=0.75,
                       source_zone={"pump_port": "Indandione_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        # Turn ON the hotplate 2
        self._add_step("heat_and_stir_ON",
                       temp=0,
                       rpm=800,
                       hotplate="hotplate2",
                       sleep=2
                       )  # --------------------> 2hr min wait
        # Turn OFF the hotplate 2
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate2",
                       )
        # Remove aqueous solution reaction 3
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone=self.available_1wash_zones_group4[2],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Wash with NaCl aq
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_1wash_zones_group4[2],
                       quantity=0.75,
                       source_zone={"pump_port": "NaCl_aq_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Remove aqueous phase
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,
                       source_zone=self.available_1wash_zones_group4[2],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[2],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[2],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[2],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Turn ON the hotplate 2
        self._add_step("heat_and_stir_ON",
                       temp=0,
                       rpm=800,
                       hotplate="hotplate2",
                       sleep=0.66
                       )  # --------------------> 40 min wait
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       sleep=1.33) # 1 hr 20 min wait
        # Turn OFF the hotplate2
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate2",
                       )
        # Remove aqueous solution reaction 4
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone=self.available_1wash_zones_group4[3],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Wash with NaCl aq
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_1wash_zones_group4[3],
                       quantity=0.75,
                       source_zone={"pump_port": "NaCl_aq_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Remove aqueous phase
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,
                       source_zone=self.available_1wash_zones_group4[3],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[3],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[3],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[3],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       sleep=10)  # ------> 10 hrs
        #
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate3",
                       wait=0.5
                       )  # -------> 30 min
        # Add Malonitrile to reaction 5
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"valve_port": "reaction_5_group_2"},
                       quantity=0.75,
                       source_zone={"pump_port": "Malononitrile_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        # Add Indandione to reaction 6
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"valve_port": "reaction_6_group_2"},
                       quantity=0.75,
                       source_zone={"pump_port": "Indandione_group_2"},
                       source_N2={"pump_port": "N2_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        self._add_step("rinse_syringe",
                       specification="liquid",
                       source_zone={"pump_port": "THF_group_2"},
                       waste={"pump_port": "waste_group_2"},
                       quantity=1,
                       iteration=3,
                       delay=1.0
                       )
        # Turn ON the hotplate 2
        self._add_step("heat_and_stir_ON",
                       temp=0,
                       rpm=800,
                       hotplate="hotplate2",
                       sleep=2
                       )  # --------------------> 2hr min wait
        # Turn OFF the hotplate 2
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate2",
                       )
        # Remove aqueous solution reaction 5
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone=self.available_1wash_zones_group4[4],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Wash with NaCl aq
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_1wash_zones_group4[4],
                       quantity=0.75,
                       source_zone={"pump_port": "NaCl_aq_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Remove aqueous phase
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,
                       source_zone=self.available_1wash_zones_group4[4],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=True
                       )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[4],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[4],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[4],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Turn ON the hotplate 3
        self._add_step("heat_and_stir_ON",
                       temp=0,
                       rpm=800,
                       hotplate="hotplate3",
                       sleep=0.66
                       )  # --------------------> 40 min wait
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       sleep=1.33)  # 1 hr 20 min wait
        # Turn OFF the hotplate3
        self._add_step("heat_and_stir_OFF",
                       hotplate=f"hotplate3",
                       )
        # Remove aqueous solution reaction 6
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,  # ----->  Verificar este volumen!!!
                       source_zone=self.available_1wash_zones_group4[5],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Wash with NaCl aq
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_1wash_zones_group4[5],
                       quantity=0.75,
                       source_zone={"pump_port": "NaCl_aq_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Remove aqueous phase
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "waste_group_4"},
                       quantity=0.75,
                       source_zone=self.available_1wash_zones_group4[5],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=2,
                       delay=7.0,
                       rinse=False
                       )
        # Organic phase to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[5],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False,
                       )
        # Clean the vial
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone=self.available_reaction_zones_group4[5],
                       quantity=1.75,
                       source_zone={"pump_port": "THF_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Residues to Flash
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=1.75,
                       source_zone=self.available_reaction_zones_group4[5],
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False
                       )
        # Clean Flash column
        self._add_step("add_solution",
                       specification="liquid",
                       target_zone={"pump_port": "column_group_4"},
                       quantity=3,
                       source_zone={"pump_port": "EtOH_group_4"},
                       source_N2={"pump_port": "N2_group_4"},
                       waste={"pump_port": "waste_group_4"},
                       purge_N2=10,
                       delay=7.0,
                       rinse=False)
        with open(Path.cwd().parent.parent / 'test_MEDUSA' / 'reconstruct' / 'data' / 'experimentOne_plan.json', 'w') as f:
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
        elif reaction["task"] == "heat_and_stir_ON":
            self.heat_and_stir_ON(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
        elif reaction["task"] == "heat_and_stir_OFF":
            self.heat_and_stir_OFF(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
        elif reaction["task"] == "heat_and_stir":
            self.heat_and_stir(**reaction["parameters"])
            print(datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))

    def run_reactions(self, rxn_steps: Dict = None):
        if rxn_steps is None:
            rxn_steps = self.reaction_steps
        for i in range(0, len(rxn_steps)):
            self.run_reaction(rxn_steps[f"{i + 1}"])