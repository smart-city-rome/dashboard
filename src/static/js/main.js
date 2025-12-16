const STYLE_URL = 'https://tiles.openfreemap.org/styles/bright';

const map = new maplibregl.Map({
  container: 'map',
  style: STYLE_URL,
  center: [12.4964, 41.9028], // Rome
  zoom: 14,
  bearing: 0,
  pitch: 0,
  attributionControl: false,
  pitchWithRotate: false
});

map.addControl(new maplibregl.AttributionControl(), 'bottom-right');
map.addControl(new maplibregl.NavigationControl(), 'top-right');

map.on('load', () => {
    map.addSource('tracklets', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        }
    });

    map.addLayer({
        id: 'tracklets-layer',
        type: 'circle',
        source: 'tracklets',
        paint: {
            'circle-radius': 7,
            'circle-color': [
                'match',
                ['get', 'class'],
                'person', '#00FF00',
                'car', '#0000FF',
                'bus', '#FFFF00',
                'truck', '#00FFFF',
                'motorcycle', '#FF00FF',
                'bicycle', '#008080',
                'traffic light', '#FFC0CB',
                'stop sign', '#FFA07A',
                '#000000' // default
            ],
            'circle-stroke-width': 3,
            'circle-stroke-color': [
               'interpolate',
               ['linear'],
               ['get', 'speed'],
               0, 'rgb(180, 0, 0)',
               10, 'rgb(255, 255, 0)',
               30, 'rgb(0, 180, 0)'
            ],
            'circle-opacity': 0.8,
            'circle-stroke-opacity': 1
        }
    });

    // State for animation
    const trackletState = {}; 
    const ANIMATION_DURATION = 500; // ms

    function lerp(start, end, t) {
        return start * (1 - t) + end * t;
    }

    // Animation Loop
    function animateTracklets() {
        const now = performance.now();
        const features = [];
        const activeIds = new Set();

        Object.keys(trackletState).forEach(id => {
            const track = trackletState[id];
            
            // Calculate progress (0 to 1)
            let progress = (now - track.startTime) / ANIMATION_DURATION;
            if (progress > 1) progress = 1;

            // Interpolate position
            const currentLon = lerp(track.startLon, track.targetLon, progress);
            const currentLat = lerp(track.startLat, track.targetLat, progress);

            // Update current estimated position for next start point
            track.currentLon = currentLon;
            track.currentLat = currentLat;

            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [currentLon, currentLat]
                },
                properties: track.properties
            });
            
            activeIds.add(id);
        });

        if (map.getSource('tracklets')) {
            map.getSource('tracklets').setData({
                type: 'FeatureCollection',
                features: features
            });
        }
        
        requestAnimationFrame(animateTracklets);
    }
    
    // Start loop
    requestAnimationFrame(animateTracklets);

    // Stream Management
    let currentEventSource = null;

    function connectToStream(topic) {
        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
            // Clear current tracklets immediately
            Object.keys(trackletState).forEach(key => delete trackletState[key]);
        }
        
        // If no topic passed (or explicit null), we just stop
        if (!topic) {
             console.log("Stream disconnected.");
             return;
        }

        let url = '/api/stream';
        url += `?topic=${encodeURIComponent(topic)}`;

        if (!!window.EventSource) {
            console.log(`Connecting to stream: ${url}`);
            const source = new EventSource(url);
            currentEventSource = source;

            source.onmessage = function(event) {
                try {
                    if (event.data.trim().startsWith('{')) {
                         const data = JSON.parse(event.data);
                         const receivedIds = new Set();
                         const now = performance.now();

                         data.features.forEach(f => {
                             const id = f.properties.id;
                             const lon = f.geometry.coordinates[0];
                             const lat = f.geometry.coordinates[1];
                             receivedIds.add(id);

                             if (trackletState[id]) {
                                 trackletState[id].startLon = trackletState[id].currentLon;
                                 trackletState[id].startLat = trackletState[id].currentLat;
                                 trackletState[id].targetLon = lon;
                                 trackletState[id].targetLat = lat;
                                 trackletState[id].startTime = now;
                                 trackletState[id].properties = f.properties; 
                             } else {
                                 trackletState[id] = {
                                     startLon: lon, startLat: lat,
                                     targetLon: lon, targetLat: lat,
                                     currentLon: lon, currentLat: lat,
                                     startTime: now,
                                     properties: f.properties
                                 };
                             }
                         });
                         Object.keys(trackletState).forEach(id => {
                             if (!receivedIds.has(id)) { delete trackletState[id]; }
                         });
                    }
                } catch(e) { console.error("Error parsing GeoJSON payload", e); }
            };
            source.onerror = function(err) { console.error("EventSource failed:", err); };
        } else {
            console.error("Server-Sent Events not supported.");
        }
    }

    // Map Interaction State
    let selectedMarkerElement = null;

    function lockMapInteraction() {
        const handlers = ['scrollZoom', 'boxZoom', 'dragRotate', 'dragPan', 'keyboard', 'doubleClickZoom', 'touchZoomRotate'];
        handlers.forEach(h => map[h].disable());
    }

    function unlockMapInteraction() {
        const handlers = ['scrollZoom', 'boxZoom', 'dragRotate', 'dragPan', 'keyboard', 'doubleClickZoom', 'touchZoomRotate'];
        handlers.forEach(h => map[h].enable());
    }

    // Load Crossroads
    fetch('/api/crossroads')
        .then(response => response.json())
        .then(crossroads => {
            crossroads.forEach(crossroad => {
                const el = document.createElement('div');
                el.className = 'marker';
                el.style.backgroundImage = 'url(https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png)';
                el.style.width = '25px';
                el.style.height = '41px';
                el.style.backgroundSize = '100%';
                el.style.cursor = 'pointer'; 
                el.style.pointerEvents = 'auto';

                const marker = new maplibregl.Marker({ element: el })
                    .setLngLat([crossroad.lon, crossroad.lat])
                    .addTo(map);
                
                el.addEventListener('click', (e) => {
                    e.stopPropagation();
                   
                    if (selectedMarkerElement) {
                        selectedMarkerElement.style.visibility = 'visible';
                    }
                   
                    if (crossroad.bbox) {
                        map.fitBounds(crossroad.bbox, {
                            padding: 100,
                            maxZoom: 21,
                            duration: 1500
                        });
                   } else {
                        const zoomLevel = crossroad.zoom || 18;
                        map.flyTo({
                            center: [crossroad.lon, crossroad.lat],
                            zoom: zoomLevel
                        });
                   }

                    lockMapInteraction();

                    selectedMarkerElement = el;
                    el.style.visibility = 'hidden';
                    
                    connectToStream(crossroad.topic);
                    window.dispatchEvent(new CustomEvent('crossroad-selected', { detail: crossroad }));
                });
            });
            
            connectToStream(null); 
        })
        .catch(err => console.error("Failed to load crossroads", err));

    window.addEventListener('map-selection-cleared', () => {
        unlockMapInteraction();
        if (selectedMarkerElement) {
            selectedMarkerElement.style.visibility = 'visible';
            selectedMarkerElement = null;
        }
        connectToStream(null);
        map.flyTo({ zoom: 14 });
    });
});
