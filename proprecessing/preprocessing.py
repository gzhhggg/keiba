import pandas as pd
import datetime

# レース結果の前処理関数
def race_preprocessing(race_results):
    df = race_results.copy()
    # 着順に数字以外の文字列が含まれているものを取り除く
    df['着順'] = pd.to_numeric(df['着順'], errors='coerce')
    df.dropna(subset=['着順'], inplace=True)
    df['着順'] = df['着順'].astype(int)
    df['rank'] = df['着順'].map(lambda x:1 if x<4 else 0)

    # 性齢を性と年齢に分ける
    df["gender"] = df["性齢"].map(lambda x: str(x)[0])
    df["age"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)

    # 馬体重を体重と体重変化に分ける
    df["weight"] = df["馬体重"].str.split("(", expand=True)[0]
    df["change_weight"] = df["馬体重"].str.split("(", expand=True)[1].str[:-1]
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    df['change_weight'] = pd.to_numeric(df['change_weight'], errors='coerce')
    df.dropna(subset=['weight',"change_weight"], inplace=True)
    df["weight"] = df["weight"].astype(int)
    df["change_weight"] = df["change_weight"].astype(int)
    
    #出走数追加
    df['n_horses'] = df.index.map(df.index.value_counts())

    # 単勝をfloatに変換
    df["単勝"] = df["単勝"].astype(float)

    # 距離は10の位を切り捨てる
    df["course_len"] = df["course_len"].astype(float) // 100

    # 人気をfloatに変換
    df["人気"] = df["人気"].astype(float)

    # 日付をdatetimeに変更
    df["date"] = pd.to_datetime(df["date"], format="%Y年%m月%d日")

    # 枠番をintに変更
    df["枠番"] = df["枠番"].astype(int)

    # 不要な列を削除
    df.drop(["タイム", "着差", "調教師", "性齢", "馬体重", '馬名', '騎手', '着順'], axis=1, inplace=True)
    #開催場所
    df['place'] = df.index.map(lambda x:str(x)[4:6])
	
    return df

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