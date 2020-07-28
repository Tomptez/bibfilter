var currentFilter = originalFilter;

// set the base url so the app knows which page to call independent whether we're in development or production
var base_url = window.location.origin;

if (window.location.pathname == "/admin") {
    var articles_url = "/articles_admin"
}
else {
    var articles_url = "/articles"
}

// Function to get articles as JSON from the flask API
async function getFilteredLiterature(input_json){
    fetch(base_url+articles_url, {
            method: 'POST',
            body: input_json, // string or object
            headers: {
                'Content-Type': 'application/json'
            }
            }).then(function (response) {
                return response.json();
            }).then(function (response_json){
                document.getElementById("result_count").textContent = Object.keys(response_json).length;
                CreateTableFromJSON(response_json);
            }).catch(function (error){
                console.error(error);
                var divContainer = document.getElementById("showData");
                divContainer.innerHTML = '<p style="font-style: italic;"> A Network Error occured. Please contact the Website administrator or try again later.</p>';
            });
}

// Function to download the .bib file as plain text from the flask API
async function downloadBib(){
    var json = JSON.stringify(currentFilter)
    fetch(base_url+'/bibfile', {
            method: 'POST',
            body: json, // string or object
            headers: {
                'Content-Type': 'application/json'
            }
            }).then(function (response) {
                return response.blob();
            }).then(function (blob){
                download(blob, "bibliography.bib", "text/plain");
            }).catch(function (error){
                console.error(error);
            });
}

// Function to sort each column in the table
function updateSort(filter,column){
    console.log("updateSort()")
    oldsortorder = filter["sortorder"]
    oldcolumn = filter["sortby"]
    filter["sortby"] = column
    if (oldcolumn == column && filter["sortorder"] == "asc"){
        filter["sortorder"] = "desc"
    }
    else {
        filter["sortorder"] = "asc"
    }
    return filter
}

// function to reset the entire base with the "filter" button in the sidebar
function resetPage() {
    console.log("resetPage()");
    document.getElementById("filterForm").reset();
    currentFilter = originalFilter;
    getFilteredLiterature(JSON.stringify(currentFilter))
}

// Function to set up the filter Form in the sidebar
function setUpFilter() {
    console.log("setUpFilter()");
    const filterForm = document.getElementById("filterForm");

    filterForm.addEventListener("submit", function (e){
        e.preventDefault();
        
        var x = document.getElementById('timestart').value;
        if (x.length != 4 && x.length != 0) {
            alert('please enter a year (YYYY)');
            return false;
        }
        var y = document.getElementById('until').value;
        if (y.length != 4 && y.length != 0) {
            alert('please enter a year (YYYY)');
            return false;
        }

        const formData = new FormData(this);

        // convert formdata to json
        var filter = currentFilter;
        formData.forEach(function(value, key){
            filter[key] = value;
        });
        currentFilter = filter
        console.log(currentFilter)
        var json = JSON.stringify(filter);
        getFilteredLiterature(json);
    });
}