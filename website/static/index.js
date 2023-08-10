
function searchByName() {
    $('#main_screen').hide();
    $('#all_fish_info').show();
    $('#all_location_info').hide();
}

function searchByLocation() {
    $('#main_screen').hide();
    $('#all_fish_info').hide();
    $('#all_location_info').show();
}

function getFishInfo(fish_name, index) {
    $('.btn-outline-primary').removeClass('active');
    $('#show_fish_' + index).addClass('active');
    $.ajax({
        url: '/api/get_fish_info?fish_name=' + fish_name,
        type: 'GET',
        success: function(response) {
            $('#fish_info').html(response);
            $('#fish_info').show();
        },
    })
}

function getLocationInfo(location_name, index) {
    $('.btn-outline-primary').removeClass('active');
    $('#show_location_' + index).addClass('active');
    $.ajax({
        url: '/api/get_location_info?location_name=' + location_name,
        type: 'GET',
        success: function(response) {
            $('#location_info').html(response);
            $('#location_info').show();
        },
    })
}