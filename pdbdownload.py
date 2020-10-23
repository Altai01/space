#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import time
import re
import copy
import logging
import zipfile
import datetime
import csv
import os

import requests
from bs4 import BeautifulSoup

import config
import mylog

logger = logging.getLogger(config.LOGGER_NAME)#日志
ONLINE_ROOT_HOST_URL = "http://172.18.48.68/"


# 下载文件
def download_file(targetFolder, file_url, override=False):
    dir_index = file_url.rfind('/')-1#从右向左查找字符，返回最后一次出现的位置
    dir_index0 = file_url.rfind('/',0,dir_index)
    #dir_index1 = file_url.find('/',dir_index0+1)#从右向左查找字符，返回最后一次出现的位置
    #dir_index2 = file_url.find('/',dir_index1+1)
    #print(dir_index2)
    #print(file_url)
    fileName = file_url[dir_index+1:]
    file_save_url=file_url[dir_index0+1:]
    save_url_end_index=file_save_url.rfind('/')
    file_save_url_end=file_save_url[save_url_end_index+1:]
    #print(targetFolder)
    #print(fileName)
    #input('a')

    if (not override) and os.path.exists(file_save_url):
        logger.info(fileName + " 已经下载过了")
        #input()
        return True

    logger.info("start download " + fileName)
    download_url =file_url
    print(download_url)
    #input('aa')
    res = requests.get(download_url)#向网站发起请求
    logger.info("下载文件：" + fileName)
    logger.info('返回状态码：' + str(res.status_code))
    if not res.ok:
        return False

    res.raise_for_status()
    save_url=targetFolder+'/'+file_save_url
    save_url=re.sub(file_save_url_end,'',save_url)
    #print(save_url)
    #input('sa')
    if not os.path.exists(save_url):
        os.makedirs(save_url)
    playFile = open(save_url +'\\'+ fileName, 'wb')
    #print(playFile)
    #input('b')
    for chunk in res.iter_content(100000):
        playFile.write(chunk)
        # logger.info("downloading...")
    playFile.close()
    logger.info(fileName + "下载完成")
    return True

def get_url_paths(url, ext='', params={}, exclude='', pref=''):#获取该目录下所有子文件的路径
    response = requests.get(url, params=params)
    #logger.debug('返回状态码：' + str(response.status_code))
    if response.ok:
        response_text = response.text
    else:
        return response.raise_for_status()

    soup = BeautifulSoup(response_text, 'html.parser')
    parent = {}
    for node in soup.find_all('a'):
        node_herf = node.get('href')
        if ((not node_herf.endswith(exclude)) and node_herf.endswith(ext) ):
            if node_herf.endswith('/'):
                node_herf = node_herf[:-1]
                if(node_herf=='ccmserver'):
                    return parent
            parent[node_herf] = url + node.get('href')
    return parent

def le_date(v1, v2):
    v1List = v1.split('-')
    v2List = v2.split('-')
    preLargeFlag = False
    for index in range(len(v1List)):
        if preLargeFlag and int(v1List[index]) > int(v2List[index]):
            return True
        preLargeFlag = int(v1List[index]) >= int(v2List[index])
    return False

def get_sub_hosts():
    sub_hosts = get_url_paths(url=ONLINE_ROOT_HOST_URL, exclude='../')
    logger.debug('获取到子服务器({0}):{1}'.format(len(sub_hosts), sub_hosts.keys()))
    return sub_hosts

def download_dmp_files(file_url_list, download_dir):
    print(download_dir)
    #input('c')
    for file_url in file_url_list:
        print(file_url)
        download_file(download_dir, file_url)

def to_csv(total, date_sts, osrole_sts, version_sts):
    csv_path = os.getcwd() + "\\CrashCount.csv"
    csvFile = open(csv_path,"w+",newline='')
    print("b")
    try:
        writer = csv.writer(csvFile)
        name = ["total_count"]
        writer.writerow(name)
        writer.writerow([total])
        writer.writerow([])
        
        name = ["date","crash_count"]
        writer.writerow(name)
        for key in date_sts:
            data = [key,str(date_sts[key]).lstrip('{').rstrip('}')]
            writer.writerow(data)
        writer.writerow([])
        
        name = ["osrole","crash_count"]
        writer.writerow(name)
        for key in osrole_sts:
            data = [key,str(osrole_sts[key]).lstrip('{').rstrip('}')]
            writer.writerow(data)
        writer.writerow([])
        
        name = ["version","crash_count"]
        writer.writerow(name)
        for key in version_sts:
            data = [key,str(version_sts[key]).lstrip('{').rstrip('}')]
            writer.writerow(data)
    finally:
        csvFile.close()
        logger.info('###### csv file generated')
    pass

