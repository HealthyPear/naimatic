Examples
========

This page contains various examples of how to use *naimatic*,
starting from the same examples that you can find in the `naima` documentation
pages.

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