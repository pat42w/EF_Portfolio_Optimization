#Import the libraries
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
import math
from datetime import timedelta 

# Import libraries to fetch historical EUR/USD prices
from datetime import datetime
from forex_python.converter import get_rate

DATE_FORMAT = '%Y-%m-%d'

# Data base maintainance functions

#Connects to a the pre-existing CSV price database
def connectAndLoadDb(exchange):
    print("Connecting database:"+str(exchange))
    filename="Price Databases\database_"+str(exchange)+".csv"
    database = pd.read_csv(filename,index_col=False) 
    print("Database connected!")
    return database

#Gets the latest date of data in the db
def getLastEntryDate(database):
    lastDateEntry = database.iloc[-1]['Date']
    lastDateEntry = datetime.datetime.strptime(lastDateEntry, DATE_FORMAT)    
    return lastDateEntry

#Writes the updated pandas dataframe to the CSV
def writeDbToExcelFile(database,exchange):
    filename='Price Databases\database_'+str(exchange)+'.csv'
    print('Writing database to filename: '+ filename)
    database.index=database['Date']
    database.drop(['Date'],axis=1,inplace=True)
    database.to_csv(filename)
    print('Database updated with new entries!!')

#Formats the date from number for printing      
def prettyPrintDate(date):
    return date.strftime(DATE_FORMAT)

#Data Fetching functions

#get ticker list from our tsv files
def getTickers(exchange):
    #We have the lists saved as TSV ie delimited wth tabs rather than commas
    df_info=pd.read_csv('Company lists/companylist_'+str(exchange)+'.tsv',sep='\t') 
    l_tickers=df_info.Symbol.tolist()
    return l_tickers

#Pulls adj closing price data from yfinance for a given list of stock tickers 'l_tickers', for all dates up to today from a given 'date' merges this data with an existing database 'database'
def fetchAndAppendToDb(date, database, exchange):  
    dateStr = prettyPrintDate(date)
    print('Fetching stock closing price of '+str(exchange)+' for days over: ' + dateStr)

    l_tickers=getTickers(exchange)
    #Pulling adj closing price data from yfinance
    mergedData = yf.download(l_tickers,date)['Adj Close']

    #Making date the index col
    mergedData['Date']=mergedData.index

    #append our new data onto the existing databae
    database = database.append(mergedData, ignore_index=True)
    return database

# Updates data for a given exchange or creates a db from a given ticker list
def fetchData(database,exchange, refetchAll = False):
    if refetchAll == True:
        lastEntryDate = datetime.datetime.strptime('2006-01-01', DATE_FORMAT) #Start date here 
    else:
        lastEntryDate = getLastEntryDate(database)
    ydaysDate = datetime.datetime.today() - timedelta(days = 1)
    if lastEntryDate >= ydaysDate:
        print('Data already loaded up to Yesterday')
        return database
    else:
        print("Last entry in Db is of :" + prettyPrintDate(lastEntryDate))
        print("----------------------------------------------")
    
        dateToFetch = lastEntryDate + timedelta(days=1)

        database = fetchAndAppendToDb(dateToFetch, database, exchange)
    
        print("----------------------------------------------")
        print("Data fill completed! 👍👍")
        return database

# one line  function to create or update a db for a given exchange 
def update_db(exchange,refetchAll = False):
    if refetchAll == True:
        #For a fresh run 
        database = pd.DataFrame()
        database = fetchData(database,exchange, refetchAll)
    else:
        # Load in & Update an existing database
        database = connectAndLoadDb(exchange)
        database = fetchData(database,exchange)

    # Drop the last entry prior to saving as it probably is not a full days data
    database.drop(database.tail(1).index, inplace = True) 

    # Write the data to CSV
    writeDbToExcelFile(database,exchange)
    return

# for a given echange removes any tickers which have all NULLS in the data base 
def cleanCompanyList(exchange):
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

def gen_curr_csv():
    """
    Generates dataframe for currency pairs between 1st Jan. 2006 and yesterday, and saves to CSV
    """

    input_currencies = ['USD','JPY','GBP']
    start_date = datetime(2006,1,1).date()
    
    # May take up to 50 minutes to generate full set of rates
    end_date = (datetime.today() - timedelta(1)).date()
    #end_date = datetime(2006,3,1).date() # For testing

    # Generate list of dates
    dates = []
    for i in range((end_date - start_date).days + 1):
        dates.append((start_date + timedelta(i)))
    
    # Add dates to dataframe
    rates_df = pd.DataFrame()
    rates_df['Date'] = dates

    rates_0 = []
    for date in dates:
        rates_0.append(get_rate(input_currencies[0],'EUR', date))

    rates_1 = []
    for date in dates:
        rates_1.append(get_rate(input_currencies[1],'EUR', date))

    rates_2 = []
    for date in dates:
        rates_2.append(get_rate(input_currencies[2],'EUR', date))
    
    rates_df[input_currencies[0]] = rates_0
    rates_df[input_currencies[1]] = rates_1
    rates_df[input_currencies[2]] = rates_2

    rates_df.to_csv('rates.csv',index = False)

    return 'rates.csv'

def load_curr_csv(stocks_df,input_curr):
    rates_df = pd.read_csv('rates.csv')
    
    rates_df=rates_df.set_index(pd.DatetimeIndex(rates_df['Date'].values))
    rates_df.drop(columns=['Date'],axis=1, inplace=True)

    if not input_curr in list(rates_df.columns):
        return 'Currency not supported'

    # Multiply each row of stocks dataframe by its' corresponding exchange rate
    result = pd.DataFrame(np.array(rates_df) * np.array(stocks_df),columns=stocks_df.columns,index=stocks_df.index)

    return result