def get_all_dump_info(start, end, pref='', download_dir=''):
    '''
    example: http://172.18.48.68/172.18.202.118/2020-04-13/macstudent/1_0_2_15/0cf6a588-a2f6-4b53-93c9-e3a05306c68d.dmp
    '''
    #统计数据
    host_sts = {}
    date_sts = {}
    osrole_sts = {}
    version_sts = {}
    all_dmp_json_file = []
	
    all_host = get_sub_hosts()
    for host, host_url in all_host.items():
        #获取日期层级目录
        all_date = get_url_paths(host_url, exclude='../')#get_url_paths获取目录
        
        #logger.debug('host:{0}\r\n: {1}'.format(host_url, all_date.keys()))
        for date, date_url in all_date.items():
            matchObj = re.match(r'(\d{4}-\d{2}-\d{2})', date)
           
            #过滤要统计的日期
            if matchObj and (date == start or date == end or (le_date(date, start) and le_date(end, date))):
                #平台和角色类型的层级目录
                os_and_role = get_url_paths(date_url, exclude='../', pref=pref)
                for osrole, osrole_url in os_and_role.items():
                    #版本号层级目录
                    if(osrole=='winstudent'):
                        all_version = get_url_paths(osrole_url, exclude='../')
                        for version, version_url in all_version.items():
                            #dmp和json文件位置
                            win_list=['1_1_6_0','1_1_5_22','1_1_5_19','1_1_5_18','1_1_5_17','1_1_5_16','1_1_4_21']#版本号
                            if version in win_list:
                                all_dmp_or_json = get_url_paths(version_url, exclude='../')
                                dmp_or_json_urls = all_dmp_or_json.values()
                                crash_num = len(all_dmp_or_json) / 2  #dmp和json文件对应一次崩溃
                                    #统计
                                all_dmp_json_file += dmp_or_json_urls
                                print('aa')
                                if host in date_sts:
                                    host_sts[host] += crash_num
                                else:
                                    host_sts[host] = crash_num

                                if date in date_sts:
                                    date_sts[date] += crash_num
                                else:
                                    date_sts[date] = crash_num

                                if osrole in osrole_sts:
                                    osrole_sts[osrole] += crash_num
                                else:
                                    osrole_sts[osrole] = crash_num

                                if version in version_sts:
                                    version_sts[version] += crash_num
                                else:
                                    version_sts[version] = crash_num

                                    #下载
                                if download_dir != '':
                                    download_dmp_files(dmp_or_json_urls, download_dir + date + "/" )
                                          
    logger.info('####################[{0} ~ {1}]###################'.format(start, end))
    logger.info('###### total crash Numbers:  {0}'.format(len(all_dmp_json_file) / 2))
    logger.info('###### date crash: \r\n{0}'.format(date_sts))
    logger.info('###### osrole crash: \r\n{0}'.format(osrole_sts))
    logger.info('###### version crash: \r\n{0}'.format(version_sts))
    to_csv(len(all_dmp_json_file) / 2,date_sts,osrole_sts,version_sts)
    #input('d')
    return all_dmp_json_file, date_sts, osrole_sts, version_sts


if __name__ == '__main__':
    logger.info('下载模块独立运行')
    all_dmp_info_files,_,_,_ = get_all_dump_info('2020-10-16', '2020-10-20','winstudent')
    #all_dmp_info_files,_,_,_ = get_all_dump_info('2020-06-05', '2020-06-07', 'win', config.DUMP_FOLDER_PATH)
    download_dmp_files(all_dmp_info_files, config.DUMP_FOLDER_PATH + "1017_1018_winstudent")
    os.system("pause")
else:
    logger.info('下载Dump模块被导入')

