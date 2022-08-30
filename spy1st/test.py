import os

import requests


def file_name_walk(file_dir):
    name_file_mapping = dict()
    for file in os.listdir(file_dir):
        if not file.split("@")[0].isdigit():
            print("err file: ", file)
            continue

        name_file_mapping[int(file.split("@")[0])] = os.path.join(file_dir, file)

        url = "http://admin.narumon.cn/image/multiple_upload/"

        querystring = {"return": "url"}

        payload = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"path\"\r\n\r\n8059894@1x.png\r\n-----011000010111000001101001--\r\n\r\n"
        headers = {
            "Cookie": "experimentation_subject_id=IjY0N2IwNjNhLTcwYWYtNDIwNC1iMjZiLTIyMTljYWE3NjQ4MCI%3D--04525c1bffee7ec3fe18ba2a409456cac714ff14; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218216634bc8335-01e878cd14b802e-1c525635-1296000-18216634bc9574%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218216634bc8335-01e878cd14b802e-1c525635-1296000-18216634bc9574%22%7D; csrftoken=ZZs4HQACHRSb3Rgiqd4TwqYtvZJN6BEwP4ZKjgc2AriJuG1Bzi4n6HMbWmL1JMtz; sessionid=o2070c2l21vl7melkgbsqsr7tl72tkra",
            "Content-Type": "multipart/form-data"
        }

        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        print(response.text)
        return name_file_mapping
    return name_file_mapping


if __name__ == '__main__':
    main_img_mapping = file_name_walk("/Users/hh/Downloads/主图导出/")
    # logo_img_mapping = file_name_walk("/Users/hh/Downloads/品牌logo导出/")

