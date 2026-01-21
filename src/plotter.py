import pandas as pd
import altair as alt
from .models import ArgumentGraph

class TopicMapPlotter:
    @staticmethod
    def generate_plot(graph: ArgumentGraph):
        """
        ArgumentGraphデータからAltairの散布図チャートを生成する。
        色はx,y座標に基づいた2次元的なグラデーションで表現する。
        テキストをノード内に表示する。
        """
        # Nodeに2D座標がなければプロット不可
        if not graph.nodes or not all(hasattr(node, 'position_2d') and node.position_2d for node in graph.nodes):
            return None

        # 1. ノードデータをPandas DataFrameに変換
        node_data = []
        for node in graph.nodes:
            speaker_prefix = f"{node.speaker}" if node.speaker else "Unknown"
            content_for_label = (node.content[:30] + '...') if len(node.content) > 30 else node.content
            label_text = f"{speaker_prefix}\n{content_for_label}"
            
            node_data.append({
                "id": node.id,
                "x": node.position_2d[0],
                "y": node.position_2d[1],
                "content_full": node.content,
                "label_text": label_text,
                "type": node.type,
                "sequence": node.sequence # sequenceを追加
            })
        nodes_df = pd.DataFrame(node_data)
        
        # ★★★ 2Dカラーマッピング処理 ★★★
        # x, y座標を0-255の範囲に正規化
        x_min, x_max = nodes_df['x'].min(), nodes_df['x'].max()
        y_min, y_max = nodes_df['y'].min(), nodes_df['y'].max()

        # 範囲が0でないことを確認
        # 50-255の範囲にマッピングすることで、暗すぎる色を避ける
        if (x_max - x_min) > 0:
            nodes_df['r'] = ((nodes_df['x'] - x_min) / (x_max - x_min) * 205 + 50).astype(int)
        else:
            nodes_df['r'] = 128

        if (y_max - y_min) > 0:
            nodes_df['g'] = ((nodes_df['y'] - y_min) / (y_max - y_min) * 205 + 50).astype(int)
        else:
            nodes_df['g'] = 128
            
        nodes_df['b'] = 128 # 青は一定に保つ
        
        # RGB値からHEXカラーコードを生成
        nodes_df['color_rgb'] = nodes_df.apply(lambda row: f"#{row['r']:02x}{row['g']:02x}{row['b']:02x}", axis=1)

        # 2. エッジデータを準備
        edge_data = []
        node_pos_map = {node["id"]: (node["x"], node["y"]) for _, node in nodes_df.iterrows()}
        
        for edge in graph.edges:
            source_pos = node_pos_map.get(edge.source)
            target_pos = node_pos_map.get(edge.target)
            if source_pos and target_pos:
                edge_data.append({"x1": source_pos[0], "y1": source_pos[1], "x2": target_pos[0], "y2": target_pos[1]})
        
        edges_df = pd.DataFrame(edge_data)

        # 3. Altairでグラフを構築
        base = alt.Chart(nodes_df).encode(
            x=alt.X('x', axis=alt.Axis(title='Topic Dimension 1', ticks=False, labels=False, grid=False)),
            y=alt.Y('y', axis=alt.Axis(title='Topic Dimension 2', ticks=False, labels=False, grid=False))
        )
        
        edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.4).encode(x='x1', y='y1', x2='x2', y2='y2')

        # 背景の図形レイヤー
        background_shape_layer = base.mark_point(
            size=2000, opacity=0.9, filled=True
        ).encode(
            color=alt.Color('color_rgb:N', scale=None),
            shape=alt.Shape('type:N', title="Node Type", scale=alt.Scale(
                domain=['issue', 'position', 'argument', 'decision'],
                range=['circle', 'square', 'triangle-right', 'diamond']
            )),
            tooltip=[alt.Tooltip('content_full:N', title='Content'), alt.Tooltip('id:N', title='Node ID')]
        )
        
        # 前面のテキストレイヤー（可読性向上のため黒と白の2層を用意）
        # 明るい背景用の黒テキスト
        black_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='black', lineBreak='\n', opacity=0.8
        ).encode(
            text=alt.Text('label_text:N'),
            # YUV輝度計算に基づき、背景が明るい場合のみ表示
            opacity=alt.condition(
                "(datum.r * 0.299 + datum.g * 0.587 + datum.b * 0.114) > 186",
                alt.value(1),
                alt.value(0)
            )
        )
        # 暗い背景用の白テキスト
        white_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='white', lineBreak='\n', opacity=0.8
        ).encode(
            text=alt.Text('label_text:N'),
             # YUV輝度計算に基づき、背景が暗い場合のみ表示
            opacity=alt.condition(
                "(datum.r * 0.299 + datum.g * 0.587 + datum.b * 0.114) <= 186",
                alt.value(1),
                alt.value(0)
            )
        )

        chart = (edge_layer + background_shape_layer + black_text_layer + white_text_layer).properties(
            width=700, height=500
        ).interactive()
        
        return chart

    @staticmethod
    def generate_timeline_plot(graph: ArgumentGraph):
        """
        ArgumentGraphデータから時系列分析チャートを生成する。
        横軸は時系列、縦軸は発言者、ノードは2Dカラーマッピング。
        線は論理関係(賛成・反対など)を表す。
        """
        # Nodeにsequenceと2D座標がなければプロット不可
        if not graph.nodes or not all(node.sequence is not None and hasattr(node, 'position_2d') and node.position_2d for node in graph.nodes):
            return None

        # 1. ノードデータをPandas DataFrameに変換
        node_data = []
        for node in graph.nodes:
            speaker_prefix = f"{node.speaker}" if node.speaker else "Unknown"
            content_for_label = (node.content[:30] + '...') if len(node.content) > 30 else node.content
            label_text = f"{speaker_prefix}\n{content_for_label}"
            
            node_data.append({
                "id": node.id,
                "sequence": node.sequence,
                "speaker": node.speaker or "Unknown",
                "x_topic": node.position_2d[0],
                "y_topic": node.position_2d[1],
                "content_full": node.content,
                "label_text": label_text,
                "type": node.type
            })
        nodes_df = pd.DataFrame(node_data)
        
        # 2Dカラーマッピング処理 (トピックマップと同じロジック)
        x_min, x_max = nodes_df['x_topic'].min(), nodes_df['x_topic'].max()
        y_min, y_max = nodes_df['y_topic'].min(), nodes_df['y_topic'].max()
        if (x_max - x_min) > 0:
            nodes_df['r'] = ((nodes_df['x_topic'] - x_min) / (x_max - x_min) * 205 + 50).astype(int)
        else:
            nodes_df['r'] = 128
        if (y_max - y_min) > 0:
            nodes_df['g'] = ((nodes_df['y_topic'] - y_min) / (y_max - y_min) * 205 + 50).astype(int)
        else:
            nodes_df['g'] = 128
        nodes_df['b'] = 128
        nodes_df['color_rgb'] = nodes_df.apply(lambda row: f"#{row['r']:02x}{row['g']:02x}{row['b']:02x}", axis=1)

        # 2. ★変更点★ 論理関係のエッジデータを準備
        edge_data = []
        # 新しい座標系(sequence, speaker)をマップ
        node_pos_map = {node["id"]: (node["sequence"], node["speaker"]) for _, node in nodes_df.iterrows()}
        
        for edge in graph.edges:
            source_pos = node_pos_map.get(edge.source)
            target_pos = node_pos_map.get(edge.target)
            if source_pos and target_pos:
                edge_data.append({
                    "x1": source_pos[0], "y1": source_pos[1],
                    "x2": target_pos[0], "y2": target_pos[1],
                    "label": edge.label,
                    "mid_x": (source_pos[0] + target_pos[0]) / 2,
                    "mid_y_num": (nodes_df.columns.get_loc('speaker') + 0.5) 
                })
        edges_df = pd.DataFrame(edge_data)

        # 3. Altairでグラフを構築
        base = alt.Chart(nodes_df).encode(
            x=alt.X('sequence:Q', axis=alt.Axis(title='Time (Chronological Order)', grid=True)),
            y=alt.Y('speaker:N', axis=alt.Axis(title='Speaker'))
        )
        
        # ★変更点★ 論理関係の線レイヤー
        argument_edge_layer = alt.Chart(edges_df).mark_rule(color='gray', opacity=0.6).encode(
            x='x1:Q', y='y1:N', x2='x2:Q', y2='y2:N'
        )

        # ★変更点★ 線ラベルのレイヤー
        edge_label_layer = alt.Chart(edges_df).mark_text(
            align='center', baseline='middle', fontSize=9, color='gray', dy=-8
        ).encode(
            x='mid_x:Q',
            y=alt.YValue(150), 
            text='label:N'
        )
        
        # 背景の図形レイヤー
        background_shape_layer = base.mark_point(
            size=2000, opacity=0.9, filled=True
        ).encode(
            color=alt.Color('color_rgb:N', scale=None),
            shape=alt.Shape('type:N', title="Node Type", scale=alt.Scale(
                domain=['issue', 'position', 'argument', 'decision'],
                range=['circle', 'square', 'triangle-right', 'diamond']
            )),
            tooltip=[alt.Tooltip('content_full:N', title='Content'), alt.Tooltip('id:N', title='Node ID')]
        )
        
        # 前面のテキストレイヤー（黒と白）
        black_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='black', lineBreak='\n', opacity=0.8
        ).encode(
            text=alt.Text('label_text:N'),
            opacity=alt.condition("(datum.r * 0.299 + datum.g * 0.587 + datum.b * 0.114) > 186", alt.value(1), alt.value(0))
        )
        white_text_layer = base.mark_text(
            align='center', baseline='middle', fontSize=10, color='white', lineBreak='\n', opacity=0.8
        ).encode(
            text=alt.Text('label_text:N'),
            opacity=alt.condition("(datum.r * 0.299 + datum.g * 0.587 + datum.b * 0.114) <= 186", alt.value(1), alt.value(0))
        )

        chart = (argument_edge_layer + edge_label_layer + background_shape_layer + black_text_layer + white_text_layer).properties(
            width=700, height=300
        ).interactive()
        
        return chart