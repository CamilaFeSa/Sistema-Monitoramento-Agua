
import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
from sklearn.model_selection import train_test_split


# 1. Carregar a base de dados
caminho_excel = "BASE_DADOS_TURBIDEZ_PH_TDS.xlsx"

if not os.path.exists(caminho_excel):
    print(f"ERRO: Arquivo '{caminho_excel}' não encontrado!")
    raise SystemExit(1)

print("1. Carregando base de dados da CETESB...")

xls = pd.ExcelFile(caminho_excel)
dfs = []

for sheet in xls.sheet_names:
    print(f"   - Lendo aba: {sheet}...")
    dfs.append(pd.read_excel(xls, sheet_name=sheet))

df_bruto = pd.concat(dfs, ignore_index=True)

print(f"   Total de registros brutos: {len(df_bruto):,}")


# 2. Tratamento dos dados
print("\n2. Processando pH, Turbidez e TDS...")

df_bruto["valor_num"] = pd.to_numeric(
    df_bruto["Resultado_Texto"],
    errors="coerce"
)

if "Resultado_numerico" in df_bruto.columns:
    valor_alternativo = pd.to_numeric(
        df_bruto["Resultado_numerico"],
        errors="coerce"
    )

    df_bruto["valor_num"] = df_bruto["valor_num"].fillna(
        valor_alternativo
    )

df_clean = df_bruto.dropna(subset=["valor_num"]).copy()

param_map = {
    "pH": "ph",
    "Turbidez": "turbidez",
    "Sólido Dissolvido Total": "tds"
}

df_clean["param"] = df_clean["Parametro"].map(param_map)
df_clean = df_clean.dropna(subset=["param"])

pivoted = df_clean.pivot_table(
    index=["CodPonto", "Coleta_Data", "Coleta_Hora"],
    columns="param",
    values="valor_num",
    aggfunc="mean"
).reset_index()

amostras = pivoted.dropna(
    subset=["ph", "turbidez", "tds"]
).copy()

print(f"   Amostras completas: {len(amostras):,}")


# 3. Classificação por regras
def classificar_qualidade(row):
    ph = row["ph"]
    turb = row["turbidez"]
    tds = row["tds"]

    # Classe 2: Crítica
    if (
        ph < 6.0 or ph > 8.5
        or turb > 15.0
        or tds > 1000.0
    ):
        return 2

    # Classe 1: Atenção
    elif (
        ph < 6.5 or ph > 8.0
        or turb > 5.0
        or tds >= 500.0
    ):
        return 1

    # Classe 0: Excelente
    else:
        return 0


amostras["classe"] = amostras.apply(
    classificar_qualidade,
    axis=1
)

X = amostras[["ph", "turbidez", "tds"]]
y = amostras["classe"]


# Função para criar um modelo
def criar_modelo():
    return RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )


# Função para apresentar os resultados
def avaliar_modelo(y_real, y_pred, titulo):

    print(f"\n========== {titulo} ==========")

    print(
        f"Acurácia: "
        f"{accuracy_score(y_real, y_pred) * 100:.2f}%"
    )

    print("\nRelatório de classificação:")

    print(
        classification_report(
            y_real,
            y_pred,
            labels=[0, 1, 2],
            target_names=[
                "Excelente",
                "Atenção",
                "Crítica"
            ],
            zero_division=0
        )
    )

    print("Matriz de confusão:")

    print(
        confusion_matrix(
            y_real,
            y_pred,
            labels=[0, 1, 2]
        )
    )


# 4. Primeira avaliação: divisão aleatória
print("\n3. AVALIAÇÃO COM DIVISÃO ALEATÓRIA")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

modelo_aleatorio = criar_modelo()
modelo_aleatorio.fit(X_train, y_train)

predicoes = modelo_aleatorio.predict(X_test)

avaliar_modelo(
    y_test,
    predicoes,
    "RESULTADOS - DIVISÃO ALEATÓRIA"
)


# 5. Segunda avaliação: divisão temporal
print("\n4. AVALIAÇÃO COM DIVISÃO TEMPORAL")

amostras_temporais = amostras.copy()

amostras_temporais["data_coleta"] = pd.to_datetime(
    pd.to_numeric(amostras_temporais["Coleta_Data"], errors="coerce"),
    unit="D",
    origin="1899-12-30",
    errors="coerce"
)

print("\nVERIFICAÇÃO DAS DATAS:")
print(amostras_temporais["data_coleta"].head(10))
print("\nQuantidade de datas válidas:")
print(amostras_temporais["data_coleta"].notna().sum())
print("\nAnos encontrados:")
print(amostras_temporais["data_coleta"].dt.year.value_counts().sort_index())

amostras_temporais = amostras_temporais.dropna(
    subset=["data_coleta"]
).copy()

amostras_temporais["ano"] = (
    amostras_temporais["data_coleta"].dt.year
)

anos = sorted(amostras_temporais["ano"].unique())

if len(anos) < 2:
    raise ValueError(
        "Não existem anos suficientes para a validação temporal."
    )

# Utiliza aproximadamente 80% dos anos para treinamento
posicao_corte = int(len(anos) * 0.8)
posicao_corte = max(1, min(posicao_corte, len(anos) - 1))

ano_corte = anos[posicao_corte]

treino_temporal = amostras_temporais[
    amostras_temporais["ano"] < ano_corte
]

teste_temporal = amostras_temporais[
    amostras_temporais["ano"] >= ano_corte
]

X_train_temp = treino_temporal[["ph", "turbidez", "tds"]]
y_train_temp = treino_temporal["classe"]

X_test_temp = teste_temporal[["ph", "turbidez", "tds"]]
y_test_temp = teste_temporal["classe"]

print(f"   Anos utilizados: {anos[0]} a {anos[-1]}")
print(f"   Treinamento: até {ano_corte - 1}")
print(f"   Teste: a partir de {ano_corte}")
print(f"   Amostras de treinamento: {len(X_train_temp):,}")
print(f"   Amostras de teste: {len(X_test_temp):,}")

if len(X_train_temp) == 0 or len(X_test_temp) == 0:
    raise ValueError("A divisão temporal gerou um conjunto vazio.")

if y_train_temp.nunique() < 2:
    raise ValueError(
        "O conjunto temporal de treinamento possui menos de "
        "duas classes. É necessário rever o período de corte."
    )

modelo_temporal = criar_modelo()
modelo_temporal.fit(X_train_temp, y_train_temp)

predicoes_temporais = modelo_temporal.predict(X_test_temp)

avaliar_modelo(
    y_test_temp,
    predicoes_temporais,
    "RESULTADOS - DIVISÃO TEMPORAL"
)


# 6. Treinar o modelo final com todos os dados
# Esse será o modelo utilizado pelo FastAPI.
print("\n5. Treinando o modelo final com todas as amostras...")

modelo_final = criar_modelo()
modelo_final.fit(X, y)

joblib.dump(modelo_final, "water_model.pkl")

print("\nModelo final treinado e salvo em water_model.pkl!")
