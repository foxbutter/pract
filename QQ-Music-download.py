# -*- coding:utf-8 -*-
import requests
import re
def parse_17(song_name):
    base_url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
    headers = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
    }
    parames = {
        'ct': 24,
        'qqmusic_ver': 1298,
        ' new_json': 1,
        'remoteplace': 'txt.yqq.top',
        'searchid': 34725291680541638,
        't': 0,
        'aggr': 1,
        'cr': 1,
        'ca tZhida': 1,
        'lossless': 0,
        'flag_qc': 0,
        'p': 1,
        'n': 20,
        'w': song_name,
        'g_tk': 5381,
        'jsonp Callback': 'MusicJsonCallback703296236531272',
        'loginUin': 0,
        'hostUin': 0,
        'format': 'jsonp',
        'inCharset': 'utf8',
        'outCharset ': 'utf-8',
        'notice': 0,
        'platform': 'yqq',
        'needNewCode': 0,
    }

    r = requests.get(base_url,params=parames,headers=headers)

    return_data = r.text
    pattern_17 = re.compile('\\((.*)?\\)')
    return_data_json = eval(pattern_17.search(return_data)[0].replace("null","None"))
    data = return_data_json["data"]["song"]["list"]
    for n,d in enumerate(data):
        songmid = (d['songmid'])
        strMediaMid = (d['strMediaMid'])

        parse_17_2 (songmid,strMediaMid,n+1,song_name)

def parse_17_2(songmid,strMediaMid,n,song_name):
    headers = {
        'use-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }
    base_url2 = "https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg"
    params_2 = {
        'g_tk': '5381',
        'jsonpCallback':'MusicJsonCallback9239412173137234',
        'loginUin':'0' ,
        'hostUin':'0' ,
        'format': 'json',
        'inCharset' :'utf8' ,
        'outCharset' :'utf-8',
        'notice': '0' ,
        'platform' :'yqq',
        'needNewCode':'0' ,
        'cid': '205361747' ,
        'callback': 'MusicJsonCallback9239412173137234' ,
        'uin' : '0' ,
        'songmid':songmid ,
        'filename': 'C400'+strMediaMid+'.m4a' ,
        'guid': '8208467632'
    }

    r = requests.get(base_url2,params=params_2,headers=headers)
    return_data = r.text
    pattern_17 = re.compile('\\((.*)?\\)')
    return_data_json = eval(pattern_17.search(return_data)[0].replace("null","None"))
    data = return_data_json["data"]["items"][0]
    filename = data['filename']
    vkey = data['vkey']

    parse_17_3(filename,vkey,n,song_name)

def parse_17_3(filename,vkey,n,song_name):
    url = "http://dl.stream.qqmusic.qq.com/"
    url = url + filename
    params = {
        'vkey': vkey ,
        'guid': '8208467632' ,
        'uin':'0'  ,
        'fromtag':'66'
    }
    headers = {
        'use-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }

    r = requests.get(url,params=params,headers=headers)
    filename = song_name + str(n) + ".m4a"
    with open(filename,"wb") as f :
        f.write(r.content)
    print("第%s首歌曲下载完成"%n)

if __name__ == "__main__":
    # filename = input("输入要下载的歌曲名:")
    parse_17("晴天")