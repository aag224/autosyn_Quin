# [Project Title]

[One or two sentences describing the goal of the project: which system is studied and what this repository combines (DFT calculations + experimental procedure under the MEDUSA protocol).]

This repository contains:

1. **Example outputs of DFT calculations** (geometry optimization, vibrational frequencies, and natural transition orbital (NTO) analysis).
2. **Execution code for the experimental procedure** developed under the MEDUSA protocol.

> **Associated article:** [Authors, *Title*, Journal, Year. DOI: ...]
> **Full dataset:** [Figshare DOI, if the complete data are deposited there]

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
└── medusa/
    ├── scripts/                 # Protocol execution code
    ├── config/                  # Configuration / parameter files
    ├── example_data/            # Example data to test the scripts
    └── requirements.txt         # Python (or other language) dependencies
```

[Adjust folder names to match your repository.]

---

## Part 1: DFT calculations

### Computational details

| Parameter | Value |
|---|---|
| Software |  ORCA 6.1.0  |
| Functional | B3LYP, CAM-B3LYP |
| Basis set | def2-TZVP |
| Dispersion correction | D3(BJ) |
| Solvation model | CPCM / SMD, solvent:THF |
| Excited states | TD-DFT, number of states: 10 |

### Folder contents

- **`geometry_optimization/`**: input and output files of the geometry optimizations. Final geometries are provided in `.xyz` format.
- **`vibrational_frequency/`**: frequency calculations performed on the optimized geometries, used to confirm that they correspond to minima (no imaginary frequencies).
- **`nto/`**: calculations and analysis files for the natural transition orbitals of the excited states.
- **`nto_images/`**: graphical representations of the NTOs, generated with visualization software Avogadro.


### Note on included files

This repository contains **example outputs** for systems 2a, 3a and 4a. Large intermediate files (checkpoints, wavefunction files) are not included. If you want the complete dataset is on Figshare: 10.6084/m9.figshare.34037556

