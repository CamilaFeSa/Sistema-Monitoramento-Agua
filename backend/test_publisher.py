import json
import random
import os
import paho.mqtt.client as mqtt
import pandas as pd

excel_path = "BASE_DADOS_TURBIDEZ_PH_TDS.xlsx"

# 1. Carregar e preparar amostras reais da CETESB
if not os.path.exists(excel_path):
    print(f"ERRO: Base '{excel_path}' não encontrada!")
    exit()

print("A carregar amostras reais da CETESB para o simulador...")
xls = pd.ExcelFile(excel_path)
dfs = [pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names]
df_bruto = pd.concat(dfs, ignore_index=True)

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

amostras_reais = pivoted.dropna(
    subset=["ph", "turbidez", "tds"]
).reset_index(drop=True)

# 2. Sortear UMA amostra real da base de dados de São Paulo
amostra = amostras_reais.sample(1).iloc[0]

payload = {
    "ph": round(float(amostra["ph"]), 2),
    "turbidez": round(float(amostra["turbidez"]), 2),
    "tds": round(float(amostra["tds"]), 1),
}

# 3. Publicar via MQTT para a API
broker = "localhost"
port = 1883
topic = "tcc/sensores/agua"

client = mqtt.Client()
client.connect(broker, port)
client.publish(topic, json.dumps(payload))

print(
    f"\n✅ Amostra REAL da CETESB enviada (Ponto: {amostra['CodPonto']}):"
)
print(f"   Payload: {payload}")