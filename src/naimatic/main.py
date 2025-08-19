"""A wrapper around naima to facilitate multiple model building and fitting."""

import argparse
import logging

import yaml
import naima


from pathlib import Path
from functools import partial

from astropy.io import ascii  # type: ignore

from .config import Config, Param, MagneticField
from .factory import (
    build_model,
    build_priors,
    extract_p0_labels,
    compute_metadata_blobs
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Run Naima models from configuration.")
parser.add_argument(
    "config",
    type=str,
    help="Path to the YAML configuration file for Naima models.",
)
parser.add_argument(
    "--output-path",
    type=str,
    default="./naimatic_results",
    help="Path to the output directory for results.",
)

args = parser.parse_args()


def load_data(data_dict):
    """Load data from the provided dictionary of file paths."""
    datasets = {}
    for key, value in data_dict.items():
        data_path = Path(value).resolve()
        if not data_path.exists():
            raise FileNotFoundError(f"Data file {value} does not exist.")
        dataset = ascii.read(data_path)
        datasets[key] = dataset
    return datasets


def model_func(data, model_cfg, radiative_models):
    """Compute the total flux for the given data and model configuration."""
    total_flux = sum(
        rad_model.flux(data, distance=model_cfg.distance)
        for rad_model in radiative_models
    )
    return total_flux


def lnprior(pars, labels, priors_dict):
    """Compute the log-prior probability for the given parameters."""
    logp = 0
    for val, name in zip(pars, labels):
        prior_func = priors_dict.get(name)
        if prior_func is None:
            continue
        logp += prior_func(val)
    return logp


def wrapped_model_func(pars, data, model_cfg, pdist, rmodels):
    """Wrapper for the model function to handle parameter extraction and units."""
    i = 0
    for pname, param_cfg in model_cfg.particle_distribution.__dict__.items():
        if not isinstance(param_cfg, Param):
            continue
        if getattr(param_cfg, "freeze", False):
            val = param_cfg.init_value.value
        else:
            val = pars[i]
            if getattr(param_cfg, "log10", False):
                val = 10**val
            i += 1
        unit = getattr(param_cfg.init_value, "unit", None)
        if unit is not None:
            val = val * unit
        setattr(pdist, pname, val)

    for proc_cfg, rmodel in zip(model_cfg.radiative_processes, rmodels):
        for pname, param_cfg in proc_cfg.__dict__.items():
            if isinstance(param_cfg, Param) and not param_cfg.freeze:
                val = pars[i]
                i += 1
                if getattr(param_cfg, "log10", False):
                    val = 10**val
                unit = getattr(param_cfg.init_value, "unit", None)
                if unit is not None:
                    val = val * unit
                setattr(rmodel, pname, val)

    total_flux =  model_func(data, model_cfg, rmodels)

    blobs = ()
    if model_cfg.metadata:
        blobs = compute_metadata_blobs(model_cfg.metadata, pdist, rmodels)
    return total_flux, *blobs


def wrapped_lnprior_func(pars, labels, priors):
    """Wrapper for the log-prior function to handle parameter extraction."""
    return lnprior(pars, labels, priors)


def main():
    yaml_path = Path(args.config).resolve()
    if not yaml_path.exists():
        raise FileNotFoundError(f"Configuration file {yaml_path} does not exist.")

    cfg = Config.model_validate(yaml.safe_load(open(yaml_path)))

    output_path = cfg.output_path if cfg.output_path else Path(args.output_path)

    data_tables_dict = load_data(cfg.data)

    for model_cfg in cfg.models:
        try:
            # Initialize magnetic field value if present
            for proc_cfg in model_cfg.radiative_processes:
                if proc_cfg.name == "Synchrotron" and isinstance(
                    proc_cfg.B, MagneticField
                ):
                    if proc_cfg.B.estimate_from:
                        proc_cfg.B = proc_cfg.B.resolve(data_tables_dict)

            overwrite_flag = model_cfg.overwrite

            logger.info(f"Running model: {model_cfg.name}")
            pdist, rmodels = build_model(model_cfg)

            p0, labels = extract_p0_labels(model_cfg)
            logger.debug(f"Initial parameters: {p0}")
            logger.debug(f"Parameter labels: {labels}")

            priors = build_priors(model_cfg.particle_distribution)

            model_callable = partial(
                wrapped_model_func,
                model_cfg=model_cfg,
                pdist=pdist,
                rmodels=rmodels,
            )
            prior_callable = partial(wrapped_lnprior_func, labels=labels, priors=priors)

            sampler, _ = naima.run_sampler(
                data_table=list(data_tables_dict.values()),
                p0=p0,
                labels=labels,
                model=model_callable,
                prior=prior_callable,
                **cfg.mcmc.model_dump(),
            )

            outdir = output_path / model_cfg.name
            outdir.mkdir(exist_ok=True, parents=True)

            results_file = outdir / f"{model_cfg.name}_results.hdf5"
            naima.save_run(results_file, sampler, clobber=overwrite_flag)
            logger.info(f"Results saved to: {results_file}")

            # Build blob labels dynamically from the metadata config
            metadata_cfg = model_cfg.metadata
            blob_labels = ["Spectrum"]  # the first return value is always the flux
            if hasattr(model_cfg, "metadata") and model_cfg.metadata:
                for key, cfg_entry in metadata_cfg.model_dump().items():
                    if cfg_entry and (cfg_entry.get("save", False)):
                        logger.debug("Processing metadata key: %s", key)
                        if key == "particle_distribution":
                            blob_labels.append("Electron energy distribution")
                        elif key == "total_particle_energy":
                            e_min = cfg_entry.get("e_min")
                            # format nicely if Quantity
                            if hasattr(e_min, "value") and hasattr(e_min, "unit"):
                                e_min_str = f"{e_min.value:g} {e_min.unit}"
                            else:
                                e_min_str = str(e_min)
                            blob_labels.append(f"$W_e (E_e>{e_min_str})$")
                        else:
                            # fallback label
                            blob_labels.append(key)

            try:
                plot_prefix = model_cfg.name
                naima.save_diagnostic_plots(
                    outdir / plot_prefix,
                    sampler,
                    sed=model_cfg.sed,
                    blob_labels=blob_labels,
                )
                logger.info("Diagnostic plots saved.")

                naima.save_results_table(
                    outdir / plot_prefix, sampler, overwrite=overwrite_flag
                )
                logger.info("Results table saved")

            except Exception as exception:
                logger.exception("Could not generate plots")
                raise exception

        except Exception as e:
            logger.exception(f"Error running sampler for model {model_cfg.name}: {e}")
            continue


if __name__ == "__main__":
    main()
