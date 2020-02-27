# -*- coding: utf-8 -*-
from pathlib import Path
from arelle import ModelManager
from arelle import Cntlr
import os
import zipfile
import glob
import pandas as pd
from distutils import dir_util
import re


def make_edinet_info_list(edinetcodedlinfo_filepath):
    edinet_info = pd.read_csv(edinetcodedlinfo_filepath, skiprows=1,
                              encoding='cp932')
    edinet_info = edinet_info[["ＥＤＩＮＥＴコード", "提出者業種"]]
    edinet_info_list = edinet_info.values.tolist()
    return edinet_info_list


def unzip_file(zip_dir):
    edinetcodedlinfo_filepath = '/Users/keigo/TEST/EdinetcodeDlInfo.csv'
    edinet_info_list = make_edinet_info_list(edinetcodedlinfo_filepath)

    zip_files = glob.glob(os.path.join(zip_dir, '*.zip'))

    number_of_zip_lists = len(zip_files)
    print("number_of_zip_lists：", number_of_zip_lists)
    file_code_list = []

    for index, zip_file in enumerate(zip_files):
        print(zip_file, ":", index + 1, "/", number_of_zip_lists)
        # zipの保存先を作成
        _filepath = zip_file.split('/')[4]
        file_code = _filepath.split('.')[0]
        save_dir = '/Users/keigo/TEST/data/raw/' + file_code
        file_code_list.append(file_code)
        # save_dirにzipを保存
        with zipfile.ZipFile(zip_file) as zip_f:
            zip_f.extractall(save_dir)
            zip_f.close()

    edinet_company_info_list = []
    employee_frame = pd.DataFrame()
    # for 各企業の情報をmergeさせて持ってくる
    for index, _path in enumerate(file_code_list):
        dir_path = '/Users/keigo/TEST/data/raw/' + _path # _path はS100HHC0等のDOC_ID
        dir_copy = '/Users/keigo/TEST'
        dir_util.copy_tree(dir_path, dir_copy)  # これでデータを取りに行ける
        # 取りに行くデータをひとつづつ指定する
        file_target = glob.glob('/Users/keigo/TEST/data/raw/' + _path + '/XBRL/PublicDoc/*.xbrl')
        _path1 = file_target[0].split('/')[9]  # jpcrp030000-asr-001_E34729-000_2019-08-31_01_2019-11-27.xbrl

        xbrl_file_expression = '/Users/keigo/TEST/XBRL/PublicDoc/' + _path1
        xbrl_file = glob.glob(xbrl_file_expression)
        xbrl_file = ' '.join([str(elem) for elem in xbrl_file])
        _edinet_company_info_list = []

        edinet_company_info_list1, df_col_list = make_edinet_company_info_list(xbrl_file, edinet_info_list,
                                                                               _edinet_company_info_list, _path)
        edinet_company_info_list.append(edinet_company_info_list1)
        # print('This is Edinet_company_info' + str(edinet_company_info_list))
        employee_frame = write_csv_of_employee_info(edinet_company_info_list, df_col_list, index, employee_frame)
        edinet_company_info_list = []
    print("************* out of unzip_file **************")

    return employee_frame


