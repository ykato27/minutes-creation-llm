# app.py

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- ページ設定とセッションステートの初期化 ---
st.set_page_config(page_title="力量マップCSV生成ツール", layout="centered")
st.title("📊 力量マップCSV生成ツール")

# final_dfをセッションステートで初期化
if 'final_df' not in st.session_state:
    st.session_state['final_df'] = pd.DataFrame()


# --- データ処理関数 (既存のロジックをそのまま移植) ---
def split_competence_category(df):
    """力量カテゴリーを「＞」で分割して20列に展開"""
    # NaNを一時的に空文字列に変換してsplitを適用
    df['力量カテゴリー'] = df['力量カテゴリー'].astype(str).str.strip()
    split_data = df['力量カテゴリー'].str.split('＞', expand=True)

    if split_data.shape[1] > 20:
        split_data = split_data.iloc[:, :20]

    split_data = split_data.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    split_data = split_data.replace('', np.nan)

    # 20列に満たない場合、NaNで列を埋める
    for i in range(split_data.shape[1], 20):
        split_data[i] = np.nan

    split_data.columns = [f'力量カテゴリー名  ###[competence_category_name_{i}]###' for i in range(1, 21)]

    # 元の df に結合する前に、元の df に'力量カテゴリー'のカラムが残っているか確認（Colab版と挙動を合わせるため）
    if '力量カテゴリー' not in df.columns:
         df['力量カテゴリー'] = split_data.apply(lambda row: "＞".join(row.dropna().astype(str)), axis=1)

    return pd.concat([df.reset_index(drop=True), split_data.reset_index(drop=True)], axis=1)


def build_category_path(df):
    """カテゴリー名から階層パスを生成"""
    category_cols = [f'力量カテゴリー名  ###[competence_category_name_{i}]###'
                     for i in range(1, 21)
                     if f'力量カテゴリー名  ###[competence_category_name_{i}]###' in df.columns]

    df["category_path"] = df[category_cols].apply(
        lambda row: "＞".join([str(x).strip() for x in row if pd.notna(x)]), axis=1
    )

    return df, category_cols


