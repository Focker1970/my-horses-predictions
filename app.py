"""My Horses AI — 競馬予測公開ページ"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PREDICTIONS_DIR = APP_DIR / "data" / "predictions"
STRATEGY_DIR = APP_DIR / "data" / "strategy"

st.set_page_config(page_title="My Horses AI 予測", page_icon="🏇", layout="wide")
st.title("🏇 My Horses AI — レース予測")

# ── タブ構成 ──
tab_pred, tab_fight, tab_bt = st.tabs(["📁 予測一覧", "🔥 勝負レース", "📈 バックテスト成績"])

# ====================================================================
# 共通: 予測JSON読み込み
# ====================================================================
if PREDICTIONS_DIR.exists():
    json_files = sorted(PREDICTIONS_DIR.glob("*.json"), reverse=True)
else:
    json_files = []

# ====================================================================
# タブ1: 予測一覧（既存機能）
# ====================================================================
with tab_pred:
    if not json_files:
        st.info("予測データはまだありません。")
    else:
        date_labels = [f.stem for f in json_files]
        selected_date = st.selectbox("日付を選択", date_labels, key="pred_date")

        if selected_date:
            pred_path = PREDICTIONS_DIR / f"{selected_date}.json"
            with open(pred_path, encoding="utf-8") as f:
                pred_data = json.load(f)

            # モードバッジ
            pred_mode = pred_data.get("mode", "")
            generated_at = pred_data.get("generated_at", "不明")
            evening_generated_at = pred_data.get("evening_generated_at", "")
            if pred_mode == "morning":
                evening_info = f"（前日予測: {evening_generated_at}）" if evening_generated_at else ""
                st.caption(f"生成日時: {generated_at}　🌅 **当日更新**（オッズ・期待値反映）{evening_info}")
            elif pred_mode == "evening":
                st.caption(f"生成日時: {generated_at}　🌙 **前日予測**（実力評価）")
            else:
                st.caption(f"生成日時: {generated_at}")

            if not pred_data.get("races"):
                st.warning("この日の予測データにレースが含まれていません。")
            else:
                for race in pred_data["races"]:
                    race_label = race.get("race_name", race.get("race_id", ""))
                    grade = race.get("grade", "")
                    venue = race.get("venue", "")
                    distance = race.get("distance", "")
                    track_cond = race.get("track_condition", "")
                    conf = race.get("confidence", {})
                    conf_label = conf.get("label", "")
                    conf_level = conf.get("level", 0)
                    conf_badge = f" {conf_label}" if conf_label and conf_label != "−" else ""
                    header = f"[{selected_date}]{conf_badge} {race_label}"
                    if grade:
                        header += f" ({grade})"
                    if venue or distance:
                        header += f" — {venue} {distance}"
                    if track_cond:
                        header += f" / {track_cond}"

                    with st.expander(header, expanded=False):
                        # 勝負度表示
                        if conf_label and conf_label != "−":
                            conf_icons = {3: "🔥", 2: "⚡", 1: "💧", 0: "❄️"}
                            conf_colors = {3: "red", 2: "orange", 1: "blue", 0: "gray"}
                            ci = conf_icons.get(conf_level, "")
                            cc = conf_colors.get(conf_level, "gray")
                            st.markdown(f"**{ci} 勝負度: :{cc}[{conf_label}]**")
                            conf_reason = conf.get("reason", "")
                            if conf_reason:
                                st.caption(conf_reason)

                        predicted_at = race.get("predicted_at", "")
                        if predicted_at:
                            st.caption(f"予測日時: {predicted_at}")

                        # 予測結果テーブル
                        preds = race.get("predictions", [])
                        if preds:
                            pred_df = pd.DataFrame(preds)
                            pred_df = pred_df.sort_values("予測順位").reset_index(drop=True)
                            if "単勝" in pred_df.columns:
                                pred_df["単勝"] = pd.to_numeric(pred_df["単勝"], errors="coerce")
                            if "期待値" in pred_df.columns:
                                pred_df["期待値"] = pd.to_numeric(pred_df["期待値"], errors="coerce")
                            elif "単勝" in pred_df.columns:
                                pred_df["期待値"] = ((pred_df["勝率(%)"] / 100) * pred_df["単勝"]).round(2)
                            if "人気" in pred_df.columns:
                                pred_df["人気"] = pd.to_numeric(pred_df["人気"], errors="coerce")
                            disp_cols = [c for c in ["予測順位", "馬番", "馬名", "勝率(%)", "単勝", "人気", "スコア", "期待値"] if c in pred_df.columns]
                            disp_df = pred_df[disp_cols].copy()
                            if "単勝" in disp_df.columns:
                                disp_df = disp_df.rename(columns={"単勝": "単勝オッズ"})
                            fmt = {}
                            if "単勝オッズ" in disp_df.columns:
                                fmt["単勝オッズ"] = "{:.1f}"
                            if "スコア" in disp_df.columns:
                                fmt["スコア"] = "{:.3f}"
                            if "期待値" in disp_df.columns:
                                fmt["期待値"] = "{:.2f}"
                            st.dataframe(disp_df.style.format(fmt, na_rep="-"), use_container_width=True, hide_index=True)

                            # Top3
                            top3 = pred_df.head(3)
                            cols = st.columns(min(3, len(top3)))
                            medals = ["🥇", "🥈", "🥉"]
                            for i, (_, row) in enumerate(top3.iterrows()):
                                with cols[i]:
                                    st.metric(f"{medals[i]} {row['馬名']}", f"{row['勝率(%)']}%", f"馬番 {int(row['馬番'])}")

                        # 購入推奨
                        rec = race.get("recommendation")
                        if rec:
                            pattern_icons = {"本命型": "🎯", "混戦型": "⚔️", "波乱型": "🌊"}
                            icon = pattern_icons.get(rec.get("パターン", ""), "")
                            st.markdown(f"**{icon} レースパターン: {rec.get('パターン', '')}**")
                            st.caption(rec.get("パターン説明", ""))

                            bets = rec.get("推奨買い目", [])
                            if bets:
                                st.markdown("**推奨買い目**")
                                for bet in bets:
                                    st.markdown(f"- **{bet['馬券種']}** {bet['買い目']}  \n  _{bet['理由']}_")
                            else:
                                st.info("期待値がプラスの馬券が見つかりませんでした。")

                            ev_list = rec.get("期待値一覧", [])
                            if ev_list:
                                st.markdown("**各馬の期待値一覧**")
                                ev_df = pd.DataFrame(ev_list).sort_values("予測順位")
                                ev_cols = [c for c in ["予測順位", "馬番", "馬名", "勝率(%)", "単勝", "期待値"] if c in ev_df.columns]
                                ev_disp = ev_df[ev_cols].copy()
                                if "単勝" in ev_disp.columns:
                                    ev_disp["単勝"] = pd.to_numeric(ev_disp["単勝"], errors="coerce")
                                    ev_disp = ev_disp.rename(columns={"単勝": "単勝オッズ"})
                                if "期待値" in ev_disp.columns:
                                    ev_disp["期待値"] = pd.to_numeric(ev_disp["期待値"], errors="coerce")
                                ev_fmt = {}
                                if "単勝オッズ" in ev_disp.columns:
                                    ev_fmt["単勝オッズ"] = "{:.1f}"
                                if "期待値" in ev_disp.columns:
                                    ev_fmt["期待値"] = "{:.2f}"
                                st.dataframe(
                                    ev_disp.style
                                    .apply(
                                        lambda row: ["background-color: #e6f4ea; color: #1a1a1a"] * len(row)
                                        if pd.notna(row.get("期待値")) and row["期待値"] > 1.0
                                        else ["background-color: #ffffff; color: #1a1a1a"] * len(row),
                                        axis=1,
                                    )
                                    .format(ev_fmt, na_rep="-"),
                                    use_container_width=True, hide_index=True,
                                )

                        # レース結果
                        result_data = race.get("result")
                        if result_data:
                            st.markdown("---")
                            st.markdown("**📊 レース結果**")
                            result_df = pd.DataFrame(result_data)
                            if "着順" in result_df.columns and len(result_df) > 0:
                                result_df["着順"] = pd.to_numeric(result_df["着順"], errors="coerce")
                                valid = result_df[result_df["着順"].notna()].copy()
                                valid["着順"] = valid["着順"].astype(int)
                                if preds and len(valid) > 0:
                                    pred_top = pred_df.iloc[0]
                                    winner = valid.loc[valid["着順"].idxmin()]
                                    pred_umaban = int(pred_top["馬番"])
                                    win_umaban = int(winner["馬番"])
                                    if pred_umaban == win_umaban:
                                        st.success(f"✅ 的中！ 予測1位 {pred_top['馬名']}（馬番{pred_umaban}）= 1着")
                                    else:
                                        pred_top_result = valid[valid["馬番"] == pred_umaban]
                                        if len(pred_top_result) > 0:
                                            actual_rank = int(pred_top_result.iloc[0]["着順"])
                                            st.error(f"❌ 不的中 — 予測1位 {pred_top['馬名']}（馬番{pred_umaban}）→ {actual_rank}着 / 1着: {winner['馬名']}（馬番{win_umaban}）")
                                        else:
                                            st.error(f"❌ 不的中 — 予測1位 {pred_top['馬名']}（馬番{pred_umaban}）→ 出走取消 / 1着: {winner['馬名']}（馬番{win_umaban}）")
                                top5 = valid.sort_values("着順").head(5)
                                disp_result_cols = [c for c in ["着順", "馬番", "馬名", "タイム", "単勝", "人気"] if c in top5.columns]
                                result_disp = top5[disp_result_cols].copy()
                                if "単勝" in result_disp.columns:
                                    result_disp = result_disp.rename(columns={"単勝": "単勝オッズ"})
                                st.dataframe(result_disp, use_container_width=True, hide_index=True)

    # 回収率の考え方
    with st.expander("📊 回収率の考え方"):
        st.markdown("""
