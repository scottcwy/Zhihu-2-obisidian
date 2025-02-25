# -*- coding:utf-8 -*-
import os
import random
import sys
import time
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import argparse
from utils import filter_title_str
import json
from dotenv import load_dotenv

from markdownify import MarkdownConverter

parser = argparse.ArgumentParser(description='知乎文章剪藏')
parser.add_argument('collection_url', metavar='collection_url', type=str,nargs=1,
                    help='收藏夹（支持公开和私密收藏夹）的网址')

# 读取cookies
def load_cookies():
    """加载知乎 cookie
    
    Returns:
        dict: cookie 字典，如果加载失败则返回 None
    """
    try:
        # 从 .env 文件加载环境变量
        load_dotenv()
        zhihu_cookie = os.getenv('ZHIHU_COOKIE')
        if not zhihu_cookie:
            print("未找到 ZHIHU_COOKIE 环境变量")
            return None
        
        # 将cookie字符串转换为字典
        cookies_dict = {}
        for item in zhihu_cookie.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookies_dict[name.strip()] = value.strip()
        
        print("从 .env 文件成功读取到 cookie")
        return cookies_dict
    except Exception as e:
        print(f"加载cookie时出错: {str(e)}")
        return None

cookies = load_cookies()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"
}

class ObsidianStyleConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def chomp(self, text):
        """
        If the text in an inline tag like b, a, or em contains a leading or trailing
        space, strip the string and return a space as suffix of prefix, if needed.
        This function is used to prevent conversions like
            <b> foo</b> => ** foo**
        """
        prefix = ' ' if text and text[0] == ' ' else ''
        suffix = ' ' if text and text[-1] == ' ' else ''
        text = text.strip()
        return (prefix, suffix, text)

    def convert_img(self, el, text, convert_as_inline):
        alt = el.attrs.get('alt', None) or ''
        src = el.attrs.get('src', None) or ''
        # 直接返回markdown格式的图片链接
        return f'![{alt}]({src})\n\n'

    def convert_a(self, el, text, convert_as_inline):
        # 处理特殊的链接卡片
        if el.get('data-draft-type') in ['mcn-link-card', 'ad-link-card']:
            return ''  # 直接移除这些特殊卡片
            
        prefix, suffix, text = self.chomp(text)
        if not text:
            return ''
        href = el.get('href')

        if el.get('aria-labelledby') and el.get('aria-labelledby').find('ref') > -1:
            text = text.replace('[', '[^')
            return '%s' % text
        if (el.attrs and 'data-reference-link' in el.attrs) or ('class' in el.attrs and ('ReferenceList-backLink' in el.attrs['class'])):
            text = '[^{}]: '.format(href[5])
            return '%s' % text

        return super(ObsidianStyleConverter, self).convert_a(el, text, convert_as_inline)

    def convert_li(self, el, text, convert_as_inline):
        if el and el.find('a', {'aria-label': 'back'}) is not None:
            return '%s\n' % ((text or '').strip())

        return super(ObsidianStyleConverter, self).convert_li(el, text, convert_as_inline)


def markdownify(html, **options):
    return ObsidianStyleConverter(**options).convert(html)


# 获取收藏夹的回答总数
def get_article_nums_of_collection(collection_id):
    """
    :param starturl: 收藏夹连接
    :return: 收藏夹的页数
    """
    try:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items".format(collection_id)
        html = requests.get(collection_url, headers=headers, cookies=cookies)
        html.raise_for_status()

        # 页面总数
        return html.json()['paging'].get('totals')
    except:
        return None


# 解析出每个回答的具体链接
def get_article_urls_in_collection(collection_id):
    collection_id =collection_id.replace('\n','')

    offset = 0
    limit = 20

    article_nums = get_article_nums_of_collection(collection_id)

    url_list = []
    title_list = []
    while offset < article_nums:
        collection_url = "https://www.zhihu.com/api/v4/collections/{}/items?offset={}&limit={}".format(collection_id,
                                                                                                       offset, limit)
        try:
            html = requests.get(collection_url, headers=headers, cookies=cookies)
            content = html.json()
        except:
            return None

        for el in content['data']:
            url_list.append(el['content']['url'])
            try:
                if el['content']['type'] == 'answer':
                    title_list.append(el['content']['question']['title'])
                else:
                    title_list.append(el['content']['title'])
            except:
                print('********')
                print('TBD 非回答, 非专栏, 想法类收藏暂时无法处理')
                for k, v in el['content'].items():
                    if k in ['type', 'url']:
                        print(k, v)
                print('********')
                url_list.pop()

        offset += limit

    return url_list, title_list


