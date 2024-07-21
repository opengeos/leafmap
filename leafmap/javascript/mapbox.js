import mapboxgl from "https://esm.sh/mapbox-gl@3.5.2";

function render({ model, el }) {
    // Header
    let center = model.get("center");
    let zoom = model.get("zoom");
    let width = model.get("width");
    let height = model.get("height");
    let style = model.get("style");

    const div = document.createElement("div");
    div.style.width = width;
    div.style.height = height;

    let token = model.get("token");
    mapboxgl.accessToken = token;

    // Map content

    const map = new mapboxgl.Map({
        container: div,
        style: style,
        center: center,
        zoom: zoom,
    });

    map.on("click", function (e) {
        model.set("clicked_lnglat", [e.lngLat.lng, e.lngLat.lat]);
        model.save_changes();
    });

    map.on("moveend", function (e) {
        model.set("center", [map.getCenter().lng, map.getCenter().lat]);
        let bbox = map.getBounds();
        let bounds = [bbox._sw.lng, bbox._sw.lat, bbox._ne.lng, bbox._ne.lat];
        model.set("bounds", bounds);
        model.save_changes();
    });

    map.on("zoomend", function (e) {
        model.set("center", [map.getCenter().lng, map.getCenter().lat]);
        model.set("zoom", map.getZoom());
        let bbox = map.getBounds();
        let bounds = [bbox._sw.lng, bbox._sw.lat, bbox._ne.lng, bbox._ne.lat];
        model.set("bounds", bounds);
        model.save_changes();
    });

    // model.on("change:center", function () {
    //     let center = model.get("center");
    //     center.reverse();
    //     map.setCenter(center);
    // });

    // model.on("change:zoom", function () {
    //     let zoom = model.get("zoom");
    //     map.setZoom(zoom);
    // });

    // Footer
    el.appendChild(div);
}
export default { render };