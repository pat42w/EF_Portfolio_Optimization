#Import the libraries
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
import math
from datetime import timedelta 

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import plotting
import cvxpy as cp

# Import libraries to fetch historical EUR/USD prices
from forex_python.converter import get_rate
from joblib import Parallel, delayed

DATE_FORMAT = '%Y-%m-%d'

# Database maintainance functions

#Connects to a the pre-existing CSV price database
def connectAndLoadDb(exchange):
    """Connects to and loads the data for an exchange.
    Parameters
    ----------
    exchange : str
        The name of the exchange stored at
        "Price Databases\database_"+str(exchange)+".csv"

    Returns
    -------
    DataFrame 
        database with dates & assets prices 
        in the native currency in each column
    """

    print("Connecting database:"+str(exchange))
    filename="Price Databases\database_"+str(exchange)+".csv"
    database = pd.read_csv(filename,index_col=False) 
    print("Database connected!")
    return database

#Gets the latest date of data in the db
def getLastEntryDate(database):
    """Gets the most recent entry date from 
    the prices database
    Parameters
    ----------
    database : DataFrame
        The database of prices with a date column or index 'Date'

    Returns
    -------
    str
        The most recent entry date in '%Y-%m-%d' format
    """
    lastDateEntry = database.iloc[-1]['Date']
    lastDateEntry = datetime.datetime.strptime(lastDateEntry, DATE_FORMAT)    
    return lastDateEntry

#Writes the updated pandas dataframe to the CSV
def writeDbToExcelFile(database,exchange):
    """Saves the database as a csv to the directory: 
    'Price Databases\database_'+str(exchange)+'.csv'
    ----------
    database : DataFrame
        The database of prices with a date column or index 'Date'
    exchange : str
        The name of the index to use in the filename 
    """
    filename='Price Databases\database_'+str(exchange)+'.csv'
    print('Writing database to filename: '+ filename)
    database.index=database['Date']
    database.drop(['Date'],axis=1,inplace=True)
    database.to_csv(filename)
    print('Database updated with new entries!!')

#Formats the date from number for printing      
def prettyPrintDate(date):
    """Formats a date string to '%Y-%m-%d' format, 
    used to consistantly print the same date format
    ----------
    date : str
        The date we want to format
    """
    return date.strftime(DATE_FORMAT)

#Data Fetching functions

#get ticker list from our tsv files
def getTickers(exchange):
    """Pulls in the list of stock tickers for an exchange
    stored at 'Company lists/companylist_'+str(exchange)+'.tsv'
    Parameters
    ----------
    exchange : str
        The name of the exchange stored at
        'Company lists/companylist_'+str(exchange)+'.tsv'

    Returns
    -------
    l_tickers : list 
        list of stock tickers listed on the exchange
    """
    #We have the lists saved as TSV ie delimited with tabs rather than commas
    df_info=pd.read_csv('Company lists/companylist_'+str(exchange)+'.tsv',sep='\t') 
    l_tickers=df_info.Symbol.tolist()
    return l_tickers

