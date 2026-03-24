import pandas as pd
from flask import Flask, render_template_string
import os
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '旅遊景點.csv')

def load_structured_data():
    if not os.path.exists(CSV_PATH):
        return {}
    
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df['緯度'] = pd.to_numeric(df['緯度'], errors='coerce')
    df['經度'] = pd.to_numeric(df['經度'], errors='coerce')
    df = df.dropna(subset=['緯度', '經度'])

    # 建立三層結構：城市 -> 主要景點 -> 周邊
    structured = {}
    cities = df['城市'].unique()

    for city in cities:
        city_df = df[df['城市'] == city]
        # 假設分類中有 "主要景點" 這個類別
        main_spots = city_df[city_df['分類'] == '主要景點'].to_dict(orient='records')
        
        city_data = []
        for main in main_spots:
            # 這裡可以自定義邏輯：例如找尋距離主要景點 1km 內的作為周邊
            # 簡單起見，我們先以相同城市的「非主要景點」作為該城市所有主要景點的共用周邊，或不分層
            others = city_df[city_df['分類'] != '主要景點'].to_dict(orient='records')
            main['sub_spots'] = others
            city_data.append(main)
        
        structured[city] = city_data
    
    return structured, df.to_dict(orient='records')

@app.route('/')
def index():
    structured, all_raw = load_structured_data()
    return render_template_string(HTML_TEMPLATE, structured=structured, all_raw=all_raw)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Japan Travel Map v2</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft JhengHei", sans-serif; overflow: hidden; }
        
        /* 側邊欄優化：手機版寬度調整 */
        #sidebar { 
            width: 320px; 
            background: #fff; 
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            display: flex; 
            flex-direction: column; 
            transition: transform 0.3s ease;
            flex-shrink: 0;
            z-index: 1001;
        }

        @media (max-width: 600px) {
            #sidebar { width: 80vw; } /* 手機版只佔 80% 寬度 */
            #sidebar.hidden { transform: translateX(-80vw); margin-right: -80vw; }
        }

        #sidebar.hidden { transform: translateX(-320px); margin-right: -320px; }

        #header { padding: 15px; background: #2c3e50; color: white; display: flex; align-items: center; }
        
        /* 層級選單樣式 */
        .city-group { background: #f1f1f1; padding: 10px; font-weight: bold; cursor: pointer; border-bottom: 1px solid #ddd; }
        .main-spot { padding: 12px 12px 12px 25px; border-bottom: 1px solid #eee; cursor: pointer; background: #fff; color: #d35400; font-weight: bold; }
        .sub-spot { padding: 8px 8px 8px 45px; border-bottom: 1px solid #f9f9f9; cursor: pointer; font-size: 13px; color: #666; background: #fafafa; }
        .sub-spot:hover { background: #eef; }

        #spot-list { overflow-y: auto; flex-grow: 1; }
        #map { flex-grow: 1; height: 100%; position: relative; z-index: 1; }

        #toggle-out {
            position: absolute; left: 10px; top: 10px; z-index: 1000;
            background: #2c3e50; color: white; border-radius: 50%; width: 40px; height: 40px; cursor: pointer;
            display: none; align-items: center; justify-content: center; border: none;
        }

        .hamburger { width: 18px; height: 2px; background: white; position: relative; }
        .hamburger::before, .hamburger::after { content: ""; width: 18px; height: 2px; background: white; position: absolute; left: 0; }
        .hamburger::before { top: -6px; } .hamburger::after { top: 6px; }
    </style>
</head>
<body>

<div id="sidebar">
    <div id="header">
        <button onclick="toggleSidebar()" style="background:none; border:none; cursor:pointer; margin-right:10px;">
            <div class="hamburger"></div>
        </button>
        <span>行程導覽</span>
    </div>
    <div id="spot-list">
        {% for city, main_spots in structured.items() %}
            <div class="city-group">📍 {{ city }}</div>
            {% for main in main_spots %}
                <div class="main-spot" onclick="focusSpot('{{ main.景點 }}')">🏯 {{ main.景點 }} ({{ main.評價 }})</div>
                {% for sub in main.sub_spots %}
                    <div class="sub-spot" onclick="focusSpot('{{ sub.景點 }}')">└ {{ sub.景點 }}</div>
                {% endfor %}
            {% endfor %}
        {% endfor %}
    </div>
</div>

<div id="map">
    <button id="toggle-out" onclick="toggleSidebar()"><div class="hamburger"></div></button>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', { zoomControl: false }).setView([35.0116, 135.7681], 12);
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var allData = {{ all_raw|tojson }};
    
    function toggleSidebar() {
        var sb = document.getElementById('sidebar');
        var btn = document.getElementById('toggle-out');
        if (sb.classList.contains('hidden')) {
            sb.classList.remove('hidden');
            btn.style.display = 'none';
        } else {
            sb.classList.add('hidden');
            btn.style.display = 'flex';
        }
        setTimeout(() => map.invalidateSize(), 350);
    }

    allData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度]).addTo(map);
        marker.bindPopup(`<b>${spot.景點}</b><br>${spot.景點說明 || ''}`);
        allMarkers[spot.景點] = marker;
    });

    function focusSpot(name) {
        var target = allData.find(s => s.景點 === name);
        if (target) {
            map.flyTo([target.緯度, target.經度], 16);
            allMarkers[name].openPopup();
            if (window.innerWidth < 600) toggleSidebar();
        }
    }
</script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
