import pandas as pd
import glob
import os
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:masterkey@localhost:5432/business')

caminho_arquivos = './' 
todos_arquivos = glob.glob(os.path.join(caminho_arquivos, "Fatura_*.csv"))
df_lista = [pd.read_csv(f, sep=';', encoding='utf-8') for f in todos_arquivos]
df_bruto = pd.concat(df_lista, ignore_index=True)

df_bruto['Data de Compra'] = pd.to_datetime(df_bruto['Data de Compra'], dayfirst=True)
df_bruto['Categoria'] = df_bruto['Categoria'].fillna('Não categorizado').replace('-', 'Não categorizado')

def tratar_parcelas(texto):
    if '/' in str(texto):
        p = texto.split('/')
        return int(p[0]), int(p[1])
    return 1, 1
df_bruto['num_parcela'], df_bruto['total_parcelas'] = zip(*df_bruto['Parcela'].apply(tratar_parcelas))

# --- CRIAÇÃO DAS DIMENSÕES ---

# DIM_TITULAR
dim_titular = df_bruto[['Nome no Cartão', 'Final do Cartão']].drop_duplicates().reset_index(drop=True)
dim_titular.columns = ['nome_titular', 'final_cartao']
dim_titular.index.name = 'id_titular'
dim_titular = dim_titular.reset_index()

# DIM_CATEGORIA
dim_categoria = df_bruto[['Categoria']].drop_duplicates().reset_index(drop=True)
dim_categoria.columns = ['nome_categoria']
dim_categoria.index.name = 'id_categoria'
dim_categoria = dim_categoria.reset_index()

# DIM_ESTABELECIMENTO
dim_estab = df_bruto[['Descrição']].drop_duplicates().reset_index(drop=True)
dim_estab.columns = ['nome_estabelecimento']
dim_estab.index.name = 'id_estabelecimento'
dim_estab = dim_estab.reset_index()

# DIM_DATA
dim_data = pd.DataFrame({'data': df_bruto['Data de Compra'].unique()})
dim_data['dia'] = dim_data['data'].dt.day
dim_data['mes'] = dim_data['data'].dt.month
dim_data['ano'] = dim_data['data'].dt.year
dim_data['trimestre'] = dim_data['data'].dt.quarter
dim_data['dia_semana'] = dim_data['data'].dt.day_name() # Ou .dt.weekday para números
dim_data.index.name = 'id_data'
dim_data = dim_data.reset_index()

fato = df_bruto.merge(dim_titular, left_on=['Nome no Cartão', 'Final do Cartão'], right_on=['nome_titular', 'final_cartao']) \
               .merge(dim_categoria, left_on='Categoria', right_on='nome_categoria') \
               .merge(dim_estab, left_on='Descrição', right_on='nome_estabelecimento') \
               .merge(dim_data, left_on='Data de Compra', right_on='data')

fato_final = fato[['id_data', 'id_titular', 'id_categoria', 'id_estabelecimento', 
                   'num_parcela', 'total_parcelas', 'Valor (em R$)', 'Valor (em US$)', 'Cotação (em R$)']]
fato_final.columns = ['id_data', 'id_titular', 'id_categoria', 'id_estabelecimento', 
                      'num_parcela', 'total_parcelas', 'valor_brl', 'valor_usd', 'cotacao']

dim_titular.to_sql('dim_titular', engine, if_exists='replace', index=False)
dim_categoria.to_sql('dim_categoria', engine, if_exists='replace', index=False)
dim_estab.to_sql('dim_estabelecimento', engine, if_exists='replace', index=False)
dim_data.to_sql('dim_data', engine, if_exists='replace', index=False)
fato_final.to_sql('fato_transacao', engine, if_exists='replace', index=False)

print("Data Warehouse atualizado com o Modelo Estrela completo!")