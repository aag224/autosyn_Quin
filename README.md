# autosyn_Quin

Theoretical calculations and automated experimental procedure for derivatives of quinolines.

This repository contains:

1. **Example outputs of DFT calculations** (geometry optimization, vibrational frequencies, and natural transition orbital (NTO) analysis).
2. **MEDUSA automation code** used to run the synthesis of the quinoline derivatives on an automated platform (pumps, valves and hotplates), together with the hardware configuration and the full experimental plan in `.json` format.

> **Associated article:** [ ]
> **Full dataset:** [Figshare DOI: 10.6084/m9.figshare.34037556](https://doi.org/10.6084/m9.figshare.34037556)

---

## Repository structure

```
.
├── README.md
├── LICENSE
├── dft/
│   ├── geometry_optimization/   # Geometry optimization inputs and outputs
│   ├── vibrational_frequency/   # Vibrational frequency calculations
│   ├── nto/                     # Natural transition orbital analysis
│   └── nto_images/              # NTO images
└── MEDUSA exe/
    ├── medusa_synQuinolinesDerivaties.py   # Reaction defined as an object (procedures + experimental plan)
    ├── run_synQuinolines.py                # Script that generates and executes the experiment
    └── data/
        ├── ports_settings.json             # Pumps, valves, COM ports and port assignments
        ├── zones.json                      # Zones (vials/reagents) and connections between devices
        └── experimentOne_plan.json         # Full step-by-step experimental procedure
```

---

## Part 1: DFT calculations

### Computational details

| Parameter | Value |
|---|---|
| Software | ORCA 6.1.0 |
| Functional | B3LYP, CAM-B3LYP |
| Basis set | def2-TZVP |
| Dispersion correction | D3(BJ) |
| Solvation model | CPCM / SMD, solvent: THF |
| Excited states | TD-DFT, number of states: 10 |

### Folder contents

- **`geometry_optimization/`**: input and output files of the geometry optimizations. Final geometries are provided in `.xyz` format.
- **`vibrational_frequency/`**: frequency calculations performed on the optimized geometries, used to confirm that they correspond to minima (no imaginary frequencies).
- **`nto/`**: calculations and analysis files for the natural transition orbitals of the excited states.
- **`nto_images/`**: graphical representations of the NTOs, generated with the visualization software Avogadro.

### Note on included files

This repository contains **example outputs** for systems 2a, 3a and 4a. Large intermediate files (checkpoints, wavefunction files) are not included. The complete dataset is available on Figshare: [10.6084/m9.figshare.34037556](https://doi.org/10.6084/m9.figshare.34037556).

---

## Part 2: Automated synthesis with MEDUSA (`MEDUSA exe/`)

The `MEDUSA exe/` folder contains the code used to run the synthesis of six quinoline derivatives in parallel on an automated liquid-handling platform. The experiment is described as a Python object: each operation (inert-atmosphere purge, reagent addition, syringe rinse, heating/stirring, work-up and transfer to the flash column) is a step of a plan that is stored as `.json` and then executed sequentially.

### Hardware

| Device | Model / driver | Role |
|---|---|---|
| Syringe pumps | J-KEM (`matterlab_pumps.JKemPump`) | Draw and dispense liquids and N₂ |
| Selection valves | J-KEM (`matterlab_valves.JKemNewValve`) | Route each pump to reaction vials 1–6 |
| Hotplates (×3) | IKA (`matterlab_hotplates.IKAHotplate`) | Heating and stirring of the reaction vials |

The setup is organized in **groups**: each group is one pump plus its selection valve, with its own reagents, THF (rinse), N₂ and waste lines.

| Group | Purpose | Reagents / lines |
|---|---|---|
| Group 1 | Coupling substrates | Boronic acids 1–3, Br-quinoline, THF, N₂, waste |
| Group 2 | Catalyst, base and second step | Pd XPhos G2, K₃PO₄, malononitrile, indandione, THF, N₂, waste |
| Group 4 | Work-up and purification | NaHCO₃, NaCl (aq), EtOH, THF, flash column, N₂, waste |

### Files

- **`medusa_synQuinolinesDerivaties.py`**
  - `BaseProcedures`: loads the port configuration and initializes pumps, valves and hotplates. It implements the unit operations:
    - `transfer_compound` – draws from a source zone and dispenses into a target zone (liquid or gas).
    - `schlenk_cycle` – N₂/evacuation cycles on the reaction vials.
    - `rinse_syringe` – rinses the syringe with solvent between reagents.
    - `add_solution` – adds a solution to a zone followed by N₂ purges of the tubing.
    - `make_solution` – prepares stock solutions.
    - `heat_and_stir` / `heat_and_stir_ON` – sets temperature and stirring on a given hotplate.
  - `Reaction(BaseProcedures)`:
    - `generate_experiment_One_details(num_reactions, temp=65)` – builds the full plan (up to 6 reactions) and saves it as `experimentOne_plan.json`.
    - `run_reaction` / `run_reactions` – read the plan and execute each step in order, printing a timestamp after every step.

- **`run_synQuinolines.py`**: entry point. Creates the `Reaction` object, generates the plan for 6 reactions and runs it.

- **`data/ports_settings.json`**: hardware definition — COM port and address of each pump and valve, and the mapping between port numbers and their content (reagent, solvent, N₂, waste, reaction vial, column).

- **`data/zones.json`**: definition of the zones (reaction vials and reagent vials), how each one is reached from each pump/valve (pump port, valve and valve port), and volume limits (min/max/current volume, addable/drawable).

- **`data/experimentOne_plan.json`**: complete experimental procedure generated by the code (104 steps), with the task and parameters of each step (volumes, source/target zones, N₂ purges, delays, temperatures and waiting times).

### Experimental sequence (summary)

1. **Inert atmosphere**: Schlenk cycles on the six reaction vials.
2. **Reagent loading**: boronic acid 1 (reactions 1–2), boronic acid 2 (reactions 3–4), boronic acid 3 (reactions 5–6), then Br-quinoline, Pd XPhos G2 and K₃PO₄ in all six vials, rinsing the syringe with THF between reagents.
3. **Coupling**: heating at 65 °C and 800 rpm on the three hotplates.
4. **Second step**: addition of malononitrile (reactions 1, 3, 5) or indandione (reactions 2, 4, 6).
5. **Work-up**: removal of the aqueous phase, wash with NaCl (aq), and second removal of the aqueous phase.
6. **Purification**: transfer of the organic phase and the THF rinse of the vial to the flash column, followed by column cleaning with EtOH.

### Requirements

- Python ≥ 3.9
- `matterlab_pumps`, `matterlab_valves`, `matterlab_hotplates`
- Devices connected to the COM ports defined in `data/ports_settings.json` (hotplates are assigned to COM7, COM9 and COM6 in the code).

### Usage

```bash
cd "MEDUSA exe"
python run_synQuinolines.py
```

> **Note:** the paths used to read `ports_settings.json` and to write `experimentOne_plan.json` are defined relative to the working directory inside `medusa_synQuinolinesDerivaties.py`. Adjust them to your local folder structure, and update the COM ports in `data/ports_settings.json` to match your computer, before running the experiment.
