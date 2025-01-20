import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt
import numpy as np
import plotly.graph_objects as go
import requests
import pytz
from sqlalchemy import create_engine , text
import xml.etree.ElementTree as ET
from io import StringIO
from streamlit_autorefresh import st_autorefresh
from pandas.tseries.offsets import DateOffset
from streamlit_option_menu import option_menu
import math
import mysql.connector


@st.cache_resource
def get_db_connection():
    username = 'root'
    password = 'mineiro01'
    host = 'localhost'
    port = '3306'
    database = 'new_schema'
    
    connection_string = f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}'
    engine = create_engine(connection_string)
    
    return engine

def insert_data_to_db(codigo, data_abertura, tipo_manutencao, descricao, acao, materiais, custo, engine):
    with engine.connect() as conn:  # Usar 'with' para garantir que a conexão será fechada automaticamente
        sql = """
        INSERT INTO dados_manutenção_2024_teste 
        (`Código`, `Data Abertura/Hora`, `Tipo de Manutenção`, `Descrição da Falha`, `Ação de correção`, `Materiais necessários`, `Custo`)
        VALUES 
        (:codigo, :data_abertura, :tipo_manutencao, :descricao, :acao, :materiais, :custo)
        """
        
        # Usando dicionário para passar parâmetros nomeados para a query
        params = {
            'codigo': codigo,
            'data_abertura': data_abertura,
            'tipo_manutencao': tipo_manutencao,
            'descricao': descricao,
            'acao': acao,
            'materiais': materiais,
            'custo': custo
        }
        
        conn.execute(text(sql), params)  # Passando os parâmetros como dicionário
        conn.connection.commit()

# Conexão com o banco de dados
engine = get_db_connection()

selected = option_menu(
        "Menu",
        [
            "ABRIR ORDEM DE SERVIÇO DE MANUTENÇÃO",
            "FECHAR ORDEM DE SERVIÇO DE MANUTENÇÃO"
        ],
        icons=[ "list-task","list-task"],
        menu_icon="list",
        default_index=0,
        orientation="vertical"
    )

if selected == "ABRIR ORDEM DE SERVIÇO DE MANUTENÇÃO":
    with st.form('my_form', clear_on_submit=True):
        st.write('Abertura de OSM')

        codigo = st.text_input('Código Máquina')
        
        data_abertura = dt.datetime.now()
        data_abertura = data_abertura.strftime("%Y/%m/%d %H:%M:%S")

        data_abertura_input = st.text_input('Data Abertura', data_abertura)

        tipo_manutencao = st.selectbox('Tipo de Manutenção', ('CORRETIVA', 'PREVENTIVA'))

        descricao = st.text_area('Descrição de Falha', height=100)

        acao = st.text_area('Ação de Correção', height=100)

        materiais = st.text_area('Materiais Necessários', height=100)

        custo = st.text_input('Custo')

        status = 0

        submitted = st.form_submit_button("Submit")

        if submitted:
            insert_data_to_db(codigo, data_abertura_input, tipo_manutencao, descricao, acao, materiais, custo, engine)
            st.success("OSM registrada com sucesso!")

        codigo = None
        data_abertura_input = None
        tipo_manutencao = None
        descricao = None
        acao = None
        materiais = None
        custo = None
        status = None
