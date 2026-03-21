import pandas as pd
from flask import Flask, render_template_string
import os
import webbrowser
from threading import Timer

app = Flask(__name__)

# --- 設定區 ---
# 請確保此路徑正確指向你的 CSV 檔案
CSV_PATH = r'F:\Python\data\旅遊景點.csv' 

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

# --- 完整 HTML/CSS/JS 模板 ---
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Japan Travel Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft JhengHei", sans-serif; overflow: hidden; }
        
        /* 側邊欄樣式 */
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
        #sidebar.hidden { transform: translateX(-320px); margin-right: -320px; }

        /* 選單頂部：恢復深色配色 */
        #header { 
            padding: 15px; 
            background: #2c3e50; 
            color: white; 
            display: flex;
            align-items: center;
            flex-shrink: 0;
        }

        /* 統一圖示樣式：三條橫線 */
        .hamburger-icon {
            width: 18px; height: 2px; background: #5f6368; position: relative; display: inline-block;
        }
        .hamburger-icon::before, .hamburger-icon::after {
            content: ""; width: 18px; height: 2px; background: #5f6368; position: absolute; left: 0;
        }
        .hamburger-icon::before { top: -6px; }
        .hamburger-icon::after { top: 6px; }

        /* 選單內的按鈕：白色橫線 */
        #toggle-in {
            background: none; border: none; cursor: pointer; padding: 0; margin-right: 15px;
            display: flex; align-items: center; justify-content: center;
        }
        #toggle-in .hamburger-icon, 
        #toggle-in .hamburger-icon::before, 
        #toggle-in .hamburger-icon::after {
            background: white;
        }

        /* 景點列表區 */
        #spot-list { overflow-y: auto; flex-grow: 1; }
        .spot-card { padding: 16px; border-bottom: 1px solid #f1f1f1; cursor: pointer; }
        .spot-card:hover { background: #f8f9fa; }
        .spot-card h3 { margin: 0 0 4px 0; font-size: 15px; color: #d35400; }
        .spot-card div { font-size: 12px; color: #70757a; }
        
        #map { flex-grow: 1; height: 100%; position: relative; z-index: 1; }

        /* 地圖上的展開按鈕：圓形白底 + 三條橫線 */
        #toggle-out {
            position: absolute; left: 12px; top: 85px; z-index: 1000;
            background: white; border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            border-radius: 50%; width: 45px; height: 45px; 
            cursor: pointer; display: none; 
            align-items: center; justify-content: center;
        }

        /* 導航面板 */
        .nav-panel { padding: 12px; background: #fff; border-top: 1px solid #eee; flex-shrink: 0; }
        .btn-nav { 
            background: #3498db; color: white; padding: 10px; 
            text-decoration: none; border-radius: 4px; display: block; 
            text-align: center; margin-top: 10px; font-size: 14px; font-weight: bold;
        }
    </style>
</head>
<body>

<div id="sidebar">
    <div id="header">
        <button id="toggle-in" onclick="toggleSidebar()">
            <div class="hamburger-icon"></div>
        </button>
        <span style="font-weight: bold; font-size: 16px;">京都景點 ({{ spots|length }})</span>
    </div>
    <div id="spot-list">
        {% for spot in spots %}
        <div class="spot-card" onclick="focusSpot('{{ spot.景點 }}')">
            <h3>{{ spot.景點 }}</h3>
            <div>評價：⭐{{ spot.評價 }}</div>
        </div>
        {% endfor %}
    </div>
    <div class="nav-panel">
        <div id="route-display" style="font-size:12px; color:#5f6368; display: none; margin-bottom:5px;">
            <b style="color:#2980b9">起點 A:</b> <span id="start-name"></span><br>
            <b style="color:#c0392b">終點 B:</b> <span id="end-name"></span>
        </div>
        <a id="go-link" href="#" target="_blank" class="btn-nav" style="display:none;">使用 Google 規劃路線</a>
    </div>
</div>

<div id="map">
    <button id="toggle-out" onclick="toggleSidebar()">
        <div class="hamburger-icon"></div>
    </button>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map').setView([35.0116, 135.7681], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var highlightLayer = L.layerGroup().addTo(map);
    var spotsData = {{ spots|tojson }};
    
    function toggleSidebar() {
        var sb = document.getElementById('sidebar');
        var btnOut = document.getElementById('toggle-out');
        if (sb.classList.contains('hidden')) {
            sb.classList.remove('hidden');
            btnOut.style.display = 'none';
        } else {
            sb.classList.add('hidden');
            btnOut.style.display = 'flex';
        }
        // 側邊欄動畫結束後刷新地圖大小
        setTimeout(() => { map.invalidateSize(); }, 350);
    }

    // 放置標記
    spotsData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度]).addTo(map);
        var popupContent = `
            <div style="width:150px">
                <h4 style="margin:0 0 8px 0">${spot.景點}</h4>
                <button onclick="setRoute('start', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="width:100%; cursor:pointer;">設為起點 A</button>
                <button onclick="setRoute('end', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="width:100%; margin-top:5px; cursor:pointer;">設為終點 B</button>
            </div>`;
        marker.bindPopup(popupContent);
        allMarkers[spot.景點] = marker;
    });

    // 路線規劃邏輯
    var startPoint = null, endPoint = null;
    function setRoute(type, name, lat, lon) {
        if (type === 'start') {
            startPoint = { name: name, pos: lat + ',' + lon };
            document.getElementById('start-name').innerText = name;
        } else {
            endPoint = { name: name, pos: lat + ',' + lon };
            document.getElementById('end-name').innerText = name;
        }
        
        if (startPoint || endPoint) {
            document.getElementById('route-display').style.display = 'block';
        }
        
        if (startPoint && endPoint) {
            var url = `https://www.google.com/maps/dir/${startPoint.pos}/${endPoint.pos}/`;
            document.getElementById('go-link').href = url;
            document.getElementById('go-link').style.display = 'block';
        }
    }

    // 點擊列表後聚焦景點
    function focusSpot(spotName) {
        var target = spotsData.find(s => s.景點 === spotName);
        if (target) {
            highlightLayer.clearLayers();
            map.flyTo([target.緯度, target.經度], 17);
            L.circle([target.緯度, target.經度], {
                radius: 100, color: '#e74c3c', weight: 2, fillOpacity: 0.2
            }).addTo(highlightLayer);
            allMarkers[spotName].openPopup();
        }
    }
</script>
</body>
</html>
"""

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    # 延遲 1 秒自動開啟瀏覽器
    Timer(1.0, open_browser).start()
    app.run(port=5000, debug=False)