# Updates data for a given exchange or creates a db from a given ticker list
def fetchData(database,exchange,start_date, refetchAll = False):
    """adds adj closing price data from a given exchange 
    from date using Yfinance.

    Parameters
    ----------
    database : DataFrame
        The data base of prices to be appended.
        Empty DataFrame if starting a new prices database.

    start_date : str
        When refetchAll=True this denotes the start date 'YYYY-MM-DD' 
        to pull data from up to yesterday
        default is '2006-01-01'.

    exchange : str
        The name of the exchange stored at
        'Company lists/companylist_'+str(exchange)+'.tsv'

    refetchAll : Boolean
        False: updates price data from the latest entry up to yesterday
        True:  refetches all price data from '2006-01-01' to yesterday
    Returns
    -------
    database : DataFrame 
        The database of with latest prices added.
    """ 

    if refetchAll == True:
        lastEntryDate = datetime.datetime.strptime(start_date, DATE_FORMAT) #Start date here 
    else:
        lastEntryDate = getLastEntryDate(database)
    ydaysDate = datetime.datetime.today() - timedelta(days = 1)

    # checks is the data base already up to date
    if lastEntryDate >= ydaysDate:
        print('Data already loaded up to Yesterday')
        return database
    else:
        print("Last entry in Db is of :" + prettyPrintDate(lastEntryDate))
        print("----------------------------------------------")
    
        dateToFetch = lastEntryDate + timedelta(days=1)

        dateStr = prettyPrintDate(dateToFetch)
        print('Fetching stock closing price of '+str(exchange)+' for days over: ' + dateStr)

        l_tickers=getTickers(exchange)

        #Pulling adj closing price data from yfinance
        mergedData = yf.download(l_tickers,dateToFetch)['Adj Close']

        #Making date the index col
        mergedData['Date']=mergedData.index

        #append our new data onto the existing databae
        database = database.append(mergedData, ignore_index=True)
    
        print("----------------------------------------------")
        print("Data fill completed! 👍👍")
        return database

# one line  function to create or update a db for a given exchange 
def update_db(exchange, start_date='2006-01-01',refetchAll = False):
    """One line funcion that pulls adj closing price data for 
    a given exchange into a DataFrame and saves as a csv to: 
    'Price Databases\database_'+str(exchange)+'.csv'.
    Parameters
    ----------
    exchange : str
        The name of the exchange stored at
        'Company lists/companylist_'+str(exchange)+'.tsv'

    start_date : str
        When refetchAll=True this denotes the start date 'YYYY-MM-DD' 
        to pull data from up to yesterday
        default is '2006-01-01'.

    refetchAll : Boolean
        False: updates price data from the latest entry up to yesterday
        True:  refetches all price data from '2006-01-01' to yesterday
    Returns
    -------
    database : DataFrame 
        The database of with latest prices added for the exchange.
    """ 
    if refetchAll == True:
        #For a fresh run 
        database = pd.DataFrame()
        database = fetchData(database, exchange, start_date, refetchAll)
    else:
        # Load in & Update an existing database
        database = connectAndLoadDb(exchange)
        database = fetchData(database,exchange, start_date)

    # Drop the last entry prior to saving as it probably is not a full days data
    database.drop(database.tail(1).index, inplace = True) 

    # Write the data to CSV
    writeDbToExcelFile(database,exchange)
    return

# for a given echange removes any tickers which have all NULLS in the data base 
def cleanCompanyList(exchange):
    """After database is created run this to check for any empty 
    columns and remove the ticket from the company list.
    After this is ran re run update_db with Refetchall = True.
    Parameters
    ----------
    exchange : str
        The name of the database stored at
        'Company lists/companylist_'+str(exchange)+'.tsv'
    """ 
    #Load db
    df=connectAndLoadDb(exchange)
    
    #create list of NULL columns
    l_drop=df.columns[df.isna().all()].tolist()

    #read in company list TSV
    df_info=pd.read_csv('Company lists/companylist_'+str(exchange)+'.tsv',sep='\t') 
    df_info.drop(columns=['Unnamed: 0'],inplace=True)
    df_info.index=df_info.Symbol

    #drop listed rows
    df_info.drop(index=l_drop, inplace=True)
    df_info.reset_index(drop=True, inplace=True)

    df_info.to_csv('Company lists/companylist_'+str(exchange)+'.tsv',sep='\t')
    print(str(len(l_drop))+' Rows dropped from '+str(exchange))
    return