def make_edinet_company_info_list(xbrl_file, edinet_info_list, edinet_company_info_list, _path):
    edinet_code = ""  # EDINETCODE
    filer_name_jp = ""  # 企業名
    industry_code = ""  # 業種
    sales_info = ""  # 売上高（円）
    ordinary_info = ""  # 経常収益（円）
    service_years = ""  # 事業年度（年）
    service_months = ""  # 平均勤続年数（月）
    age_years = ""  # 平均年齢（歳）
    age_months = ""  # 平均年齢（月）
    number_of_employees = ""  # 従業員数（人）
    company_info_list = []  # 企業情報

    model_xbrl = Cntlr.Cntlr().modelManager.load(xbrl_file)

    for fact in model_xbrl.facts:
        if fact.concept.qname.localName == 'EDINETCodeDEI':
            print("EDINETコード", fact.value)
            edinet_code = fact.value

            for code_name in edinet_info_list:
                if code_name[0] == edinet_code:
                    print("業種", code_name[1])
                    industry_code = code_name[1]
                    break

        elif fact.concept.qname.localName == 'FilerNameInJapaneseDEI':
            print("企業名", fact.value)
            filer_name_jp = fact.value

        elif fact.concept.qname.localName == 'NetSalesSummaryOfBusinessResults':
            print("売上高（円）", fact.value)
            sales_info = fact.value

        elif fact.concept.qname.localName == 'NetAssetsSummaryOfBusinessResults':
            print("純資産額（円）", fact.value)
            ordinary_info = fact.value

        elif fact.concept.qname.localName == 'FiscalYearCoverPage':
            print("事業年度", fact.value)
            service_years = fact.value

    print("")
    company_info_list.append(edinet_code)
    company_info_list.append(filer_name_jp)
    company_info_list.append(industry_code)
    company_info_list.append(sales_info)
    company_info_list.append(ordinary_info)

    if len(service_months) != 0:
        service_years_decimal = round(int(service_months) / 12, 1)
        service_years = int(service_years) + service_years_decimal
        service_years = str(service_years)

    company_info_list.append(service_years)

    if len(age_months) != 0:
        age_years_decimal = round(int(age_months) / 12, 1)
        age_years = int(age_years) + age_years_decimal
        age_years = str(age_years)

    # ここからmegi2_test.py とやつと合体させます
    import megi2_test

    new_list, df_col_list = megi2_test.main(_path)

    # Merge newlist & company_info_list
    final_list = company_info_list + new_list
    print('%%%%%%%%%%%% This is final list %%%%%%%%%%%%%%')
    print(final_list)
    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

    return final_list, df_col_list

def write_csv_of_employee_info(edinet_company_info_list, df_col_list, index, employee_frame):
    col_this_code = ['EDINETCODE', '企業名', '業種', '売上高（円）', '純資産額(円)', '事業年度']
    col_final = col_this_code + df_col_list
    com_code = edinet_company_info_list[0][0]
    _employee_frame = pd.DataFrame(edinet_company_info_list, columns=col_final)


    # columns=['EDINETCODE', '企業名', '業種', '売上高（円）', '純資産額(円)',  '事業年度'])
    print('index :' + str(index))
    print(_employee_frame)


    def duplicated_varnames(df):
        """Return a dict of all variable names that
        are duplicated in a given dataframe."""
        repeat_dict = {}
        var_list = list(df)  # list of varnames as strings
        for varname in var_list:
            # make a list of all instances of that varname
            test_list = [v for v in var_list if v == varname]
            # if more than one instance, report duplications in repeat_dict
            if len(test_list) > 1:
                repeat_dict[varname] = len(test_list)
        return repeat_dict

    """ If you wanna check 'Duplicated words' run below code :
            dup = duplicated_varnames(_employee_frame)
            print('dup before :' + str(dup))
    """
    dup = duplicated_varnames(_employee_frame)
    print('dup before :' + str(dup))

    _col = _employee_frame.columns.tolist()
    _val = _employee_frame.values.tolist()
    dup = duplicated_varnames(_employee_frame)
    for key, val in dup.items():
        for v in range(val):
            for i in range(len(_col)):
                if _col[i] == key:
                    _col[i] = key+str(v)
                    break
    _employee_frame = pd.DataFrame(_val, columns=_col)

    dup = duplicated_varnames(_employee_frame)
    print('dup after :' + str(dup))

    # Execute
    if index == 0:
        employee_frame = _employee_frame
        print(employee_frame)

    else:
        print('When index != 0')
# Making the same columns
        for c in _employee_frame.columns:
            if c not in employee_frame.columns:
                employee_frame[c] = None
        for c in employee_frame.columns:
            if c not in _employee_frame.columns:
                _employee_frame[c] = None

        dup_em = duplicated_varnames(employee_frame)
        dup_em1 = duplicated_varnames((_employee_frame))

        print('dup_em :' + str(dup_em))
        print('dup_em1 :' + str(dup_em1))

        print('AFTER FIXED')
        employee_frame = pd.concat([employee_frame, _employee_frame], join="outer", sort=False)
        print(employee_frame)

    return employee_frame

def main():
    edinetcodedlinfo_filepath = '/Users/keigo/TEST/EdinetcodeDlInfo.csv'
    edinet_info_list = make_edinet_info_list(edinetcodedlinfo_filepath)

    zip_dir = '/Users/keigo/TEST/'
    employee_frame = unzip_file(zip_dir)

    print(employee_frame)
    employee_frame.to_csv("/Users/keigo/TEST/try2.csv", encoding='utf-8-sig')
    print("extract finish")

if __name__ == "__main__":
    main()
