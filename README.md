# minutes-creation-llm

## 概要
このアプリは、力量マップ関連のCSVファイルを簡単に生成・加工できるStreamlitアプリです。
複数のCSV（力量カテゴリ、スキル、教育、資格）をアップロードし、必要な情報をまとめた新しいCSVをダウンロードできます。

## 必要要件
- Python 3.8以上
- 必要パッケージ: streamlit, pandas, numpy

## セットアップ方法
1. リポジトリをクローン
	```bash
	git clone https://github.com/ykato27/minutes-creation-llm.git
	cd minutes-creation-llm
	```
2. 必要なパッケージをインストール
	```bash
	pip install -r requirements.txt
	```

## 使い方
1. Streamlitアプリを起動
	```bash
	streamlit run app.py
	```
2. ブラウザで表示されるUIに従い、必要な情報を入力し、CSVファイルをアップロードしてください。
3. 「データ処理を実行」ボタンを押すと、処理結果のCSVをダウンロードできます。

## 入力ファイルについて
- 力量カテゴリCSV: 必須
- 力量（スキル/教育/資格）CSV: いずれか1つ以上必須

## 出力
- 加工済みのCSVファイル（competence_map_related_item_for_map.csv）をダウンロードできます。

## ライセンス
MIT License