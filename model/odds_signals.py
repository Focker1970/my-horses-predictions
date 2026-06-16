"""オッズ変動シグナル検出（pure stdlib・public/ アプリと共有）。"""
from __future__ import annotations

ODDS_CRASH_THRESHOLD = 0.40  # 前日夜→最終 で 40% 以上下落で警告


def detect_odds_crash(
    predictions: list[dict],
    threshold: float = ODDS_CRASH_THRESHOLD,
) -> list[dict]:
    """各馬の単勝_evening → 単勝 の下落率を計算し、threshold 以上の急落馬を返す。

    Returns:
        [{馬名, 馬番, 単勝_evening, 単勝, 下落率, 下落率_raw, 予測順位, 人気}, ...]
        下落率の大きい順。下落率は表示用%（小数1位）、下落率_raw は 0.0〜1.0 の生値。
        人気・予測順位・馬番が欠損していても None で返り、UI 側で安全に扱える。
    """
    crashed = []
    for p in predictions or []:
        eve = p.get("単勝_evening")
        cur = p.get("単勝")
        if eve is None or cur is None:
            continue
        try:
            eve_f, cur_f = float(eve), float(cur)
        except (TypeError, ValueError):
            continue
        if eve_f <= 0 or cur_f <= 0:
            continue
        drop = (eve_f - cur_f) / eve_f
        if drop < threshold:
            continue

        def _safe_int(v):
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        crashed.append({
            "馬名": p.get("馬名") or "(不明)",
            "馬番": _safe_int(p.get("馬番")),
            "単勝_evening": eve_f,
            "単勝": cur_f,
            "下落率": round(drop * 100, 1),
            "下落率_raw": drop,
            "予測順位": _safe_int(p.get("予測順位")),
            "人気": _safe_int(p.get("人気")),
        })
    crashed.sort(key=lambda x: -x["下落率_raw"])
    return crashed
