/**
 * Created by marija on 13/05/17.
 */
var map;
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 43.858783,  lng: 16.417554},
        zoom: 7
    });
    putMussels()
}

function addMarker(lat, lng, musselId, active)
{
    if (active == 0) {
        var marker = new google.maps.Marker({
            position: {lat: lat, lng: lng},
            label: musselId,
            map: map,
            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
            });
    }
    else {
        var marker = new google.maps.Marker({
            position: {lat: lat, lng: lng},
            label: musselId,
            map: map,
            icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
        });
    }
    return musselId;
}


function putMussels() {
    var jmap;
    addMarker(44.989999, 14.555552, "5",0);
}
