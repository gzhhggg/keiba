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
    df.drop(["タイム", "着差", "調教師", "性齢", "馬体重", '馬名', '騎手'], axis=1, inplace=True)
    #開催場所
    df['place'] = df.index.map(lambda x:str(x)[4:6])
	
    return df

# 馬情報の前処理
def horse_preprocessing(horse_results):
  df = horse_results[['日付', '着順', '賞金', "頭数"]]

  # 数値以外の欠損値を削除
  df["着順"] = pd.to_numeric(df["着順"], errors="coerce")
  df.dropna(subset=["着順"], inplace=True)
  df["着順"] = df["着順"].astype(int)

  # 賞金のNANを0で埋める
  df["賞金"].fillna(0, inplace=True)

  # (1 - 着順/頭数)の計算
  df["着順/頭数"] = (1 - df["着順"] / df["頭数"]) * 100

  # 日付型に変換
  df["date"] = pd.to_datetime(df["日付"])
  df.drop(["日付"], axis=1, inplace=True)
  return df

# 馬情報とレース情報をマージする関数
def merge_race_with_horse(race_results, horse_results, n_samples={3, 5, 7, "all"}):
  df_r = race_results.copy()
  df_h = horse_results.copy()
  date_list = df_r["date"].unique()
  for n_sample in n_samples:
    merged_all_df = pd.DataFrame()
    for date in date_list:
      df = df_r[df_r["date"] == date]
      horse_id_list = df["horse_id"]
      target_df = df_h.loc[horse_id_list]
      if n_sample == "all":
        filtered_df = target_df[target_df["date"] < date]
      else:
        filtered_df = target_df[target_df["date"] < date].sort_values("date", ascending = False).groupby(level=0).head(n_sample)
      average_df = filtered_df.groupby(level=0)[["着順", "賞金", "着順/頭数"]].mean()
      average_df.rename(columns={"着順":"着順_{}R".format(n_sample), "賞金":"賞金_{}R".format(n_sample) ,"着順/頭数":"着順/頭数_{}R".format(n_sample)},inplace=True)
      merged_df = pd.merge(df, average_df, how="left", left_on="horse_id", right_index=True)
      merged_all_df = pd.concat([merged_all_df, merged_df])
    df_r = merged_all_df.copy()
  return df_r

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