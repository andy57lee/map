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
        
        /* 側邊欄優化：增加滾動條與過渡動畫 */
        #sidebar { 
            width: 300px; 
            background: #fff; 
            border-right: 1px solid #ccc; 
            display: flex; 
            flex-direction: column; 
            transition: transform 0.3s ease;
            z-index: 1000;
            flex-shrink: 0;
        }
        
        /* 當隱藏時位移 */
        #sidebar.hidden { transform: translateX(-300px); margin-right: -300px; }

        #header { padding: 15px; background: #2c3e50; color: white; flex-shrink: 0; }
        
        /* 景點列表：允許獨立上下捲動 */
        #spot-list { 
            overflow-y: auto; 
            flex-grow: 1; 
            -webkit-overflow-scrolling: touch; /* 優化手機滑動流暢度 */
        }

        .spot-card { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; }
        .spot-card:hover { background: #f1f4f6; }
        .spot-card h3 { margin: 0; font-size: 16px; color: #d35400; }
        
        #map { flex-grow: 1; height: 100%; position: relative; }

        /* 收納按鈕設計 */
        #toggle-btn {
            position: absolute;
            left: 10px;
            top: 10px;
            z-index: 1100;
            background: white;
            border: 2px solid rgba(0,0,0,0.2);
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            font-weight: bold;
        }

        .nav-panel { padding: 10px; background: #ecf0f1; border-top: 1px solid #ccc; font-size: 13px; flex-shrink: 0; }
        .btn-nav { background: #3498db; color: white; padding: 8px; text-decoration: none; border-radius: 4px; display: block; text-align: center; margin-top: 5px; }
        
        /* 手機橫向微調 */
        @media (max-height: 450px) {
            #header { padding: 5px 15px; }
            #header h3 { font-size: 16px; margin: 5px 0; }
        }
    </style>
</head>
<body>

<div id="sidebar">
    <div id="header">
        <h3>京都景點規劃</h3>
        <small>點擊列表可捲動查看</small>
    </div>
    <div id="spot-list">
        {% for spot in spots %}
        <div class="spot-card" onclick="focusSpot('{{ spot.景點 }}')">
            <h3>{{ spot.景點 }}</h3>
            <small>{{ spot.城市 }} · ⭐{{ spot.評價 }}</small>
        </div>
        {% endfor %}
    </div>
    <div class="nav-panel" id="route-info">
        <span id="start-name">未設定起點</span> → <span id="end-name">未設定終點</span>
        <a id="go-link" href="#" target="_blank" class="btn-nav" style="display:none;">Google 導航</a>
    </div>
</div>

<div id="map">
    <button id="toggle-btn" onclick="toggleSidebar()">☰ 選單</button>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map').setView([35.0116, 135.7681], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var allMarkers = {};
    var highlightLayer = L.layerGroup().addTo(map);
    var spotsData = {{ spots|tojson }};
    
    // 側邊欄切換功能
    function toggleSidebar() {
        document.getElementById('sidebar').classList.toggle('hidden');
        setTimeout(() => { map.invalidateSize(); }, 300); // 重新計算地圖大小
    }

    spotsData.forEach(function(spot) {
        var marker = L.marker([spot.緯度, spot.經度]).addTo(map);
        marker.bindTooltip(spot.景點);
        
        var popupContent = `
            <div style="width:150px">
                <h4>${spot.景點}</h4>
                <button onclick="setRoute('start', '${spot.景點}', ${spot.緯度}, ${spot.經度})">設為起點</button>
                <button onclick="setRoute('end', '${spot.景點}', ${spot.緯度}, ${spot.經度})" style="margin-top:5px">設為終點</button>
            </div>`;
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
            L.circle([target.緯度, target.經度], {radius: 500, color: '#e74c3c', fillOpacity: 0.1}).addTo(highlightLayer);
            allMarkers[spotName].openPopup();
            
            // 行動裝置點選後自動縮回選單 (可選)
            if (window.innerWidth < 768) toggleSidebar();
        }
    }
</script>
</body>
</html>
"""