def net_gains(principal,expected_returns,years,people=1):
    """Calculates the net gain after Irish Capital Gains Tax of a given principal for a given expected_returns over a given period of years"""
    cgt_tax_exemption=1270*people  #tax free threashold all gains after this are taxed at the cgt_ta_rate
    cgt_tax_rate=0.33  #cgt_tax_rate as of 19/3/21
    total_p=principal
    year=0
    while year < years:
        year+=1
        gross_returns=total_p*expected_returns
        if gross_returns >cgt_tax_exemption:
            taxable_returns=gross_returns-cgt_tax_exemption
            net_returns=cgt_tax_exemption+(taxable_returns*(1-cgt_tax_rate))
        else:
            net_returns=gross_returns
        total_p= total_p + net_returns
    return total_p


def gen_curr_csv(start_date='2006-01-01'):
    """
    Generates dataframe for currency pairs between 1st Jan. 2006 up to yesterday, 
    and saves to "Price Databases\curr_rates.csv

    start_date : str
        When refetchAll=True this denotes the start date 'YYYY-MM-DD' 
        to pull data from up to yesterday
        default is '2006-01-01'.
    """
    input_currencies = ['USD','JPY','GBP']
    start_date = datetime.datetime.strptime(start_date, DATE_FORMAT)
    print("Fetching Currecy rates from : "+prettyPrintDate(start_date))
    print("For Eur from : "+str(input_currencies))

    # May take up to 50 minutes to generate full set of rates
    end_date = (datetime.datetime.today() - timedelta(1))
    #end_date = datetime.datetime(2008,2,2).date() # For testing

    print("Generating date list")
    # Generate list of dates
    dates = []
    for i in range((end_date - start_date).days + 1):
        dates.append((start_date + timedelta(i)))
    
    # Add dates to dataframe
    rates_df = pd.DataFrame()
    rates_df['Date'] = dates

    #attempted to speed up by parallelising the date loops, this just over halves the time to run on the 15 years of data
    for curr in input_currencies:
        print("Fetching exchange data for: "+str(curr))
        rates_df[curr]=Parallel(n_jobs=-1)(delayed(get_rate)(curr,'EUR', date) for date in dates)

    print("Currecy rates updated")

    # Saved into the folder with the rest of our pricing data
    print("Writing database to filename: Price Databases\curr_rates.csv")
    rates_df.to_csv("Price Databases\curr_rates.csv")
    
    print("Database updated with new entries!!")
    return 

def load_curr_csv(stocks_df,input_curr):
    """
    Loads FX rates data, and converts historical stock prices to EUR using the rate at the time
    """
    rates_df = pd.read_csv("Price Databases\curr_rates.csv")
    
    rates_df=rates_df.set_index(pd.DatetimeIndex(rates_df['Date'].values))
    rates_df.drop(columns=['Date'],axis=1, inplace=True)

    if not input_curr in list(rates_df.columns):
        return 'Currency not supported'

    rates_df = rates_df.merge(stocks_df,left_index=True, right_index=True).drop(columns=stocks_df.columns)
    # Multiply each row of stocks dataframe by its' corresponding exchange rate
    result = pd.DataFrame(np.expand_dims(np.array(rates_df[input_curr]), axis=-1) * np.array(stocks_df),columns=stocks_df.columns,index=stocks_df.index)

    return result


def priceDB_validation(database):
    """Takes the prices database checkes for negative stock prices, 
    if there are it attempts to repull the data, 
    if it cannot it drops those columns.
    Parameters
    ----------
    database : DataFrame
        The dataframe of stock prices to be checked.

    Returns
    -------
    database : DataFrame 
        The database of negative prices ammended 
        or offending stocks removed.
    """