**期待値（EV）とは？**
- `期待値 = モデル勝率(%) / 100 × 単勝オッズ`
- **EV > 1.0** → モデルが市場（オッズ）より高く評価 → 購入価値あり
- **EV < 1.0** → オッズなりか過大評価 → 見送り

**回収率とは？**
- `回収率(%) = 払戻金の合計 ÷ 購入金額の合計 × 100`
- 100%超え = 利益が出ている状態、100%未満 = 損失（トリガミ含む）

**パターン別の戦略**
- 🎯 **本命型**: 1位の勝率が突出 → 単勝・複勝で堅実に
- ⚔️ **混戦型**: 上位が拮抗 → 馬連・ワイドで的中範囲を広げる
- 🌊 **波乱型**: 高オッズ馬が上位 → 3連複・馬単で高配当を狙う
""")

# ====================================================================
# タブ2: 本日の勝負レース
# ====================================================================
with tab_fight:
    st.subheader("勝負レース")

    if not json_files:
        st.info("予測データがありません。")
    else:
        date_labels_f = [f.stem for f in json_files]
        selected_f = st.selectbox("日付", date_labels_f, key="fight_date")

        pred_path_f = PREDICTIONS_DIR / f"{selected_f}.json"
        with open(pred_path_f, encoding="utf-8") as f:
            pred_data_f = json.load(f)

        races_f = pred_data_f.get("races", [])
        if not races_f:
            st.warning("この日のレースデータがありません。")
        else:
            for r in races_f:
                r["_conf_level"] = r.get("confidence", {}).get("level", 0)
            races_sorted = sorted(races_f, key=lambda x: x["_conf_level"], reverse=True)

            min_level = st.slider("最低勝負度", 0, 3, 2, key="fight_min_conf")

            conf_icons = {3: "🔥", 2: "⚡", 1: "💧", 0: "❄️"}
            shown = 0
            for race in races_sorted:
                conf = race.get("confidence", {})
                level = conf.get("level", 0)
                if level < min_level:
                    continue
                shown += 1

                label = conf.get("label", "−")
                reason = conf.get("reason", "")
                race_name = race.get("race_name", race.get("race_id", ""))
                grade = race.get("grade", "")
                distance = race.get("distance", "")
                icon = conf_icons.get(level, "")

                header = f"{icon} {label} — {race_name}"
                if grade:
                    header += f" ({grade})"
                if distance:
                    header += f" {distance}"

                with st.expander(header, expanded=(level >= 3)):
                    if reason:
                        st.caption(reason)

                    preds = race.get("predictions", [])
                    if preds:
                        pred_df = pd.DataFrame(preds).sort_values("予測順位").reset_index(drop=True)
                        if "単勝" in pred_df.columns:
                            pred_df["単勝"] = pd.to_numeric(pred_df["単勝"], errors="coerce")
                        if "期待値" in pred_df.columns:
                            pred_df["期待値"] = pd.to_numeric(pred_df["期待値"], errors="coerce")
                        elif "単勝" in pred_df.columns:
                            pred_df["期待値"] = ((pred_df["勝率(%)"] / 100) * pred_df["単勝"]).round(2)
                        if "人気" in pred_df.columns:
                            pred_df["人気"] = pd.to_numeric(pred_df["人気"], errors="coerce")

                        disp_cols = [c for c in ["予測順位", "馬番", "馬名", "勝率(%)", "単勝", "人気", "期待値"] if c in pred_df.columns]
                        disp = pred_df[disp_cols].copy()
                        if "単勝" in disp.columns:
                            disp = disp.rename(columns={"単勝": "単勝オッズ"})
                        fmt = {}
                        if "単勝オッズ" in disp.columns:
                            fmt["単勝オッズ"] = "{:.1f}"
                        if "期待値" in disp.columns:
                            fmt["期待値"] = "{:.2f}"
                        st.dataframe(disp.style.format(fmt, na_rep="-"), use_container_width=True, hide_index=True)

                    rec = race.get("recommendation", {})
                    bets = rec.get("推奨買い目", [])
                    if bets:
                        st.markdown("**推奨買い目**")
                        for bet in bets:
                            st.markdown(f"- **{bet['馬券種']}** {bet['買い目']}  \n  _{bet['理由']}_")

            if shown == 0:
                st.info(f"勝負度{min_level}以上のレースはありません。スライダーを下げて表示範囲を広げてください。")

    # 勝負度の説明
    with st.expander("勝負度（★1〜3）とは？"):
        st.markdown("""
