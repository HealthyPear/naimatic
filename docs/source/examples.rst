Examples
========

This page contains various examples of how to use *naimatic*,
starting from the same examples that you can find in the `naima` documentation
pages.

.. important::

  | A general note on the configuration of parameters:

  | I preferred to give the user an interface that makes physical sense,
    so parameter initial values and priors are *always* defined by the
    physical quantity together with its unit,
    even if what is fit in the end is the base-10
    exponent.
  
  | For example, the following snippet is equivalent to set a prior
  | ``logprob = naima.uniform_prior(pars[0], 0, np.inf)``
  | for ``amplitude = 10 ** pars[0] / u.eV``.

  .. code-block:: yaml

    amplitude:
      freeze: false
      log10: true
      init_value: 1e30 eV-1
      prior:
      name: uniform
        min: 1 eV-1   # this is equivalent to 10**0 eV-1
        max: inf eV-1 # this is equivalent to 10**inf eV-1

Fitting a minimal radiative model
---------------------------------

.. code-block:: yaml

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

Fitting IC emission from an electron distribution
-------------------------------------------------

.. code-block:: yaml

    output_path: /where/you/want/to/save/your/data

    data:
      hess: /path/to/RXJ1713_HESS_2007.dat

    models:
    - name: inverse_compton
      overwrite: true
      sed: true
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
            - ["FIR", "26.5 K", "0.415 eV cm-3"]
            Eemin: 100 GeV
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

Fitting Synchrotron and IC emission from an electron distribution
-----------------------------------------------------------------

.. code-block:: yaml

    output_path:

    data: # Data tables for the model (in order of increasing energy range!)
      suzaku: RXJ1713_Suzaku-XIS.dat
      hess: RXJ1713_HESS_2007.dat

    models:
      - name: ElectronSynIC
        overwrite: true
        sed: true
        distance: "1 kpc"
        particle_distribution:
          name: ExponentialCutoffPowerLaw
          amplitude:
            freeze: false
            log10: true
            init_value: 1e33 eV-1
            prior:
              name: uniform
              min: 1 eV-1
              max: inf eV-1
          e_0:
            freeze: true
            init_value: 10 TeV
          alpha:
            freeze: false
            init_value: 2.5
            prior:
              name: uniform
              min: -1
              max: 5
          e_cutoff:
            freeze: false
            log10: true
            init_value: 48 TeV
          beta:
            freeze: true
            init_value: 1.0
        radiative_processes:
          - name: Synchrotron
            B:
              freeze: false
              estimate_from: ["suzaku", "hess"] # 1st soft X-ray, 2nd VHE data
              prior:
                name: uniform
                min: 0 uG
                max: inf uG
          - name: InverseCompton
            seed_photon_fields:
              - "CMB"
              - ["FIR", "26.5 K", "0.415 eV cm-3"]
            Eemin: 100 GeV
        metadata:
          total_particle_energy:
            save: true # if true save to blob metadata
            e_min: 1 TeV

    mcmc:
      nwalkers: 32
      nburn: 100
      nrun: 20
      threads: 4
      prefit: true
      interactive: false

Fitting PionDecay emission from a proton distribution
-----------------------------------------------------

.. code-block:: yaml

  output_path:

  data:
    hess: RXJ1713_HESS_2007.dat

  models:
    - name: PionDecay
      overwrite: true
      distance: "1.5 kpc"
      particle_distribution:
        name: ExponentialCutoffPowerLaw
        amplitude:
          freeze: false
          log10: true
          init_value: 1e45 TeV-1
          prior:
            name: uniform
            min: 1 TeV-1
            max: inf TeV-1
        e_0:
          freeze: true
          init_value: 1 TeV
        alpha:
          init_value: 1.6
          prior:
            name: uniform
            min: -1
            max: 5
        e_cutoff:
          log10: true
          init_value: 12 TeV
        beta:
          freeze: true
          init_value: 0.54
      radiative_processes:
        - name: PionDecay
          nh: "10 cm-3"
      metadata:
        particle_distribution:
          save: true # if true save to blob metadata
          energy_range: np.logspace(-3, 2, 50) * u.TeV
        total_particle_energy:
          save: true # if true save to blob metadata
          e_min: 1 TeV

  mcmc:
    nwalkers: 32
    nburn: 100
    nrun: 20
    threads: 4
    prefit: true
    interactive: false
