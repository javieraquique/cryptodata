#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Docstring
"""
  ______ .______     ____    ____ .______   .___________.  ______    _______       ___   .___________.    ___      
 /      ||   _  \    \   \  /   / |   _  \  |           | /  __  \  |       \     /   \  |           |   /   \     
|  ,----'|  |_)  |    \   \/   /  |  |_)  | `---|  |----`|  |  |  | |  .--.  |   /  ^  \ `---|  |----`  /  ^  \    
|  |     |      /      \_    _/   |   ___/      |  |     |  |  |  | |  |  |  |  /  /_\  \    |  |      /  /_\  \   
|  `----.|  |\  \----.   |  |     |  |          |  |     |  `--'  | |  '--'  | /  _____  \   |  |     /  _____  \  
 \______|| _| `._____|   |__|     | _|          |__|      \______/  |_______/ /__/     \__\  |__|    /__/     \__\ 
 
 Indicadores de criptomonedas en tiempo real!

 Datos extraídos de kraken.com a través de la API krakenex
"""

# # Importando librerías
import krakenex
import pandas as pd
import plotly.graph_objects as go

# Definiendo variables locales
# Asignando API de Kraken como variable global
kraken = krakenex.API()

# Asignando criptomonédas a analizar y tipos de cambio
cryptos = ["BTC", "ETH"]
currencies = ["USD", "EUR"]


# Definiendo funciones

# Función de limpieza de datos
def cleaningData(df):

    time_vars = ["time"]
    float_vars = ["open", "high", "low", "close", "vwap", "volume"]

    for var in time_vars:
        df[var] = pd.to_datetime(df[var], unit="s")

    for var in float_vars:
        df[var] = pd.to_numeric(df[var], errors="coerce")

    return df


# Función para extraer los datos
def getData():
    ohlc = []
    for crypto in cryptos:
        for currency in currencies:
            try:
                fresh_data = kraken.query_public("OHLC", {"pair": crypto + currency})
                ohlc.append(fresh_data)
            except kraken.query_public("OHLC", {"pair": crypto + currency})[
                "error"
            ] as e:
                print(e)

    return ohlc


# Función para constriuir el Data Frame
def buildDf(data):
    df = pd.DataFrame()
    for pair in data:
        pair_name = list(pair["result"].keys())[0]
        pair_data = pair["result"][pair_name]
        pair_df = pd.DataFrame.from_records(
            pair_data,
            columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"],
        )
        pair_df["pair_name"] = pair_name
        df = pd.concat([df, pair_df], axis=0)

    return df


# Función generar media móvil
def calculateMovingAverage(df):

    df["SMA25"] = df["close"].rolling(25).mean()

    return df


# Función generar RSI
def calculateRsi(df, periods=14, ema=True):
    """
    Returns a pd.Series with the relative strength index.
    """
    close_delta = df["close"].diff()

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


# Función generar indicadores
def calculateIndicators(df):

    # Identificando todos los pares disponibles en la extracción
    pairs = df["pair_name"].unique()

    # Calculado los indicadores para cada par y almacenando en un data frame independiente
    list_of_dfs = []
    for pair in pairs:
        df_pair = df[df["pair_name"] == pair]

        df_pair = calculateMovingAverage(df_pair)
        df_pair = calculateRsi(df_pair)
        df_pair["SMA25"] = df_pair["close"].rolling(25).mean()

        list_of_dfs.append(df_pair)

    # Uniendo todos los data frames en un solo data frame resultante
    new_df = pd.DataFrame()
    for x in list_of_dfs:
        new_df = new_df.append(x)
    return new_df


# Definiendo la función principal
def main():

    # Extrayendo datos
    data = getData()

    # Validando errores
    for x in data:
        if list(x.values())[0]:
            print(f"Se ha producido el siguiente error: {list(x.values())[0][0]}")
            break
        else:
            print("Datos cargados correctamente")

    # Construyendo Data Frame
    df = buildDf(data)
    df = df.reset_index(drop=True)

    # Limpiando datos
    df = cleaningData(df)

    # Calculado indicadores
    df = calculateIndicators(df)

    # Generando visualizaciones
    df_test = df[df["pair_name"] == "XXBTZUSD"]

    # Gráfico precio

    hovertext = []
    for i in range(len(df_test["open"])):
        hovertext.append("<br>Precio: " + str(df_test["close"][i]))

    fig = go.Figure(
        data=go.Ohlc(
            x=df_test["time"],
            open=df_test["open"],
            high=df_test["high"],
            low=df_test["low"],
            close=df_test["close"],
            text=hovertext,
            hoverinfo="text",
        )
    )

    fig.update_layout(
        title="Precio histórico. Últimos 720 periodos",
        yaxis_title="Precio del par XXBTZUSD",
    )

    fig.show()

    # Gráfico média móvil
    hovertext = []
    for i in range(len(df_test["open"])):
        hovertext.append("<br>Precio: " + str(df_test["close"][i]))

    fig = go.Figure(
        data=[
            go.Ohlc(
                x=df_test["time"],
                open=df_test["open"],
                high=df_test["high"],
                low=df_test["low"],
                close=df_test["close"],
                text=hovertext,
                hoverinfo="text",
                name="Precio",
            ),
            go.Scatter(
                x=df_test["time"],
                y=df_test["SMA25"],
                line=dict(color="blue", width=1),
                name="Media móvil 25 períodos",
            ),
        ]
    )

    fig.update_layout(
        title="Media móvil. Últimos 720 periodos", yaxis_title="Precio del par XXBTZUSD"
    )

    fig.show()

    # Gráfico RSI
    hovertext = []
    for i in range(len(df_test["open"])):
        hovertext.append("<br>Precio: " + str(df_test["close"][i]))
    layout = {"yaxis": {"domain": [0, 0.33]}, "yaxis2": {"domain": [0.33, 1]}}
    fig = go.Figure(
        data=[
            go.Ohlc(
                x=df_test["time"],
                open=df_test["open"],
                high=df_test["high"],
                low=df_test["low"],
                close=df_test["close"],
                text=hovertext,
                hoverinfo="text",
                name="Precio",
                yaxis="y2",
            ),
            go.Scatter(
                x=df_test["time"],
                y=df_test["RSI"],
                line=dict(color="purple", width=1),
                name="Índice de fortaleza realativa",
                yaxis="y",
            ),
        ],
        layout=layout,
    )

    fig.update_layout(
        title="Índice de fortaleza relativa (RSI). Últimos 720 periodos",
        yaxis_title="Precio del par XXBTZUSD",
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )

    fig.show()


if __name__ == "__main__":
    main()