#check for negative prices (should not have any)
    neg_cols=database.columns[(database < 0).any()]
    print('---------------------------------------------------------------------')
    print('Negative prices are seen in the following assets: '+str(len(neg_cols)))
    if len(neg_cols) >0:
        print(neg_cols.tolist())

        #Drop the offending columns
        print('The following columns have been dropped: ')
        print(neg_cols.tolist())
        database.drop(columns=neg_cols.tolist(), inplace=True)
       
        
        #I cant get this part working so i am just droping the columns that have issues for now
        #Try to fix by rerunning the data
        #df_retry=yf.download(neg_cols.tolist(),'2006-1-1')['Adj Close']
        #print('Are there negatives in the repulled data : '+str((df_retry< 0).any()))
        #if (df_retry< 0).any() ==True:
        #    print('Issue not solved by repulling data so the following columns have been dropped:')
        #    print(neg_cols.tolist())
        #    database.drop(columns=neg_cols.tolist(), inplace=True)

        
        #else:
        #   print('Issue has been solved by repulling data, the following columns have been updated with repulled data:')
        #    print(neg_cols.tolist())
        #    database[neg_cols]=yf.download(neg_cols.tolist(),'2006-1-1')['Adj Close']
        
        return database

#generates historic performance data
def portfolio_generate_test(database,startdate,enddate,p_max=400, min_returns=0.01, s_asset=0, asset_len=50, obj_method='SHARPE', target_percent=0.1, silent=True):
    """Takes the prices database checkes for negative stock prices, 
    if there are it attempts to repull the data, 
    if it cannot it drops those columns.
    Parameters
    ----------
    database : DataFrame
        The dataframe of stock prices.

    Returns
    -------
    database : DataFrame 
        The database of negative prices ammended 
        or offending stocks removed.
    """
    if silent == False:
        print('Running for :'+str(startdate)+' to '+str(enddate))
    # Subset for date range
    df_input=database[startdate:enddate]
    if silent == False:
        print ("Initial number of stocks: "+str(len(df_input.columns)))

    #Check for stocks which are too expensive for us to buy & drop those
    p_now=database.iloc[-1,:]
    df_unaffordable=p_now[p_now>p_max] #we can set max price here maybe as an optional
    l_unaffordable=df_unaffordable.index.tolist()
    df_input.drop(columns=l_unaffordable, inplace=True)
    if silent == False:
        print ("-----------------------------------------------------")
        print ("Our max price is : €"+str(p_max))
        print ("Number of stocks to drop due being unnaffordble: "+str(len(l_unaffordable)))
        print ("Number of stocks remaining: "+str(len(df_input.columns)))


    # drop any columns with more than half or more Nas as the models dont like these
    half_length=int(len(df_input)*0.50)
    l_drop=df_input.columns[df_input.iloc[:half_length,:].isna().all()].tolist()
    df_input.drop(columns=l_drop, inplace=True)
    if silent == False:
        print ("-----------------------------------------------------")
        print ("Number of stocks due to NAs: "+str(len(l_drop)))
        print ("Number of stocks remaining: "+str(len(df_input.columns)))

    # drop any columns with more  Nas for their last 5 rows as these have been delisted
    l_drop=df_input.columns[df_input.iloc[-3:,:].isna().all()].tolist()
    df_input.drop(columns=l_drop, inplace=True)
    if silent == False:
        print ("-----------------------------------------------------")
        print ("Number of stocks due to being delisted: "+str(len(l_drop)))
        print ("Number of stocks remaining: "+str(len(df_input.columns)))


    #see which stocks have negative returns or low returns in the period & drop those
    df_pct=(df_input.iloc[-1,:].fillna(0) / df_input.iloc[0,:])
    df_pct=df_pct[df_pct<= (min_returns + 1)] #we can set minimum returns here maybe as an optional
    l_pct=df_pct.index.tolist()
    df_input.drop(columns=l_pct, inplace=True)
    if silent == False:
        print ("-----------------------------------------------------")
        print ("Number of stocks due to Negative returns: "+str(len(l_pct)))
        print ("Number of stocks remaining: "+str(len(df_input.columns)))
        print ("Number of days data: "+str(len(df_input)))
        print ("As default we will only keep the top 50 performing stocks when creating our portfolio(this can be varied using s_asset & asset_len)")

    #We will only keep the X best performing assets can make this an optional input
    e_asset=s_asset + asset_len
    df=df_input
    mu = expected_returns.mean_historical_return(df)
    top_stocks = mu.sort_values(ascending=False).index[s_asset:e_asset]
    df = df[top_stocks]

    #Calculate expected annulised returns & annual sample covariance matrix of the daily asset
    mu = expected_returns.mean_historical_return(df)
    S = risk_models.sample_cov(df)

    # Optomise for maximal Sharpe ratio
    ef= EfficientFrontier(mu, S) #Create the Efficient Frontier Object

    #We can try a variety of objectives look at adding this as an input
    if obj_method == "SHARPE":
        objective_summary=obj_method #description of the objective we used for our output df
        weights = ef.max_sharpe()

    elif obj_method == "MIN_VOL":
        objective_summary=obj_method #description of the objective we used for our output df
        weights = ef.min_volatility()

    elif obj_method == "RISK":
        objective_summary=obj_method+"_"+str(target_percent) #description of the objective we used for our output df
        weights = ef.efficient_risk(target_percent)

    elif obj_method == "RETURN":
        objective_summary=obj_method+"_"+str(target_percent) #description of the objective we used for our output df
        weights = ef.efficient_return(target_percent)

    else:   
        print("obj_method must be one of SHARPE, MIN_VOL, RISK, RETURN")

    cl_weights= ef.clean_weights()
    #print(cl_weights)
    if silent == False:
        print("-------------------------------------------------------------")
        print("Our Benchmark portfolio the S&P 500 has: Volatility  18.1% & Annual Return: 10.6%")
        ef.portfolio_performance(verbose=True)
    expected_portfolio_returns=ef.portfolio_performance()[0]
    volatility=ef.portfolio_performance()[1]
    r_sharpe=ef.portfolio_performance()[2]

    #calculates the actual performance date range work on this
    actual_startdate = pd.to_datetime(enddate) + pd.DateOffset(days=2)
    actual_enddate = pd.to_datetime(actual_startdate) + pd.DateOffset(years=1)

    #create df of price changes in the folowing year
    df_actual=database[actual_startdate:actual_enddate]

    #some days have nans in them use the next valid value to fill the gap
    df_actual=df_actual.fillna(method='bfill')
    #then fill any tail nans with 0 as we assume delisted
    df_actual=df_actual.fillna(0)
    #select only the stocks we used for our porfolio generator
    df_actual=df_actual[top_stocks]
    #create the percentage daily changes for easch stock
    df_actual=df_actual.apply(lambda x: x.div(x.iloc[0]))

    #refomat the weights so we can apply them to the df_actual
    df_weights=pd.DataFrame(cl_weights.values())
    df_weights=df_weights.transpose()
    df_weights.columns=df_actual.columns

    #our total weighted returns by day
    df_weighted_actual=df_actual.mul(df_weights.iloc[-1,:])
    df_weighted_actual=df_weighted_actual.sum(axis=1)

    #now we calculate some stats more can be added here
    max_returns=df_weighted_actual.max()-1
    mean_returns=df_weighted_actual.mean()-1
    min_returns=df_weighted_actual.min()-1
    actual_returns=df_weighted_actual[-1]-1

    if silent == False:
        #Create dataframe for graph
        df_graph=pd.DataFrame(df_weighted_actual, columns=['Actual_Returns'])
        df_graph['Actual_Returns']=df_graph['Actual_Returns']-1
        df_graph['Expected_Returns']=expected_portfolio_returns
        df_graph.plot(figsize=(10,5))
        plt.show()
        print("-------------------------------------------------------------")
        print("Our portfolio performed at : " + str(f'{actual_returns*100:.{1}f}')+"%")
        print("Max : " + str(f'{max_returns*100:.{1}f}')+"%, "
             +"Min : " + str(f'{min_returns*100:.{1}f}')+"%, "
             +"Mean : " + str(f'{mean_returns*100:.{1}f}')+"%")

    return [pd.to_datetime(startdate), pd.to_datetime(enddate), expected_portfolio_returns, volatility, r_sharpe, max_returns, min_returns, actual_returns,mean_returns, objective_summary]