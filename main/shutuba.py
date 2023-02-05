import pandas as pd
import numpy as np
import datetime
from tqdm.notebook import tqdm
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.request import urlopen
from itertools import combinations, permutations
import matplotlib.pyplot as plt

def shutuba_scrape(race_id_list, date):
    data = pd.DataFrame()
    for race_id in tqdm(race_id_list):
        time.sleep(1)
        url = 'https://race.netkeiba.com/race/shutuba.html?race_id=' + race_id
        df = pd.read_html(url)[0]

        # 列名に半角スペースがあれば除去する
        df = df.rename(columns=lambda x: x.replace(' ', ''))

        df = df.T.reset_index(level=0, drop=True).T

        html = requests.get(url)
        html.encoding = "EUC-JP"
        soup = BeautifulSoup(html.text, "html.parser")
        texts = soup.find('div', attrs={'class': 'RaceData01'}).text
        texts = re.findall(r'\w+', texts)
        for text in texts:
            if 'm' in text:
                df['course_len'] = [int(re.findall(r'\d+', text)[-1])] * len(df)
            if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
                df["weather"] = [text] * len(df)
            if text in ["良", "稍重", "重"]:
                df["ground_state"] = [text] * len(df)
            if '不' in text:
                df["ground_state"] = ['不良'] * len(df)
            # 2020/12/13追加
            if '稍' in text:
                df["ground_state"] = ['稍重'] * len(df)
            if '芝' in text:
                df['race_type'] = ['芝'] * len(df)
            if '障' in text:
                df['race_type'] = ['障害'] * len(df)
            if 'ダ' in text:
                df['race_type'] = ['ダート'] * len(df)
        df['date'] = [date] * len(df)

        # horse_id
        horse_id_list = []
        horse_td_list = soup.find_all("td", attrs={'class': 'HorseInfo'})
        for td in horse_td_list:
            horse_id = re.findall(r'\d+', td.find('a')['href'])[0]
            horse_id_list.append(horse_id)
        # jockey_id
        jockey_id_list = []
        jockey_td_list = soup.find_all("td", attrs={'class': 'Jockey'})
        for td in jockey_td_list:
            jockey_id = re.findall(r'\d+', td.find('a')['href'])[0]
            jockey_id_list.append(jockey_id)
        df['horse_id'] = horse_id_list
        df['jockey_id'] = jockey_id_list
        df.index = [race_id] * len(df)
        data = pd.concat([data, df])
    # 出走取り消しの馬を除外
    data = data[data["印"] != "取消"]
    return data

def shutuba_scraping_horse_id(race_id):
    url = 'https://race.netkeiba.com/race/shutuba.html?race_id=' + race_id
    html = requests.get(url)
    html.encoding = "EUC-JP"
    soup = BeautifulSoup(html.text, "html.parser")
    horse_id_list = []
    horse_td_list = soup.find_all("td", attrs={'class': 'HorseInfo'})
    for td in horse_td_list:
      horse_id = re.findall(r'\d+', td.find('a')['href'])[0]
      horse_id_list.append(horse_id)
    return horse_id_list

def shutuba_preprocessing(data):
    df = data.copy()
    
    df["gender"] = df["性齢"].map(lambda x: str(x)[0])
    df["age"] = df["性齢"].map(lambda x: str(x)[1:]).astype(int)

    # 馬体重を体重と体重変化に分ける
    df = df[df["馬体重(増減)"] != '--']
    df["weight"] = df["馬体重(増減)"].str.split("(", expand=True)[0].astype(int)
    df["change_weight"] = df["馬体重(増減)"].str.split("(", expand=True)[1].str[:-1]
    df['change_weight'] = pd.to_numeric(df['change_weight'], errors='coerce')
    
    df["date"] = pd.to_datetime(df["date"])
    
    df['枠番'] = df['枠'].astype(int)
    df['馬番'] = df['馬番'].astype(int)
    df['斤量'] = df['斤量'].astype(int)
    df['place'] = df.index.map(lambda x:str(x)[4:6])
    df["place"] = df["place"].astype(int)
    
    #6/6出走数追加
    df['n_horses'] = df.index.map(df.index.value_counts())

    # 距離は10の位を切り捨てる
    df["course_len"] = df["course_len"].astype(float) // 100

    # 使用する列を選択
    df = df[['枠番', '馬番', '斤量', "人気", 'course_len', 'weather',
       'race_type', 'ground_state', 'date', 'horse_id', 'jockey_id',
       'gender', 'age', 'weight', 'change_weight', 'n_horses', 'place']]
    return df