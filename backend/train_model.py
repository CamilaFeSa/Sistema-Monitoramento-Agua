import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

caminho_excel = "BASE_DADOS_TURBIDEZ_PH_TDS.xlsx"

if not os.path.exists(caminho_excel):
    print(f"ERRO: Ficheiro '{caminho_excel}' não encontrado na pasta backend!")
    print("Por favor, coloque o ficheiro .xlsx dentro do diretório 'backend'.")
    exit()

print("1. A carregar base de dados real da CETESB (1978-2024)...")
xls = pd.ExcelFile(caminho_excel)

dfs = []
for sheet in xls.sheet_names:
    print(f"   - A ler aba: {sheet}...")
    df_sheet = pd.read_excel(xls, sheet_name=sheet)
    dfs.append(df_sheet)

df_bruto = pd.concat(dfs, ignore_index=True)
print(f"   Total de registos brutos encontrados: {len(df_bruto):,}")

print("\n2. A processar e a organizar os parâmetros (pH, Turbidez, TDS)...")
df_bruto["valor_num"] = pd.to_numeric(
    df_bruto["Resultado_Texto"], errors="coerce"
)
if "Resultado_numerico" in df_bruto.columns:
    df_bruto["valor_num"] = df_bruto["valor_num"].fillna(
        df_bruto["Resultado_numerico"]
    )

df_clean = df_bruto.dropna(subset=["valor_num"]).copy()

param_map = {
    "pH": "ph",
    "Turbidez": "turbidez",
    "Sólido Dissolvido Total": "tds",
}
df_clean["param"] = df_clean["Parametro"].map(param_map)

pivoted = df_clean.pivot_table(
    index=["CodPonto", "Coleta_Data", "Coleta_Hora"],
    columns="param",
    values="valor_num",
    aggfunc="mean",
).reset_index()

amostras = pivoted.dropna(subset=["ph", "turbidez", "tds"]).copy()
print(f"   Amostras completas e válidas para treino: {len(amostras):,} linhas")


# 3. Regra de Rotulagem alinhada à Faixa de Referência do sistema (água doce)
def classificar_qualidade(row):
    ph = row["ph"]
    turb = row["turbidez"]
    tds = row["tds"]

    # 2 = Fora da faixa de referência
    if ph < 6.0 or ph > 9.0 or turb > 100.0 or tds > 500.0:
        return 2
    # 1 = No limite da faixa de referência (próximo às bordas)
    elif ph < 6.3 or ph > 8.7 or turb > 80.0 or tds > 400.0:
        return 1
    # 0 = Dentro da faixa de referência
    else:
        return 0


amostras["classe"] = amostras.apply(classificar_qualidade, axis=1)
print("   Distribuição das classes na base:")
print(amostras["classe"].value_counts().sort_index().to_dict())

X = amostras[["ph", "turbidez", "tds"]]
y = amostras["classe"]

print("\n3. A treinar o algoritmo Random Forest Classifier...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acuracia = accuracy_score(y_test, y_pred)
print(f"   Acurácia do modelo treinado: {acuracia * 100:.2f}%")

joblib.dump(model, "water_model.pkl")
print(
    "\n✅ Modelo de IA treinado com DADOS REAIS de SP e salvo com sucesso em"
    " 'water_model.pkl'!"
)