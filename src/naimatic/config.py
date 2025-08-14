"""This module defines the configuration schema for Naima models using Pydantic.

It includes definitions for particle distributions, radiative processes, and model configurations."""

import warnings

import astropy.units as u  # type: ignore

from pathlib import Path
from typing import Literal, Optional, Union, List

from astropy.units import Quantity, Unit
from pydantic import BaseModel, model_validator
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

__all__ = [
    "QuantityType",
    "UniformPrior",
    "NormalPrior",
    "LogUniformPrior",
    "Prior",
    "Param",
    "ExponentialCutoffPowerLawConfig",
    "PowerLawConfig",
    "ParticleDistributionConfig",
    "RadiativeProcessConfig",
    "SynchrotronConfig",
    "InverseComptonConfig",
    "PionDecayConfig",
    "BremsstrahlungConfig",
    "CompoundRadiativeProcessConfig",
    "ModelConfig",
    "MCMCConfig",
    "Config",
]


class QuantityType:
    """Pydantic type for handling astropy Quantity objects."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        def validate_QuantityType(value):
            if isinstance(value, Quantity):
                return value
            if isinstance(value, str):
                return Quantity(value)
            if isinstance(value, (int, float)):
                return Quantity(value, Unit(""))
            raise TypeError(f"Cannot convert {value!r} to QuantityType")

        return core_schema.no_info_plain_validator_function(validate_QuantityType)


class UniformPrior(BaseModel):
    name: Literal["uniform"]
    min: QuantityType
    max: QuantityType


class NormalPrior(BaseModel):
    name: Literal["normal"]
    mu: float
    sigma: float


class LogUniformPrior(BaseModel):
    name: Literal["loguniform"]
    min: QuantityType
    max: QuantityType


Prior = Union[UniformPrior, NormalPrior, LogUniformPrior]


class Param(BaseModel):
    """Model for the parameter of a particle distribution."""

    freeze: bool = False
    init_value: QuantityType
    prior: Prior | None = None
    log10: bool = False


class ExponentialCutoffPowerLawConfig(BaseModel):
    name: Literal["ExponentialCutoffPowerLaw"]
    amplitude: Param
    e_0: Param
    alpha: Param
    e_cutoff: Param
    beta: Param
    save: bool = True


class PowerLawConfig(BaseModel):
    name: Literal["PowerLaw"]
    amplitude: Param
    alpha: Param
    save: bool = True


ParticleDistributionConfig = Union[
    ExponentialCutoffPowerLawConfig,
    PowerLawConfig,
]


class RadiativeProcessConfig(BaseModel):
    name: str
    particle_distribution: ParticleDistributionConfig | None = None


class SynchrotronConfig(RadiativeProcessConfig):
    name: Literal["Synchrotron"]
    B: QuantityType | Literal["estimate"] = 3.24e-6 * u.G
    Eemin: QuantityType
    Eemax: QuantityType
    nEed: int


class InverseComptonConfig(RadiativeProcessConfig):
    name: Literal["InverseCompton"]
    seed_photon_fields: Optional[list[str]] = None
    Eemin: Optional[QuantityType] = None
    Eemax: Optional[QuantityType] = None
    nEed: Optional[int] = None


class PionDecayConfig(RadiativeProcessConfig):
    name: Literal["PionDecay"]
    nh: QuantityType = 1 * u.cm**-3
    nuclear_enhancement: bool = False
    Epmin: QuantityType = 1.22 * u.GeV
    Epmax: QuantityType = 10 * u.PeV
    nEpd: int = 100
    hiEmodel: Literal["Geant4", "Pythia8", "SIBYLL", "QGSJET"] = "Pythia8"
    useLUT: bool = False


class BremsstrahlungConfig(RadiativeProcessConfig):
    name: Literal["Bremsstrahlung"]
    n0: QuantityType
    weight_ee: float = 1.088
    weight_ep: float = 1.263


CompoundRadiativeProcessConfig = Union[
    SynchrotronConfig,
    InverseComptonConfig,
    PionDecayConfig,
    BremsstrahlungConfig,
]


class ModelConfig(BaseModel):
    """Configuration for a Naima model, including particle distributions and radiative processes."""

    name: str
    overwrite: bool = False
    distance: QuantityType = 1.0 * u.kpc
    particle_distribution: ParticleDistributionConfig | None = None
    radiative_processes: list[CompoundRadiativeProcessConfig]

    @model_validator(mode="after")
    def check_particle_distribution_rules(self):
        any_proc_has_pd = any(
            getattr(proc, "particle_distribution", None) is not None
            for proc in self.radiative_processes
        )

        if self.particle_distribution is None and not any_proc_has_pd:
            raise ValueError(
                f"Model '{self.name}' must define either a shared particle_distribution "
                "or at least one per-process particle_distribution."
            )

        if self.particle_distribution is not None and any_proc_has_pd:
            warnings.warn(
                f"Model '{self.name}': Shared particle_distribution will be overridden "
                "for processes that define their own.",
                UserWarning,
            )

        return self


class MCMCConfig(BaseModel):
    """Configuration for MCMC sampling parameters."""

    nwalkers: int
    nburn: int
    nrun: int
    threads: int
    prefit: bool = False
    interactive: bool = False


class Config(BaseModel):
    """Model for the configuration of naimatic"""

    output_path: Path | None = None
    data: dict[str, str]
    models: List[ModelConfig]
    mcmc: MCMCConfig
