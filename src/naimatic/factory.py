"""Library of factory functions."""

import astropy.units as u
import naima
import naima.models as nm
import numpy as np

from functools import partial

from .config import (
    ModelConfig,
    Param,
    ParticleDistributionConfig,
    RadiativeProcessConfig,
)

__all__ = [
    "build_priors",
    "build_particle_distribution",
    "build_radiative_process",
    "build_model",
    "extract_p0_labels",
    "compute_metadata_blobs",
]


def _prior2_caller(x, fn, a, b):
    """Call a Naima prior function with two hyperparameters (e.g., min/max or mu/sigma)."""
    return fn(x, a, b)


def build_priors(particle_dist_cfg: ParticleDistributionConfig):
    """Build a dictionary of priors from the particle distribution configuration."""
    priors = {}

    for param_name, param_cfg in particle_dist_cfg.__dict__.items():
        if isinstance(param_cfg, Param) and param_cfg.prior is not None:
            prior_cfg = param_cfg.prior
            prior_func = getattr(naima, f"{prior_cfg.name}_prior", None)
            if prior_func is None:
                raise ValueError(f"Unknown prior type: {prior_cfg.name}")

            # Pull numeric bounds/hyperparameters
            if prior_cfg.name in {"uniform", "loguniform"}:
                a = float(getattr(prior_cfg.min, "value", prior_cfg.min))
                b = float(getattr(prior_cfg.max, "value", prior_cfg.max))
                if getattr(param_cfg, "log10", False):
                    a = np.log10(a)
                    b = np.log10(b)
                priors[param_name] = partial(_prior2_caller, fn=prior_func, a=a, b=b)

            elif prior_cfg.name == "normal":
                mu = float(prior_cfg.mu)
                sigma = float(prior_cfg.sigma)
                if getattr(param_cfg, "log10", False):
                    mu = np.log10(mu)

                priors[param_name] = partial(
                    _prior2_caller, fn=prior_func, a=mu, b=sigma
                )

    return priors


def build_particle_distribution(cfg: ParticleDistributionConfig):
    """Build a particle distribution from configuration."""
    model_cls = getattr(nm, cfg.name, None)
    if model_cls is None:
        raise ValueError(f"Unknown distribution: {cfg.name}")

    kwargs = {
        k: v.init_value
        for k, v in cfg.__dict__.items()
        if isinstance(v, Param) and v.init_value is not None
    }
    return model_cls(**kwargs)


def build_radiative_process(cfg: RadiativeProcessConfig, particle_distribution):
    """Build a single radiative process from configuration."""
    model_cls = getattr(nm, cfg.name, None)
    if model_cls is None:
        raise ValueError(f"Unknown radiative model: {cfg.name}")

    kwargs = {}
    for key, value in cfg.__dict__.items():
        if isinstance(value, Param):
            if value.init_value is not None:
                kwargs[key] = value.init_value
        elif key not in ("name", "particle_distribution") and value is not None:
            kwargs[key] = value

    return model_cls(particle_distribution, **kwargs)


def build_model(model_cfg: ModelConfig):
    """Build a full Naima model from configuration."""
    shared_pd = build_particle_distribution(model_cfg.particle_distribution)

    processes = []
    for proc_cfg in model_cfg.radiative_processes:
        # If the process has its own particle distribution, build and pass it
        pd_cfg = getattr(proc_cfg, "particle_distribution", None)
        if pd_cfg:
            pd = build_particle_distribution(pd_cfg)
        else:
            pd = shared_pd

        process = build_radiative_process(proc_cfg, pd)
        processes.append(process)

    return shared_pd, processes


def extract_p0_labels(model_cfg):
    """Ëxtract initial parameter values and their labels from the model configuration."""
    p0 = []
    labels = []
    for param_name, param_cfg in model_cfg.particle_distribution.__dict__.items():
        if isinstance(param_cfg, Param) and not param_cfg.freeze:
            if getattr(param_cfg, "log10", True):
                p0.append(np.log10(param_cfg.init_value.value))
                labels.append(f"log10({param_name})")
            else:
                p0.append(param_cfg.init_value.value)
                labels.append(param_name)
    return np.array(p0), labels

def compute_metadata_blobs(metadata_cfg, pdist, rmodels):
    blobs = []
    for key, cfg_entry in metadata_cfg.model_dump().items():
        if not cfg_entry.get("save", False):
            continue

        if key == "particle_distribution":
            energy_range = cfg_entry.get("energy_range")
            blobs.append((energy_range, pdist(energy_range)))  # tuple, not list

        elif key == "total_particle_energy":
            e_min = cfg_entry.get("e_min", 1 * u.TeV)
            total_energy = sum(r.compute_We(Eemin=e_min) for r in rmodels)
            blobs.append(total_energy)  # scalar Quantity

    return blobs
