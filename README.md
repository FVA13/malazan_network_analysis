# malazan_network_analysis

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

The Malazan Book of the Fallen is arguably one if the most complex and rich on intrinsic connections masterpiece
from the world of literature. The goal of this research is to take a closer look at characters interactions from
Network Science perspective.


## Project Organization

```
├── Makefile           <- Makefile with convenience commands like `make data` or `make help`.
├── README.md          <- The top-level README for developers using this project.
├── params.yaml        <- yaml file with some of the hyperparameters.
├── data
│   ├── processed      <- The final, preprocessed data with nodes, edges, and a separate Graph file.
│   ├── interim        <- The collected and cleaned data with nodes and edges.
│   └── raw            <- The original, immutable data dump.
│
├── notebooks          <- Jupyter notebooks with network analysis.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         src and configuration for tools like black.
│
├── reports            <- Generated analysis as analysis_report.md.
│   └── figures        <- Generated graphics and figures to be used in reporting.
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment.
│
├── setup.cfg          <- Configuration file for flake8.
│
└── src   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes src a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── dataset_process.py      <- Code to clean data
    │
    ├── my_utils.py             <- Store useful functions and classes for Network Analysis
    │
    ├── structural_analysis.py  <- Code with classes and functions for Structural Analysis of the Network
    │
    ├── community_detection.py  <- Code with classes and functions for Community Detection
    │
    ├── plots.py                <- Code to create visualizations
    │
    └── update_report.py        <- Update reports/analysis_report.md using the latest data
```

--------

