var Map = function Map( container ) {
    var parent = this;

    google.maps.visualRefresh = true;
    this.settings = {
        here: new google.maps.LatLng( 35.960162, -86.802699 ),
        api_key: 'AIzaSyBO7uBiTXNj8U1aDVQR5snr4XDd3xitHRE'
    }
    this.markers = [];
    this.map = this.init_map( container );

    this.nearby();

    return this;
}


Map.prototype.init_map = function( container ) {
    var map, parent;

    parent = this;

    map = new google.maps.Map(container, {
        center: this.settings.here,
        zoom: 13,
        mapTypeID: google.maps.MapTypeId.ROADMAP
    });

    google.maps.event.addDomListener(map, 'center_changed', function() {
        parent.nearby();
    });

    return map
}


Map.prototype.add_marker = function( name, lat, lon ) {
    var marker;

    marker = new google.maps.Marker({
        map: this.map,
        position: new google.maps.LatLng( lat, lon ),
        title: name
    });
    google.maps.event.addDomListener(marker, 'click', function() {
        var w;
        w = new google.maps.InfoWindow({
            content: name
        });
        w.open(this.map, this);
        google.maps.event.addDomListener(w, 'closeclick', function() {
            this.close();
        });
    }, false);
    this.markers.push( marker );
}


Map.prototype.nearby = function() {
    var here,
        map,
        B;

    map = this;
    here = this.map.getCenter();

    B = new BusinessCollection({
        lat: toFloat(here.lat()),
        lon: toFloat(here.lng())
    });
    B.get(function( businesses ) {
        var m,
            i;

        while ( m = map.markers.pop() ) {
            m.setMap( null );
        }
        for ( i = 0; i < businesses.length; i++ ) {
            businesses[i].get(function( b ) {
                this.add_marker( b.name, b.lat, b.lon );
            });
        }
    });
}
