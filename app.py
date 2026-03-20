import pandas as pd
from flask import Flask, render_template_string, jsonify, request
import os

app = Flask(__name__)

# 請確保路徑與你的電腦環境一致
CSV_PATH = r'F:\Python\data\旅遊景點.csv'

def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    # 使用 utf-8-sig 處理中日文字元，避免亂碼
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df['緯度'] = pd.to_numeric(df['緯度'], errors='coerce')
    df['經度'] = pd.to_numeric(df['經度'], errors='coerce')
    return df.dropna(subset=['緯度', '經度'])

@app.route('/')
def index():
    df = load_data()
    all_spots = df.to_dict(orient='records')
    return render_template_string(HTML_TEMPLATE, spots=all_spots)

# 使用原始字串避免 Python 轉義字元干擾 JavaScript
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>京都行程規劃工具</title>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft JhengHei", sans-serif; }
        #sidebar { width: 320px; background: #fff; border-right: 1px solid #ccc; display: flex; flex-direction: column; }
        #header { padding: 15px; background: #2c3e50; color: white; }
        #spot-list { overflow-y: auto; flex-grow: 1; }
        .spot-card { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; transition: 0.2s; }
        .spot-card:hover { background: #f1f4f6; }
        .spot-card h3 { margin: 0; font-size: 16px; color: #d35400; }
        #map { flex-grow: 1; }
        .nav-panel { padding: 10px; background: #ecf0f1; border-top: 1px solid #ccc; font-size: 13px; }
        .btn-nav { background: #3498db; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: block; text-align: center; margin-top: 5px; }
    </style>
</head>
<body>

<div id="sidebar">
    <div id="header">
        <h3>京都景點規劃</h3>
        <small>滑鼠移過點位預覽，點擊設定航線</small>
    </div>
    <div id="spot-list">
        {% for spot in spots %}
        <div class="spot-card" onclick="focusSpot('{{ spot.景點 }}')">
            <h3>{{ spot.景點 }}</h3>
            <small>{{ spot.城市 }} · {{ spot.分類 }} · ⭐{{ spot.評價 }}</small>
        </div>
        {% endfor %}
    </div>
    <div class="nav-panel" id="route-info">
        <b>路線規劃：</b><br>
        起點 (A)：<span id="start-name">未設定</span><br>
        終點 (B)：<span id="end-name">未設定</span>
        <a id="go-link" href="#" target="_blank" class="btn-nav" style="display:none;">開啟 Google 路線規劃</a>
    </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // 初始化地圖
    var map = L.map('map').setView([35.0116, 135.7681], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var highlightLayer = L.layerGroup().addTo(map);
    var spotsData = {{ spots|tojson }};
    
    var startPoint = null;
    var endPoint = null;

    // 建立所有標記
    spotsData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度]).addTo(map);
        
        // 1. 滑鼠移入預覽 (Tooltip)
        marker.bindTooltip(`<b>${spot.景點}</b><br>評價: ${spot.評價}`, { direction: 'top' });

        // 2. 點擊彈出視窗 (設定 A/B 點)
        var popupContent = document.createElement('div');
        popupContent.innerHTML = `
            <div style="width:180px">
                <h4>${spot.景點}</h4>
                <p style="font-size:12px">${spot.景點說明}</p>
                <button onclick="setRoute('start', '${spot.景點}', ${spot.緯度}, ${spot.經度})">設為起點 A</button>
                <button onclick="setRoute('end', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="margin-top:5px">設為終點 B</button>
            </div>
        `;
        marker.bindPopup(popupContent);
        
        allMarkers[spot.景點] = marker;
    });

    // 路線設定邏輯
    function setRoute(type, name, lat, lon) {
        if (type === 'start') {
            startPoint = { name: name, pos: lat + ',' + lon };
            document.getElementById('start-name').innerText = name;
        } else {
            endPoint = { name: name, pos: lat + ',' + lon };
            document.getElementById('end-name').innerText = name;
        }

        if (startPoint && endPoint) {
            var url = `https://www.google.com/maps/dir/?api=1&origin=${startPoint.pos}&destination=${endPoint.pos}&travelmode=transit`;
            var link = document.getElementById('go-link');
            link.href = url;
            link.style.display = 'block';
            link.innerText = `規劃 ${startPoint.name} ➔ ${endPoint.name}`;
        }
    }

    // 左側選單連動
    function focusSpot(spotName) {
        var target = spotsData.find(s => s.景點 === spotName);
        if (target) {
            highlightLayer.clearLayers();
            map.flyTo([target.緯度, target.經度], 17);
            
            // 畫出 500m 範圍圈
            L.circle([target.緯度, target.經度], {
                radius: 500,
                color: '#e74c3c',
                fillOpacity: 0.1,
                weight: 1
            }).addTo(highlightLayer);

            allMarkers[spotName].openPopup();
        }
    }
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
