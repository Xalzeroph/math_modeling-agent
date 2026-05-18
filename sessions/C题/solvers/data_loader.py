#!/usr/bin/env python3
"""
C题 — 数据加载与共享模块
使用固定路径避免中文编码问题
"""
import pandas as pd
import numpy as np
import os, glob

SESSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_national_emissions():
    """加载全国日度碳排放时序 (附件1)"""
    pattern = os.path.join(SESSION_DIR, '*附件1*.csv')
    files = glob.glob(pattern)
    df = pd.read_csv(files[0])
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def load_province_emissions():
    """加载 2022 年 30 省碳排放 (附件2)"""
    pattern = os.path.join(SESSION_DIR, '*附件2*.xlsx')
    files = glob.glob(pattern)
    xl = pd.ExcelFile(files[0])
    sheets = [s for s in xl.sheet_names if s != 'NOTE']
    records = []
    for s in sheets:
        df = pd.read_excel(xl, sheet_name=s)
        for i in range(len(df)):
            val = str(df.iloc[i, 0])
            if 'TotalEmissions' in val:
                scope1 = float(df.iloc[i, -1])
                province = s.replace('2022', '')
                records.append({'Province': province, 'CO2_Mt': scope1})
                break
    pdf = pd.DataFrame(records)
    pdf['Province'] = pdf['Province'].str.replace(r'\d+', '', regex=True)
    return pdf

def get_province_gdp_population():
    data = {
        '北京':    {'GDP': 41610, 'Pop': 2184},
        '天津':    {'GDP': 16311, 'Pop': 1363},
        '河北':    {'GDP': 42370, 'Pop': 7420},
        '山西':    {'GDP': 25642, 'Pop': 3481},
        '内蒙古':  {'GDP': 23159, 'Pop': 2401},
        '辽宁':    {'GDP': 28975, 'Pop': 4197},
        '吉林':    {'GDP': 13070, 'Pop': 2347},
        '黑龙江':  {'GDP': 15901, 'Pop': 3099},
        '上海':    {'GDP': 44653, 'Pop': 2475},
        '江苏':    {'GDP': 122876, 'Pop': 8515},
        '浙江':    {'GDP': 77715, 'Pop': 6577},
        '安徽':    {'GDP': 45045, 'Pop': 6127},
        '福建':    {'GDP': 53109, 'Pop': 4188},
        '江西':    {'GDP': 32074, 'Pop': 4528},
        '山东':    {'GDP': 87435, 'Pop': 10163},
        '河南':    {'GDP': 61345, 'Pop': 9872},
        '湖北':    {'GDP': 53735, 'Pop': 5844},
        '湖南':    {'GDP': 48670, 'Pop': 6604},
        '广东':    {'GDP': 129119, 'Pop': 12657},
        '广西':    {'GDP': 26301, 'Pop': 5047},
        '海南':    {'GDP': 6818, 'Pop': 1027},
        '重庆':    {'GDP': 29129, 'Pop': 3213},
        '四川':    {'GDP': 56750, 'Pop': 8374},
        '贵州':    {'GDP': 20165, 'Pop': 3856},
        '云南':    {'GDP': 28954, 'Pop': 4693},
        '西藏':    {'GDP': 2165, 'Pop': 364},
        '陕西':    {'GDP': 32773, 'Pop': 3956},
        '甘肃':    {'GDP': 11202, 'Pop': 2492},
        '青海':    {'GDP': 3610, 'Pop': 595},
        '宁夏':    {'GDP': 5069, 'Pop': 728},
        '新疆':    {'GDP': 17741, 'Pop': 2585},
    }
    return pd.DataFrame(data).T.rename_axis('Province').reset_index()

def get_national_stats():
    """2019-2023 全国宏观数据"""
    stats = {
        2019: {'Pop': 140005, 'GDP': 986515, 'Urban_pct': 60.60, 'Ind2_pct': 38.6, 'Coal_pct': 57.7},
        2020: {'Pop': 141212, 'GDP': 1013567, 'Urban_pct': 63.89, 'Ind2_pct': 37.8, 'Coal_pct': 56.9},
        2021: {'Pop': 141260, 'GDP': 1149237, 'Urban_pct': 64.72, 'Ind2_pct': 39.4, 'Coal_pct': 56.0},
        2022: {'Pop': 141175, 'GDP': 1210207, 'Urban_pct': 65.22, 'Ind2_pct': 39.3, 'Coal_pct': 55.5},
        2023: {'Pop': 140967, 'GDP': 1260582, 'Urban_pct': 66.16, 'Ind2_pct': 38.3, 'Coal_pct': 55.3},
    }
    return pd.DataFrame(stats).T.rename_axis('Year').reset_index()

def get_national_emissions():
    df = load_national_emissions()
    total = df[df['Sector'] == 'Total'].copy()
    total['Year'] = total['Date'].dt.year
    yearly = total.groupby('Year')['CO2 (Mt)'].sum()
    return yearly

def province_name_map():
    return {
        'Shanghai': '上海', 'Yunnan': '云南', 'InnerMongolia': '内蒙古',
        'Beijing': '北京', 'Jilin': '吉林', 'Sichuan': '四川',
        'Tianjin': '天津', 'Ningxia': '宁夏', 'Anhui': '安徽',
        'Shandong': '山东', 'Shanxi': '山西', 'Guangdong': '广东',
        'Guangxi': '广西', 'Xinjiang': '新疆', 'Jiangsu': '江苏',
        'Jiangxi': '江西', 'Hebei': '河北', 'Henan': '河南',
        'Zhejiang': '浙江', 'Hainan': '海南', 'Hubei': '湖北',
        'Hunan': '湖南', 'Gansu': '甘肃', 'Fujian': '福建',
        'Guizhou': '贵州', 'Liaoning': '辽宁', 'Chongqing': '重庆',
        'Shaanxi': '陕西', 'Qinghai': '青海', 'Heilongjiang': '黑龙江',
    }

if __name__ == '__main__':
    pdf = load_province_emissions()
    print("Provinces:", len(pdf))
    print(pdf.head())
    print(f"Total CO2: {pdf['CO2_Mt'].sum():.2f} Mt")
