import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# ページ設定
st.set_page_config(
    page_title="予実管理アプリ",
    page_icon="📊",
    layout="wide"
)

# セッション状態の初期化
if 'initiatives' not in st.session_state:
    st.session_state.initiatives = pd.DataFrame(columns=['施策名', '予算'])

if 'actuals' not in st.session_state:
    st.session_state.actuals = pd.DataFrame(columns=['施策名', '年月', '実績'])

# メイン関数
def main():
    st.title("📊 予実管理アプリ")
    
    # サイドバーでページ選択
    page = st.sidebar.selectbox(
        "ページを選択",
        ["施策管理", "実績入力", "データ表示", "可視化"]
    )
    
    if page == "施策管理":
        initiative_management()
    elif page == "実績入力":
        actual_input()
    elif page == "データ表示":
        data_display()
    elif page == "可視化":
        visualization()

def initiative_management():
    """施策管理ページ"""
    st.header("🎯 施策管理")
    
    # 新しい施策の追加
    st.subheader("新しい施策を追加")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        new_initiative = st.text_input("施策名", key="new_initiative")
    with col2:
        new_budget = st.number_input("予算（円）", min_value=0, step=1000, key="new_budget")
    with col3:
        if st.button("追加", type="primary"):
            if new_initiative and new_budget > 0:
                # 既存の施策名チェック
                if new_initiative in st.session_state.initiatives['施策名'].values:
                    st.error("既に存在する施策名です。")
                else:
                    new_row = pd.DataFrame({'施策名': [new_initiative], '予算': [new_budget]})
                    st.session_state.initiatives = pd.concat([st.session_state.initiatives, new_row], ignore_index=True)
                    st.success(f"施策「{new_initiative}」を追加しました。")
                    st.rerun()
            else:
                st.error("施策名と予算を正しく入力してください。")
    
    # 既存施策の表示と編集
    st.subheader("既存の施策")
    
    if not st.session_state.initiatives.empty:
        # 施策の編集・削除
        for idx, row in st.session_state.initiatives.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                edited_name = st.text_input(f"施策名", value=row['施策名'], key=f"edit_name_{idx}")
            with col2:
                edited_budget = st.number_input(f"予算", value=int(row['予算']), min_value=0, step=1000, key=f"edit_budget_{idx}")
            with col3:
                if st.button("更新", key=f"update_{idx}"):
                    if edited_name:
                        # 他の施策名との重複チェック（自分以外）
                        other_names = st.session_state.initiatives.drop(idx)['施策名'].values
                        if edited_name in other_names:
                            st.error("既に存在する施策名です。")
                        else:
                            st.session_state.initiatives.loc[idx, '施策名'] = edited_name
                            st.session_state.initiatives.loc[idx, '予算'] = edited_budget
                            
                            # 実績データの施策名も更新
                            if not st.session_state.actuals.empty:
                                st.session_state.actuals.loc[st.session_state.actuals['施策名'] == row['施策名'], '施策名'] = edited_name
                            
                            st.success("更新しました。")
                            st.rerun()
                    else:
                        st.error("施策名を入力してください。")
            
            with col4:
                if st.button("削除", key=f"delete_{idx}", type="secondary"):
                    # 関連する実績データも削除
                    st.session_state.actuals = st.session_state.actuals[st.session_state.actuals['施策名'] != row['施策名']]
                    st.session_state.initiatives = st.session_state.initiatives.drop(idx).reset_index(drop=True)
                    st.success("削除しました。")
                    st.rerun()
    else:
        st.info("まだ施策が登録されていません。")

def actual_input():
    """実績入力ページ"""
    st.header("📝 実績入力")
    
    if st.session_state.initiatives.empty:
        st.warning("施策を先に登録してください。")
        return
    
    # 年月選択
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("年", range(2020, 2030), index=5)  # デフォルト2025年
    with col2:
        month = st.selectbox("月", range(1, 13), index=datetime.now().month - 1)
    
    year_month = f"{year}-{month:02d}"
    
    st.subheader(f"{year}年{month}月の実績入力")
    
    # 各施策の実績入力
    for _, initiative in st.session_state.initiatives.iterrows():
        initiative_name = initiative['施策名']
        budget = initiative['予算']
        
        # 既存の実績値を取得
        existing_actual = st.session_state.actuals[
            (st.session_state.actuals['施策名'] == initiative_name) & 
            (st.session_state.actuals['年月'] == year_month)
        ]
        
        current_value = int(existing_actual['実績'].iloc[0]) if not existing_actual.empty else 0
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{initiative_name}** (予算: ¥{budget:,})")
        with col2:
            actual_value = st.number_input(
                f"実績（円）",
                min_value=0,
                value=current_value,
                step=1000,
                key=f"actual_{initiative_name}_{year_month}"
            )
        with col3:
            if st.button("保存", key=f"save_{initiative_name}_{year_month}"):
                # 既存データの更新または新規追加
                if not existing_actual.empty:
                    # 更新
                    st.session_state.actuals.loc[
                        (st.session_state.actuals['施策名'] == initiative_name) & 
                        (st.session_state.actuals['年月'] == year_month), '実績'
                    ] = actual_value
                else:
                    # 新規追加
                    new_row = pd.DataFrame({
                        '施策名': [initiative_name],
                        '年月': [year_month],
                        '実績': [actual_value]
                    })
                    st.session_state.actuals = pd.concat([st.session_state.actuals, new_row], ignore_index=True)
                
                st.success(f"{initiative_name}の実績を保存しました。")

