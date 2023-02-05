import pandas as pd
from tqdm.notebook import tqdm
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.request import urlopen


# レース結果データをスクレイピングする関数
def race_scraping(race_id_list):
    # race_idをkeyにしてDaexpected 2 blank lines, found 1flake8(E302taFrame型を格納
    race_results = {}
    for race_id in race_id_list:
        time.sleep(1)
        try:
            url = "https://db.netkeiba.com/race/" + race_id
            # メインとなるテーブルデータを取得
            df = pd.read_html(url)[0]
            html = requests.get(url)
            html.encoding = "EUC-JP"
            soup = BeautifulSoup(html.text, "html.parser")
            # 天候、レースの種類、コースの長さ、馬場の状態、日付をスクレイピング
            texts = (
                soup.find("div", attrs={"class": "data_intro"}).find_all("p")[0].text
                + soup.find("div", attrs={"class": "data_intro"}).find_all("p")[1].text
            )
            info = re.findall(r'\w+', texts)
            for text in info:
                if text in ["芝", "ダート"]:
                    df["race_type"] = [text] * len(df)
                if "障" in text:
                    df["race_type"] = ["障害"] * len(df)
                if "m" in text:
                    df["course_len"] = [int(re.findall(r"\d+", text)[-1])] * len(df)
                if text in ["良", "稍重", "重", "不良"]:
                    df["ground_state"] = [text] * len(df)
                if text in ["曇", "晴", "雨", "小雨", "小雪", "雪"]:
                    df["weather"] = [text] * len(df)
                if "年" in text:
                    df["date"] = [text] * len(df)
            # 馬ID、騎手IDをスクレイピング
            horse_id_list = []
            horse_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                "a", attrs={"href": re.compile("^/horse")}
            )
            for a in horse_a_list:
                horse_id = re.findall(r"\d+", a["href"])
                horse_id_list.append(horse_id[0])
            jockey_id_list = []
            jockey_a_list = soup.find("table", attrs={"summary": "レース結果"}).find_all(
                "a", attrs={"href": re.compile("^/jockey")}
            )
            for a in jockey_a_list:
                jockey_id = re.findall(r"\d+", a["href"])
                jockey_id_list.append(jockey_id[0])
            df["horse_id"] = horse_id_list
            df["jockey_id"] = jockey_id_list
            # インデックスをrace_idにする
            df.index = [race_id] * len(df)
            race_results[race_id] = df
        # 存在しないrace_idを飛ばす
        except IndexError:
            continue
        # 存在しないrace_idでAttributeErrorになるページもあるので追加
        except AttributeError:
            continue
        # wifiの接続が切れた時などでも途中までのデータを返せるようにする
        except Exception as e:
            print(e)
            break
    # pd.DataFrame型にして一つのデータにまとめる
    race_results_df = pd.concat([race_results[key] for key in race_results])
    return race_results_df


# 馬の過去成績データをスクレイピングする関数
def horse_scraping(horse_id_list):
    # horse_idをkeyにしてDataFrame型を格納
    horse_results = {}
    for horse_id in tqdm(horse_id_list):
        time.sleep(1)
        try:
            url = 'https://db.netkeiba.com/horse/' + horse_id
            df = pd.read_html(url)[3]
            # 受賞歴がある馬の場合、3番目に受賞歴テーブルが来るため、4番目のデータを取得する
            if df.columns[0] == '受賞歴':
                df = pd.read_html(url)[4]
            df.index = [horse_id] * len(df)
            horse_results[horse_id] = df
        except IndexError:
            continue
        except Exception as e:
            print(e)
            break
    # pd.DataFrame型にして一つのデータにまとめる
    horse_results_df = pd.concat([horse_results[key] for key in horse_results])
    return horse_results_df


# 払い戻し表データをスクレイピングする関数
def return_table_scraping(race_id_list):
    return_tables = {}
    for race_id in tqdm(race_id_list):
        time.sleep(1)
        try:
            url = "https://db.netkeiba.com/race/" + race_id

            # 普通にスクレイピングすると複勝やワイドなどが区切られないで繋がってしまう。
            # そのため、改行コードを文字列brに変換して後でsplitする
            f = urlopen(url)
            html = f.read()
            html = html.replace(b'<br />', b'br')
            dfs = pd.read_html(html)

            # dfsの1番目に単勝〜馬連、2番目にワイド〜三連単がある
            df = pd.concat([dfs[1], dfs[2]])

            df.index = [race_id] * len(df)
            return_tables[race_id] = df
        except IndexError:
            continue
        # 存在しないrace_idでAttributeErrorになるページもあるので追加
        except AttributeError:
            continue
        except Exception as e:
            print(e)
            break
    # pd.DataFrame型にして一つのデータにまとめる
    return_tables_df = pd.concat([return_tables[key] for key in return_tables])
    return return_tables_df


# 出馬表のスクレイピングする関数
def shutuba_scraping(race_id_list, date):
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
            if '稍' in text:
                df["ground_state"] = ['稍重'] * len(df)
            if '芝' in text:
                df['race_type'] = ['芝'] * len(df)
            if '障' in text:
                df['race_type'] = ['障害'] * len(df)
            if 'ダ' in text:
                df['race_type'] = ['ダート'] * len(df)
        df['date'] = [date] * len(df)
        # horse_idの取得
        horse_id_list = []
        horse_td_list = soup.find_all("td", attrs={'class': 'HorseInfo'})
        for td in horse_td_list:
            horse_id = re.findall(r'\d+', td.find('a')['href'])[0]
            horse_id_list.append(horse_id)
        # jockey_idの取得
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


# 出馬表のhorse_idが過去データに存在しない場合はエラーになる、出馬表のhorse_idをリストで取得する関数
def shutuba_horse_id_scraping(race_id):
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
