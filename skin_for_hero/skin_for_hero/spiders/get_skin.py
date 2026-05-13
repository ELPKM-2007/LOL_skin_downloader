import scrapy
import random
import os
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.exceptions import CloseSpider
from skin_for_hero.items import SkinForHeroItem
from ..settings import BASE_STORAGE_PATH, DEFAULT_HEADERS, ua_pools

class GetSkinSpider(scrapy.Spider):
    name = "get_skin"

    def __init__(self, hero=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hero:
            hero = input("输入英雄称号 (输入ALL下载全部)")
        self.hero = hero
        self.batch_mode = (hero.upper() == "ALL")
        self.start_urls = ["https://splash.buguoguo.cn/"]
        self.allowed_domains = ["splash.buguoguo.cn", "communitydragon.buguoguo.cn"]
        self.completed_count = 0
        if not self.batch_mode:
            self.folder_path = os.path.join(BASE_STORAGE_PATH, self.hero)
            self.check_folder_empty()
            os.makedirs(self.folder_path, exist_ok=True)

    def check_folder_empty(self):
        if os.path.exists(self.folder_path):
            if any(os.scandir(self.folder_path)):
                print(f"{self.hero}已有对应文件夹，跳过")
                raise CloseSpider(f"找找文件夹吧，应该有")
            else:
                print(f"已有{self.hero}皮肤夹但为空，自动继续下载")
        else:
            print(f"开始下载: {self.hero}")

    def parse(self, response: HtmlResponse):
        if self.batch_mode:
            # Batch mode: get all hero links
            hero_links = response.css('div.styles_champions___b7bp a')
            for link in hero_links:
                hero_name = link.css('span img::attr(alt)').get()
                hero_url = link.css('::attr(href)').get()
                if hero_name and hero_url:
                    # Check if already exists
                    folder_path = os.path.join(BASE_STORAGE_PATH, hero_name)
                    if os.path.exists(folder_path) and any(os.scandir(folder_path)):
                        print(f"[跳过] {hero_name} 已有皮肤")
                        continue
                    os.makedirs(folder_path, exist_ok=True)
                    target_url = response.urljoin(hero_url)
                    yield Request(
                        url=target_url, 
                        callback=self.parse2,
                        cb_kwargs={'current_hero': hero_name, 'folder': folder_path},
                        dont_filter=True
                    )
            print(f"批量模式: 已扫描所有英雄")
        else:
            # Single hero mode
            target_url = response.xpath(f'//a[.//span//img[@alt="{self.hero}"]]/@href').get()
            if not target_url:
                print(f"未找到英雄: {self.hero}")
                return
            target_url1 = response.urljoin(target_url)
            yield Request(url=target_url1, callback=self.parse2,
                         cb_kwargs={'current_hero': self.hero, 'folder': self.folder_path})

    def parse2(self, response: HtmlResponse, current_hero=None, folder=None):
        all_skins = response.css('div.styles_grid__Th2O3 > a')
        for one_skin in all_skins:
            target_url = one_skin.css('::attr(href)').get()
            target_url1 = response.urljoin(target_url)
            skin_name = one_skin.css('span img::attr(alt)').get()
            if not skin_name:
                continue
            file_name = f'{skin_name}.jpg'
            target_file = os.path.join(folder, file_name)
            yield Request(
                url=target_url1,
                callback=self.parse3,
                cb_kwargs={'filepath': target_file},
                dont_filter=True
            )

    def parse3(self, response: HtmlResponse, filepath=None):
        last_url = response.css('body link::attr(href)').get()
        if not last_url:
            return
        headers = DEFAULT_HEADERS.copy()
        headers['User-Agent'] = random.choice(ua_pools)
        headers['Referer'] = response.url
        yield Request(
            url=last_url,
            callback=self.parse4,
            cb_kwargs={'filepath': filepath},
            headers=headers,
            dont_filter=True
        )

    def parse4(self, response: HtmlResponse, filepath=None):
        try:
            with open(filepath, 'wb') as f:
                f.write(response.body)
            self.completed_count += 1
            if self.completed_count % 10 == 0:
                print(f"已下载 {self.completed_count} 张皮肤图片...")
        except Exception as e:
            print(f"下载失败: {filepath}, 错误: {e}")
