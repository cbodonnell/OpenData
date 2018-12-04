// map.js

mapboxgl.accessToken = mapbox_access_key;

var map = new mapboxgl.Map({
    container: map_container, // container id
    style: map_style, // stylesheet location
    center: map_center, // starting position [lng, lat]
    zoom: map_zoom, // starting zoom
    preserveDrawingBuffer: true
});

map.on("load", function() {
    add_sources();
    generate_layers();
//    generate_thumbnail();
});

var add_sources = function() {
    for(var i = 0; i < sources.length; i++) {
        var source = sources[i];

        if (map.getSource(source["name"])){
            map.removeSource(source["name"]);
        }

        map.addSource(source["name"], {
            "type": source["data"]["type"],
            "data": source["data"]["file"]
        });
    }
}

var generate_layers = function() {
    for(var i = 0; i < layers.length; i++) {
        var layer = layers[i];

        if (map.getLayer(layer["id"])){
            map.removeLayer(layer["id"]);
        }

        map.addLayer({
            'id': layer["id"],
            'type': layer["type"],
            'source': layer["source"],
            'source-layer': layer["source-layer"],
            'layout': layer["layout"],
            'paint': layer["paint"]
        });

        if (layer["popup"] !== null) {
            // TODO: Don't allow "{};" into popup fields
            map.on('click', layer["id"], function (e) {
                // loop through layers and check if clicked
                for(var i = 0; i < layers.length; i++) {
                    var layer = layers[i];

                    if (e.features[0]["layer"]["id"] == layer["id"]) {
                        var varRegExp = /{(.*?)}/;

                        // TODO: Can this be more programmatic?
                        // get popup title
                        var titleRegExec = varRegExp.exec(layer["popup"]["title"]);
                        if (titleRegExec !== null) {
                            var title = titleRegExec["input"]
                                .replace(titleRegExec[0],e.features[0]["properties"][titleRegExec[1]]);
                        } else {
                            var title = layer["popup"]["title"];
                        }
                        var titleHTML = "<h5 class='popup-title'>" + title + "</h5>";

                        // get popup subtitle
                        var subtitleRegExec = varRegExp.exec(layer["popup"]["subtitle"]);
                        if (subtitleRegExec !== null) {
                            var subtitle = subtitleRegExec["input"]
                                .replace(subtitleRegExec[0],e.features[0]["properties"][subtitleRegExec[1]]);
                        } else {
                            var subtitle = layer["popup"]["subtitle"];
                        }
                        var subtitleHTML = "<p class='popup-subtitle' style='margin: 0 0 5px 0;'>" + subtitle + "</p>";

                        // get properties
                        var properties = layer["popup"]["properties"].split(";")
                        var propertiesHTML = "";
                        for(var i = 0; i < properties.length; i++) {
                            var property = properties[i];
                            var propertyRegExec = varRegExp.exec(property);
                            if (propertyRegExec !== null) {
                                property = propertyRegExec["input"]
                                    .replace(propertyRegExec[0],e.features[0]["properties"][propertyRegExec[1]]);
                            } else {
                                // property remains unchanged
                            }
                            propertiesHTML += "<p class='popup-property' style='margin: 0;'>" + property + "</p>"
                        }

                        new mapboxgl.Popup()
                            .setLngLat(e.lngLat)
                            .setHTML(titleHTML + subtitleHTML + propertiesHTML)
                            .addTo(map);
                    }
                }
            });

            map.on('mouseenter', layer["id"], function () {
                map.getCanvas().style.cursor = 'pointer';
            });

            map.on('mouseleave', layer["id"], function () {
                map.getCanvas().style.cursor = '';
            });
        }
    }
}

// This is not used
var generate_thumbnail = function () {
    var data = map.getCanvas().toDataURL();
    $.post( "/" + map_id + "/generate_thumbnail", {
        javascript_data: data
    });
}
