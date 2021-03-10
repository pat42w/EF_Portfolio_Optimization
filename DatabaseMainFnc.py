#Import the libraries
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import yfinance as yf
import datetime
import math
from datetime import timedelta 

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