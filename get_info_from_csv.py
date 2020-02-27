import os
from pathlib import Path
import edinet
import requests
from datetime import datetime
from zipfile import ZipFile
import requests
import zipfile
import glob
import pandas as pd
import os
from bs4 import BeautifulSoup
import sys
from edinet.xbrl_file import XBRLDir

class Element():
    def __init__(self, name, element, location, taxonomy):
        self.name = name
        self.element = element
        self.location = location
        self.taxonomy = taxonomy

    def definition(self):
        def_dir = self.taxonomy.root
        path, element_name = self.location.split("#")
        location = self.location

        if path.startswith(self.taxonomy.reference_prefix):
            path = path.replace(self.taxonomy.reference_prefix, "")
            path = os.path.join(self.taxonomy.reference_root, path)
        else:
            path = os.path.join(self.taxonomy.root, path)

        xml = self.taxonomy._read_from_cache(path)
        _def = xml.find("xsd:element", {"id": element_name})
        return _def

    def label(self, kind="ja", verbose=True):
        label_ext = "_lab.xml"
        if kind == "en":
            label_ext = "_lab-en.xml"
        elif kind == "g":
            label_ext = "_gla.xml"

        label = None
        label_dir = self.taxonomy.root
        path, element_name = self.location.split("#")
        location = self.location

        if path.startswith(self.taxonomy.reference_prefix):
            path = path.replace(self.taxonomy.reference_prefix, "")
            label_dir_reference = os.path.join(
                self.taxonomy.reference_root,
                f"{os.path.dirname(path)}/label")
            label_dir = label_dir_reference
            location = f"../{os.path.basename(path)}#{element_name}"

        targets = []
        for f in os.listdir(label_dir):
            label_path = os.path.join(label_dir, f)
            if not label_path.endswith(label_ext):
                continue

            label_xml = self.taxonomy._read_from_cache(label_path)
            targets = self._read_link(
                xml=label_xml, arc_name="link:labelArc", location=location,
                target_name="link:label", target_attribute="id")

        if len(targets) > 1:
            for lb in targets:
                if lb["xlink:role"].endswith("verboseLabel") and verbose:
                    label = lb
                    break
                else:
                    label = lb

        elif len(targets) > 0:
            label = targets[0]

        return label

    def _read_link(self, xml, arc_name, location="",
                   target_name="", target_attribute=""):

        location = location if location else self.location
        label = xml.find("link:loc", {"xlink:href": location})
        arc = None

        if label is not None:
            arc = xml.find(arc_name, {"xlink:from": label["xlink:label"]})
        else:
            arc = xml.find(arc_name, {"xlink:label": self.name})

        if arc is None:
            return []

        target_name = target_name if target_name else "link:loc"
        target_attribute = target_attribute if target_attribute else "xlink:label"
        targets = []
        if arc is not None:
            targets = xml.find_all(target_name, {target_attribute: arc["xlink:to"]})

        return targets

class Taxonomy():
    def __init__(self, root, reference_root, reference_prefix=""):
        self.root = root
        self.reference_root = reference_root
        self.reference_prefix = reference_prefix
        self._cache = {}
        if not self.reference_prefix:
            self.reference_prefix = "http://disclosure.edinet-fsa.go.jp/taxonomy/"

    def _read_from_cache(self, path):
        xml = None
        if path in self._cache:
            xml = self._cache[path]
        else:
            with open(path, encoding="utf-8-sig") as f:
                xml = BeautifulSoup(f, "lxml-xml")
            self._cache[path] = xml
        return self._cache[path]

    def read(self, href):
        path = href
        element = ""
        use_parent = False

        if "#" in path:
            path, element = path.split("#")

        if path.startswith(self.reference_prefix):
            path = path.replace(self.reference_prefix, "")
            path = os.path.join(self.reference_root, path)
        else:
            path = os.path.join(self.root, path)

        xml = self._read_from_cache(path)

        if element:
            xml = xml.select(f"#{element}")
            if len(xml) > 0:
                xml = xml[0]
            xml = Element(element, xml, href, self)

        return xml

class Node():
    def __init__(self, element, order=0):
        self.element = element
        self.parent = None
        self.order = order

    def add_parent(self, parent):
        self.parent = parent

    @property
    def name(self):
        return self.element["xlink:href"].split("#")[-1]

    @property
    def label(self):
        return self.element["xlink:label"]

    @property
    def location(self):
        return self.element["xlink:href"]

    @property
    def depth(self):
        return len(self.get_parents())

    @property
    def path(self):
        parents = list(reversed(self.get_parents()))
        if len(parents) == 0:
            return self.name
        else:
            path = str(self.order) + " " + self.name
            for p in parents:
                path = p.name + "/" + path
            return path
    def get_parents(self):
        parents = []
        if self.parent is None:
            return parents
        else:
            p = self.parent
            while p is not None:
                parents.insert(0, p)
                p = p.parent
            return parents

