"""
Os dois modelos XGBoost encadeados que formam o previsor.

A ideia do encadeamento: prever chuva tem duas perguntas dentro
dela. Esta chovendo agora, sim ou nao, e uma pergunta de deteccao.
Chovendo, quantos milimetros por hora, e uma pergunta de intensidade.

Por isso o classificador treina em todos os minutos, mas o regressor
treina so nos minutos com chuva de verdade. Se ele visse a massa de
minutos secos, o zero puxaria as previsoes para baixo. Na hora de
prever, o classificador decide primeiro: minuto seco recebe taxa
zero direto, minuto chuvoso passa pelo regressor.
"""

import numpy as np
from xgboost import XGBClassifier, XGBRegressor


class PrevisorDeChuva:
    """Classificador de evento e regressor de intensidade, juntos."""

    def __init__(self, n_estimators=600):
        # hist e o metodo rapido de crescimento de arvores, e o
        # enable_categorical deixa estacao e clima entrarem como
        # categoria de verdade, sem one-hot manual
        self._parametros = dict(
            n_estimators=n_estimators,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            tree_method="hist",
            enable_categorical=True,
            early_stopping_rounds=30,
            random_state=42,
        )
        self.classificador = None
        self.regressor = None
        self.limiar = 0.5

    def treinar(self, X_treino, y_evento, y_taxa, X_val, y_evento_val, y_taxa_val):
        """Treina os dois modelos com parada antecipada na validacao."""

        # neste dataset os minutos com chuva sao quase metade, entao o
        # peso fica proximo de 1, mas calcular protege contra versoes
        # futuras do benchmark com chuva mais rara
        positivos = int(y_evento.sum())
        negativos = len(y_evento) - positivos
        peso = negativos / max(positivos, 1)

        self.classificador = XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=peso,
            **self._parametros,
        )
        self.classificador.fit(
            X_treino, y_evento,
            eval_set=[(X_val, y_evento_val)],
            verbose=False,
        )

        # o regressor so ve minutos chuvosos, no treino e na validacao
        chuva_treino = y_evento == 1
        chuva_val = y_evento_val == 1

        self.regressor = XGBRegressor(
            objective="reg:squarederror",
            eval_metric="rmse",
            **self._parametros,
        )
        self.regressor.fit(
            X_treino[chuva_treino], y_taxa[chuva_treino],
            eval_set=[(X_val[chuva_val], y_taxa_val[chuva_val])],
            verbose=False,
        )

        # o limiar de decisao vem da validacao, nao do 0.5 padrao
        probabilidades = self.classificador.predict_proba(X_val)[:, 1]
        self.limiar = self._escolher_limiar(probabilidades, y_evento_val.to_numpy())

    def _escolher_limiar(self, probabilidades, y_verdadeiro):
        """Varre limiares e devolve o que maximiza o F1 na validacao."""
        melhor_limiar = 0.5
        melhor_f1 = -1.0

        for limiar in np.arange(0.05, 0.96, 0.05):
            previsto = probabilidades >= limiar
            verdadeiros = np.logical_and(previsto, y_verdadeiro == 1).sum()
            if verdadeiros == 0:
                continue
            precisao = verdadeiros / previsto.sum()
            revocacao = verdadeiros / (y_verdadeiro == 1).sum()
            f1 = 2 * precisao * revocacao / (precisao + revocacao)
            if f1 > melhor_f1:
                melhor_f1 = f1
                melhor_limiar = float(limiar)

        return melhor_limiar

    def prever(self, X):
        """
        Devolve (evento, taxa, probabilidade) para cada linha de X.

        Minutos abaixo do limiar recebem taxa zero. Nos demais a taxa
        vem do regressor, presa no chao fisico de zero porque perto
        do limite ele pode devolver valores levemente negativos.
        """
        probabilidade = self.classificador.predict_proba(X)[:, 1]
        evento = (probabilidade >= self.limiar).astype(int)

        taxa = np.zeros(len(X), dtype=np.float64)
        chuvosos = evento == 1
        if chuvosos.any():
            taxa[chuvosos] = np.maximum(self.regressor.predict(X[chuvosos]), 0.0)

        return evento, taxa, probabilidade

    def importancias(self):
        """
        Devolve as importancias por ganho dos dois modelos, cada uma
        como lista de pares (feature, ganho) ja ordenada.
        """
        resultado = {}
        modelos = {"classificador": self.classificador, "regressor": self.regressor}
        for nome, modelo in modelos.items():
            ganhos = modelo.get_booster().get_score(importance_type="gain")
            resultado[nome] = sorted(ganhos.items(), key=lambda par: par[1], reverse=True)
        return resultado
