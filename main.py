import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime as dt
import pandas as pd
import psycopg2
import altair as alt
import os

user = os.getenv('HAA_DB_USER')
password = os.getenv('HAA_DB_PASSWORD')
host = os.getenv('HAA_DB_HOST')

print('test1')
print(host)

st.set_page_config(layout="wide")
col1, col2, col3 = st.columns(3)

def make_connection():
    conn = psycopg2.connect(user=user, password=password, host=host, database='postgres', port=5432)
    return conn


# temperaturen vandaag
def get_temperature(ruimte):
    conn = make_connection()
    sql = "select * from temperatuur where tijd > '"+str(dt.today())[0:10]+" 00:00:00';"
    df = pd.read_sql_query(sql, con = conn)[['tijd', ruimte]].set_index('tijd')
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

st_autorefresh(interval=60 * 1000, key="dataframerefresh")

def main():
    buiten = get_temperature('buiten')
    kamer = get_temperature('kamer')
    keuken = get_temperature('keuken')
    alles = get_temperature_total()

    alles = buiten.buiten.to_list()+keuken.keuken.to_list()+kamer.kamer.to_list()
    min_value = int(min(alles))
    max_value = round(max(alles), 0)
    with col1:
        st.write('Buiten')
        st.write(get_actual_temp('buiten'))
        # chart = alt.Chart(buiten).mark_line().encode(
        #     x='tijd:T',
        #      y=alt.Y('buiten:Q'))
        # st.altair_chart(chart)
        st.line_chart(alles)
        #alt.Chart(buiten).mark_line(color='black').encode()

    with col2:
        st.write('Keuken')
        st.write(get_actual_temp('keuken'))
        st.line_chart(keuken)
    with col3:
        st.write('Kamer')
        st.write(get_actual_temp('kamer'))
        st.line_chart(kamer)


if __name__ == "__main__":
    print('test2')
    print(host)
    main()