// Application variables
const grade_class_map = {
    'A': 'list-group-item-success',
    'B': 'list-group-item-info',
    'C': 'list-group-item-warning',
    'E': 'list-group-item-danger'
};

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
    output = ''
    for (chapter_idx in guideline_data) {
        chapter = guideline_data[chapter_idx];

        // Building current ID
        current_id = constructID(chapter.chapter_number, chapter.chapter_title);

        // Open 'card' div
        output += '<div class="card">';

        // Adding card header
        output += buildCardHeader(current_id, chapter.chapter_number, chapter.chapter_title, 'btn-outline-info');

        // Adding card body
        output += buildCardBody(current_id, chapter.recommendation_groups);

        // Close 'card' div
        output += '</div>';
    }
    console.log(output);
    // Appending to view
    $('#accordion').append(output);
}

const buildCardHeader = function (current_id, chapter_number, chapter_name, btn_type) {
    output = '';

    // Open card header div
    output += '<div class="card-header" id="' + current_id + 'title">';

    // Open button tag
    output += '<button class="btn ' + btn_type + ' container-fluid" data-toggle="collapse" data-target="#' + current_id + '" aria-expanded="true" aria-controls="' + current_id + '">';
    // Adding button text
    output += replaceSpecial(chapter_number + '. ' + chapter_name);
    // Closing button tag
    output += '</button>'

    // Close card header div
    output += '</div>';

    return output
}

const buildCardBody = function (current_id, recommendation_groups) {
    output = '';

    // Open collapse div
    output += '<div class="collapse" id="' + current_id + '" aria-labelledby="' + current_id + 'title" data-parent="#accordion">';

    // Opne card body div
    output += '<div class="card-body">';

    for (group_idx in recommendation_groups) {
        current_group = recommendation_groups[group_idx];
        // add title
        output += '<h6>' + current_group.title + '</h6>';
        // start list
        output += '<ul class="list-group">';

        // Iterate through recommendations, add each one
        for (rec_idx in current_group.recommendations) {
            recommendation = current_group.recommendations[rec_idx];
            output += '<li class="list-group-item ' + grade_class_map[recommendation.grade] + '">';
            output += '<span class="badge badge-primary badge-pill">' + recommendation.grade + '</span> ' + replaceSpecial(recommendation.content);
            output += '</li>';
        }

        // close list tag
        output += '</ul>';

        output += '<br>'
    }

    // Close card body div
    output += '</div>';

    // Close collapse div
    output += '</div>';

    return output;
}
const constructID = function (chapter_number, chapter_name) {
    return 'no' + chapter_number + 'title' + chapter_name.replace(/\s+/g, '');
}

const replaceSpecial = function (text) {
    return text.replace(/&/g, "&amp;").replace(/>/g, "&gt;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

// Get guidelines from server 
guideline_get = $.get('ADA2018Guidelines.json', function (response) {
    const full_guidelines = response
    populateGuidelineView(full_guidelines)
});
