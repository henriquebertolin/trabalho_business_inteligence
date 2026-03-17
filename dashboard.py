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
        # Ordenar barras para melhor visualização
        if x == 'total_acumulado' or x == 'total' or x == 'qtd' or x == 'media':
             df = df.sort_values(by=x, ascending=False)
        sns.barplot(data=df, x=x, y=y, hue=hue, palette='viridis')
    
    plt.title(titulo)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("Gerando Dashboards do Data Warehouse...")

    # --- 1. Gasto Total Acumulado por Titular (Pergunta 5.1.1) ---
    q0 = """
    SELECT t.nome_titular, SUM(f.valor_brl) as total_acumulado
    FROM fato_transacao f
    JOIN dim_titular t ON f.id_titular = t.id_titular
    GROUP BY t.nome_titular
    """
    gerar_grafico(q0, 'total_acumulado', 'nome_titular', '1. Gasto Total Acumulado por Titular')

    # --- 2. Quantidade de Transações por Titular (Pergunta 5.1.4) ---
    q4a = """
    SELECT t.nome_titular, COUNT(*) as qtd 
    FROM fato_transacao f 
    JOIN dim_titular t ON f.id_titular = t.id_titular 
    GROUP BY t.nome_titular
    """
    gerar_grafico(q4a, 'qtd', 'nome_titular', '2. Quantidade Total de Transações por Titular')

    # --- 3. Valor Médio por Transação (Pergunta 5.1.4) ---
    q4b = """
    SELECT t.nome_titular, AVG(f.valor_brl) as media 
    FROM fato_transacao f 
    JOIN dim_titular t ON f.id_titular = t.id_titular 
    GROUP BY t.nome_titular
    """
    gerar_grafico(q4b, 'media', 'nome_titular', '3. Valor Médio por Transação (Ticket Médio)')

    # --- 4. Evolução Mensal por Titular (Pergunta 5.1.3) ---
    q1_3 = """
    SELECT t.nome_titular, d.ano || '-' || LPAD(d.mes::text, 2, '0') as periodo, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_titular t ON f.id_titular = t.id_titular
    JOIN dim_data d ON f.id_data = d.id_data
    GROUP BY t.nome_titular, periodo ORDER BY periodo
    """
    gerar_grafico(q1_3, 'periodo', 'total', '4. Evolução Mensal de Gastos por Titular', tipo='line', hue='nome_titular')

    # --- 5. Top 10 Categorias (Pergunta 5.1.2) ---
    q2 = """
    SELECT c.nome_categoria, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_categoria c ON f.id_categoria = c.id_categoria
    WHERE f.valor_brl > 0 GROUP BY c.nome_categoria ORDER BY total DESC LIMIT 10
    """
    gerar_grafico(q2, 'total', 'nome_categoria', '5. Top 10 Categorias em Valor (R$)')

    # --- 6. Principais Estabelecimentos (Pergunta 5.1.5) ---
    q5 = """
    SELECT e.nome_estabelecimento, SUM(f.valor_brl) as total
    FROM fato_transacao f
    JOIN dim_estabelecimento e ON f.id_estabelecimento = e.id_estabelecimento
    GROUP BY e.nome_estabelecimento ORDER BY total DESC LIMIT 10
    """
    gerar_grafico(q5, 'total', 'nome_estabelecimento', '6. Top 10 Estabelecimentos por Valor')

    # --- 7. Comportamento de Parcelamento (Pergunta 5.1.6) ---
    q6 = "SELECT CASE WHEN total_parcelas > 1 THEN 'Parcelado' ELSE 'À Vista' END as tipo, COUNT(*) as qtd FROM fato_transacao f GROUP BY tipo"
    gerar_grafico(q6, 'tipo', 'qtd', '7. Compras à Vista vs Parceladas', is_pie=True)

    # --- 8. Volume por Dia da Semana (Pergunta 5.1.7) ---
    q7 = "SELECT d.dia_semana, SUM(f.valor_brl) as volume FROM fato_transacao f JOIN dim_data d ON f.id_data = d.id_data GROUP BY d.dia_semana ORDER BY volume DESC"
    gerar_grafico(q7, 'dia_semana', 'volume', '8. Volume de Gastos por Dia da Semana')

    # --- 9. Impacto de Estornos e Créditos (Pergunta 5.1.8) ---
    q8 = """
    SELECT t.nome_titular, ABS(SUM(f.valor_brl)) as total_estornos
    FROM fato_transacao f
    JOIN dim_titular t ON f.id_titular = t.id_titular
    WHERE f.valor_brl < 0 GROUP BY t.nome_titular
    """
    gerar_grafico(q8, 'total_estornos', 'nome_titular', '9. Total de Estornos/Créditos Recuperados por Titular')

    print("Dashboards finalizados.")