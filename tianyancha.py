#!/usr/bin/python
# -*- coding:utf-8 -*-
# author: oyj
# CreateTime: 2019/5/15
# software-version: python 3.7

import os
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import re
from PIL import Image
from time import sleep, time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import json
import time
import pymongo
from pyquery import PyQuery as pq

class GetHospitalInfo(object):
    """
    爬取天眼查下的医院的信息
    """
    # 初始化
    def __init__(self):
        """
         初始化爬虫执行代理，使用chrome访问
         """
        # 定义为全局变量，方便其他模块使用
        global url, browser, wait
        # 登录界面的url
        url = 'https://www.tianyancha.com'
        # 实例化一个chrome浏览器
        browser = webdriver.Chrome()
        # 设置等待超时
        wait = WebDriverWait(browser, 20)


    # 登录
    def login(self):
        try:
            # 打开登录页面
            browser.get(url)
            # 将页面放到最大
            browser.maximize_window()
            # 点击登录链接
            # loginLink = WebDriverWait(driver, 30).until(lambda x:x.find_element_by_xpath('//a[@onclick="header.loginLink(event)"]'))
            loginLink = WebDriverWait(browser, 30).until(lambda x: x.find_element_by_xpath('//a[text()="登录/注册"]'))
            loginLink.click()

            # 切换到密码登录方式
            # login_by_pwd = WebDriverWait(driver, 30).until(lambda x:x.find_element_by_xpath('//div[@onclick="loginObj.changeCurrent(1);"]'))
            login_by_pwd = WebDriverWait(browser, 30).until(lambda x: x.find_element_by_xpath('//div[text()="密码登录"]'))
            login_by_pwd.click()

            # 输入用户名
            username = WebDriverWait(browser, 30).until(lambda x: x.find_elements_by_xpath('//input[@type="text"]')[4])
            username.send_keys('***********')

            # 输入密码
            password = WebDriverWait(browser, 30).until(
                lambda x: x.find_element_by_css_selector('div.input-warp.-block > input.input.contactword'))
            password.send_keys('***********')

            # 取消登录保留一周的选项
            saveoneweek = WebDriverWait(browser, 30).until(
                lambda x: x.find_element_by_css_selector('input.contactautoLogin'))
            saveoneweek.click()

            # 点击登录按钮
            # login_button = WebDriverWait(driver, 30).until(lambda x:x.find_element_by_xpath('//div[@onclick="loginObj.loginByPhone(event);"]'))
            login_button = WebDriverWait(browser, 30).until(lambda x: x.find_element_by_xpath('//div[text()="登录"]'))
            browser.execute_script("arguments[0].click();", login_button)
            # 获得cookie，判断是否登录
            yzcg = yzsb = browser.get_cookies()
            while (yzcg == yzsb):
                browser.page_source
                yzcg = browser.get_cookies()
                print(yzcg == yzsb)
                if yzcg != yzsb:
                    break
                # 获取缺口图片及其位置信息
                bg, bg_position = self.get_image_info('bg')
                # 获取完整图片及其位置信息
                fullbg, fullbg_position = self.get_image_info('fullbg')
                # 将混乱的缺口图片裁剪成小图，获取两行的位置信息
                bg_first_line_img, bg_second_line_img = self.Corp(bg, bg_position)
                # 将混乱的完整图片裁剪成小图，获取两行的位置信息
                fullbg_first_line_img, fullbg_second_line_img = self.Corp(fullbg, fullbg_position)
                # 根据两行图片信息拼接出缺口图片正确排列的图片
                bg_image = self.put_imgs_together(bg_first_line_img, bg_second_line_img, 'bg.jpg')
                # 根据两行图片信息拼接出完整图片正确排列的图片
                fullbg_image = self.put_imgs_together(fullbg_first_line_img, fullbg_second_line_img, 'fullbg.jpg')
                # 计算滑块移动距离
                distance = self.get_distance(bg_image, fullbg_image)
                # 计算移动轨迹
                trace = self.get_trace(distance - 10)
                # 移动滑块
                self.move_to_gap(trace)
        except:
            self.login()



    # 获取图片信息
    def get_image_info(self,img):
        '''
        :param img: (Str)想要获取的图片类型：带缺口、原始
        :return: 该图片(Image)、位置信息(List)
        '''
        try:
            # 将网页源码转化为能被解析的lxml格式
            soup = BeautifulSoup(browser.page_source, 'lxml')
            # 获取验证图片的所有组成片标签
            imgs = soup.find_all('div', {'class': 'gt_cut_' + img + '_slice'})
            # 用正则提取缺口的小图片的url，并替换后缀
            img_url = re.findall('url\(\"(.*)\"\);', imgs[0].get('style'))[0].replace('webp', 'jpg')
            # 使用urlretrieve()方法根据url下载缺口图片对象
            urlretrieve(url=img_url, filename=img + '.jpg')
            # 生成缺口图片对象
            image = Image.open(img + '.jpg')
            # 获取组成他们的小图片的位置信息
            position = self.get_position(imgs)
            # 返回图片对象及其位置信息
            return image, position
        except IndexError or TypeError as e:
            self.get_image_info(img)





    # 获取小图片位置
    def get_position(self,img):
        '''
        :param img: (List)存放多个小图片的标签
        :return: (List)每个小图片的位置信息
        '''
        try:
            img_position = []
            for small_img in img:
                position = {}
                # 获取每个小图片的横坐标
                position['x'] = int(re.findall('background-position: (.*)px (.*)px;', small_img.get('style'))[0][0])
                # 获取每个小图片的纵坐标
                position['y'] = int(re.findall('background-position: (.*)px (.*)px;', small_img.get('style'))[0][1])
                img_position.append(position)
            return img_position
        except:
            self.get_position(img)



    # 裁剪图片
    def Corp(self,image, position):
        '''
        :param image:(Image)被裁剪的图片
        :param position: (List)该图片的位置信息
        :return: (List)存放裁剪后的每个图片信息
        '''
        try:
            # 第一行图片信息
            first_line_img = []
            # 第二行图片信息
            second_line_img = []
            for pos in position:
                if pos['y'] == -58:
                    first_line_img.append(image.crop((abs(pos['x']), 58, abs(pos['x']) + 10, 116)))
                if pos['y'] == 0:
                    second_line_img.append(image.crop((abs(pos['x']), 0, abs(pos['x']) + 10, 58)))
            return first_line_img, second_line_img
        except:
            self.Corp(image,position)



    # 拼接大图
    def put_imgs_together(self,first_line_img, second_line_img, img_name):
        '''
        :param first_line_img: (List)第一行图片位置信息
        :param second_line_img: (List)第二行图片信息
        :return: (Image)拼接后的正确顺序的图片
        '''
        try:
            # 新建一个图片，new()第一个参数是颜色模式，第二个是图片尺寸
            image = Image.new('RGB', (260, 116))
            # 初始化偏移量为0
            offset = 0
            # 拼接第一行
            for img in first_line_img:
                # past()方法进行粘贴，第一个参数是被粘对象，第二个是粘贴位置
                image.paste(img, (offset, 0))
                # 偏移量对应增加移动到下一个图片位置,size[0]表示图片宽度
                offset += img.size[0]
            # 偏移量重置为0
            x_offset = 0
            # 拼接第二行
            for img in second_line_img:
                # past()方法进行粘贴，第一个参数是被粘对象，第二个是粘贴位置
                image.paste(img, (x_offset, 58))
                # 偏移量对应增加移动到下一个图片位置，size[0]表示图片宽度
                x_offset += img.size[0]
            # 保存图片
            image.save(img_name)
            # 返回图片对象
            return image
        except:
            self.put_imgs_together(first_line_img,second_line_img,img_name)



    # 判断像素是否相同
    def is_pixel_equal(self,bg_image, fullbg_image, x, y):
        """
        :param bg_image: (Image)缺口图片
        :param fullbg_image: (Image)完整图片
        :param x: (Int)位置x
        :param y: (Int)位置y
        :return: (Boolean)像素是否相同
        """
        try:
            # 获取缺口图片的像素点(按照RGB格式)
            bg_pixel = bg_image.load()[x, y]
            # 获取完整图片的像素点(按照RGB格式)
            fullbg_pixel = fullbg_image.load()[x, y]
            # 设置一个判定值，像素值之差超过判定值则认为该像素不相同
            threshold = 60
            # 判断像素的各个颜色之差，abs()用于取绝对值
            if (abs(bg_pixel[0] - fullbg_pixel[0] < threshold) and abs(
                    bg_pixel[1] - fullbg_pixel[1] < threshold) and abs(
                    bg_pixel[2] - fullbg_pixel[2] < threshold)):
                # 如果差值在判断值之内，返回是相同像素
                return True

            else:
                # 如果差值在判断值之外，返回不是相同像素
                return False
        except:
            self.is_pixel_equal(bg_image,fullbg_image,x,y)



    # 计算滑块移动距离
    def get_distance(self,bg_image, fullbg_image):
        '''
        :param bg_image: (Image)缺口图片
        :param fullbg_image: (Image)完整图片
        :return: (Int)缺口离滑块的距离
        '''
        try:
            # 滑块的初始位置
            distance = 57
            # 遍历像素点横坐标
            for i in range(distance, fullbg_image.size[0]):
                # 遍历像素点纵坐标
                for j in range(fullbg_image.size[1]):
                    # 如果不是相同像素
                    if not self.is_pixel_equal(fullbg_image, bg_image, i, j):
                        # 返回此时横轴坐标就是滑块需要移动的距离
                        return i
        except:
            self.get_distance(bg_image,fullbg_image)



    # 构造滑动轨迹
    def get_trace(self,distance):
        '''
        :param distance: (Int)缺口离滑块的距离
        :return: (List)移动轨迹
        '''
        try:
            # 创建存放轨迹信息的列表
            trace = []
            # 设置加速的距离
            faster_distance = distance * (4 / 5)
            # 设置初始位置、初始速度、时间间隔
            start, v0, t = 0, 0, 0.5
            # 当尚未移动到终点时
            while start < distance:
                # 如果处于加速阶段
                if start < faster_distance:
                    # 设置加速度为2
                    a = 2
                # 如果处于减速阶段
                else:
                    # 设置加速度为-2
                    a = -2
                # 移动的距离公式
                move = v0 * t + 1 / 2 * a * t * t
                # 此刻速度
                v = v0 + a * t
                # 重置初速度
                v0 = v
                # 重置起点
                start += move
                # 将移动的距离加入轨迹列表
                trace.append(round(move))
            # 返回轨迹信息
            return trace
        except:
            self.get_trace(distance)



    # 模拟拖动
    def move_to_gap(self,trace):
        try:
            sleep(3)
            # 得到滑块标签
            slider = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gt_slider_knob')))
            # 使用click_and_hold()方法悬停在滑块上，perform()方法用于执行
            ActionChains(browser).click_and_hold(slider).perform()
            for x in trace:
                # 使用move_by_offset()方法拖动滑块，perform()方法用于执行
                ActionChains(browser).move_by_offset(xoffset=x, yoffset=0).perform()
            # 模拟人类对准时间
            sleep(0.5)
            # 释放滑块
            ActionChains(browser).release().perform()
        except:
            self.move_to_gap(trace)


    # 获取主要内容
    def parser_one_page(self,u):
        try:
            browser.get(u)
            # 获得页面
            html = browser.page_source
            doc = pq(html)
            items = doc('.result-list .search-item').items()
            for item in items:
                company_name = item.find('.content .header a').text()  # 公司名称
                company_link = item.find('.content .header a').attr('href') #详细链接
                zhuangtai = item.find('.content .header div').text()  # 公司状态
                daibiao = item.find('.content .info .title').eq(0).text().replace("法定代表人：","")  # 法定代表人
                zhuceziben = item.find('.content .info .title').eq(1).text().replace("注册资本：","")  # 注册资本
                chengli = item.find('.content .info .title').eq(2).text().replace("成立日期：","")  # 成立日期
                dianhua = item.find('.content .contact div').eq(0).find('span').eq(1).text().replace("查看更多","") # 电话
                youxiang = item.find('.content .contact div').eq(1).find('span').eq(1).text()  # 邮箱
                qita = item.find('.content .match span').eq(1).text()  # 其他信息
                shengfen = item.find('.site').text() #省份
                score = item.find('.score').text() #评分
                print(company_name)
                print(company_link)
                print(zhuangtai)
                print(daibiao)
                print(zhuceziben)
                print(chengli)
                print(dianhua)
                print(youxiang)
                print(qita)
                print(shengfen)
                print(score)

                yield {
                    'company_name': company_name,
                    'company_link': company_link,
                    'zhuangtai': zhuangtai,
                    'daibiao': daibiao,
                    'zhuceziben': zhuceziben,
                    'chengli': chengli,
                    'dianhua': dianhua,
                    'youxiang': youxiang,
                    'qita': qita,
                    'shengfen': shengfen,
                    'score': score
                }
        except IndexError as e:
            self.parser_one_page(u)


    # 写入文件
    def write_to_file(self,c):  # 写入文本
        with open('tianyancha.txt', 'a', encoding='utf-8') as f:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    # 插入数据库
    def insertdb(self,item):
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client.test
        collection = db['tianyancha']
        collection.insert_many([item])  # 插入数据


    # 主程序
    def main(self):
        # 登录
        self.login()
        for i in range(1, 6):
            #抓取医院信息
            u = url +'/search/p'+str(i)+'?key=医院'
            for item in self.parser_one_page(u):
                self.write_to_file(item)
                self.insertdb(item)


# 程序入口
if __name__ == '__main__':
    tianyancha = GetHospitalInfo()
    tianyancha.main()