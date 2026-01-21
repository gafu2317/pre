import os
import streamlit as st
from dotenv import load_dotenv

from src.strategies.ibis import IBISStrategy
from src.strategies.toulmin import ToulminStrategy
from src.llm import LLMClient
from src.clustering import reduce_dimensions_pca
from src.plotter import TopicMapPlotter
from src.models import ArgumentGraph

load_dotenv()

def load_sample_file(filename):
    path = os.path.join("data", "samples", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def main():
    st.set_page_config(page_title="Argument Miner", layout="wide")
    st.subheader("🧩 議論構造可視化 (Argument Structure)")

    # ==========================================
    # 0. セッションステート初期化 (データの永続化)
    # ==========================================
    if "graph_data" not in st.session_state:
        st.session_state["graph_data"] = None

    # ==========================================
    # 1. サイドバー (設定と入力)
    # ==========================================
    with st.sidebar:
        st.header("⚙️ 設定")
        
        if os.getenv("OPENAI_API_KEY"):
            st.caption("✅ API Key Active")
        else:
            st.error("API Key missing!")

        strategy_option = st.selectbox("分析モデル", ["IBIS (議論・意思決定)", "Toulmin (論理・正当性)"])
        
        st.divider()
        use_topic_analysis = st.checkbox("トピックマップ分析を実行する", value=True)
        st.divider()

        input_mode = st.radio("入力ソース", ["📂 サンプル", "📝 直接入力"], horizontal=True)
        
        default_text = ""
        if input_mode == "📂 サンプル":
            sample_dir = os.path.join("data", "samples")
            if not os.path.exists(sample_dir):
                os.makedirs(sample_dir)
            files = [f for f in os.listdir(sample_dir) if f.endswith(".txt")]
            files.sort()
            if files:
                selected_file = st.selectbox("ファイル選択", files)
                default_text = load_sample_file(selected_file)
        
        text_area_val = st.text_area("会話ログ", value=default_text, height=300)
        
        if st.button("🚀 構造化を実行", type="primary", use_container_width=True):
            if not text_area_val.strip():
                st.warning("👈 テキストを入力してください")
            else:
                try:
                    with st.spinner('AIが議論構造を分析中...'):
                        if "IBIS" in strategy_option:
                            strategy = IBISStrategy()
                        else:
                            strategy = ToulminStrategy()
                        
                        graph = strategy.analyze(text_area_val)
                        # position_2d属性を初期化
                        for node in graph.nodes:
                            # Pydanticモデルにフィールドがないとエラーになるため、Noneで初期化しておく
                            node.position_2d = None
                        st.session_state["graph_data"] = graph

                    # --- トピック分析処理 (ベクトル化と2次元化) ---
                    if use_topic_analysis and graph and graph.nodes:
                        with st.spinner('ベクトル化とトピックマップ分析を実行中...'):
                            llm = LLMClient()
                            node_contents = [node.content for node in graph.nodes]
                            
                            vectors = llm.fetch_embeddings(node_contents)
                            positions = reduce_dimensions_pca(vectors)
                            
                            for i, node in enumerate(graph.nodes):
                                node.position_2d = positions[i]
                            
                            st.session_state["graph_data"] = graph # 分析結果で更新
                            
                except Exception as e:
                    st.error(f"エラー: {e}")

    # ==========================================
    # 2. メインエリア (統合されたトピックマップを表示)
    # ==========================================
    
    if st.session_state["graph_data"]:
        graph = st.session_state["graph_data"]
        
        # タブを再導入
        tab1, tab2 = st.tabs(["🗺️ トピックマップ", "📈 時間軸分析"])

        with tab1:
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
                <h5 style="margin:0 0 10px 0;">💡 図の見方 (Legend)</h5>
                <p style="margin:0;">各ノード（発言）を、話題の近さに応じて2次元マップ上に配置したものです。線は議論の親子関係を表します。</p>
                <ul style="font-size: smaller; margin-bottom:0;">
                    <li><b>ノードの位置 (X軸):</b> 議論の主要なテーマの方向（左右）</li>
                    <li><b>ノードの位置 (Y軸):</b> 議論の二番目に重要なテーマの方向（上下）</li>
                    <li><b>ノードの色:</b> 話題のスペクトル（X軸とY軸の組み合わせで決定）</li>
                    <li><b>ノードの形:</b> ノードの種類（論点、提案など）</li>
                    <li><b>ノードのテキスト:</b> 発言者と内容の要約</li>
                    <li><b>点と点の距離:</b> 話題の近さ</li>
                    <li><b>線:</b> 議論の親子関係</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            topic_map_chart = TopicMapPlotter.generate_plot(graph)
            if topic_map_chart:
                st.altair_chart(topic_map_chart, use_container_width=True)
            else:
                st.info("トピックマップの描画には、2つ以上のノードと「トピックマップ分析」の実行が必要です。")
            
            with st.expander("詳細データを見る"):
                st.json(graph.model_dump())

        with tab2:
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:15px; border-radius:8px; border:1px solid #ddd; margin-bottom:20px;">
                <h5 style="margin:0 0 10px 0;">💡 図の見方 (Legend)</h5>
                <p style="margin:0;">会話の進行順にノードが横一直線上に並び、各ノードの色の変化で話題の移り変わりを追います。</p>
                <ul style="font-size: smaller; margin-bottom:0;">
                    <li><b>横軸:</b> 会話の進行順（時間）</li>
                    <li><b>縦軸:</b> （明示的な意味はありませんが、ノード配置の基準となります）</li>
                    <li><b>ノードの色:</b> 話題のスペクトル（トピックマップと同じ、X軸とY軸の組み合わせで決定）</li>
                    <li><b>ノードの形:</b> ノードの種類（論点、提案など）</li>
                    <li><b>ノードのテキスト:</b> 発言者と内容の要約</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            timeline_chart = TopicMapPlotter.generate_timeline_plot(graph) # 新しいメソッドを呼び出し
            if timeline_chart:
                st.altair_chart(timeline_chart, use_container_width=True)
            else:
                st.info("時間軸分析の描画には、2つ以上のノードと「トピック分析」の実行が必要です。")

            with st.expander("詳細データを見る"):
                st.json(graph.model_dump())

    else:
        st.info("👈 左のサイドバーから「構造化を実行」してください。")

if __name__ == "__main__":
    main()