#TODO scale on rain values scale=alt.Scale(domain=[min_value, max_value])

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from buienradar.buienradar import (get_data, parse_data)
from buienradar.constants import (CONTENT, RAINCONTENT, SUCCESS)
from datetime import datetime as dt
from datetime import date, timedelta
import pandas as pd
import psycopg2
import altair as alt
import os
import solaredge
import time
#from dotenv import load_dotenv
#load_dotenv()

user = os.getenv('HAA_DB_USER')
password = os.getenv('HAA_DB_PASSWORD')
host = os.getenv('HAA_DB_HOST')
se_token = os.getenv('HAA_SOLAREDGE')
se_site_id = os.getenv('HAA_SE_SITE_ID')
lat = float(os.getenv('HAA_LAT'))
lon = float(os.getenv('HAA_LON'))
s = solaredge.Solaredge(se_token)
yesterday = date.today() - timedelta(days=1)

print(user)
print(host)

st.set_page_config(layout="wide")
col1, col2, col3 = st.columns(3)

def make_connection():
    attempts = 0
    while attempts < 5:
        try:
            conn = psycopg2.connect(user=user, password=password, host=host, database='postgres', port=5432)
            return conn
        except psycopg2.OperationalError:
            attempt +=1


# def get_temperature(ruimte):
#     conn = make_connection()
#     sql = "select * from temperatuur where tijd > '"+str(dt.today())[0:10]+" 00:00:00';"
#     df = pd.read_sql_query(sql, con = conn)[['tijd', ruimte]].set_index('tijd')
#     df['uur'] = df.index.floor('H')
#     df = df.set_index('uur')
#     df = df.groupby('uur').mean()
#     df['tijd'] = df.index

#     return df

def get_temperature(ruimte):
    conn = make_connection()
    sql = "select * from temperatuur where tijd > '"+str(yesterday)+" 00:00:00';"
    df = pd.read_sql_query(sql, con = conn)[['tijd', ruimte]].set_index('tijd')
    df['uur'] = df.index.floor('H')
    df = df.set_index('uur')
    df = df.groupby('uur').mean()
    df['tijd'] = df.index
    df['day'] = df.tijd.dt.strftime('%Y-%m-%d')
    df['hour'] = df.tijd.dt.strftime('%H')

    return df

def get_temperature_total():
    conn = make_connection()    
    sql = "select * from temperatuur where tijd > '"+str(dt.today())[0:10]+" 00:00:00';"
    df = pd.read_sql_query(sql, con = conn)[['tijd', 'buiten', 'keuken', 'kamer']].set_index('tijd')
    return df


# actuele temperatuur
def get_actual_temp(ruimte):
    conn = make_connection()
    sql = "select * from temperatuur order by tijd desc limit 1;"
    df = pd.read_sql_query(sql, con = conn)
    value = round(df[ruimte][0], 1)
    return value

# energy details SolarEdge
def get_energy(begin, end):
    res = s.get_energy_details(se_site_id, begin, end, time_unit='HOUR')
    
    return res

st_autorefresh(interval=5*60*1000, key="dataframerefresh")

# sensoren
buiten = get_temperature('buiten')
kamer = get_temperature('kamer')
keuken = get_temperature('keuken')
alles = get_temperature_total()
alles = buiten.buiten.to_list()+keuken.keuken.to_list()+kamer.kamer.to_list()
min_value = int(min(alles))
max_value = round(max(alles), 0) + 2

# solaredge
se_energy = get_energy(str(yesterday)+" 00:00:00", str(dt.today())[0:10]+" 23:59:59")

se_date = []
se_value = []

for i in se_energy['energyDetails']['meters'][0]['values']:
    se_date.append(i['date'])
    if len(i) == 1:
        se_value.append(None)
    else:
        se_value.append(round(i['value'], 1))

se_df = pd.DataFrame({'se_date': se_date, 'se_value': se_value})

se_df['day'] = se_df.se_date.str[0:10]
se_df['hour'] = se_df.se_date.str[10:13]

# rain data
rain_url = 'https://gpsgadget.buienradar.nl/data/raintext/?lat='+str(lat)+'&lon='+str(lon)
rain_df = pd.read_csv(rain_url, sep ='|', header=None, names = ['value', 'tijd'])

# buienradar overige info
result = get_data(lat, lon)

if result.get(SUCCESS):

    data = result[CONTENT]
    raindata = result[RAINCONTENT]


    br = parse_data(data, raindata, lat, lon, 120)

br_forecast_text = br['data']['forecast'][0]['condition']['exact_nl']
br_min_temp = str(br['data']['forecast'][0]['mintemp'])
br_max_temp = str(br['data']['forecast'][0]['maxtemp'])
br_winddir = br['data']['forecast'][0]['winddirection']
br_windspeed = str(br['data']['forecast'][0]['windspeed'])

# dashboard
with col1:
    st.header('Buiten')
    st.subheader(get_actual_temp('buiten'))
    line_buiten = alt.Chart(buiten).mark_line().encode(
        x=alt.X('hour'),
        y=alt.Y('buiten', scale=alt.Scale(domain=[min_value, max_value], nice=False)),
        color=alt.Color('day',scale=alt.Scale(range= ['grey', '#1f77b4']), legend=None)
    ).properties(width=400)

    st.altair_chart(line_buiten)

    st.subheader(br_forecast_text)
    st.subheader('Temperatuur: '+br_min_temp+' - '+br_max_temp)
    st.subheader('Wind: '+br_winddir+' '+br_windspeed+' km/h')

with col2:
    st.header('Keuken')
    st.subheader(get_actual_temp('keuken'))
    line_keuken = alt.Chart(keuken).mark_line().encode(
        x=alt.X('hour'),
        y=alt.Y('keuken', scale=alt.Scale(domain=[min_value, max_value], nice=False)),
        color=alt.Color('day',scale=alt.Scale(range= ['grey', '#1f77b4']), legend=None)
    ).properties(width=400)
    st.altair_chart(line_keuken)

    area_rain = alt.Chart(rain_df).mark_area().encode(
        x=alt.X('tijd'),
        y=alt.Y('value')
    ).properties(width=400)
    st.altair_chart(area_rain)


with col3:
    st.header('Kamer')
    st.subheader(get_actual_temp('kamer'))
    
    line_kamer = alt.Chart(kamer).mark_line().encode(
        x=alt.X('hour'),
        y=alt.Y('kamer', scale=alt.Scale(domain=[min_value, max_value])),
        color=alt.Color('day',scale=alt.Scale(range= ['grey', '#1f77b4']), legend=None)
    ).properties(width=400)
    st.altair_chart(line_kamer)

    line_se = alt.Chart(se_df).mark_line().encode(
        x='hour',
        y='se_value',
        color=alt.Color('day',scale=alt.Scale(range= ['grey', '#1f77b4']), legend=None)
        ).properties(width=400)
    st.altair_chart(line_se)



