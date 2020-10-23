import os
import requests
import zipfile
import shutil

#逐个将.zip文件解压
def get_url_paths(url, ext='', params={}, exclude='', pref='',override=False):#获取该目录下所有子文件的路径
    for root1,dirs,files in os.walk(url):
        for name in files:
            path=os.path.join(root1,name)
            file_name, extension_name = os.path.splitext(name)
            if(extension_name=='.zip'):
                app_target_path=root1+'\\'+file_name
                f = zipfile.ZipFile(path)
                targetFolderPath=path
                if (not override) and os.path.exists(app_target_path):
                    print(app_target_path + '已经解压过了！！')
                #删除原来
                else:
                   f.extractall(root1)
                #if os.path.exists(targetFolderPath):
                    #os.remove(targetFolderPath)
                   
                #input('a')
    
           

                   

def get_url():
    workdir=os.getcwd()
    return workdir
if __name__ == "__main__":
    exec_file_list = []
    work_dir=get_url()
    file_url=get_url_paths(work_dir+'\\run'+'\dumpfiles')