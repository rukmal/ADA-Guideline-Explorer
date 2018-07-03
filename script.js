const search = function () {
    // Getting search term
    let searchTerm = $('#search-input').val();

    // Get concatenated data with only search text
    searchData = getSearchData(searchTerm);
}

const getSearchData = function () {
    // Return modified JSON, with only data that shows up in search terms
}

const populateGuidelineView = function (guideline_data) {
    // Populate page with guideline data
}


// Get guidelines from server 
guideline_get = $.get('ADA2018Guidelines.json', function (response) {
    const full_guidelines = response
    console.log(full_guidelines)
});
