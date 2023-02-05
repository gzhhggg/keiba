import pandas as pd
import datetime
from sklearn.preprocessing import LabelEncoder

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
  df_r["horse_id"] = df_r["horse_id"].astype(int)
  df_r["jockey_id"] = df_r["jockey_id"].astype(int)
  return df_r

# ダミー変数化して、category型に変更する
def dummy_with_category(le_horse, le_jockey, race_results, train_race_results):
  df = race_results.copy()
  t_df = train_race_results.copy()
  df["horse_id"] = le_horse.transform(df["horse_id"])
  df["jockey_id"] = le_jockey.transform(df["jockey_id"])  
  df["horse_id"] = df["horse_id"].astype("category")
  df["jockey_id"] = df["jockey_id"].astype("category")
  #そのほかのカテゴリ変数をpandasのcategory型に変換してからダミー変数化(出馬表とカラム数を揃えるため)
  weathers = t_df['weather'].unique()
  race_types = t_df['race_type'].unique()
  ground_states = t_df['ground_state'].unique()
  genders = t_df['gender'].unique()
  df['weather'] = pd.Categorical(df['weather'], weathers)
  df['race_type'] = pd.Categorical(df['race_type'], race_types)
  df['ground_state'] = pd.Categorical(df['ground_state'], ground_states)
  df['gender'] = pd.Categorical(df['gender'], genders)
  df = pd.get_dummies(df, columns=['weather', 'race_type', 'ground_state', 'gender'])
  return df

#時系列に沿って訓練データとテストデータに分ける関数
def split_data(df, test_size=0.3):
    sorted_id_list = df.sort_values("date").index.unique()
    train_id_list = sorted_id_list[: round(len(sorted_id_list) * (1 - test_size))]
    test_id_list = sorted_id_list[round(len(sorted_id_list) * (1 - test_size)) :]
    train = df.loc[train_id_list]
    test = df.loc[test_id_list]
    return train, test