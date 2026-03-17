import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# 1. Conexão com o Data Warehouse
engine = create_engine('postgresql://postgres:masterkey@localhost:5432/business')

sns.set_theme(style="whitegrid")

def gerar_grafico(query, x, y, titulo, tipo='bar', hue=None, is_pie=False):
    df = pd.read_sql(query, engine)
    if df.empty:
        print(f"Sem dados para: {titulo}")
        return

    plt.figure(figsize=(12, 6))
    if is_pie:
        plt.pie(df[y], labels=df[x], autopct='%1.1f%%', startangle=140)
    elif tipo == 'line':
        sns.lineplot(data=df, x=x, y=y, hue=hue, marker='o')
        plt.xticks(rotation=45)
    else:
        sns.barplot(data=df, x=x, y=y, hue=hue, palette='viridis')
    
    plt.title(titulo)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 1 & 3. Gasto Total por Titular e Evolução Mensal [cite: 122, 124]
    q1_3 = """
    SELECT t.nome_titular, d.ano || '-' || LPAD(d.mes::text, 2, '0') as periodo, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_titular t ON f.id_titular = t.id_titular
    JOIN dim_data d ON f.id_data = d.id_data
    GROUP BY t.nome_titular, periodo ORDER BY periodo
    """
    gerar_grafico(q1_3, 'periodo', 'total', 'Evolução Mensal por Titular', tipo='line', hue='nome_titular')

    # 2. Top 10 Categorias [cite: 123]
    q2 = """
    SELECT c.nome_categoria, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_categoria c ON f.id_categoria = c.id_categoria
    WHERE f.valor_brl > 0 GROUP BY c.nome_categoria ORDER BY total DESC LIMIT 10
    """
    gerar_grafico(q2, 'total', 'nome_categoria', 'Top 10 Categorias em Valor')

    # 4a. Quantidade de Transações por Titular 
    q4a = "SELECT t.nome_titular, COUNT(*) as qtd FROM fato_transacao f JOIN dim_titular t ON f.id_titular = t.id_titular GROUP BY t.nome_titular"
    gerar_grafico(q4a, 'nome_titular', 'qtd', 'Quantidade de Transações por Titular')

    # 4b. Valor Médio por Transação 
    q4b = "SELECT t.nome_titular, AVG(f.valor_brl) as media FROM fato_transacao f JOIN dim_titular t ON f.id_titular = t.id_titular GROUP BY t.nome_titular"
    gerar_grafico(q4b, 'nome_titular', 'media', 'Valor Médio por Transação (R$)')

    # 5. Principais Estabelecimentos (Top 10) 
    q5 = """
    SELECT e.nome_estabelecimento, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_estabelecimento e ON f.id_estabelecimento = e.id_estabelecimento
    GROUP BY e.nome_estabelecimento ORDER BY total DESC LIMIT 10
    """
    gerar_grafico(q5, 'total', 'nome_estabelecimento', 'Top 10 Estabelecimentos por Valor')

    # 6. Comportamento de Parcelamento [cite: 128]
    q6 = "SELECT CASE WHEN total_parcelas > 1 THEN 'Parcelado' ELSE 'À Vista' END as tipo, COUNT(*) as qtd FROM fato_transacao f GROUP BY tipo"
    gerar_grafico(q6, 'tipo', 'qtd', 'Compras à Vista vs Parceladas', is_pie=True)

    # 7. Volume por Dia da Semana [cite: 130]
    q7 = "SELECT d.dia_semana, SUM(f.valor_brl) as volume FROM fato_transacao f JOIN dim_data d ON f.id_data = d.id_data GROUP BY d.dia_semana ORDER BY volume DESC"
    gerar_grafico(q7, 'dia_semana', 'volume', 'Volume de Gastos por Dia da Semana')

    # 8. Impacto de Estornos e Créditos 
    q8 = """
    SELECT t.nome_titular, ABS(SUM(f.valor_brl)) as total_estornos
    FROM fato_transacao f
    JOIN dim_titular t ON f.id_titular = t.id_titular
    WHERE f.valor_brl < 0 GROUP BY t.nome_titular
    """
    gerar_grafico(q8, 'nome_titular', 'total_estornos', 'Total de Estornos/Créditos por Titular')