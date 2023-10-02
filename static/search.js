function ajaxSearch(searchTerm) {
    $.ajax({
        url: `/chart-data?ticker=${searchTerm}`,
        dataType: 'json',
        success: function (data) {
            if (data.length === 0) {
                // Handle case when data is empty
            } else {
                render_chart(data);
            }
        },
        error: function (error) {
            console.log(error);
        }
    });
}

// on site load
const defaultTicker = "SPY"
$(function () {
    ajaxSearch(defaultTicker)
});

$(function () {
    const $searchInput = $("#search-input");

    $searchInput.on('keydown', function (event) {
        const searchTerm = $searchInput.val().trim();
        if (event.key === 'Enter') {
            ajaxSearch(searchTerm);
        }
    });

    function ajaxAutocomplete() {
        $.ajax({
            url: `/autocomplete`,
            dataType: 'json',
            success: function (data) {
                var autocomplete_members = data.members;
                $searchInput.autocomplete({
                    // source: autocomplete_members,
                    source: function (request, response) {
                        var results = $.ui.autocomplete.filter(autocomplete_members, request.term);

                        var term = $.ui.autocomplete.escapeRegex(request.term);
                        var matcher1 = new RegExp("^" + term, "i");
                        var matcher2 = new RegExp("^.+" + term, "i");

                        function subarray(matcher) {
                            return $.grep(results, function (item) {
                                return matcher.test(item);
                            });
                        }

                        results = $.merge(subarray(matcher1), subarray(matcher2));
                        response(results.slice(0, 8));
                    }
                });
            },
            error: function (error) {
                console.log(error);
            }
        });
    }

    ajaxAutocomplete();
});

