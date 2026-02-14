"""My Horses AI — 競馬予測公開ページ"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PREDICTIONS_DIR = Path(__file__).resolve().parent / "data" / "predictions"

st.set_page_config(page_title="My Horses AI 予測", page_icon="🏇", layout="wide")
st.title("🏇 My Horses AI — レース予測")

# data/predictions/*.json をスキャン
if PREDICTIONS_DIR.exists():
    json_files = sorted(PREDICTIONS_DIR.glob("*.json"), reverse=True)
else:
    json_files = []

if not json_files:
    st.info("予測データはまだありません。")
else:
    # 日付リスト
    date_labels = [f.stem for f in json_files]
    selected_date = st.selectbox("日付を選択", date_labels)

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
                header = f"[{selected_date}] {race_label}"
                if grade:
                    header += f" ({grade})"
                if venue or distance:
                    header += f" — {venue} {distance}"
                if track_cond:
                    header += f" / {track_cond}"

                with st.expander(header, expanded=False):
                    # 予測日時
                    predicted_at = race.get("predicted_at", "")
                    if predicted_at:
                        st.caption(f"予測日時: {predicted_at}")

                    # 予測結果テーブル
                    preds = race.get("predictions", [])
                    if preds:
                        pred_df = pd.DataFrame(preds)
                        pred_df = pred_df.sort_values("予測順位").reset_index(drop=True)

                        # 期待値列を追加
                        if "単勝" in pred_df.columns:
                            pred_df["単勝"] = pd.to_numeric(pred_df["単勝"], errors="coerce")
                        if "期待値" in pred_df.columns:
                            pred_df["期待値"] = pd.to_numeric(pred_df["期待値"], errors="coerce")
                        elif "単勝" in pred_df.columns:
                            pred_df["期待値"] = (
                                (pred_df["勝率(%)"] / 100) * pred_df["単勝"]
                            ).round(2)
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

                        st.dataframe(
                            disp_df.style.format(fmt, na_rep="-"),
                            use_container_width=True,
                            hide_index=True,
                        )

                        # Top3
                        top3 = pred_df.head(3)
                        cols = st.columns(min(3, len(top3)))
                        medals = ["🥇", "🥈", "🥉"]
                        for i, (_, row) in enumerate(top3.iterrows()):
                            with cols[i]:
                                st.metric(
                                    f"{medals[i]} {row['馬名']}",
                                    f"{row['勝率(%)']}%",
                                    f"馬番 {int(row['馬番'])}",
                                )

                    # 購入推奨
                    rec = race.get("recommendation")
                    if rec:
                        # 妙味診断
                        myomi = rec.get("妙味診断", "")
                        myomi_reason = rec.get("妙味理由", "")
                        if myomi:
                            myomi_icons = {"高": "🔥", "中": "⚡", "低": "❄️"}
                            myomi_colors = {"高": "green", "中": "orange", "低": "gray"}
                            mi = myomi_icons.get(myomi, "")
                            mc = myomi_colors.get(myomi, "gray")
                            st.markdown(f"**{mi} 妙味: :{mc}[{myomi}]**")
                            st.caption(myomi_reason)

                        pattern_icons = {"本命型": "🎯", "混戦型": "⚔️", "波乱型": "🌊"}
                        icon = pattern_icons.get(rec.get("パターン", ""), "")
                        st.markdown(f"**{icon} レースパターン: {rec.get('パターン', '')}**")
                        st.caption(rec.get("パターン説明", ""))

                        bets = rec.get("推奨買い目", [])
                        if bets:
                            st.markdown("**推奨買い目**")
                            for bet in bets:
                                st.markdown(
                                    f"- **{bet['馬券種']}** {bet['買い目']}  \n"
                                    f"  _{bet['理由']}_"
                                )
                        else:
                            st.info("期待値がプラスの馬券が見つかりませんでした。")

                        # 期待値一覧テーブル
                        ev_list = rec.get("期待値一覧", [])
                        if ev_list:
                            st.markdown("**各馬の期待値一覧**")
                            ev_df = pd.DataFrame(ev_list)
                            ev_df = ev_df.sort_values("予測順位")
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
                                use_container_width=True,
                                hide_index=True,
                            )

                    # レース結果（JSONに埋め込み済みの場合）
                    result_data = race.get("result")
                    if result_data:
                        st.markdown("---")
                        st.markdown("**📊 レース結果**")

                        result_df = pd.DataFrame(result_data)
                        if "着順" in result_df.columns and len(result_df) > 0:
                            result_df["着順"] = pd.to_numeric(result_df["着順"], errors="coerce")
                            valid = result_df[result_df["着順"].notna()].copy()
                            valid["着順"] = valid["着順"].astype(int)

                            # 的中判定
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

                            # 上位5着
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
- 競馬の平均回収率は約75%前後（払戻率70〜80%）に収束
- **的中率と回収率は別物** — 全レース的中でも払戻が少なければ赤字になる

**期待値重視で馬を選ぶ**
- 「勝つ確率が高い馬」ではなく「勝率に対してオッズが高い馬」を狙う
- 過剰人気の馬は配当が低く回収率を下げる → 避ける
- 実力があるのに前走不利などで低評価の穴馬を絡めると効果的

**券種ごとの控除率を意識する**
| 券種 | 払戻率 |
|------|--------|
| 単勝・複勝 | 約80% |
| 馬連 | 約77.5% |
| 3連単 | 約72.5% |

控除率の低い単勝・複勝はプロも愛用する優秀な券種。

**トリガミを徹底排除する**
- BOX買いは買い目が増えすぎて利益が削られる
- 合成オッズを確認し、十分なリターンが見込めないレースは見送る勇気も必要

**NGな買い方**
- 3連単など高配当券種だけにこだわる
- 利益の出ない「押さえ」馬券を買いすぎる
- 根拠なく人気馬ばかりを並べる

**パターン別の戦略**
- 🎯 **本命型**: 1位の勝率が突出 → 単勝・複勝で堅実に
- ⚔️ **混戦型**: 上位が拮抗 → 馬連・ワイドで的中範囲を広げる
- 🌊 **波乱型**: 高オッズ馬が上位 → 3連複・馬単で高配当を狙う
""")
