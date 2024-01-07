$(document).ready(function () {

    $('input[type="radio"]').on('change', function () {
        const selectedOption = $('input[name="selectedAddress"]:checked').val();
        console.log(selectedOption);

        // Make a GET request with data as query parameters
        $.ajax({
            url: '/cart/selected_address/',
            method: 'GET',
            data: { selectedOption: selectedOption }, // Send data as query parameters
            dataType: 'json', // Specify the expected response data type
            success: function (response) {
                $('#username').val(response.username);
                $('#email').val(response.email);
                $('#phone').val(response.phone);
                $('#house_no').val(response.house_no);
                $('#street').val(response.street);
                $('#district').val(response.district);
                $('#state').val(response.state);
                $('#country').val(response.country);
                $('#pincode').val(response.pincode);


            },
            error: function (error) {
                console.error('Error:', error);
            }
        });
    });
})


