#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import requests
from pathlib import Path
from urllib.parse import urljoin
from lxml import html

# ================== 配置 ==================
UA_POOLS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

HEADERS = {
    'User-Agent': random.choice(UA_POOLS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

session = requests.Session()
session.headers.update(HEADERS)

# ================== 爬虫函数 ==================
def get_hero_link(main_url, hero_name):
    """在首页找到英雄对应的链接"""
    resp = session.get(main_url)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)
    for a in tree.cssselect('div.styles_champions___b7bp a'):
        alt = a.cssselect('span img')[0].get('alt') if a.cssselect('span img') else ''
        if alt == hero_name:
            href = a.get('href')
            return urljoin(main_url, href)
    return None

def get_skin_links(hero_url):
    """在英雄页面获取所有皮肤的图片最终下载链接"""
    resp = session.get(hero_url)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)
    skin_links = []
    for a in tree.cssselect('div.styles_grid__Th2O3 > a'):
        href = a.get('href')
        skin_page_url = urljoin(hero_url, href)
        skin_resp = session.get(skin_page_url)
        skin_resp.raise_for_status()
        skin_tree = html.fromstring(skin_resp.text)
        last_url = skin_tree.cssselect('body link')
        if last_url:
            img_url = last_url[0].get('href')
            if img_url:
                skin_name = a.cssselect('span img')[0].get('alt') if a.cssselect('span img') else 'unknown'
                skin_links.append((skin_name, img_url))
    return skin_links

def download_image(url, save_path):
    """下载图片并保存"""
    resp = session.get(url, headers={**HEADERS, 'Referer': url})
    resp.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(resp.content)

def main():
    print("英雄联盟皮肤下载器")
    print("图片来源：布锅锅联盟宇宙")
    hero = input("请输入英雄中文称号(例如疾风剑豪,不要输入亚索,因为那是英雄名字而非称号)，输入 ALL 下载全部: ").strip()
    if not hero:
        print("英雄名称不能为空")
        return

    save_root = input("请输入图片保存的目录(绝对路径，例如 D:\\LOL_Skins): ").strip()
    if not save_root:
        print("保存路径不能为空")
        return
    # 去除用户可能误输入的引号
    save_root = save_root.strip('\'"')
    save_root = Path(save_root)
    save_root.mkdir(parents=True, exist_ok=True)

    main_url = "https://splash.buguoguo.cn/"

    if hero.upper() == "ALL":
        # 批量模式
        resp = session.get(main_url)
        resp.raise_for_status()
        tree = html.fromstring(resp.text)
        all_heroes = []
        for a in tree.cssselect('div.styles_champions___b7bp a'):
            hero_name = a.cssselect('span img')[0].get('alt') if a.cssselect('span img') else ''
            hero_href = a.get('href')
            if hero_name and hero_href:
                all_heroes.append((hero_name, urljoin(main_url, hero_href)))
        print(f"共发现 {len(all_heroes)} 个英雄")
        for idx, (hero_name, hero_url) in enumerate(all_heroes, 1):
            hero_folder = save_root / hero_name
            if hero_folder.exists() and any(hero_folder.iterdir()):
                print(f"[{idx}/{len(all_heroes)}] 跳过 {hero_name}（已有皮肤）")
                continue
            hero_folder.mkdir(exist_ok=True)
            print(f"[{idx}/{len(all_heroes)}] 正在处理 {hero_name} ...")
            try:
                skin_list = get_skin_links(hero_url)
                for skin_name, img_url in skin_list:
                    filename = f"{skin_name}.jpg"
                    save_path = hero_folder / filename
                    if save_path.exists():
                        continue
                    download_image(img_url, save_path)
                    print(f"  已下载: {skin_name}")
            except Exception as e:
                print(f"  处理 {hero_name} 时出错: {e}")
        print("全部下载完成！")
    else:
        # 单个英雄模式
        hero_url = get_hero_link(main_url, hero)
        if not hero_url:
            print(f"未找到英雄: {hero}")
            return
        hero_folder = save_root / hero
        hero_folder.mkdir(exist_ok=True)
        print(f"开始下载 {hero} ...")
        skin_list = get_skin_links(hero_url)
        for skin_name, img_url in skin_list:
            filename = f"{skin_name}.jpg"
            save_path = hero_folder / filename
            if save_path.exists():
                print(f"跳过已存在: {skin_name}")
                continue
            download_image(img_url, save_path)
            print(f"已下载: {skin_name}")
        print(f"{hero} 皮肤下载完成,共 {len(skin_list)} 张,皮肤来源:布锅锅联盟宇宙")

if __name__ == "__main__":
    main()