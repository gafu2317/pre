import pandas as pd
import altair as alt
import textwrap
import colorsys # colorsysをインポート
from .models import ArgumentGraph

class TopicMapPlotter:
    # ノードタイプと日本語名のマッピング
    NODE_TYPE_MAP = {
        'issue': '論点',
        'position': '提案',
        'argument': '根拠',
        'decision': '決定'
    }

    @staticmethod
    def _prepare_node_data(graph: ArgumentGraph):
        """共通のノードデータ準備処理"""
        node_data = []
        for node in graph.nodes:
            speaker_prefix = f"{node.speaker}" if node.speaker else "不明"
            content_summary = (node.content[:30] + '...') if len(node.content) > 30 else node.content
            
            # 内容の要約部分を自動で折り返し
            wrapped_content = '\n'.join(textwrap.wrap(content_summary, width=15))
            
            label_text = f"{speaker_prefix}\n{wrapped_content}"
            
            node_data.append({
                "id": node.id,
                "x_topic": node.position_2d[0] if node.position_2d else 0,
                "y_topic": node.position_2d[1] if node.position_2d else 0,
                "sequence": node.sequence,
                "speaker": node.speaker or "不明",
                "content_full": node.content,
                "label_text": label_text,
                "type": node.type,
                "type_jp": TopicMapPlotter.NODE_TYPE_MAP.get(node.type, node.type),
                "cosine_sim_to_first": node.cosine_sim_to_first # コサイン類似度を追加
            })
        nodes_df = pd.DataFrame(node_data)
        
        # HSVカラーマッピング処理
        if not nodes_df.empty and 'cosine_sim_to_first' in nodes_df.columns:
            # コサイン類似度を色相(H)にマッピング (0-1の範囲)
            # コサイン類似度は-1から1の範囲。これを0から1の色相に線形マッピング
            # 例えば、-1を0 (赤)、0を0.5 (緑)、1を1 (赤に戻る) のようにマッピング。
            # 今回は、-1を0 (赤)、1を0.66 (青) の範囲にマッピングしてみる。
            # H = (cosine_sim + 1) / 2 とすると、-1が0、1が1になる。
            # 0.0 (赤) から 0.66 (青) の範囲で色相を変化させる。
            nodes_df['h'] = nodes_df['cosine_sim_to_first'].apply(lambda x: (x + 1) / 2 * 0.66) # -1 -> 0, 1 -> 0.66

            # 彩度(S)と明度(V)は固定
            fixed_s = 0.9 # 鮮やかに
            fixed_v = 0.9 # 明るく
            
            # HSVからRGBに変換
            nodes_df['color_rgb'] = nodes_df.apply(
                lambda row: '#%02x%02x%02x' % tuple(int(x * 255) for x in colorsys.hsv_to_rgb(row['h'], fixed_s, fixed_v)), 
                axis=1
            )
        else:
            # cosine_sim_to_firstがない場合、デフォルト色を設定
            nodes_df['color_rgb'] = '#808080' # 灰色
        
        return nodes_df

    @staticmethod
    def generate_plot(graph: ArgumentGraph):
        """トピックマップ（散布図）を生成する"""
        nodes_df = TopicMapPlotter._prepare_node_data(graph)
        if nodes_df is None or nodes_df.empty or len(nodes_df) < 2:
            return None

        # エッジデータ準備
        edge_data = []
        node_pos_map = {node["id"]: (node["x_topic"], node["y_topic"]) for _, node in nodes_df.iterrows()}
        for edge in graph.edges:
            source_pos, target_pos = node_pos_map.get(edge.source), node_pos_map.get(edge.target)
            if source_pos and target_pos:
                edge_data.append({
                    "x1": source_pos[0], "y1": source_pos[1],
                    "x2": target_pos[0], "y2": target_pos[1],
                    "label": edge.label,
                    "mid_x": (source_pos[0] + target_pos[0]) / 2,
                    "mid_y": (source_pos[1] + target_pos[1]) / 2
                })
        edges_df = pd.DataFrame(edge_data)

        # グラフ構築
        base = alt.Chart(nodes_df).encode(
            x=alt.X('x_topic', axis=None),
            y=alt.Y('y_topic', axis=None)
        )
        edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.5).encode(x='x1', y='y1', x2='x2', y2='y2')
        edge_label_layer = alt.Chart(edges_df).mark_text(
            align='center', baseline='middle', fontSize=9, color='gray', dy=-8
        ).encode(x='mid_x:Q', y='mid_y:Q', text='label:N')

        background_shape_layer = base.mark_point(size=5000, opacity=0.9, filled=True).encode(
            color=alt.Color('color_rgb:N', scale=None),
            shape=alt.Shape('type_jp:N', title="ノード種別", scale=alt.Scale(
                domain=list(TopicMapPlotter.NODE_TYPE_MAP.values()),
                range=['circle', 'square', 'triangle-right', 'diamond']
            )),
            tooltip=[alt.Tooltip('content_full:N', title='内容'), alt.Tooltip('id:N', title='ノードID'), alt.Tooltip('cosine_sim_to_first:Q', title='コサイン類似度', format='.2f')]
        )
        foreground_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='black', lineBreak='\n', opacity=0.9
        ).encode(text=alt.Text('label_text:N'))

        return (edge_layer + edge_label_layer + background_shape_layer + foreground_text_layer).properties(
            width=700, height=500
        ).interactive()

    @staticmethod
    def generate_timeline_plot(graph: ArgumentGraph):
        """時系列分析チャートを生成する"""
        valid_nodes_df = TopicMapPlotter._prepare_node_data(graph)
        valid_nodes_df = valid_nodes_df[valid_nodes_df['sequence'].notna()]
        if valid_nodes_df is None or valid_nodes_df.empty or len(valid_nodes_df) < 2:
            return None
        valid_nodes_df = valid_nodes_df.sort_values(by='sequence').reset_index(drop=True)

        # エッジデータ準備
        edge_data = []
        node_pos_map = {node["id"]: {"sequence": node["sequence"], "speaker": node["speaker"]} for _, node in valid_nodes_df.iterrows()}
        for edge in graph.edges:
            source_node_info, target_node_info = node_pos_map.get(edge.source), node_pos_map.get(edge.target)
            if source_node_info and target_node_info:
                edge_data.append({
                    "x1": source_node_info["sequence"], "y1": source_node_info["speaker"],
                    "x2": target_node_info["sequence"], "y2": target_node_info["speaker"],
                    "label": edge.label,
                    "mid_x": (source_node_info["sequence"] + target_node_info["sequence"]) / 2
                })
        edges_df = pd.DataFrame(edge_data)

        # グラフ構築
        base = alt.Chart(valid_nodes_df).encode(
            x=alt.X('sequence:Q', axis=alt.Axis(title='時系列順', grid=True)),
            y=alt.Y('speaker:N', axis=alt.Axis(title='発言者'))
        )
        argument_edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.6).encode(x='x1:Q', y='y1:N', x2='x2:Q', y2='y2:N')
        edge_label_layer = alt.Chart(edges_df).mark_text(
            align='center', baseline='middle', fontSize=9, color='gray', dy=-8
        ).encode(x='mid_x:Q', y='y1:N', text='label:N')

        background_shape_layer = base.mark_point(size=5000, opacity=0.9, filled=True).encode(
            color=alt.Color('color_rgb:N', scale=None),
            shape=alt.Shape('type_jp:N', title="ノード種別", scale=alt.Scale(
                domain=list(TopicMapPlotter.NODE_TYPE_MAP.values()),
                range=['circle', 'square', 'triangle-right', 'diamond']
            )),
            tooltip=[alt.Tooltip('content_full:N', title='内容'), alt.Tooltip('id:N', title='ノードID'), alt.Tooltip('cosine_sim_to_first:Q', title='コサイン類似度', format='.2f')]
        )
        foreground_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='black', lineBreak='\n', opacity=0.9
        ).encode(text=alt.Text('label_text:N'))

        return (argument_edge_layer + edge_label_layer + background_shape_layer + foreground_text_layer).properties(
            width=700, height=300
        ).interactive()