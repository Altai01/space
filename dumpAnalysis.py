import subprocess
import json
import os
import shutil
import time
import re
import copy
import logging
import zipfile
import datetime

import config
import myLogger

logger = logging.getLogger(config.LOGGER_NAME)

DUMP_SYMS_FILE = config.DUMP_TOOLS_FOLDER + 'dump_syms'
MINIDUMP_STACKWALK_FILE = config.DUMP_TOOLS_FOLDER + 'minidump_stackwalk'


def unzip_pkg(zip_pkg_path, override=False):
    '''
        zip_pkg_path: zip包的路径
        @return : 解压后app路径
    '''
    f = zipfile.ZipFile(zip_pkg_path)
    dir_index = zip_pkg_path.rfind('/')
    zip_file_name = zip_pkg_path[dir_index+1:]
    targetFolderPath = config.PKG_FOLDER_PATH + zip_file_name[:zip_file_name.rfind('.')]
    app_target_path = targetFolderPath + '/' + config.ZIP_ROOT_FOLDER_NAME

    if (not override) and os.path.exists(app_target_path):
        logger.info(app_target_path + '已经解压过了！！')
        return app_target_path
    #删除原来
    if os.path.exists(targetFolderPath):
        shutil.rmtree(targetFolderPath)

    logger.debug("解压到文件夹：" + app_target_path)
    f.extractall(config.PKG_FOLDER_PATH)
    #移动
    shutil.move(config.PKG_FOLDER_PATH +
                config.ZIP_ROOT_FOLDER_NAME, app_target_path)
    f.close()
    return app_target_path

def get_execfiles_for_sym(dir_path, result_files: list):
    if not os.path.isdir(dir_path):
        logger.error(dir_path + ': 不是个文件夹！')
        return
    items =os.listdir(dir_path)
    for item in items:
        if item.startswith('Headers') or item.endswith('Resources') \
            or item.startswith('.D') or item.startswith('Modules') \
            or item.endswith('.sym'):
            continue

        temp_path = os.path.join(dir_path, item)
        if os.path.isfile(temp_path) and (not os.path.islink(temp_path)) \
            and (not temp_path in result_files):
            #过滤：
            predir = temp_path[:temp_path.rfind('/')]
            if predir.endswith('.framework') or predir.endswith('MacOS') \
                or predir.endswith('A') or temp_path.endswith('.dylib'):
                #temp_path = os.path.realpath(temp_path)
                logger.debug(temp_path)
                result_files.append(temp_path)
        elif os.path.isdir(temp_path):
            #递归
            get_execfiles_for_sym(temp_path, result_files)


def export_exec_syms(exec_file_path, syms_root_folder):
    # dir_index = exec_file_path.rfind('/')
    # exec_file_name = exec_file_path[dir_index+1:]
    sym_file_path = exec_file_path + '.sym'

    # 导出符号 dump_syms ./test > test.sym
    sym_cmd = DUMP_SYMS_FILE + ' ' + exec_file_path + ' > ' + sym_file_path
    res = subprocess.Popen(sym_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    if res.stderr.readline().decode('utf-8') != '':
        logger.error(exec_file_path + ': 导出符号出错!!')
        return False

    deal_sym_file(sym_file_path, config.SYM_FOLDER_PATH)


def deal_sym_file(sym_file_path, target_sym_root_dir):
    logger.info('开始处理符号文件：' + sym_file_path)
    # setup 1 : head -n1 test.sym : 
    head_cmd = 'head -n1 ' + sym_file_path
    res = subprocess.Popen(head_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    # res ex: MODULE Linux x86_64 6EDC6ACDB282125843FD59DA9C81BD830 test
    head_res_content = res.stdout.readline().decode('utf-8').strip()
    if (not head_res_content) or head_res_content == '':
        logger.error(sym_file_path + ': 处理符号出错' )
        return False
    res_content_list = head_res_content.split(' ')
    if len(res_content_list) != 5 :
        logger.error('符号文件问题:' + head_res_content)
        return False
    # setup 2: mkdir -p ./symbols/test/6EDC6ACDB282125843FD59DA9C81BD830/
    if not target_sym_root_dir.endswith('/'):
        target_sym_root_dir += '/'
    sym_target_dir = target_sym_root_dir + res_content_list[4] + '/' + res_content_list[3] + '/'
    if not os.path.exists(sym_target_dir):
        os.makedirs(sym_target_dir)
    # setup 3: mv test.sym ./symbols/test/6EDC6ACDB282125843FD59DA9C81BD830/
    shutil.move(sym_file_path, sym_target_dir)
    logger.info('处理符号文件完成: ' + sym_file_path )
    return True


def produce_dmp_result_file(dmp_file_path, symbol_root_dir):
    # minidump_stackwalk 293892838*.dmp ./symbols [ >293892838*.dmp.txt]
    #dir_index = dmp_file_path.rfind('.')
    #result_file_path = dmp_file_path[dir_index+1:] + 'txt'
    result_file_path = dmp_file_path + '.txt'

    minidump_cmd = MINIDUMP_STACKWALK_FILE + ' ' + dmp_file_path + ' ' + symbol_root_dir + ' > ' + result_file_path
    res = subprocess.Popen(minidump_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    if res.returncode != 0:
        logger.error(dmp_file_path + ' 处理出错:' + res.stderr.readlines())
        return False

    logger.info('产生dmp结果完成：' + result_file_path)
    return True

#def analysis_dmp_result

def analysis_dmp_result(dmp_file_reuslt_dir):
    items =os.listdir(dmp_file_reuslt_dir)
    result_files = []
    for item in items:
        if item.endswith('.dmp.txt'): # 处理dmp崩溃信息
            result_files.append(item)
        elif item.endswith('.json'):  # 处理dmp json信息
            pass
 
if __name__ == '__main__':
    exec_file_list = []
    app_path = unzip_pkg(config.PKG_FOLDER_PATH + 'demo_1.1.4.2_1427_0371ff2_ReleasePDB.zip')
    get_execfiles_for_sym(app_path, exec_file_list)
    for exec_file in exec_file_list:
        export_exec_syms(exec_file, config.SYM_FOLDER_PATH)
    pass
