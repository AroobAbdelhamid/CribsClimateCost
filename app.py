<<<<<<< HEAD
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import altair as alt
import os
from vega_datasets import data

#concatenates the all US and the single US from the prediction    
def createdf(zip, X_ypred_avg):
    #average of all zip codes for scatter plot
    # allzip = X_ypred_avg.groupby(X_ypred_avg.Date.dt.year)[['Zip', 'Year', 'ppsf_doll_pred', 'Latitude', 'Longitude']].transform('mean').drop_duplicates()
    # allzip['Year']= pd.to_datetime(allzip['Year'], format = "%Y")
    allzip = pd.read_csv("allzip.csv",index_col=0, parse_dates=['Year'] )
    #data for the map
    # X_ypred_avg = X_ypred_avg.groupby([X_ypred_avg.Date.dt.year, 'Zip'])[['Zip', 'Year', 'ppsf_doll_pred', 'Latitude', 'Longitude']].transform('mean').drop_duplicates()

    #eventually this wil go into its own procedure so that I don't have to recalculate everything
    singlezip = X_ypred_avg[X_ypred_avg['Zip']==zip].drop_duplicates()
    singlezip['Year']= pd.to_datetime(singlezip['Year'], format = "%Y")

    single_all= pd.merge(left=allzip, right=singlezip, on='Year', suffixes=("US", 'single'))
    single_all= single_all.rename(columns={"ppsf_doll_predUS": 'US', "ppsf_doll_predsingle": str(singlezip['Zip'].iloc[0])})
    single_all = single_all.drop(columns=['ZipUS'])
    return X_ypred_avg, single_all, singlezip

#creates the chaart for the line plot on the top of the graph
def createlineplot(single_all, singlezip):
    summ_chart= alt.Chart(single_all).transform_fold(
    ['US', str(singlezip['Zip'].iloc[0])],
    ).encode(
        x=alt.X('Year:T'),
        y=alt.Y('value:Q', axis=alt.Axis(format='$2f', title='Price Per Square Foot')),
        color = alt.Color('key:N', title = "Location"),
        tooltip=[alt.Tooltip('Year', title='Year', timeUnit='year'), alt.Tooltip('value:Q', title='PPSF', format='$.2f')]
    )

    both_charts = alt.layer(summ_chart.mark_circle(color='gray', size=3),
            summ_chart.mark_circle(size=95, color='purple')
    ).configure_axis(
        labelFontSize=20,
        titleFontSize=20,
        labelAngle =0
    ).properties(
        width=600,
        height=400
    ).configure_legend(
        gradientLength=400,
        gradientThickness=60,
        titleFontSize=18,
        labelFontSize=20
    ).interactive() 

    return both_charts

def createmap(X_ypred_avg, singlezip):
   states = alt.topo_feature(data.us_10m.url, feature='states')
    # US states background
   background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).properties(
        width=900,
        height=400
    ).project('albersUsa')

   select_year = alt.selection_single(
        name='Change', fields=['Year'], init={'Year': X_ypred_avg['Year'].min() },
        bind=alt.binding_range(min=X_ypred_avg['Year'].min(), max=2060, step=5)
    )
   map_plot = pd.read_csv("map_plot_grplatlonyr.csv")
   points = alt.Chart(map_plot).mark_circle( #X_ypred_avg
        size=30,
    ).encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        color=alt.Color('ppsf_doll_pred', scale=alt.Scale( scheme='inferno')),#, title='Price Per Square Foot ($)')), #domain = [X_ypred_avg['ppsf_doll_pred'].min(), X_ypred_avg['ppsf_doll_pred'].max()],
        tooltip=[alt.Tooltip('ppsf_doll_pred', title='PPSF', format='.2f')] #'Zip', #alt.Tooltip('air', title='Temp', format = '2f C'), 
    ).add_selection(select_year
    ).transform_filter(select_year)

   point = alt.Chart(singlezip).mark_circle(
        size=75,
        filled=False,
        stroke='black',
        strokeWidth = 1
    ).encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q'
    )
   return background, points, point

def app():
    st.title("Your Crib's Climate Cost")

    st.markdown("""Predicting Housing Prices In the Era Of Climate Change""")
    st.markdown(""" By: Aroob Abdelhamid
    """)
    
    st.sidebar.markdown("How it Works:")

    st.sidebar.markdown("""
    It's easy! Input in a zip code! You can see how housing prices will be affected by climate change for that 
    zip codes! Note: Unavailable prediction data for your zipcode will automatically default to 64093
    """)
    
    zipcode = int(st.sidebar.text_input("What Is Your Zip Code?", '64093'))
    
    st.sidebar.markdown("""
    About the Project: As climate change affects the places that we live, we need a tool to predict the effect of climate 
    change on housing prices, specifically the effects of temperature and precipitation. This can help you decide whioh region of the
    country to buy a home to ensure the home's purchase price increases over time. 
    """)

    st.sidebar.markdown("""
    Data Sources: Housing data comes from [RedFin](https://www.redfin.com/news/data-center/), historical temperature and precipitation data comes from [NOAA](https://psl.noaa.gov/data/gridded/data.cmap.html),
    and forecased temperature and precipitation data comes from the [NASA NEX DCP-30](https://registry.opendata.aws/nasanex/) program
    Data Processing: I downloaded all the relevant historical data and synthesized it all together using pandas dataframes
    Predictions: I used a mixture of random forest and linear regression to fit the data to each zip code and used that to predict future housing prices 
    """)

    st.subheader('Plot of Housing Price Changes Relative to the US')
    X_ypred_avg = pd.read_csv(os.path.join(os.getcwd(), "Predictions_withzip_yravg.csv"), index_col=0, parse_dates=['Date']) # "Predictions_withZip.csv", parse_dates=['Date']
    if not X_ypred_avg['Zip'].isin([zipcode]).any():
        zipcode = 64093

    X_ypred_avg, single_all, singlezip = createdf(zipcode, X_ypred_avg)

    #approximately 40 secs to get here 7.31
    both_charts = createlineplot(single_all, singlezip)
    st.altair_chart(both_charts)

    st.subheader('Map of Housing Price Changes Around your Zipcode (highlighted with a black circle) over time')
    background, points, point = createmap(X_ypred_avg, singlezip)
    #approx 45 secs to get here 7.31
    st.altair_chart(background + points + point )


   # df = pd.DataFrame({'a':[2,3,4], 'b': [3,1,5]})
   # st.write(df)


if __name__ == '__main__':
    app()