/**
 * Created by marija on 13/05/17.
 */
var map;
var markers = [];

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 43.458783,  lng: 16.217554},
        zoom: 7
    });

}

//read cyclic mussels and update map


function deleteMarker(musselId) {
    markers[musselId].setMap(null);
    delete markers[musselId]
}


function addMarker(lat, lng, musselId, active)
{
    if (musselId in markers)
        deleteMarker(musselId)
    var marker;
    if (active == 0) {
        marker = new google.maps.Marker({
            position: {lat: lat, lng: lng},
            label: musselId,
            map: map,
            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
            });

    }
    else {
        marker = new google.maps.Marker({
            position: {lat: lat, lng: lng},
            label: musselId,
            map: map,
            icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
        });
    }
    google.maps.event.addListener(marker, 'click', function () {
        var selected = marker.label
        console.log(selected)
        //send id to python
    })
    markers[musselId] = marker;
    return musselId;
}

