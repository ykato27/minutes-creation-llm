# minutes-creation-llm

## 概要
力量マップ関連のCSVファイル（カテゴリ・スキル・教育・資格）を統合・加工し、最終的な力量マップCSVを生成するStreamlitアプリです。

## 必要要件
- Python 3.8以上
- 必要パッケージ: streamlit>=1.28.0, pandas>=2.0.0, numpy>=1.24.0

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
2. ブラウザで表示されるUIに従い、以下の手順で操作してください。
	1. ステップ1: 力量マップの基本情報を入力し「情報を確定」
	2. ステップ2: 力量カテゴリCSVファイルをアップロード
	3. ステップ3: 力量（スキル/教育/資格）のCSVファイルを1つ以上アップロード
	4. ステップ4: 「処理を開始」ボタンをクリックし、結果CSVをダウンロード

## 入力ファイルについて
- 力量カテゴリCSV: 必須（「力量カテゴリー」列が必要）
- 力量（スキル/教育/資格）CSV: いずれか1つ以上必須

## 出力
- 加工済みのCSVファイル（competence_map_related_item_for_map.csv）をダウンロードできます。

## 注意事項
- 入力CSVの列名や形式はサンプルに従ってください。
- ファイルサイズや行数が多い場合、処理に時間がかかることがあります。

## ライセンス
MIT License