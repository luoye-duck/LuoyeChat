# -*- coding: utf-8 -*-
"""把 Natural Earth 陆地轮廓采样成点阵，按行做位图编码（hex），供官网 canvas 绘制"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "land110.geojson")
OUT = os.path.join(HERE, "land_bitmap.json")

LON_MIN, LON_MAX = -180.0, 180.0
LAT_MIN, LAT_MAX = -58.0, 84.0        # 去掉南极，画面更紧凑
STEP = 1.5


def point_in_ring(x, y, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def main():
    data = json.load(open(SRC, "r", encoding="utf-8"))
    polys = []
    for feat in data["features"]:
        geom = feat["geometry"]
        coords = geom["coordinates"]
        groups = [coords] if geom["type"] == "Polygon" else coords
        for rings in groups:
            outer = rings[0]
            xs = [p[0] for p in outer]
            ys = [p[1] for p in outer]
            polys.append(((min(xs), min(ys), max(xs), max(ys)), rings))

    def is_land(lon, lat):
        for (x0, y0, x1, y1), rings in polys:
            if lon < x0 or lon > x1 or lat < y0 or lat > y1:
                continue
            if point_in_ring(lon, lat, rings[0]):
                hit = True
                for hole in rings[1:]:
                    if point_in_ring(lon, lat, hole):
                        hit = False
                        break
                if hit:
                    return True
        return False

    cols = int(round((LON_MAX - LON_MIN) / STEP))      # 240
    rows = int(round((LAT_MAX - LAT_MIN) / STEP))      # 95
    out_rows = []
    total = 0
    for r in range(rows):
        lat = LAT_MAX - (r + 0.5) * STEP
        bits = 0
        hexs = []
        for c in range(cols):
            lon = LON_MIN + (c + 0.5) * STEP
            if is_land(lon, lat):
                bits |= 8 >> (c & 3)
                total += 1
            if (c & 3) == 3:
                hexs.append("%x" % bits)
                bits = 0
        if cols & 3:
            hexs.append("%x" % bits)
        out_rows.append("".join(hexs))

    meta = {"cols": cols, "rows": rows, "step": STEP,
            "lonMin": LON_MIN, "lonMax": LON_MAX,
            "latMin": LAT_MIN, "latMax": LAT_MAX,
            "bits": out_rows}
    json.dump(meta, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
    print("陆地格点 %d / %d，%d 行，%d 列 -> %s (%.1f KB)" % (
        total, rows * cols, rows, cols, OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    main()
