#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: ??
@file: mdpicker_github.py
@time: 2018/8/23 10:19
@desc:
"""

import datetime
import base64
import hashlib
import os
import pyperclip
import urllib2
import json


from configparser import ConfigParser
from PIL import ImageGrab, Image, ImageFilter


API_TEMPLATE = 'https://api.github.com{0}'


class ClipToGithub(object):
    def __init__(self):
        """初始化操作类，获取配置文件信息

        """
        self.__tmp_image = 'tmp.jpg'
        config = ConfigParser()
        config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'github.ini'))
        self.__github_user = config.get('config', 'github_user')
        self.__github_repo = config.get('config', 'github_repo')
        self.__github_token = config.get('config', 'github_token')
        self.__add_shadow = config.get('handle', 'shadow')

    def upload_and_return_url(self):
        file_path = self.__tmp_image
        # 生成远端存储别名
        remote_name = self.generate_remote_name(file_path)
        # 上传时间
        upload_dt = datetime.datetime.now()
        url = API_TEMPLATE.format(
         '/repos/{user}/{repo}/contents/{filename}'.format(user=self.__github_user,repo=self.__github_repo,filename=remote_name))
        # print(url)
        content = self.load_file(file_path)
        print(content)
        body = {
            "message": "commit a image from clipboard." + upload_dt.strftime('%Y-%m-%d %H:%M:%S'),
            "content": content
        }
        json_body = json.dumps(body)
        print(json_body)
        request = urllib2.Request(url, json_body)
        request.add_header('Content-Type', 'application /json; charset=utf-8')
        request.add_header('Authorization', "token " + self.__github_token )
        request.get_method = lambda:'PUT'
        request = urllib2.urlopen(request)
        download_url = json.loads(request.read())['content']['download_url']
        # print(json.loads(request.read()))
        # print(download_url)
        # print(download_url.replace('raw.githubusercontent.com','rawcdn.githack.com',1))
        md_img_url = download_url.replace('raw.githubusercontent.com','rawcdn.githack.com',1)
        # 整理 md 图片链接格式到剪贴板
        md_img_string = '![image](' + md_img_url + ')'
        pyperclip.copy(md_img_string)
        pyperclip.paste()

    @staticmethod
    def headers(config):
        return {
            'Authorization': 'token {token}'.format(**config),
            'Content-Type': 'application/json; charset=utf-8',
        }

    @staticmethod
    def generate_remote_name(file_path):
        """计算文件名

        :return:
        """
        # 获取文件扩展名
        img_ext = file_path.split('.')[-1]
        # 计算文件 md5 值
        with open(file_path, 'rb') as fh:
            md5 = hashlib.md5(fh.read()).hexdigest()

        # remote name: filetype/year/month/day/md5.filetype
        now = datetime.datetime.now()
        remote_name = img_ext + '/' + str(now.year) + '/' + str(
            now.month) + '/' + str(now.day) + '/' + md5 + '.' + img_ext
        return remote_name

    @staticmethod
    def load_file(file_path):
        with open(file_path, 'rb') as fin:
            data = fin.read()
        return base64.b64encode(data)

    def save_from_screen(self):
        """将剪贴板的图片保存到本地为临时图片文件

        :return:
        """
        pic = ImageGrab.grabclipboard()
        if pic is None:
            print("No image is on the clipboard.")
            return
        pic.save(self.__tmp_image)

    def add_shadow(self, offset=(0, 0), background_color=0xffffff,
                   shadow_color=0x000000, border=20, iterations=10):
        """为图像添加阴影，即将图像放在一个高斯模糊的背景上

        :param offset: 阴影相对图像的偏移，用(x, y)表示，可以为正数或者负数
        :param background_color: 背景色
        :param shadow_color: 阴影色
        :param border: 图像边框，必须足够用来制作阴影模糊
        :param iterations: 过滤器处理次数，次数越多越模糊，处理过程也越慢
        :return: 添加阴影后的图片
        """

        if self.__add_shadow == '0':
            return
        # 要放在背景上的原始图像
        original_image = Image.open(self.__tmp_image)
        # 创建背景块
        total_width = original_image.size[0] + abs(offset[0]) + 2 * border
        total_height = original_image.size[1] + abs(offset[1]) + 2 * border
        background = Image.new(
            original_image.mode,
            (total_width, total_height),
            background_color
        )

        # 放置阴影块，考虑图像偏移
        shadow_left = border + max(offset[0], 0)
        shadow_top = border + max(offset[1], 0)
        background.paste(
            shadow_color,
            [shadow_left, shadow_top,
             shadow_left + original_image.size[0],
             shadow_top + original_image.size[1]]
        )

        # 处理阴影的边缘模糊
        n = 0
        while n < iterations:
            background = background.filter(ImageFilter.BLUR)
            n += 1

        # 把图像粘贴到背景上
        image_left = border - min(offset[0], 0)
        image_top = border - min(offset[1], 0)
        background.paste(original_image, (image_left, image_top))

        # 将处理后的图片覆盖原图片
        background.save(self.__tmp_image)

    def close(self):
        """删除保存在本地的临时图片文件

        :return:
        """
        os.remove(self.__tmp_image)


if __name__ == '__main__':
    clip_to_github = ClipToGithub()
    clip_to_github.save_from_screen()
    clip_to_github.upload_and_return_url()
    clip_to_github.add_shadow()
    clip_to_github.close()