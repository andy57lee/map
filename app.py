from flask import Flask, render_template_string
import pandas as pd
import os

app = Flask(__name__)

# 讀取 CSV 檔案
def get_spots():
    try:
        # 讀取你上傳的旅遊景點.csv
        df = pd.read_csv('旅遊景點.csv')
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

# 這裡是針對手機橫放優化的 HTML 模板
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>京都行程規劃工具</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft JhengHei", sans-serif; overflow: hidden; }
        
        /* 側邊欄優化：增加獨立捲動與響應式寬度 */
        #sidebar { 
            width: 300px; 
            background: #fff; 
            border-right: 1px solid #ccc; 
            display: flex; 
            flex-direction: column; 
            transition: width 0.3s ease; 
            z-index: 1000;
            flex-shrink: 0;
            overflow: hidden;
        }
        
        #header { padding: 15px; background: #2c3e50; color: white; flex-shrink: 0; }
        #header h3 { margin: 0; font-size: 18px; }
        
        /* 景點列表：允許獨立上下捲動，解決景點太多無法滑動的問題 */
        #spot-list { 
            overflow-y: auto; 
            flex-grow: 1; 
            -webkit-overflow-scrolling: touch; 
        }

        .spot-card { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .spot-card:hover { background: #f1f4f6; }
        .spot-card h3 { margin: 0; font-size: 16px; color: #d35400; }
        .spot-card small { font-size: 12px; }
        
        #map { flex-grow: 1; height: 100%; position: relative; }

        .nav-panel { padding: 10px; background: #ecf0f1; border-top: 1px solid #ccc; font-size: 13px; flex-shrink: 0; }
        .btn-nav { background: #3498db; color: white; padding: 8px; text-decoration: none; border-radius: 4px; display: block; text-align: center; margin-top: 5px; font-weight: bold; }
        
        /* === 手機橫向響應式微調 === */
        /* 當螢幕高度小於 450px 時（手機橫放），自動縮窄選單以增加地圖視野 */
        @media (max-height: 450px) {
            #sidebar { width: 180px; } 
            #header { padding: 8px 12px; }
            #header h3 { font-size: 15px; }
            #header small { display: none; }
            
            .spot-card { padding: 8px 10px; }
            .spot-card h3 { font-size: 14px; }
            
            .nav-panel { padding: 5px; font-size: 11px; }
            .btn-nav { padding: 5px; font-size: 12px; }
        }
    </style>
</head>
<body>

<div id="sidebar">
    <div id="header">
        <h3>京都景點 ({{ spots|length }})</h3>
        <small>列表可滑動捲動</small>
    </div>
    <div id="spot-list">
        {% for spot in spots %}
        <div class="spot-card" onclick="focusSpot('{{ spot.景點 }}')">
            <h3>{{ spot.景點 }}</h3>
            <small>⭐{{ spot.評價 }} · {{ spot.分類 }}</small>
        </div>
        {% endfor %}
    </div>
    <div class="nav-panel">
        <div>起點: <span id="start-name">未設定</span></div>
        <div>終點: <span id="end-name">未設定</span></div>
        <a id="go-link" href="#" target="_blank" class="btn-nav" style="display:none;">Google 導航</a>
    </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // 初始化地圖中心點
    var map = L.map('map').setView([35.0116, 135.7681], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var highlightLayer = L.layerGroup().addTo(map);
    var spotsData = {{ spots|tojson }};
    
    // 放置所有景點標記
    spotsData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度]).addTo(map);
        marker.bindTooltip(spot.景點);
        
        var popupContent = `
            <div style="min-width:140px">
                <b>${spot.景點}</b><br>
                <button onclick="setRoute('start', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="margin-top:8px; width:100%;">設為起點</button>
                <button onclick="setRoute('end', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="margin-top:4px; width:100%;">設為終點</button>
            </div>
        `;
        marker.bindPopup(popupContent);
        allMarkers[spot.景點] = marker;
    });

    var startPoint = null, endPoint = null;
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
            L.circle([target.緯度, target.經度], {radius: 500, color: 'red', fillOpacity: 0.1}).addTo(highlightLayer);
            allMarkers[spotName].openPopup();
        }
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    spots = get_spots()
    return render_template_string(HTML_TEMPLATE, spots=spots)

if __name__ == '__main__':
    # Render 部署需要的設定
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
