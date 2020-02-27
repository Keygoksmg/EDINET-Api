# -*- coding: utf-8 -*-

import requests
import datetime
import zipfile


def make_day_list(start_date, end_date):
    print("start_date：", start_date)
    print("end_day：", end_date)

    period = end_date - start_date
    period = int(period.days)
    day_list = []
    for d in range(period):
        day = start_date + datetime.timedelta(days=d)
        day_list.append(day)

    day_list.append(end_date)

    return day_list


def make_doc_id_list(day_list):
    securities_report_doc_list = []
    for index, day in enumerate(day_list):
        url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents.json"
        params = {"date": day, "type": 2}

        proxies = {
            "http_proxy": "http://username:password@proxy.example.com:8080",
            "https_proxy": "https://username:password@proxy.example.com:8080"
        }

        res = requests.get(url, params=params, proxies=proxies)
        json_data = res.json()
        print(day)

        for num in range(len(json_data["results"])):

            ordinance_code = json_data["results"][num]["ordinanceCode"]
            form_code = json_data["results"][num]["formCode"]

            if ordinance_code == "010" and form_code == "030000":
                print(json_data["results"][num]["filerName"], json_data["results"][num]["docDescription"],
                      json_data["results"][num]["docID"])
                securities_report_doc_list.append(json_data["results"][num]["docID"])

    return securities_report_doc_list


def download_xbrl_in_zip(securities_report_doc_list, number_of_lists):
    for index, doc_id in enumerate(securities_report_doc_list):
        print(doc_id, ":", index + 1, "/", number_of_lists)
        url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/" + doc_id
        params = {"type": 1}
        filename = doc_id + ".zip"
        res = requests.get(url, params=params, stream=True)

        if res.status_code == 200:
            with open(filename, 'wb') as file:
                for chunk in res.iter_content(chunk_size=1024):
                    file.write(chunk)

        # with zipfile.ZipFile(filename) as existing_zip:
        #     existing_zip.extractall(doc_id)


def main():
    start_date = datetime.date(2019, 11, 1)
    end_date = datetime.date(2019, 11, 15)
    day_list = make_day_list(start_date, end_date)

    securities_report_doc_list = make_doc_id_list(day_list)
    number_of_lists = len(securities_report_doc_list)
    print("number_of_lists：", len(securities_report_doc_list))
    print("get_list：", securities_report_doc_list)

    download_xbrl_in_zip(securities_report_doc_list, number_of_lists)
    print("download finish")


if __name__ == "__main__":
    main()
