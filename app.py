import streamlit as st
import pandas as pd
import datetime as dt
import numpy as np
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
from streamlit_js_eval import streamlit_js_eval
import pytz

@st.cache_resource
def get_db_connection():
    MYSQL_USER = st.secrets["MYSQL_USER"]
    MYSQL_PASSWORD = st.secrets["MYSQL_PASSWORD"]
    MYSQL_HOST = st.secrets["MYSQL_HOST"]
    MYSQL_DATABASE = st.secrets["MYSQL_DATABASE"]

    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{'3306'}/{MYSQL_DATABASE}")
    
    return engine

def insert_data_to_db(codigo, data_abertura, tipo_manutencao, descricao, acao, materiais, custo, motivo,engine):
    with engine.connect() as conn:
        sql = """
        INSERT INTO dados_manutencao
        (`Código`, `Data Abertura/Hora`, `Tipo de Manutenção`, `Descrição da Falha`,`Motivo da Falha`, `Ação de correção`, `Materiais necessários`, `Custo`, `status`)
        VALUES 
        (:codigo, :data_abertura, :tipo_manutencao, :descricao, :motivo, :acao, :materiais, :custo, :status)
        """
        
        params = {
            'codigo': codigo,
            'data_abertura': data_abertura,
            'tipo_manutencao': tipo_manutencao,
            'descricao': descricao,
            'motivo': motivo,
            'acao': acao,
            'materiais': materiais,
            'custo': custo,
            'status': status
        }
        
        conn.execute(text(sql), params)
        conn.connection.commit()

def insert_status_to_db(status, codigo_fechamento, data_fechamento,engine):
    with engine.connect() as conn: 
        update_sql = """
        UPDATE dados_manutencao
        SET `status` = :status,
            `Data Fechamento/Hora` = :data_fechamento    
        WHERE `Código` = :codigo
        """
        
        params = {
            'status': status,
            'codigo': codigo_fechamento, 
            'data_fechamento': data_fechamento
        }
        
        conn.execute(text(update_sql), params) 

        conn.connection.commit()

def fetch_data(_engine):
    query_dados = "SELECT * FROM dados_manutencao"
    dados = pd.read_sql(query_dados, engine)

    return dados


engine = get_db_connection()

st.image('logo.png', width= 150)


with st.sidebar:
    selected = option_menu(
            "Selecione uma das Opções",
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
        st.markdown("<h3 style='font-size:26px;text-align:center;'>Abrir OSM</h3>",unsafe_allow_html=True)

        codigo = st.text_input('Código Máquina ou Nome Máquina')
        
        data_abertura = dt.datetime.now(pytz.timezone('Brazil/East'))
        data_abertura = data_abertura.strftime("%Y/%m/%d %H:%M:%S")

        data_abertura_input = st.text_input('Data Abertura', data_abertura)

        tipo_manutencao = st.selectbox('Tipo de Manutenção', ('CORRETIVA', 'PREVENTIVA'))

        descricao = st.text_area('Descrição de Falha', height=100)

        motivo = st.text_area('Motivo da falha', height=100)

        acao = st.text_area('Ação de Correção', height=100)

        materiais = st.text_area('Materiais Necessários', height=100)

        custo = st.text_input('Custo')

        status = 0

        submitted = st.form_submit_button("Abrir OSM")

        if submitted:
            insert_data_to_db(codigo, data_abertura_input, tipo_manutencao, descricao, acao, materiais, custo,motivo, engine)
            st.success("OSM registrada com sucesso!")
            streamlit_js_eval(js_expressions="parent.window.location.reload()")

        codigo = None
        data_abertura_input = None
        tipo_manutencao = None
        descricao = None
        acao = None
        materiais = None
        custo = None
        status = None

elif selected == "FECHAR ORDEM DE SERVIÇO DE MANUTENÇÃO":

    dados = fetch_data(engine)

    dados = dados[dados['status'] == 0]

    with st.form('my_form_2',clear_on_submit=True):
        st.markdown("<h3 style='font-size:26px;text-align:center;'>Fechar OSM</h3>",unsafe_allow_html=True)
        data_fechamento = dt.datetime.now(pytz.timezone('Brazil/East'))
        data_fechamento = data_fechamento.strftime("%Y/%m/%d %H:%M:%S")
        
        codigo_fechamento = st.selectbox('Código Máquina ou Nome Máquina', dados['Código'].unique())
        data_fechamento_input = st.text_input('Data Fechamento', data_fechamento)

        status = 1

        submitted_2 = st.form_submit_button("Submit")

        if submitted_2:
            insert_status_to_db(status,codigo_fechamento, data_fechamento,engine)
            st.success("OSM registrada com sucesso!")
            streamlit_js_eval(js_expressions="parent.window.location.reload()")



