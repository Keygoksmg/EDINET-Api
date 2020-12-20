# EDINET-Api
EDINETのApiを使って各企業の有価証券報告書などのデータを抽出します <br>


## Overview
get_zip.py : 指定した期間ないに提出された書類をzipfileで取得

get_info_from_csv.py : タクソノミを利用して取得可能な表からデータを取得します <br>

get_info.py : 取得した各書類のzipfileから情報を取得します。その後get_info_from_csv.pyで取得したデータとマージさせて結果を返します。

EdinetcodeDlInfo.csv : タクソノミをつかってデータを取得する際に参照するcsv

file : 一時的に使うディレクトリなので消さないでください

data : タクソノミ原本が保存されているディレクトリ

data/raw : zipから回答された書類データが保存されます

data/external : タクソノミ原本が保存されてます

## Requirement
python

(もしpythonの環境がなかった場合: https://prog-8.com/docs/python-env)

## Usage
以下のコードでpython fileを走らせてください

1 <br>
python get_zip.py : 指定した日付間に提出された書類を取得します。<br>
データはget_zip.py内に保存されます


2 <br>
python get_info.py : 取得したzipfileのデータを取得します path ('/Users/keigo/TEST/のようなものを) を自分のものに変更してください

3 <br>
'/home/nagat/' に関するエラーが出た場合は <br>
File "/Users/keigo/.pyenv/versions/3.6.2/lib/python3.6/site-packages/arelle/Cntlr.py", line 235, in __init__ <br>
をクリックして, Cntlr.py の中の # self.userAppDir = r'/home/nagat/.local/lib/python3.5/site-packages/arelle'
 を # でコメントアウト
 →ryというディレクトリーができますが関係ないので無視してください
 
4 <br>
これでエラーが無くなったらpython get_info.py で情報をゲットできる

(注) get_info_from_csv.py は get_info.py の中で使っています。
(注) path の変更はget_info.py だけで大丈夫です

 
## 参考にした記事
報告書インスタンス 作成ガイドライン(https://www.fsa.go.jp/search/20140919/2b_1.pdf)

XBRLから上場企業の決算書の情報を得る。(https://qiita.com/teatime77/items/3ed6d4cd27f6440e163a#xbrl%E3%81%A8%E3%81%AF)

タクソノミを使ってデータを取る (https://medium.com/programming-soda/%E8%B2%A1%E5%8B%99%E5%88%86%E6%9E%90%E3%81%AB%E6%AC%A0%E3%81%8B%E3%81%9B%E3%81%AA%E3%81%84-xbrl%E3%82%92%E7%90%86%E8%A7%A3%E3%81%99%E3%82%8B-part3-4cffee01d92a)

EDINET XBRLの勘定科目タグ集約リスト(https://srbrnote.work/archives/1615)

EDINET APIについて (https://qiita.com/XBRLJapan/items/27e623b8ca871740f352)

EDINET XBRLを読み込むPythonライブラリ【有報対応】(https://srbrnote.work/archives/1430)

get_zip.py の元になった記事 (有価証券報告書以外の報告書の集め方): (https://qiita.com/XBRLJapan/items/27e623b8ca871740f352)