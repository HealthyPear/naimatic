.. naimatic documentation master file, created by
   sphinx-quickstart on Thu Aug 14 11:35:03 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

naimatic documentation
======================

*naimatic* is a Python package that provides a framework for building and running multiple
astrophysical models using `naima <https://naima.readthedocs.io/en/latest/index.html>`_.

It allows users to define particle distributions, radiative processes,
and model configurations in a structured way from a single YAML configuration file,
facilitating the fitting and visualization of multiple models.

The implementation is that of a wrapper around *naima* which defines a configuration schema
validated by `pydantic <https://docs.pydantic.dev/2.11/>`_ and produces the necessary objects by means of
factory functions.

If you find ``naima`` useful in your research, you can cite `Zabalza (2015)
<http://arxiv.org/abs/1509.03319>`_ to acknowledge its use. The BibTeX entry for
the paper is:

.. code-block:: bibtex

    @ARTICLE{naima,
       author = {{Zabalza}, V.},
        title = {naima: a Python package for inference of relativistic particle
                 energy distributions from observed nonthermal spectra},
         year = 2015,
      journal = {Proc.~of International Cosmic Ray Conference 2015},
        pages = "922",
       eprint = {1509.03319},
       adsurl = {http://adsabs.harvard.edu/abs/2015arXiv150903319Z},
    }

Installation
------------

Within any Python >= 3.9 virtual environment with `pip` installed, do

.. code-block:: bash

   pip install git+https://github.com/HealthyPear/naimatic

Usage
-----

To use *naimatic*, you start from a configuration file that defines your models,
particle distributions, and radiative processes.

Assuming this file is called `config.yaml`, the usage is as simple as:

.. code-block:: bash

   naimatic config.yaml

See ``naimatic -h`` for more options.

The results from each model will be saved in their own subdirectories under the specified output director.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   config
   examples
   autoapi/index.rst
   changelog