# 获得单条答案的数据
def get_single_answer_content(answer_url):
    html_content = requests.get(answer_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(html_content.text, "lxml")
    try:
        answer_content = soup.find('div', class_="AnswerCard").find("div", class_="RichContent-inner")
    except:
        print(answer_url, 'failed')
        return -1
    # 去除不必要的style标签
    for el in answer_content.find_all('style'):
        el.extract()

    for el in answer_content.select('img[src*="data:image/svg+xml"]'):
        el.extract()
    
    for el in answer_content.find_all('a'): # 处理回答中的卡片链接
        aclass = el.get('class')
        if isinstance(aclass, list):
            if aclass[0] == 'LinkCard':
                linkcard_name = el.get('data-text')
                el.string = linkcard_name if linkcard_name is not None else el.get('href')
        else:
            pass
        try:
            if el.get('href').startswith('mailto'): # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                el.name = 'p'
        except:
            print(answer_url, el) # 一些广告卡片, 不需要处理
        
    # 添加html外层标签
    answer_content = html_template(answer_content)

    return answer_content


# 获取单条专栏文章的内容
def get_single_post_content(paper_url):
    html_content = requests.get(paper_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(html_content.text, "lxml")
    post_content = soup.find("div", class_="Post-RichText")
    # 去除不必要的style标签
    if post_content:
        for el in post_content.find_all('style'):
            el.extract()

        for el in post_content.select('img[src*="data:image/svg+xml"]'):
            el.extract()
        
        for el in post_content.find_all('a'): # 处理专栏文章中的卡片链接
            aclass = el.get('class')
            if isinstance(aclass, list):
                if aclass[0] == 'LinkCard':
                    linkcard_name = el.get('data-text')
                    el.string = linkcard_name if linkcard_name is not None else el.get('href')
            else:
                pass
            try:
                if el.get('href').startswith('mailto'): # 特殊bug, 正文的aaa@bbb.ccc会被识别为邮箱, 嵌入<a href='mailto:xxx'>中, markdown转换时会报错
                    el.name = 'p'
            except:
                print(paper_url, el)
    else:
        post_content = "该文章链接被404, 无法直接访问"

    # 添加html外层标签
    post_content = html_template(post_content)

    return post_content


def html_template(data):
    # api content
    html = '''
        <html>
        <head>
        </head>
        <body>
        %s
        </body>
        </html>
        ''' % data
    return html


if __name__=='__main__':
    args = parser.parse_args()
    collection_url = args.collection_url[0]
    collection_id = collection_url.split('?')[0].split('/')[-1]
    urls, titles = get_article_urls_in_collection(collection_id)

    assert len(urls) == len(titles), '地址标题列表长度不一致'

    print('共获取 %d 篇可导出回答或专栏' % len(urls))

    # 修改为指定的保存路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    downloadDir = os.path.join(project_root, 'data', 'zhihu_downloads')
    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
        print(f"创建下载目录: {downloadDir}")

    for i in tqdm(range(len(urls))):
        content = None
        url = urls[i]
        title = titles[i]

        file_path = os.path.join(downloadDir, filter_title_str(title) + ".md")
        if os.path.exists(file_path): # 跳过已经保存的文件
            continue

        if url.find('zhuanlan')!= -1:
            content = get_single_post_content(url)
        else:
            content = get_single_answer_content(url)
        
        if content == -1:
            print(f"\n{url} 获取内容失败")
            continue
        
        try:
            md = markdownify(content, heading_style="ATX")
            md = '> %s\n' % url + md

            with open(file_path, "w", encoding='utf-8') as md_file:
                md_file.write(md)
            print(f"\n成功保存: {os.path.basename(file_path)}")
            time.sleep(random.uniform(0.5, 3))
        except Exception as e:
            print(f"\n处理失败: {url}")
            print(f"错误信息: {str(e)}")

    print("\n全部下载完毕")
    print(f"文件保存在: {downloadDir}")