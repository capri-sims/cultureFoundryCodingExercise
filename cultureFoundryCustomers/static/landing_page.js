$(function() {
    $.get('api/generate_guid', function(data) {
        document.cookie = "tracking_guid=" + data; 
    }); 
});