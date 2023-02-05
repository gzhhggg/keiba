import pandas as pd


# 3着以内に入る確率を予測
def predict_proba(model, X):
    proba = pd.Series(model.predict_proba(X, axis=1)[:, 1], index=X.index)
    # レース内で標準化して、相対評価する。「レース内偏差値」みたいなもの。
    standard_scaler = lambda x: (x - x.mean()) / x.std(ddof=0)
    proba = proba.groupby(level=0).transform(standard_scaler)
    # データ全体を0~1にする
    # proba = (proba - proba.min()) / (proba.max() - proba.min())
    return proba


# 特徴量の需要度を表示する
def feature_importance(model, X, n_display=20):
    importances = pd.DataFrame({"features": X.columns,
                                "importance": model.feature_importances_})
    return importances.sort_values("importance", ascending=False)[:n_display]


def pred_table(proba, X, return_table):
    df = X.copy()[["着順", "人気", "馬番"]]
    df["proba"] = proba
    df = pd.merge(df, return_table, how="left", left_index=True, right_index=True)
    return df


# 同レースで期待値が1番高い馬にかけた時の期待値
def same_race_return_bets(pred_table, n_samples=100, lower=50, min_threshold=0.5):
    gain = {}
    df = pred_table.copy()
    df = df.reset_index()
    df = df.loc[df.groupby("index")["proba"].idxmax()]
    for i in range(n_samples):
        threshold = 1 * i / n_samples + min_threshold * (1-i/n_samples)
        df_bets = df[df["proba"] > threshold]
        n_bets = len(df_bets)
        money = -100 * n_bets + df_bets[df_bets["着順"] == 1]["return"].sum()
        if n_bets > lower:
            gain[n_bets] = (n_bets*100 + money) / (n_bets*100)
    return pd.Series(gain)


# 期待値がthreshold以上の馬にかけた時の期待値
def race_return_bets(pred_table, n_samples=100, lower=50, min_threshold=0.5):
    gain = {}
    df = pred_table.copy()
    for i in range(n_samples):
        threshold = 1 * i / n_samples + min_threshold * (1-i/n_samples)
        df_bets = df[df["proba"] > threshold]
        n_bets = len(df_bets)
        money = -100 * n_bets + df_bets[df_bets["着順"] == 1]["return"].sum()
        if n_bets > lower:
            gain[n_bets] = (n_bets*100 + money) / (n_bets*100)
    return pd.Series(gain)


# 人気が３位以内ではない馬にかけた時の期待値
def race_return_not_popular_bets(pred_table, n_samples=100, lower=50, min_threshold=0.5):
    gain = {}
    df = pred_table.copy()
    df = df[(df["人気"] != 1) & (df["人気"] != 2) & (df["人気"] != 3)]
    for i in range(n_samples):
        threshold = 1 * i / n_samples + min_threshold * (1-i/n_samples)
        df_bets = df[df["proba"] > threshold]
        n_bets = len(df_bets)
        money = -100 * n_bets + df_bets[df_bets["着順"] == 1]["return"].sum()
        if n_bets > lower:
            gain[n_bets] = (n_bets*100 + money) / (n_bets*100)
    return pd.Series(gain)
