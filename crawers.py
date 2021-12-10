import json
import threading

import requests
from pyquery import PyQuery as pq
import os
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By  # 查找元素的方式
from selenium.webdriver.support import expected_conditions as EC  # 响应元素的存在以及类型
from selenium import webdriver
from requests.cookies import RequestsCookieJar
from urllib.parse import urlencode
import multiprocessing


headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
}
driver_path = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"


class Pageup():
    def __init__(self, target_link, page, pre_link, c_for_requests, dirname):
        self.page = page
        self.target_link = target_link
        self.pre_link = pre_link
        self.c_for_requests = c_for_requests
        self.dirname = dirname

    def run(self):
        params = getParams(self.target_link, self.page)
        getImglink(self.pre_link, params, self.c_for_requests, self.dirname)


class ImgDownLoad(threading.Thread):
    def __init__(self, imglink, dirname):
        threading.Thread.__init__(self)
        self.imglink = imglink
        self.dirname = dirname

    def run(self):
        """
        获取到的image_link此时不完整，
        格式如下: //wx4.sinaimg.cn/(thumb150/orj360)/005MnE0rgy1gsbpbnqlctj61k9165qpp02.jpg
        所以代码中要进行修改，加上https://, 同时括号内内容需要替换为mw690获取大图
        :return:
        """
        imglist = f'{self.imglink}'.split('/')
        imglist[3] = 'mw690'
        str = '/'
        if imglist[0] == "https:":
            imglink = str.join(imglist)
        else:
            imglink = str.join(imglist)
            imglink = 'https:' + imglink
        print(imglink)
        img = requests.get(imglink, headers=headers)
        imgname = f'{self.imglink}'.split('/')[-1]
        with open(self.dirname + "/" + imgname, 'wb') as f:
            f.write(img.content)


def refreshCookie():
    driver = webdriver.Chrome(driver_path)
    driver.maximize_window()
    driver.get('https://weibo.com/login.php')
    time.sleep(20)  # 延迟20秒，执行手动登录操作，20秒后才从浏览器下载cookie
    dict_cookies = driver.get_cookies()  # 获取list的cookies
    json_cookies = json.dumps(dict_cookies)  # 转换成字符串保存
    with open('weibo_cookies.txt', 'w') as f:
        f.write(json_cookies)
    print('cookies保存成功！')
    driver.close()


def getCookie():
    """
    :return: login_cookies 从cookies文件中打开cookie, 加载为json字符串
    """
    with open('weibo_cookies.txt', 'r', encoding='utf8') as f:
        login_cookies = json.loads(f.read())
    return login_cookies


def cookie_getter(is_refresh):
    """

    :param is_refresh:
    :return:
    """

    cookies = {}
    if is_refresh == "Y":
        refreshCookie()
        cookies = getCookie()
    elif is_refresh == "N":
        cookies = getCookie()
    return cookies


def getParams(target_link, page):
    """
    :param target_link: 博主的主页url
    :param page: 请求的页面
    :return: params dict格式的参数
    """
    script_uri = f'{target_link}'
    script_uri = script_uri.replace('https://weibo.com', '')
    idlater = script_uri.replace('/p/', '')  # 分离target_link中的id
    domain = f'{idlater}'[0:6]  # target_link中，前6个为domain参数（和本地主机有关）, 用切片将其提取出来
    params = {
        'ajwvr': '6',
        'domain': domain,
        'is_all': '1',
        'profile_ftype': '1',
        'pagebar': '0',
        'pl_name': 'Pl_Official_MyProfileFeed__20',
        'id': idlater,
        'script_uri': script_uri,
        'feed_type': '0',
        'page': f'{page}',
        'pre_page': f'{page}',
        'domain_op': domain
    }
    return params


def getImglink(pre_link, params, c_for_requests, dirnames):
    """
    :param pre_link: 数据的通用前半部分连接
    :param params: dict格式参数
    :param c_for_requests: cookieJar值
    :param dirnames: 保存目录名
    :return:
    """
    complete_link = pre_link + urlencode(params)  # urllib下的库函数urlencode把dicts形式的参数编码为get请求中拼接在url中的形式
    data = requests.get(complete_link, headers=headers, cookies=c_for_requests)
    data = data.json()
    data = data['data']
    source = pq(data)
    imglinks = source('img').items()
    for item in imglinks:
        imglink = item.attr('src')  # 提取图片src
        img_test = f'{imglink}'.split('.')
        if not img_test.__len__() > 4:
            dirname = dirnames
            imgdown = ImgDownLoad(imglink, dirname)
            imgdown.start()  # 每次start, 启动一个图片下载线程


def getTarget(browser, name):
    target_name = name
    wait = WebDriverWait(browser, 15)
    enter = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.W_input')))
    submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.W_ficon.ficon_search.S_ficon')))
    enter.clear()
    enter.send_keys(target_name)
    submit.click()
    page_source = browser.page_source
    page_source = pq(page_source)
    target_link = 'https:' + page_source('.avator a').attr('href')
    browser.get(target_link)
    page_source = browser.page_source
    page_source = pq(page_source)
    target_link = page_source('.WB_innerwrap .S_line1 a').attr('href')
    target_link = f'{target_link}'.replace('/follow?from=page_100505&wvr=6&mod=headfollow#place', '')
    target_link = f'https:{target_link}'
    return target_link





def crawersinit(name, is_fresh, pages):
    """
    :param is_fresh: 判断是否刷新cookie
    :param name:  所需要查看的博主
    :return:
    """
    if not os.path.exists(f'{name}'):
        os.mkdir(name)
    dirname = name
    browser = webdriver.Chrome(driver_path)
    browser.get('https://weibo.com/login.php')
    time.sleep(5)
    cookies = cookie_getter(is_fresh)
    # requests使用的cookie为cookieJar格式，json格式的cookie需要重新编码
    for cookie in cookies:
        cookie_dict = {
            'domain': '.weibo.com',
            'name': cookie.get('name'),
            'value': cookie.get('value'),
            "expires": '',
            'path': '/',
            'httpOnly': False,
            'HostOnly': False,
            'Secure': False
        }
        browser.add_cookie(cookie_dict)
    time.sleep(3)  # 延迟三秒等待cookie注入回浏览器
    jar = RequestsCookieJar()
    for cooike_item in cookies:
        jar.set(cooike_item['name'], cooike_item['value'])

    target_link = getTarget(browser, name)
    print("target_link", target_link)
    pre_link = 'https://weibo.com/p/aj/v6/mblog/mbloglist?'  # 数据的公共头，数据请求完整的url由参数生成

    pool = multiprocessing.Pool(3)  # 指定最大进程数
    for i in range(1, pages+1):
        page = Pageup(target_link, i, pre_link, jar, dirname)  # 分页请求类，在pageUp中，生成具体的数据请求url，请求每一张图片
        pool.apply_async(page.run())
    pool.close()
    pool.join()
