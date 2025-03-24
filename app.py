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
import plotly.express as px

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

header_styles = {
    'selector': 'th.col_heading',
    'props': [('background-color', 'grey'), 
              ('color', 'black'),
              ('font-size', '18px'),
              ('font-weight', 'bold')]
}

engine = get_db_connection()
st.set_page_config(layout="wide")
st.image('logo.png', width= 150)

with st.sidebar:
    selected = option_menu(
            "Selecione uma das Opções",
            [
                "ABRIR ORDEM DE SERVIÇO DE MANUTENÇÃO",
                "FECHAR ORDEM DE SERVIÇO DE MANUTENÇÃO",
                "ACOMPANHAMENTO OSM"
            ],
            icons=[ "list-task","list-task","list-task"],
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

elif selected == "ACOMPANHAMENTO OSM":
    df = fetch_data(engine)
    
    df.sort_values(by = 'Data Abertura/Hora', ascending = False, ignore_index=True, inplace = True)

    target_year = st.selectbox("Selecione o ano desejado", df["Data Abertura/Hora"].dropna().dt.year.astype(int).sort_values().unique(), key=2, index=1, placeholder='Escolha uma opção')

    df = df[df['Data Abertura/Hora'].dt.year == target_year]

    mask_1 = df['status'] == 1
    slice_1 = pd.IndexSlice[mask_1[mask_1].index, ['Código', 'Data Abertura/Hora', 'Data Fechamento/Hora', 'Descrição da Falha', 'Tipo de Manutenção', 'Motivo da Falha', 'Ação de correção', 'Materiais necessários', 'Custo']] 

    mask_2 = df['status'] == 0
    slice_2 = pd.IndexSlice[mask_2[mask_2].index, ['Código', 'Data Abertura/Hora', 'Data Fechamento/Hora', 'Descrição da Falha', 'Tipo de Manutenção', 'Motivo da Falha', 'Ação de correção', 'Materiais necessários', 'Custo']] 

    df['month'] = df['Data Abertura/Hora'].dt.month 

    custo_total_anual = df['Custo'].sum()

    st.metric(label = f'Custo Anual Total {target_year}',value = f'R${custo_total_anual:.2f}')

    col1, col2 = st.columns(2)

    df_group_month = df.groupby('month', as_index=False)['Custo'].sum()

    df_group_month['Custo_label'] = df_group_month['Custo'].apply(lambda x: f"R${x:.2f}")

    fig_1 = px.bar(df_group_month,x = 'month', y = 'Custo',title= 'Custo Mensal de Manutenção',text='Custo_label', width=800, height=600)
    fig_1.update_traces(textfont_size=16, textangle=0, textposition="outside", cliponaxis=False, marker_color='#e53737', )
    fig_1.update_layout(yaxis_title = 'Custo (R$)', xaxis_title = 'Mês', title_x = 0.55, title_y = 0.95,title_xanchor = 'center',xaxis=dict(tickfont=dict(size=14)),title=dict(font=dict(size=16)), showlegend=False)
    fig_1.update_xaxes(tickmode='linear',dtick=1)

    col1.plotly_chart(fig_1)

    df_group_month_size = df.groupby('month', as_index=False).size()

    fig_2 = px.bar(df_group_month_size,x = 'month', y = 'size',title= 'Quantidade de Manutenções Mensais',text='size', width=800, height=600)
    fig_2.update_traces(textfont_size=16, textangle=0, textposition="outside", cliponaxis=False, marker_color='#e53737', )
    fig_2.update_layout(yaxis_title = 'Quantidade de Manutenções', xaxis_title = 'Mês', title_x = 0.55, title_y = 0.95,title_xanchor = 'center',xaxis=dict(tickfont=dict(size=14)),title=dict(font=dict(size=16)), showlegend=False)
    fig_2.update_xaxes(tickmode='linear',dtick=1)
    fig_2.update_yaxes(tickmode='linear',dtick=1)

    col2.plotly_chart(fig_2)

    df_group_codigo_size = df.groupby('Código', as_index = False).size()

    fig_3 = px.bar(df_group_codigo_size,x = 'Código', y = 'size',title= 'Quantidade de Manutenções por Máquina',text='size', height=600)
    fig_3.update_traces(textfont_size=16, textangle=0, textposition="outside", cliponaxis=False, marker_color='#e53737', )
    fig_3.update_layout(yaxis_title = 'Quantidade de Manutenções', xaxis_title = 'Código', title_x = 0.55, title_y = 0.95,title_xanchor = 'center',xaxis=dict(tickfont=dict(size=14)),title=dict(font=dict(size=16)), showlegend=False)
    fig_3.update_xaxes(tickmode='linear',dtick=1)
    fig_3.update_yaxes(tickmode='linear',dtick=1)

    st.plotly_chart(fig_3)

    st.table(df[['Código', 'Data Abertura/Hora', 'Data Fechamento/Hora', 'Descrição da Falha', 'Tipo de Manutenção', 'Motivo da Falha', 'Ação de correção', 'Materiais necessários', 'Custo']].style.set_table_styles([header_styles]).set_properties(**{'background-color': '#8efaa4'},subset=slice_1).set_properties(**{'background-color': '#fc5b5b'},subset=slice_2))




st.markdown("""
    <style>
    /* Centralizar o conteúdo dentro do label do st.metric */
    [data-testid="stMetricLabel"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Centralizar o conteúdo interno do label */
    [data-testid="stMetricLabel"] div {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }

    /* Centralizar o valor do st.metric */
    [data-testid="stMetricValue"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Centralizar o conteúdo interno do valor */
    [data-testid="stMetricValue"] div {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    /* Centralizar o valor do st.metric */
    [data-testid="stMetricDelta"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Centralizar o conteúdo interno do valor */
    [data-testid="stMetricDelta"] div {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
