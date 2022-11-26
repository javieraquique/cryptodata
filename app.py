#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importando librerías
import krakenex
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import time
from dateutil.relativedelta import relativedelta
import streamlit as st
from plotly.subplots import make_subplots
from PIL import Image


# Definiendo variables globales
# Asignando API de Kraken como variable global
kraken = krakenex.API()

# Definiendo funciones

# Función para determinar la hora del servidor


def serverTime():
    server_time = kraken.query_public("Time")
    if server_time["error"]:
        return server_time["error"]
    else:
        return server_time["result"]


# Función para determinar el estado del sistema
def systemStatus():
    system_status = kraken.query_public("SystemStatus")
    if system_status["error"]:
        return system_status["error"]
    else:
        return system_status["result"]


# Función para extraer los datos
def getData(start_date, end_date, old_data, asset_selected, quote_selected):
    new_data = kraken.query_public(
        "Trades",
        {"pair": asset_selected + quote_selected, "since": int(start_date)},
    )

    if new_data["error"]:
        st.error(new_data['error'], icon="🚨")
    else:
        new_data = buildDf(
            new_data["result"][asset_selected + quote_selected]
        )

        if old_data is None:
            pass
        else:
            new_data = pd.concat([old_data, new_data], axis=0)

        new_start_date = new_data["time"].iloc[-1]

        if new_start_date >= end_date:
            pass
        else:
            time.sleep(1.8)
            new_data = getData(
                new_start_date,
                end_date, new_data,
                asset_selected,
                quote_selected)

        return new_data


# Función para construir el Dataframe
def buildDf(data):
    df = pd.DataFrame.from_records(
        data,
        columns=[
            "price",
            "volume",
            "time",
            "buy/sell",
            "market/limit",
            "miscellaneous",
            "?",
        ],
    )

    return df


# Función para limpieza de datos
def cleaningData(df):

    time_vars = ["time"]
    float_vars = ["price", "volume"]

    for var in time_vars:
        df[var] = pd.to_datetime(df[var], unit="s")

    for var in float_vars:
        df[var] = pd.to_numeric(df[var], errors="coerce")

    df.reset_index(inplace=True, drop=True)
    df = df.sort_values(by=['time'])

    return df


# Función para definir marco temporal


def defineTimeFrames(server_time):
    # now = datetime.datetime.now()
    hour = server_time - datetime.timedelta(hours=1)
    day = server_time - datetime.timedelta(days=1)
    week = server_time - relativedelta(weeks=1)
    month = server_time - relativedelta(month=1)
    year = server_time - relativedelta(years=1)
    return {
        "hour": hour, 
        "day": day, 
        "week": week, 
        "month": month, 
        "year": year}

# Función para transformar
# fecha de tipo datetime a epoch


def transformDatetimeToEpohc(since):
    return int(time.mktime((since).timetuple()))


# Función para generar la media móvil
def calculateMovingAverage(df):
    df["SMA75"] = df["price"].rolling(75).mean()
    return df


# Función para generar RSI
def calculateRsi(df, periods=14, ema=True):
    """
    Returns a pd.Series with the relative strength index.
    """
    close_delta = df["price"].diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)

    if ema == True:
        # Use exponential moving average
        ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window=periods, adjust=False).mean()
        ma_down = down.rolling(window=periods, adjust=False).mean()

    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))

    df["RSI"] = rsi
    return df


# Función para calcular indicadores
def calculateIndicators(df):

    # Identificando todos los pares disponibles en la extracción
    pairs = df["pair_name"].unique()

    # Calculado los indicadores para cada par y almacenando en un data frame independiente
    list_of_dfs = []
    for pair in pairs:
        df_pair = df[df["pair_name"] == pair]

        df_pair = calculateMovingAverage(df_pair)
        df_pair = calculateRsi(df_pair)
        # df_pair["SMA75"] = df_pair["close"].rolling(50).mean()

        list_of_dfs.append(df_pair)

    # Uniendo todos los data frames en un solo data frame resultante
    # new_df = pd.DataFrame()
    dfs = [df.reset_index(drop=True) for df in list_of_dfs]
    return pd.concat(dfs, axis=0)