**勝負度**は、バックテスト（4,206レース）の多次元分析で特定した「回収率の高い条件」に基づく加点方式のスコアです。

| 勝負度 | 意味 |
|--------|------|
| 🔥 ★★★ | 好条件が揃っている。積極的に勝負 |
| ⚡ ★★ | まずまず。標準的に賭ける |
| 💧 ★ | 条件が揃わない。見送りも検討 |
| ❄️ − | 情報不足 or 悪条件。見送り推奨 |

**主な加点条件**:
- モデル1位が2〜3番人気（バックテスト回収率89.4%）
- 波乱型パターン（回収率91.3%）
- 勝率差 < 5%（回収率89.4%）
- 中距離1800〜2200m（回収率86.8%）
- オッズ3〜30倍帯（回収率87.2%）
""")

# ====================================================================
# タブ3: バックテスト成績
# ====================================================================
with tab_bt:
    st.subheader("バックテスト成績")

    filter_csv = STRATEGY_DIR / "filter_results.csv"
    race_csv = STRATEGY_DIR / "race_analysis.csv"

    if not filter_csv.exists():
        st.info("バックテスト分析データはまだありません。")
    else:
        filter_df = pd.read_csv(filter_csv)
        st.caption(f"合計 {len(filter_df)} 条件を分析")

        # 全体ベースライン
        if race_csv.exists():
            race_df = pd.read_csv(race_csv)
            total = len(race_df)
            hits = race_df["的中"].sum()
            payout = race_df["払戻額"].sum()
            inv = total * 100

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("対象レース", f"{total:,}")
            col2.metric("的中率", f"{hits/total*100:.1f}%")
            col3.metric("回収率", f"{payout/inv*100:.1f}%")
            col4.metric("収支", f"{payout - inv:+,.0f}円")

        # 軸数フィルタ
        st.markdown("---")
        axes_filter = st.multiselect("軸数フィルタ", [1, 2, 3], default=[1, 2], key="bt_axes")
        min_races_filter = st.slider("最低レース数", 10, 200, 30, key="bt_min_races")

        filtered = filter_df[
            (filter_df["軸数"].isin(axes_filter)) & (filter_df["レース数"] >= min_races_filter)
        ].copy()

        st.markdown(f"**条件数: {len(filtered)}**")

        top_n = st.slider("表示件数", 10, 100, 30, key="bt_top_n")
        display = filtered.head(top_n)[["軸数", "条件", "値", "レース数", "的中率", "回収率", "収支"]].copy()

        def _color_roi(val):
            if val >= 100:
                return "background-color: #e6f4ea; color: #1a1a1a"
            elif val >= 80:
                return "background-color: #fff8e1; color: #1a1a1a"
            return "background-color: #ffffff; color: #1a1a1a"

        st.dataframe(
            display.style
            .applymap(_color_roi, subset=["回収率"])
            .format({"的中率": "{:.1f}%", "回収率": "{:.1f}%", "収支": "{:+,}円"}),
            use_container_width=True, hide_index=True,
        )

        # 月別回収率チャート
        if race_csv.exists():
            st.markdown("---")
            st.subheader("月別回収率推移")
            race_df["race_date"] = pd.to_datetime(race_df["race_date"], errors="coerce")
            race_df["月"] = race_df["race_date"].dt.to_period("M").astype(str)
            monthly = race_df.groupby("月").agg(
                レース数=("的中", "count"),
                的中数=("的中", "sum"),
                払戻額=("払戻額", "sum"),
            ).reset_index()
            monthly["投資額"] = monthly["レース数"] * 100
            monthly["回収率"] = (monthly["払戻額"] / monthly["投資額"] * 100).round(1)
            monthly["的中率"] = (monthly["的中数"] / monthly["レース数"] * 100).round(1)

            st.bar_chart(monthly.set_index("月")["回収率"])
            st.dataframe(
                monthly[["月", "レース数", "的中数", "的中率", "回収率"]].style.format(
                    {"的中率": "{:.1f}%", "回収率": "{:.1f}%"}
                ),
                use_container_width=True, hide_index=True,
            )
