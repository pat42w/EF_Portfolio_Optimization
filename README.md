# EF_Portfolio_Optimization

## Introduction

This project began as an attempt to test portfolio generation methods.

We soon realised that to consolidate stock price data was no small task, so our initial focus became building out libraries for data acquisition. 

When researching algorithms for portfolio generation, we found Efficient Frontier methods interesting, and to use these have leveraged a great package called [Py Portfolio Opt](https://github.com/robertmartin8/PyPortfolioOpt). 

We step through the theory behind these methods & using them in Python in [EF_method_example.ipynb](https://github.com/pat42w/EF_Portfolio_Optimization/blob/release_0.1.0/EF_method_example.ipynb).

Our homebrew functions are at [DatabaseMainFnc.py](https://github.com/pat42w/EF_Portfolio_Optimization/blob/release_0.1.0/DatabaseMainFnc.py); if you see room for improvements please let us know through Issues and Pull Requests.

Currently we have compiled ticker lists for NASDAQ & NYSE exchanges, but more can be easily added. The code currently expects ticker lists in TSV format. If you compile these do share them & we will add them to the repo.

## Notebooks

We attempt to split out our proccess into 3 clear parts, each with its' own notebook, and make these as modular and self-explanatory as possible.

### 1. Gathering Stock Price & Forex Rates
[Database_maintainance.ipynb](https://github.com/pat42w/EF_Portfolio_Optimization/blob/main/1_Database_maintainance.ipynb)

### 2. Establishing Historic Performance
[Historic_portfolio_nb.ipynb](https://github.com/pat42w/EF_Portfolio_Optimization/blob/main/2_EF_Histportfolio_gen.ipynb)

### 3. Analysing Historic Performance
[EF_analysis.ipynb](https://github.com/pat42w/EF_Portfolio_Optimization/blob/main/EF_analysis.ipynb)

## Notes

Using [Semantic Versioning](https://semver.org/) for version control.

## Authors

Patrick Walsh BSc. 
Email: patrickwalsh1995@gmail.com

Eoghan O'Hara BSc.