def data_display():
    """データ表示ページ"""
    st.header("📋 データ表示")
    
    if st.session_state.initiatives.empty:
        st.warning("施策が登録されていません。")
        return
    
    # タブで表示切り替え
    tab1, tab2, tab3 = st.tabs(["施策別集計", "月別集計", "詳細データ"])
    
    with tab1:
        st.subheader("施策別集計")
        
        # 施策別の集計計算
        initiative_summary = []
        for _, initiative in st.session_state.initiatives.iterrows():
            initiative_name = initiative['施策名']
            budget = initiative['予算']
            
            # 実績合計計算
            total_actual = st.session_state.actuals[
                st.session_state.actuals['施策名'] == initiative_name
            ]['実績'].sum()
            
            # 消化率計算
            consumption_rate = (total_actual / budget * 100) if budget > 0 else 0
            remaining = budget - total_actual
            
            initiative_summary.append({
                '施策名': initiative_name,
                '予算': budget,
                '実績合計': total_actual,
                '残予算': remaining,
                '消化率(%)': round(consumption_rate, 1)
            })
        
        summary_df = pd.DataFrame(initiative_summary)
        
        # 表示用フォーマット
        display_df = summary_df.copy()
        for col in ['予算', '実績合計', '残予算']:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:,}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # 合計値表示
        total_budget = summary_df['予算'].sum()
        total_actual = summary_df['実績合計'].sum()
        total_remaining = total_budget - total_actual
        overall_rate = (total_actual / total_budget * 100) if total_budget > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総予算", f"¥{total_budget:,}")
        with col2:
            st.metric("総実績", f"¥{total_actual:,}")
        with col3:
            st.metric("総残予算", f"¥{total_remaining:,}")
        with col4:
            st.metric("全体消化率", f"{overall_rate:.1f}%")
    
    with tab2:
        st.subheader("月別集計")
        
        if not st.session_state.actuals.empty:
            # 月別集計
            monthly_summary = st.session_state.actuals.groupby('年月')['実績'].sum().reset_index()
            monthly_summary['実績'] = monthly_summary['実績'].apply(lambda x: f"¥{x:,}")
            monthly_summary = monthly_summary.sort_values('年月')
            
            st.dataframe(monthly_summary, use_container_width=True)
        else:
            st.info("実績データがありません。")
    
    with tab3:
        st.subheader("詳細データ")
        
        if not st.session_state.actuals.empty:
            # 詳細データ表示
            detail_df = st.session_state.actuals.copy()
            detail_df['実績'] = detail_df['実績'].apply(lambda x: f"¥{x:,}")
            detail_df = detail_df.sort_values(['施策名', '年月'])
            
            st.dataframe(detail_df, use_container_width=True)
        else:
            st.info("実績データがありません。")

def visualization():
    """可視化ページ"""
    st.header("📈 可視化")
    
    if st.session_state.initiatives.empty:
        st.warning("施策が登録されていません。")
        return
    
    if st.session_state.actuals.empty:
        st.warning("実績データがありません。")
        return
    
    # 施策別予算消化状況
    st.subheader("施策別予算消化状況")
    
    # データ準備
    initiative_data = []
    for _, initiative in st.session_state.initiatives.iterrows():
        initiative_name = initiative['施策名']
        budget = initiative['予算']
        
        total_actual = st.session_state.actuals[
            st.session_state.actuals['施策名'] == initiative_name
        ]['実績'].sum()
        
        consumption_rate = (total_actual / budget * 100) if budget > 0 else 0
        
        initiative_data.append({
            '施策名': initiative_name,
            '予算': budget,
            '実績': total_actual,
            '消化率': consumption_rate
        })
    
    viz_df = pd.DataFrame(initiative_data)
    
    # 進捗バー表示
    for _, row in viz_df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{row['施策名']}**")
            progress_value = min(row['消化率'] / 100, 1.0)  # 100%を超えても1.0でキャップ
            st.progress(progress_value)
            st.write(f"¥{row['実績']:,} / ¥{row['予算']:,} ({row['消化率']:.1f}%)")
        with col2:
            # 色分け（消化率に応じて）
            if row['消化率'] < 50:
                color = "🟢"
            elif row['消化率'] < 80:
                color = "🟡"
            elif row['消化率'] < 100:
                color = "🟠"
            else:
                color = "🔴"
            st.write(f"{color} {row['消化率']:.1f}%")
    
    st.divider()
    
    # 円グラフ（予算配分）
    st.subheader("予算配分")
    fig_pie = px.pie(
        viz_df, 
        values='予算', 
        names='施策名',
        title="施策別予算配分"
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # 棒グラフ（予算vs実績）
    st.subheader("予算 vs 実績比較")
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name='予算',
        x=viz_df['施策名'],
        y=viz_df['予算'],
        marker_color='lightblue'
    ))
    fig_bar.add_trace(go.Bar(
        name='実績',
        x=viz_df['施策名'],
        y=viz_df['実績'],
        marker_color='orange'
    ))
    
    fig_bar.update_layout(
        title="施策別予算vs実績",
        xaxis_title="施策名",
        yaxis_title="金額（円）",
        barmode='group'
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # 月別推移（実績データがある場合）
    if len(st.session_state.actuals['年月'].unique()) > 1:
        st.subheader("月別実績推移")
        
        # 月別・施策別データの準備
        monthly_data = st.session_state.actuals.pivot(
            index='年月', 
            columns='施策名', 
            values='実績'
        ).fillna(0)
        
        fig_line = go.Figure()
        
        for initiative in monthly_data.columns:
            fig_line.add_trace(go.Scatter(
                x=monthly_data.index,
                y=monthly_data[initiative],
                mode='lines+markers',
                name=initiative
            ))
        
        fig_line.update_layout(
            title="月別実績推移",
            xaxis_title="年月",
            yaxis_title="実績（円）"
        )
        
        st.plotly_chart(fig_line, use_container_width=True)

if __name__ == "__main__":
    main()