# Definiendo la función principal
def main():

    # Cargando nombre de los pares
    assets_codes_df = pd.read_csv("asset_names.csv")

    # Almacenando estado de la API
    system_status = systemStatus()
    
    # Verificando conexión
    if system_status['status']:
        if system_status['status'] == 'online':
            message = 'Conexión establecida!' 
            icon="✅"
        else:
            message = system_status['status']
            icon="⚠️"
    else:
        st.error(system_status['error'], icon="🚨")
        exit()
        
    
    # Cargando activos
    # Extrayendo las cryptomonedas a analizar
    assets = list(kraken.query_public('Assets', {'asset':'XBT, ETH'})['result'].keys())

    assets_dict = {}
    for asset in assets:
        asset_name = assets_codes_df[assets_codes_df['code'] == asset]['name']
        assets_dict[asset_name.iloc[0]] = asset

    #Extrayendo todos pares disponibles en la API
    all_tradable_assets = []
    for item in kraken.query_public('AssetPairs')['result'].items():
        all_tradable_assets.append(item[1])

    # Generando Data frame con todos los pares disponibles en la API
    tradable_assets = pd.DataFrame.from_records(
    all_tradable_assets,
    columns=[
        'altname',
        'wsname	',
        'aclass_base',
        'base',
        'aclass_quote',
        'quote',
        'lot',
        'cost_decimals',
        'pair_decimals',
        'lot_decimals',
        'lot_multiplier',
        'leverage_buy',
        'leverage_sell',
        'fees',
        'fees_maker',
        'fee_volume_currency',
        'margin_call',
        'margin_stop',
        'ordermin',
        'costmin',
        'tick_size',
        'status'])

    # Filtrando la lista para localizar las posibles combinaciones con las criptomonedas a analizar
    tradable_assets['inlist'] = tradable_assets['base'].isin(assets)
    tradable_assets = tradable_assets[tradable_assets['inlist'] == True]

    #Estableciendo configuración de la página
    st.set_page_config(
    page_title="cryptoData",
    page_icon="🦈",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={

        'About': "# jaquiquepin@alumni.unav.es"
    })
    
    # Importando logo
    image = Image.open('img/cryptodata-logo.png')
    

    # Creando logo
    col1, col2, col3 = st.columns([0.1,0.6,0.1])

    with col1:
        st.empty()
    with col2:
        st.image(image, caption='Analizano criptoactivos', width=500)
    with col3:
        st.empty()
    
    # Generando desplegables
    c = st.container()

    col3, col4 = st.columns([0.5,0.5])
    
    with c:
        st.title("Seleccione una criptoactivo para analizar")
        with col3:
            asset_selected = st.selectbox(
                "Criptoactivo", assets_dict)
        with col4:
            asset_selected_code = assets_codes_df[assets_codes_df['name'] == asset_selected]['code'].item()
            quote_selected = st.selectbox(
                "Tipo de cambio", 
                tradable_assets[tradable_assets['base'] == asset_selected_code]['quote'].sort_values(ascending=False))

    # Selección de espacio temporal
    st.title("Seleccione un espacio temporal")
    time_frame = st.radio(
        "Espacio temporal",
        ('hour', 'day', 'month'),
        horizontal=True
        )

    # Estableciendo hora del servidor
    end_date = datetime.datetime.now()

    #Definiendo marco temporal por defecto de 24 horas
    # start_date = defineTimeFrames(datetime.datetime.utcfromtimestamp(end_date['unixtime']))
    # time_frame = 'month'
    start_date = defineTimeFrames(end_date)
    start_date = transformDatetimeToEpohc(start_date[time_frame])

    # Cargando datos
    with st.spinner('Cargando datos'):
        data = getData(start_date, transformDatetimeToEpohc(end_date), None, asset_selected_code, quote_selected)


    # Limpieza de datos
    try:
        data = cleaningData(data)
        data = calculateMovingAverage(data)
        data = calculateRsi(data)



        # Generando panales de indicadores
        tab1, tab2, tab3 = st.tabs(["Precio", "Média móvil", "RSI"])

        with tab1:
            st.header(f"Precio {asset_selected} en {quote_selected}")
            st.metric(label=f"Precio en {quote_selected}", value=data['price'].iloc[-1])
            fig = px.line(data, data['time'], data['price'])
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.header(f"Media móvil de {asset_selected} en {quote_selected}")
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(x=data['time'], y=data['price'],
                                mode='lines',
                                name='Precio'))
            fig.add_trace(go.Scatter(x=data['time'], y=data['SMA75'],
                                mode='lines',
                                name='SMA75'))
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.header(f"RSI de {asset_selected} en {quote_selected}")
            fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])

            fig.add_trace(
                go.Scatter(
                    x=data['time'], 
                    y=data['price'],
                    name='Precio'), 
                    row=1, 
                    col=1)

            fig.add_trace(
                go.Scatter(
                    x=data['time'],
                    y=data['RSI'],
                    name='RSI'), 
                    row=2,
                    col=1)

            st.plotly_chart(fig, use_container_width=True)

    
    except TypeError:
        pass

    info_display = st.info(message, icon=icon)

if __name__ == "__main__":
    main()