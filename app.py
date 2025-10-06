import streamlit as st
import pandas as pd
import numpy as np
import io

# ページ設定
st.set_page_config(
    page_title="力量マップCSV生成ツール",
    page_icon="📊",
    layout="wide"
)

# タイトル
st.title("📊 力量マップCSV生成ツール")
st.markdown("---")

# -------------------------------
# データ処理関数
# -------------------------------
def split_competence_category(df):
    """力量カテゴリーを「＞」で分割して20列に展開"""
    split_data = df['力量カテゴリー'].str.split('＞', expand=True)

    if split_data.shape[1] > 20:
        split_data = split_data.iloc[:, :20]

    split_data = split_data.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)
    split_data = split_data.replace('', np.nan)

    for i in range(split_data.shape[1], 20):
        split_data[i] = np.nan

    split_data.columns = [f'力量カテゴリー名  ###[competence_category_name_{i}]###' for i in range(1, 21)]

    return pd.concat([df, split_data], axis=1)


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

    for _, comp_row in df_competence.iterrows():
        comp_path = comp_row["category_path"]

        # 力量カテゴリ行を追加
        category_row_dict = {"アイテムタイプ  ###[item_type]###": "CATEGORY_IN_MAP"}

        for i in range(1, 21):
            old_col = f'力量カテゴリー名  ###[competence_category_name_{i}]###'
            new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'
            category_row_dict[new_col] = comp_row[old_col] if old_col in comp_row.index else np.nan

        results.append(category_row_dict)

        # マッチする力量コード行を追加
        matched_rows = df_output[df_output["category_path"] == comp_path]

        for _, out_row in matched_rows.iterrows():
            skill_row_dict = {"アイテムタイプ  ###[item_type]###": item_type_name}

            # カテゴリー名をコピー
            for i in range(1, 21):
                old_col = f'力量カテゴリー名  ###[competence_category_name_{i}]###'
                new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'

                if old_col in comp_row.index:
                    val = comp_row[old_col]
                    skill_row_dict[new_col] = val if pd.notna(val) else np.nan
                else:
                    skill_row_dict[new_col] = np.nan

            # 左から順に探して最初のNULLに力量コードを挿入
            for i in range(1, 21):
                new_col = f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###'
                if pd.isna(skill_row_dict[new_col]):
                    skill_row_dict[new_col] = out_row[skill_code_col]
                    break

            results.append(skill_row_dict)

    df_result = pd.DataFrame(results).drop(columns=["category_path"], errors="ignore")

    # カラムの順序を整理
    item_type_col = "アイテムタイプ  ###[item_type]###"
    item_code_cols = [f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###' for i in range(1, 21)]
    cols = [item_type_col] + item_code_cols
    cols = [c for c in cols if c in df_result.columns]

    return df_result[cols]


def process_skill_file(file_content, df_competence, item_type_name, skill_code_col):
    """スキル/教育/資格ファイルを処理してマップ行を生成"""
    df_skill = pd.read_csv(file_content)
    df_skill = split_competence_category(df_skill)
    df_skill, _ = build_category_path(df_skill)
    df_competence_copy, _ = build_category_path(df_competence.copy())

    return expand_with_skill_codes(df_skill, df_competence_copy, item_type_name, skill_code_col)


def get_category_path(row, item_code_cols):
    """行からカテゴリーパスを生成（NaN以外の値を＞で結合）"""
    path_parts = []
    for col in item_code_cols:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            path_parts.append(str(row[col]).strip())
    return "＞".join(path_parts)


# -------------------------------
# Streamlit UI
# -------------------------------

# ステップ1: 力量マップ情報入力
st.header("📋 ステップ1: 力量マップ情報を入力")
with st.form("map_info_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        主管プロジェクト = st.text_input(
            "主管プロジェクト *", 
            value="11_デモ_設備部",
            help="必須項目です"
        )
        力量マップコード = st.text_input(
            "力量マップコード *", 
            value="GuRdXPEmx6y5EqcMeyKA",
            help="必須項目です"
        )
    
    with col2:
        力量マップ名 = st.text_input(
            "力量マップ名 *", 
            value="デモ_力量マップ",
            help="必須項目です"
        )
        フォルダ名 = st.text_input(
            "フォルダ名", 
            value="",
            help="オプション項目です"
        )
    
    submit_info = st.form_submit_button("✅ 情報を確定")

if submit_info:
    if not 主管プロジェクト.strip() or not 力量マップコード.strip() or not 力量マップ名.strip():
        st.error("❌ 主管プロジェクト、力量マップコード、力量マップ名は必須項目です。")
    else:
        st.success("✅ 力量マップ情報の入力が完了しました")
        st.session_state['map_info'] = {
            '主管プロジェクト': 主管プロジェクト,
            '力量マップコード': 力量マップコード,
            '力量マップ名': 力量マップ名,
            'フォルダ名': フォルダ名
        }

st.markdown("---")

# ステップ2: 力量カテゴリCSVアップロード
st.header("📁 ステップ2: 力量カテゴリCSVファイルをアップロード")
competence_file = st.file_uploader(
    "力量カテゴリCSVファイルを選択 (必須)",
    type=['csv'],
    key='competence'
)

if competence_file:
    try:
        df_competence = pd.read_csv(competence_file)
        st.success(f"✅ 力量カテゴリファイル読み込み完了: {len(df_competence)}行")
        st.session_state['df_competence'] = df_competence
        
        with st.expander("📊 データプレビュー"):
            st.dataframe(df_competence.head(10))
    except Exception as e:
        st.error(f"❌ ファイル読み込みエラー: {e}")

st.markdown("---")

# ステップ3: 力量CSVファイルアップロード
st.header("📁 ステップ3: 力量CSVファイルをアップロード")
st.info("スキル/教育/資格のいずれか1つ以上をアップロードしてください")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("力量（スキル）")
    skill_file = st.file_uploader("スキルCSV", type=['csv'], key='skill')
    if skill_file:
        st.success("✅ アップロード完了")

with col2:
    st.subheader("力量（教育）")
    education_file = st.file_uploader("教育CSV", type=['csv'], key='education')
    if education_file:
        st.success("✅ アップロード完了")

with col3:
    st.subheader("力量（資格）")
    license_file = st.file_uploader("資格CSV", type=['csv'], key='license')
    if license_file:
        st.success("✅ アップロード完了")

st.markdown("---")

# ステップ4: データ処理実行
st.header("⚙️ ステップ4: データ処理を実行")

if st.button("🚀 処理を開始", type="primary", use_container_width=True):
    # 必須項目チェック
    if 'map_info' not in st.session_state:
        st.error("❌ ステップ1の力量マップ情報を先に入力・確定してください")
    elif 'df_competence' not in st.session_state:
        st.error("❌ ステップ2の力量カテゴリCSVをアップロードしてください")
    elif not skill_file and not education_file and not license_file:
        st.error("❌ ステップ3で力量（スキル/教育/資格）のいずれか1つ以上をアップロードしてください")
    else:
        try:
            with st.spinner("⏳ データ処理中..."):
                # 処理開始
                map_info = st.session_state['map_info']
                df_competence = st.session_state['df_competence']
                
                all_results = []
                file_configs = [
                    (skill_file, "SKILL", "力量コード  ###[skill_code]###"),
                    (education_file, "EDUCATION", "力量コード  ###[education_code]###"),
                    (license_file, "LICENSE", "力量コード  ###[license_code]###")
                ]
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, (file, item_type, code_col) in enumerate(file_configs):
                    if file is None:
                        continue
                    
                    status_text.text(f"処理中: {item_type}...")
                    df_result = process_skill_file(io.BytesIO(file.getvalue()), df_competence, item_type, code_col)
                    
                    type_counts = df_result['アイテムタイプ  ###[item_type]###'].value_counts()
                    st.info(f"✓ {item_type}ファイル処理完了: {len(df_result)}行生成")
                    
                    all_results.append(df_result)
                    progress_bar.progress((idx + 1) / 3)
                
                status_text.text("結果を統合中...")
                
                # 結果を統合
                final_df = pd.concat(all_results, ignore_index=True)
                
                # ソート処理
                item_code_cols = [f'力量コード（カテゴリ名）{i}  ###[item_code_{i:02d}]###' for i in range(1, 21)]
                final_df["_sort_path"] = final_df.apply(lambda row: get_category_path(row, item_code_cols), axis=1)
                
                item_type_order = {"CATEGORY_IN_MAP": 0, "SKILL": 1, "EDUCATION": 2, "LICENSE": 3}
                final_df["_item_type_order"] = final_df["アイテムタイプ  ###[item_type]###"].map(
                    lambda x: item_type_order.get(x, 99)
                )
                
                final_df = final_df.sort_values(
                    by=["_sort_path", "_item_type_order"],
                    ascending=[True, True]
                ).reset_index(drop=True)
                
                # 重複削除
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
                
                # 追加カラム設定
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
                
                final_df["主管プロジェクト  ###[principal_project_name]###"] = map_info['主管プロジェクト']
                final_df["力量マップコード  ###[competence_map_code]###"] = map_info['力量マップコード']
                final_df["力量マップ名"] = map_info['力量マップ名']
                final_df["フォルダ名"] = map_info['フォルダ名']
                
                final_df = final_df[additional_cols + [c for c in final_df.columns if c not in additional_cols]]
                
                progress_bar.progress(100)
                status_text.empty()
                
                # 結果表示
                st.success("✅ 処理完了！")
                st.info(f"📊 最終結果: {len(final_df)}行")
                
                with st.expander("📊 結果プレビュー（最初の50行）"):
                    st.dataframe(final_df.head(50))
                
                # ダウンロードボタン
                csv_buffer = io.StringIO()
                final_df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 CSVファイルをダウンロード",
                    data=csv_data,
                    file_name="competence_map_related_item_for_map.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ 処理エラー: {e}")
            st.exception(e)

# フッター
st.markdown("---")
st.markdown("**📌 使い方:**")
st.markdown("""
1. ステップ1で力量マップの基本情報を入力し「情報を確定」ボタンをクリック
2. ステップ2で力量カテゴリCSVファイルをアップロード
3. ステップ3で力量（スキル/教育/資格）のCSVファイルを1つ以上アップロード
4. ステップ4で「処理を開始」ボタンをクリックして結果をダウンロード
""")