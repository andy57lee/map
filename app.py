import pandas as pd
from flask import Flask, render_template_string, jsonify, request
import os

app = Flask(__name__)
CSV_PATH = '旅遊景點.csv' 

def load_data():
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df['緯度'] = pd.to_numeric(df['緯度'], errors='coerce')
    df['經度'] = pd.to_numeric(df['經度'], errors='coerce')
    return df.dropna(subset=['緯度', '經度'])

@app.route('/')
def index():
    df = load_data()
    all_spots = df.to_dict(orient='records')
    return render_template_string(HTML_TEMPLATE, spots=all_spots)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>京都行程規劃工具</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        /* 調大基礎字體 */
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft JhengHei", sans-serif; font-size: 16px; }
        
        /* 側邊欄寬度調整，並加大內距 */
        #sidebar { width: 35%; min-width: 140px; background: #fff; border-right: 1px solid #ccc; display: flex; flex-direction: column; }
        #header { padding: 10px; background: #2c3e50; color: white; }
        #header h3 { margin: 0; font-size: 1.2rem; }
        
        /* 加大清單字體與間距，方便手指點擊 */
        .spot-card { padding: 15px 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .spot-card h3 { margin: 0; font-size: 1.1rem; color: #d35400; }
        .spot-card small { font-size: 0.9rem; color: #666; display: block; margin-top: 4px; }
        
        #spot-list { overflow-y: auto; flex-grow: 1; }
        #map { flex-grow: 1; }

        /* 加大路徑規劃面板的按鈕 */
        .nav-panel { padding: 10px; background: #ecf0f1; border-top: 1px solid #ccc; font-size: 14px; }
        .btn-nav { background: #3498db; color: white; padding: 12px; text-decoration: none; border-radius: 6px; 
                   display: block; text-align: center; margin-top: 8px; font-weight: bold; font-size: 1rem; }
        
        /* Leaflet 標籤字體加大 */
        .leaflet-tooltip { font-size: 14px !important; font-weight: bold; }
        .leaflet-popup-content { font-size: 16px !important; line-height: 1.5; }
        .leaflet-popup-content button { padding: 8px; font-size: 14px; width: 100%; margin-top: 5px; cursor: pointer; }
    </style>
</head>
<body>
<div id="sidebar">
    <div id="header">
        <h3>京都景點</h3>
    </div>
    <div id="spot-list">
        {% for spot in spots %}
        <div class="spot-card" onclick="focusSpot('{{ spot.景點 }}')">
            <h3>{{ spot.景點 }}</h3>
            <small>⭐{{ spot.評價 }} · {{ spot.分類 }}</small>
        </div>
        {% endfor %}
    </div>
    <div class="nav-panel" id="route-info">
        <span id="start-name" style="color:#2980b9">起點未設</span> ➔ 
        <span id="end-name" style="color:#c0392b">終點未設</span>
        <a id="go-link" href="#" target="_blank" class="btn-nav" style="display:none;">開始導航</a>
    </div>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', { zoomControl: false }).setView([35.0116, 135.7681], 13);
    L.control.zoom({ position: 'topright' }).addTo(map); // 將縮放按鈕移到右邊，避免擋到側邊欄
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var highlightLayer = L.layerGroup().addTo(map);
    var spotsData = {{ spots|tojson }};
    var startPoint = null;
    var endPoint = null;

    // 自定義標記圖示：變大一點
    var bigIcon = L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [30, 46], // 原本是 [25, 41]
        iconAnchor: [15, 46],
        popupAnchor: [1, -34],
        shadowSize: [46, 46]
    });

    spotsData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度], {icon: bigIcon}).addTo(map);
        marker.bindTooltip(spot.景點, { direction: 'top', permanent: false });
        
        var popupContent = document.createElement('div');
        popupContent.innerHTML = `
            <div style="min-width:150px">
                <strong style="font-size:1.2rem">${spot.景點}</strong><br>
                <p style="margin:5px 0">${spot.景點說明 || ''}</p>
                <button onclick="setRoute('start', '${spot.景點}', ${spot.緯度}, ${spot.經度})">設為起點 A</button>
                <button onclick="setRoute('end', '${spot.景點}', ${spot.緯度}, ${spot.經度})">設為終點 B</button>
            </div>
        `;
        marker.bindPopup(popupContent);
        allMarkers[spot.景點] = marker;
    });

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
        }
    }

    function focusSpot(spotName) {
        var target = spotsData.find(s => s.景點 === spotName);
        if (target) {
            highlightLayer.clearLayers();
            map.flyTo([target.緯度, target.經度], 16);
            L.circle([target.緯度, target.經度], {
                radius: 300, color: '#e74c3c', fillOpacity: 0.15, weight: 2
            }).addTo(highlightLayer);
            allMarkers[spotName].openPopup();
        }
    }
</script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
