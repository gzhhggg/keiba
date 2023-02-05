import pandas as pd
import numpy as np
import datetime
from tqdm.notebook import tqdm

# 払い戻しの前処理
# 単勝
def tansho(df_return):
    tansho = df_return[df_return[0]=='単勝'][[1,2]]
    tansho.columns = ['win', 'return']
    for column in tansho.columns:
        tansho[column] = pd.to_numeric(tansho[column], errors='coerce')
    return tansho

# 複勝
def fukusho(df_return):
    fukusho = df_return[df_return[0]=='複勝'][[1,2]]
    wins = fukusho[1].str.split('br', expand=True)[[0,1,2]]
    wins.columns = ['win_0', 'win_1', 'win_2']
    returns = fukusho[2].str.split('br', expand=True)[[0,1,2]]
    returns.columns = ['return_0', 'return_1', 'return_2']
    df = pd.concat([wins, returns], axis=1)
    for column in df.columns:
        df[column] = df[column].str.replace(',', '')
    return df.fillna(0).astype(int)

#3着以内に入る確率を予測
def predict_proba(model, X, train=True, std=True, minmax=False):
  if train:
    proba = pd.Series(
        model.predict_proba(X.drop(['単勝'], axis=1))[:, 1], index=X.index
    )
  else:
    proba = pd.Series(
        model.predict_proba(X, axis=1)[:, 1], index=X.index
    )
  if std:
    #レース内で標準化して、相対評価する。「レース内偏差値」みたいなもの。
    standard_scaler = lambda x: (x - x.mean()) / x.std(ddof=0)
    proba = proba.groupby(level=0).transform(standard_scaler)
  if minmax:
    #データ全体を0~1にする
    proba = (proba - proba.min()) / (proba.max() - proba.min())
  return proba