#*****************************************************************************************************************

def main(DOC_ID):
    # 企業を選択
    DOC_ID = str(DOC_ID)
    print(DOC_ID)
    # DOC_ID = DOC_ID
    # Data Folder
    DATA_ROOT = Path.cwd().joinpath("data")
    # Confirm fiscal year and date
    from edinet.xbrl_file import XBRLDir
    # Download and load document
    xbrl_path = edinet.api.document.get_xbrl(
        DOC_ID, save_dir=DATA_ROOT.joinpath("raw"),
        expand_level="dir")
    xbrl_dir = XBRLDir(xbrl_path)

    # タクソノミの年を選択
    taxonomy_year = 2018
    """
    fiscal_year_end = xbrl_dir.xbrl.find("jpdei_cor:CurrentFiscalYearEndDateDEI").text
    fiscal_year_end = datetime.strptime(fiscal_year_end, "%Y-%m-%d")
    taxonomy_year = -1
    for y in taxonomies:
        boarder_date = datetime(y, 3, 16)
        if fiscal_year_end > boarder_date:
            taxonomy_year = y
        else:
            break
    """
    # タクソノミ・ファイルの設定
    external_dir = DATA_ROOT.joinpath("external")
    expand_dir = external_dir.joinpath("taxonomy").joinpath(str(taxonomy_year))
    taxonomy_file = external_dir.joinpath(f"{taxonomy_year}_taxonomy.zip")

    # 実行
    taxonomy = Taxonomy(xbrl_dir._document_folder, expand_dir)

    # 表のリストの表示
    print('インスタンス文書で使用されている表示リンク一覧; 以下の文書は表示させれます')
    role_ref_tags = xbrl_dir.xbrl.find_all("link:roleRef")
    role_ref_elements = [t.element for t in role_ref_tags]
    # print(role_ref_elements)
    role_refs = {}
    for e in role_ref_elements:
        role_refs[e["roleURI"]] = e["xlink:href"]

    roles = {}
    for r in role_refs:
        role_name = taxonomy.read(role_refs[r]).element.find("link:definition").text
        try:
            role_name = role_name.split()[1]
        except:
            None
        roles[role_name] = r
    #     print(roles[role_name]) #url/場所を示す

    # 表示させたい表を示したかったらコメントアウトを外してください

    # Show roles
    for r in roles:
        print(f"{r}\t{roles[r]}")

    if not "連結貸借対照表" in roles:
        df_val_list, df_col_list = [], []
    else:
        # 表を抽出ステップ１
        pre_def = xbrl_dir.pre.find(
            "link:presentationLink", {"xlink:role": roles["連結貸借対照表"]})

        nodes = {}
        for i, arc in enumerate(pre_def.find_all("link:presentationArc")):
            if not arc["xlink:arcrole"].endswith("parent-child"):
                print("Unexpected arctype.")
                continue

            parent = Node(pre_def.find("link:loc", {"xlink:label": arc["xlink:from"]}), i)
            child = Node(pre_def.find("link:loc", {"xlink:label": arc["xlink:to"]}), arc["order"])

            if child.name not in nodes:
                nodes[child.name] = child
            else:
                nodes[child.name].order = arc["order"]

            if parent.name not in nodes:
                nodes[parent.name] = parent

            nodes[child.name].add_parent(nodes[parent.name])

        # ステップ２
        parent_depth = -1
        for name in nodes:
            if parent_depth < nodes[name].depth:
                parent_depth = nodes[name].depth

        data = []
        for name in nodes:
            n = nodes[name]
            item = {}
            parents = n.get_parents()
            parents = parents + ([""] * (parent_depth - len(parents)))

            for i, p in enumerate(parents):
                name = p if isinstance(p, str) else p.name
                order = "0" if isinstance(p, str) else p.order
                item[f"parent_{i}"] = name
                item[f"parent_{i}_order"] = order

            item["element"] = n.name
            item["order"] = n.order
            item["depth"] = n.depth

            # print(n.location)
            # Label
            if taxonomy.read(n.location).label() == None:
                print('There is nothing')
            else:
                # Definition
                _def = taxonomy.read(n.location).definition()
                # print(_def)
                item["label"] = taxonomy.read(n.location).label().text
                item["abstract"] = _def["abstract"]
                item["type"] = _def["type"]

                if "xbrli:periodType" in _def.attrs:
                    item["period_type"] = _def["xbrli:periodType"]

                if "xbrli:balance" in _def.attrs:
                    item["balance"] = _def["xbrli:balance"]

                data.append(item)

        data = pd.DataFrame(data)
        data.sort_values(by=[c for c in data.columns if c.endswith("order")], inplace=True)

        # ファイルを探す
        xbrl = xbrl_dir.xbrl
        schema = xbrl.find("xbrli:xbrl")
        namespaces = {}
        for a in schema.element.attrs:
            if a.startswith("xmlns:"):
                namespaces[a.replace("xmlns:", "")] = schema.element.attrs[a]

        # ステップ３ データを丸ごと取ってくる
        # ステップ３ データを丸ごと取ってくる
        xbrl_data = []

        for i, row in data.iterrows():
            tag_name = row["element"]

            for n in namespaces:
                if tag_name.startswith(n):
                    tag_name = f"{n}:{tag_name.replace(n + '_', '')}"
                    break

            tag = xbrl.find(tag_name)
            element = tag.element
            if element is None:
                continue

            item = {}
            for k in data.columns:
                item[k] = row[k]

            for i in range(parent_depth):
                parent_label = data[data["element"] == row[f"parent_{i}"]]["label"]
                item[f"parent_{i}_name"] = "" if len(parent_label) == 0 else parent_label.tolist()[0]

            item["value"] = element.text
            item["unit"] = element["unitRef"]

            context_id = element["contextRef"]
            if context_id.endswith("NonConsolidatedMember"):
                item["individual"] = True
            else:
                item["individual"] = False

            context = xbrl.find("xbrli:context", {"id": context_id})
            if item["period_type"] == "duration":
                item["period"] = context.find("xbrli:endDate").text
                item["period_begin"] = context.find("xbrli:startDate").text
            else:
                item["period"] = context.find("xbrli:instant").text
                item["period_begin"] = None

            xbrl_data.append(item)

        xbrl_data = pd.DataFrame(xbrl_data)

        # ステップ4 csvfileにして企業IDを付け加える準備
        # xbrl_data.to_csv
        xbrl_data.to_csv("xbrl_data.csv", index=False, encoding='utf-8-sig')

        # Read and make desiable table
        df = pd.read_csv("xbrl_data.csv")

        try:
            df = df.drop(['abstract', 'balance', 'depth', 'element', 'individual',
                          'order', 'parent_0', 'parent_0_name', 'parent_0_order',
                          'parent_1', 'parent_1_name', 'parent_1_order', 'parent_2',
                          'parent_2_name', 'parent_2_order', 'parent_3', 'parent_3_name',
                          'parent_3_order', 'parent_4', 'parent_4_name', 'parent_4_order',
                          'parent_5', 'parent_5_name', 'parent_5_order', 'period', 'period_begin',
                          'period_type', 'type', 'unit'], axis=1)
        except:
            df = df.drop(['abstract', 'balance', 'depth', 'element', 'individual',
                          'order', 'parent_0', 'parent_0_name', 'parent_0_order',
                          'parent_1', 'parent_1_name', 'parent_1_order', 'parent_2',
                          'parent_2_name', 'parent_2_order', 'parent_3', 'parent_3_name',
                          'parent_3_order', 'parent_4', 'parent_4_name', 'parent_4_order',
                          'period', 'period_begin', 'period_type', 'type', 'unit'], axis=1)

        df1 = df.copy()
        df1.set_index('label')
        df2 = df1.transpose()

        for i in range(len(df2.columns)):
            temp = df2.loc['label', i]
            df2 = df2.rename(columns={i: temp})

        df3 = df2.drop(index=['label'])

        # このfileだけrunする時にcsvに保存
        # df3.to_csv("df3.csv", index=False, encoding='utf-8-sig')
        # print(type(df3))
        df_val_list = df3.values.tolist()
        df_val_list = df_val_list[0]
        # print(df_val_list)
        df_col_list = df3.columns.tolist()

    return df_val_list, df_col_list


# if __name__ == "megi1_test":
#     main()
def run_megi2_test():
    if __name__ == "__main__":
        list2, df_col_list = main()
        return list2, df_col_list
    else:
        print(__name__)


if __name__ == "__main__":
    main('S100HG62')
