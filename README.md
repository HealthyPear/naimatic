# naimatic

_naimatic_ is a Python package that provides a framework for building and running multiple
astrophysical models using [naima](https://naima.readthedocs.io/en/latest/index.html).

It allows users to define particle distributions, radiative processes,
and model configurations in a structured way from a single YAML configuration file,
facilitating the fitting and visualization of multiple models.

The implementation is that of a wrapper around `naima` which defines a configuration schema
validated by `pydantic` and produces the necessary objects by means of
factory functions.

## Requirements

Any Python>=3.9 virtual environment with `pip` installed.

## Installation

`pip install https://github.com/HealthyPear/naimatic`

## Usage

To use _naimatic_, you start from a configuration file that defines your models, particle distributions, and radiative processes.

Assuming this file is called `config.yaml`, the usage is as simple as:

```bash
naimatic config.yaml
```

See `naimatic -h` for more options.

The results from each model will be saved in their own subdirectories under the specified output director.

## Examples

Following the examples from _naima_'s documentation, here are the equivalent example configurations that you can use with _naimatic_.

### Fitting a minimal radiative model

```yaml
output_path: /where/you/want/to/save/your/data

data:
  hess: /path/to/RXJ1713_HESS_2007.dat

models:
  - name: minimal_radiative_model
    overwrite: true
    distance: "1 kpc"
    particle_distribution:
      name: ExponentialCutoffPowerLaw
      amplitude:
        freeze: false
        init_value: 1e30 eV-1
        prior:
          name: uniform
          min: 0 eV-1
          max: inf eV-1
      e_0:
        freeze: true
        init_value: 10 TeV
      alpha:
        freeze: false
        init_value: 3.0
      e_cutoff:
        freeze: false
        log10: true
        init_value: 30 TeV
      beta:
        freeze: true
        init_value: 1.0
    radiative_processes:
      - name: InverseCompton
        seed_photon_fields:
          - "CMB"
    metadata:
      particle_distribution:
        save: true # if true save to blob metadata
        energy_range: np.logspace(11, 15, 100) * u.eV
      total_particle_energy:
        save: true # if true save to blob metadata
        e_min: 1 TeV

mcmc:
  nwalkers: 32
  nburn: 100
  nrun: 20
  threads: 4
  prefit: false
  interactive: false
```

### Fitting IC emission from an electron distribution

TODO

### Fitting Synchrotron and IC emission from an electron distribution

TODO

### Multiple radiative processes with different particle distributions

TODO