def expand_with_skill_codes(df_output, df_competence, item_type_name, skill_code_col):
    """力量カテゴリーと力量コードを統合してマップ行を生成"""
    results = []
    
    # 既存のカテゴリーパスを先に作成（df_competenceはすでにパスを持っている前提）

    for _, comp_row in df_competence.iterrows():
        comp_path = comp_row["category_path"]

        # 力量カテゴリ行を追加
        category_row_dict = {"アイテムタイプ  ###[item_type]###": "CATEGORY_IN_MAP"}

        for i in range(1, 21):
            old_col = f'力量カテゴリー名  ###[competence_category_name_{i}]###'
            new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'
            category_row_dict[new_col] = comp_row.get(old_col, np.nan)

        results.append(category_row_dict)

        # マッチする力量コード行を追加
        matched_rows = df_output[df_output["category_path"] == comp_path]

        for _, out_row in matched_rows.iterrows():
            skill_row_dict = {"アイテムタイプ  ###[item_type]###": item_type_name}

            # カテゴリー名をコピー
            for i in range(1, 21):
                old_col = f'力量カテゴリー名  ###[competence_category_name_{i}]###'
                new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'

                val = comp_row.get(old_col)
                skill_row_dict[new_col] = val if pd.notna(val) else np.nan

            # 左から順に探して最初のNULLに力量コードを挿入
            for i in range(1, 21):
                new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'
                if pd.isna(skill_row_dict[new_col]):
                    skill_row_dict[new_col] = out_row[skill_code_col]
                    break

            results.append(skill_row_dict)

    df_result = pd.DataFrame(results)

    # カラムの順序を整理
    item_type_col = "アイテムタイプ  ###[item_type]###"
    item_code_cols = [f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###' for i in range(1, 21)]
    cols = [item_type_col] + item_code_cols
    cols = [c for c in cols if c in df_result.columns]

    return df_result[cols]


def process_skill_file(file_content, df_competence, item_type_name, skill_code_col):
    """スキル/教育/資格ファイルを処理してマップ行を生成"""
    # StreamlitのファイルアップローダーはBytesIOライクなオブジェクトを返すため、そのまま使用
    df_skill = pd.read_csv(file_content)
    df_skill = split_competence_category(df_skill)
    df_skill, _ = build_category_path(df_skill)
    
    # df_competenceも処理が必要
    df_competence_copy = df_competence.copy()
    df_competence_copy = split_competence_category(df_competence_copy)
    df_competence_copy, _ = build_category_path(df_competence_copy)

    return expand_with_skill_codes(df_skill, df_competence_copy, item_type_name, skill_code_col)


# --- UI: ステップ1: 力量マップ情報を入力 ---
st.header("📋 ステップ1: 力量マップ情報を入力")

col1, col2 = st.columns(2)
with col1:
    主管プロジェクト = st.text_input("主管プロジェクト", "11_デモ_設備部")
    力量マップコード = st.text_input("力量マップコード", "GuRdXPEmx6y5EqcMeyKA")
with col2:
    力量マップ名 = st.text_input("力量マップ名", "デモ_力量マップ")
    フォルダ名 = st.text_input("フォルダ名", "")


# --- UI: ステップ2: 力量カテゴリCSVファイルをアップロード ---
st.header("📁 ステップ2: 力量カテゴリCSVファイルをアップロード (必須)")
uploaded_competence = st.file_uploader(
    "competence_category.csvを選択", 
    type=["csv"], 
    key="comp_uploader"
)


# --- UI: ステップ3: 力量CSVファイルをアップロード ---
st.header("📁 ステップ3: 力量CSVファイルをアップロード (いずれか1つ以上必須)")

uploaded_skill = st.file_uploader("力量（スキル）CSV", type=["csv"], key="skill_uploader")
uploaded_education = st.file_uploader("力量（教育）CSV", type=["csv"], key="edu_uploader")
uploaded_license = st.file_uploader("力量（資格）CSV", type=["csv"], key="lic_uploader")

# --- UI: ステップ4: 実行ボタン ---
st.markdown("---")
if st.button("⚙️ データ処理を実行", type="primary"):
    # 必須入力チェック
    if not all([主管プロジェクト.strip(), 力量マップコード.strip(), 力量マップ名.strip(), uploaded_competence]):
        st.error("❌ 主管プロジェクト、力量マップコード、力量マップ名、および力量カテゴリファイルのアップロードは必須です。")
        st.stop()
        
    uploaded_files = {
        'skill': uploaded_skill,
        'education': uploaded_education,
        'license': uploaded_license
    }
    if all(f is None for f in uploaded_files.values()):
        st.error("❌ 力量（スキル/教育/資格）のいずれか1つ以上のCSVファイルをアップロードしてください。")
        st.stop()

    # ローディングスピナー表示
    with st.spinner('⏳ データ処理中...'):
        try:
            # 力量カテゴリファイルの読み込み
            df_competence = pd.read_csv(uploaded_competence)

            # 各ファイルを処理
            all_results = []
            file_configs = [
                ('skill', "SKILL", "力量コード  ###[skill_code]###"),
                ('education', "EDUCATION", "力量コード  ###[education_code]###"),
                ('license', "LICENSE", "力量コード  ###[license_code]###")
            ]

            for file_key, item_type, code_col in file_configs:
                file_content = uploaded_files[file_key]
                if file_content is not None:
                    df_result = process_skill_file(file_content, df_competence, item_type, code_col)
                    all_results.append(df_result)
                else:
                    st.info(f"⊘ {item_type}ファイル: スキップ（未アップロード）")

            # 結果を統合
            if not all_results:
                st.error("処理する力量データがありませんでした。")
                st.stop()

            final_df = pd.concat(all_results, ignore_index=True)

            # --- 既存のソートと重複削除ロジック ---
            item_code_cols = [f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###' for i in range(1, 21)]

            def get_category_path(row):
                path_parts = []
                for col in item_code_cols:
                    if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
                        path_parts.append(str(row[col]).strip())
                return "＞".join(path_parts)

            final_df["_sort_path"] = final_df.apply(get_category_path, axis=1)
            item_type_order = {"CATEGORY_IN_MAP": 0, "SKILL": 1, "EDUCATION": 2, "LICENSE": 3}
            final_df["_item_type_order"] = final_df["アイテムタイプ  ###[item_type]###"].map(lambda x: item_type_order.get(x, 99))
            final_df = final_df.sort_values(by=["_sort_path", "_item_type_order"], ascending=[True, True]).reset_index(drop=True)

            # 重複するCATEGORY_IN_MAP行を削除
            seen_category_paths = set()
            rows_to_keep = []
            for idx, row in final_df.iterrows():
                if row["アイテムタイプ  ###[item_type]###"] == "CATEGORY_IN_MAP":
                    category_path = row["_sort_path"]
                    if category_path not in seen_category_paths:
                        seen_category_paths.add(category_path)
                        rows_to_keep.append(idx)
                else:
                    rows_to_keep.append(idx)
            
            final_df = final_df.loc[rows_to_keep].reset_index(drop=True)
            final_df = final_df.drop(columns=["_sort_path", "_item_type_order"])

            # --- 追加カラムの設定 ---
            additional_cols = [
                "主管プロジェクト  ###[principal_project_name]###",
                "力量マップコード  ###[competence_map_code]###",
                "力量マップ名",
                "フォルダ名",
                "必要レベル(以上)  ###[required_competence_level_label]###",
                "必要人数  ###[required_head_count]###"
            ]
            for col in additional_cols:
                if col not in final_df.columns:
                    final_df[col] = ""

            final_df["主管プロジェクト  ###[principal_project_name]###"] = 主管プロジェクト.strip()
            final_df["力量マップコード  ###[competence_map_code]###"] = 力量マップコード.strip()
            final_df["力量マップ名"] = 力量マップ名.strip()
            final_df["フォルダ名"] = フォルダ名.strip()

            final_df = final_df[additional_cols + [c for c in final_df.columns if c not in additional_cols]]
            
            # 処理結果をセッションステートに保存
            st.session_state['final_df'] = final_df
            
            st.success(f"✅ 処理完了！最終結果: {len(final_df)}行")

        except Exception as e:
            st.error(f"⚠️ 処理中にエラーが発生しました: {e}")
            st.exception(e)


# --- 結果のダウンロードと表示 ---
st.markdown("---")
if not st.session_state['final_df'].empty:
    st.subheader("📥 結果ファイルのダウンロード")
    
    # CSVに変換（BytesIOを使用するとファイルサイズを節約できる）
    csv_buffer = BytesIO()
    st.session_state['final_df'].to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="🚀 competence_map_related_item_for_map.csv をダウンロード",
        data=csv_data,
        file_name="competence_map_related_item_for_map.csv",
        mime="text/csv"
    )

    st.subheader("📑 結果プレビュー (先頭5行)")
    st.dataframe(st.session_state['final_df'].head())