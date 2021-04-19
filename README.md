# EF_Portfolio_Optimization
We will be using [Semantic Versioning](https://semver.org/) for this repo's version control.
Database files should only be held localy as they are too large for GIT , so you need to run Database_maintainance.ipynb first.

This project began as an attempt to test portfolio generation methods.
We soon realised that to pull together stock price data was no small task, so we moved to generalise ways to pull together stockprices using yfinance and some database methods as it was an area we wished to learn more about. We found Efficient Frontier methods interesting and have leveraged a great repo for these methods [Py Portfolio Opt](https://github.com/robertmartin8/PyPortfolioOpt). We step out the theory behind these methods & using them in python in *EF_method_example.ipynb*.

Our homebrew functions are at *DatabaseMainFnc.py*, if you see improvements please do make them and let us know through issues or pull reuests.

Currently we have compiled ticker lists for NASDAQ & NYSE, more can easily added once you have the ticker list in tsv format, if you compile these do share them & we will add them to the repo for others to be able to use too.

We attempt to split out our proccess into 3 clear parts stepped out in 3 distinct workbooks, and make these as self contained and self explandatory as possible.

## 1. Gathering stock closing price & currency Forex price data
Database_maintainance.ipynb

## 2. Using portfolio generation methods on histoic data to establish historic performance
Historic_portfolio_nb.ipynb

## 3. Analyse historic performance
Not yet added


