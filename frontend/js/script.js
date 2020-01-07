var currentFilter = {"title":"","author":"","sortby":"year","sortorder":"asc"}

async function getFilteredLiterature(input_json){

    fetch('http://127.0.0.1:5000/articles', {
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
            });
}

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

function resetPage() {
    document.getElementById("filterForm").reset();
    currentFilter = {"title":"","author":"","sortby":"year","sortorder":"asc"}
    getFilteredLiterature(JSON.stringify(currentFilter))
}
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
        var json = JSON.stringify(filter);
        getFilteredLiterature(json);
    });
}

function CreateTableFromJSON(data) {
    console.log("Start CreateTableFromJSON()")
    
    // EXTRACT VALUE FOR HTML HEADER. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    var col = [];
    for (var i = 0; i < data.length; i++) {
        for (var key in data[i]) {
            if (col.indexOf(key) === -1) {
                col.push(key);
            }
        }
    }

    // CREATE DYNAMIC TABLE.
    var table = document.createElement("table");

    // CREATE HTML TABLE HEADER ROW USING THE EXTRACTED HEADERS ABOVE.

    var tr = table.insertRow(-1);                   // TABLE ROW.
    tr.className = "table table-hover table-striped ht-tm-element"

    for (var i = 0; i < col.length; i++) {
        var th = document.createElement("th");      // TABLE HEADER.
        th.className = "table thead-dark sticky-top" 
        //th.innerHTML = 

        var a = document.createElement('a');
        var linkText = document.createTextNode(col[i]);
        a.appendChild(linkText);
        a.href = "";
        a.onclick = function(){
            event.preventDefault();
            currentFilter = updateSort(currentFilter,this.text);
            getFilteredLiterature(JSON.stringify(currentFilter))};
        th.appendChild(a);
        tr.appendChild(th); 
        
    }

    // ADD JSON DATA TO THE TABLE AS ROWS.
    for (var i = 0; i < data.length; i++) {

        tr = table.insertRow(-1);

        for (var j = 0; j < col.length; j++) {
            var tabCell = tr.insertCell(-1);
            tabCell.innerHTML = data[i][col[j]];
        }
    }

    // FINALLY ADD THE NEWLY CREATED TABLE WITH JSON DATA TO A CONTAINER.
    var divContainer = document.getElementById("showData");
    divContainer.innerHTML = "";
    divContainer.appendChild(table);
}

window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter))
    setUpFilter();
}