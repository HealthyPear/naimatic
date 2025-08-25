"""This module defines the configuration schema for Naima models using Pydantic.

It includes definitions for particle distributions, radiative processes, and model configurations."""

import warnings

import astropy.units as u  # type: ignore
import naima
import numpy as np

from pathlib import Path
from typing import Annotated, Literal, Optional, Union, List

from astropy.units import Quantity
from pydantic import BaseModel, Field, model_validator, field_validator
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
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate_QuantityType(value):
            if isinstance(value, Quantity):
                return value
            if isinstance(value, str):
                # first try to parse as Quantity string, e.g., "1 kpc"
                try:
                    return Quantity(value)
                except Exception:
                    # fallback: eval Python expressions like np.logspace(...)*u.eV
                    ns = {"np": np, "u": u}
                    try:
                        result = eval(value, {}, ns)
                    except Exception:
                        raise TypeError(f"Cannot evaluate '{value}' as a Quantity")
                    if isinstance(result, Quantity):
                        return result
                    return Quantity(result)
            if isinstance(value, (int, float)):
                return Quantity(value, u.dimensionless_unscaled)
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


class MagneticField(BaseModel):
    freeze: bool = False
    init_value: Optional[QuantityType] = None
    estimate_from: Optional[list[str]] = None
    photon_energy_density: Optional[QuantityType] = None
    prior: Optional[Prior] = None

    def resolve(self, data_dict: dict) -> Param:
        if self.init_value is not None:
            return Param(
                freeze=self.freeze, init_value=self.init_value, prior=self.prior
            )
        elif self.estimate_from:
            selected_data = [data_dict[k] for k in self.estimate_from]
            kwargs = {}
            if self.photon_energy_density is not None:
                kwargs["photon_energy_density"] = self.photon_energy_density
            Bval = 2 * naima.estimate_B(*selected_data, **kwargs)
            return Param(freeze=self.freeze, init_value=Bval, prior=self.prior)
        else:
            raise ValueError(
                "MagneticField requires either init_value or estimate_from"
            )


class SynchrotronConfig(RadiativeProcessConfig):
    name: Literal["Synchrotron"]
    B: Optional[MagneticField] = None
    Eemin: Optional[QuantityType] = None
    Eemax: Optional[QuantityType] = None
    nEed: Optional[int] = None

PhotonField = Union[
    str,
    list[Union[str, QuantityType, QuantityType]],
    list[Union[str, QuantityType, QuantityType, QuantityType]],
]

class InverseComptonConfig(RadiativeProcessConfig):
    name: Literal["InverseCompton"]
    seed_photon_fields: Optional[list[PhotonField]] = None
    Eemin: Optional[QuantityType] = None
    Eemax: Optional[QuantityType] = None
    nEed: Optional[int] = None

    @field_validator("seed_photon_fields", mode="before")
    def convert_quantities(cls, v):
        if v is None:
            return v
        out = []
        for item in v:
            if isinstance(item, list):
                new_item = []
                for x in item:
                    if isinstance(x, str):
                        try:
                            # try to convert to Quantity; if fails, keep as string
                            xq = Quantity(x)
                            new_item.append(xq)
                        except Exception:
                            new_item.append(x)
                    else:
                        new_item.append(x)
                out.append(new_item)
            else:
                out.append(item)
        return out

class PionDecayConfig(RadiativeProcessConfig):
    name: Literal["PionDecay"]
    nh: Optional[QuantityType] = None
    nuclear_enhancement: Optional[bool] = None
    Epmin: Optional[QuantityType] = None
    Epmax: Optional[QuantityType] = None
    nEpd: Optional[int] = None
    hiEmodel: Optional[Literal["Geant4", "Pythia8", "SIBYLL", "QGSJET"]] = None
    useLUT: Optional[bool] = None


class BremsstrahlungConfig(RadiativeProcessConfig):
    name: Literal["Bremsstrahlung"]
    n0: QuantityType
    weight_ee: float = 1.088
    weight_ep: float = 1.263


CompoundRadiativeProcessConfig = Annotated[
    Union[SynchrotronConfig, InverseComptonConfig, PionDecayConfig, BremsstrahlungConfig],
    Field(discriminator='name')
]

class ParticleDistributionMetadata(BaseModel):
    save: bool
    energy_range: Optional[QuantityType] = None

class TotalParticleEnergyMetadata(BaseModel):
    save: bool
    e_min: Optional[QuantityType] = None

class MetadataConfig(BaseModel):
    particle_distribution: Optional[ParticleDistributionMetadata] = None
    total_particle_energy: Optional[TotalParticleEnergyMetadata] = None


class ModelConfig(BaseModel):
    """Configuration for a Naima model, including particle distributions and radiative processes."""

    name: str
    overwrite: bool = False
    sed: bool = True
    distance: QuantityType = 1.0 * u.kpc
    particle_distribution: ParticleDistributionConfig | None = None
    radiative_processes: list[CompoundRadiativeProcessConfig]
    metadata: Optional[MetadataConfig] = None

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
