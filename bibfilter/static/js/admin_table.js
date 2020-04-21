function CreateTableFromJSON(data) {
    console.log("Start CreateTableFromJSON()")
    
    // EXTRACT VALUE FOR HTML HEADER. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    var col = [];
    colname = {"title": "Title", "author": "Author", "year": "Year", "url": "URL", "journal": "Journal", "ID": "Delete", "_date_created_str": "Added"}
    for (var i = 0; i < data.length; i++) {
        for (var key in data[i]) {
            if (col.indexOf(key) === -1) {
                col.push(key);
            }
        }
    }

    // CREATE DYNAMIC TABLE.
    var table = document.createElement("table");
    var tbody = document.createElement("tbody")
    var colgroup = document.createElement("colgroup")

    // create cols with width
    for (var i = 0; i < col.length; i++){
        var newcol = document.createElement("col")
        newcol.id = col[i]
        colgroup.appendChild(newcol)
    }

    // CREATE HTML TABLE HEADER ROW USING THE EXTRACTED HEADERS ABOVE.

    var tr = tbody.insertRow(-1);                   // tbody ROW.
    tr.className = "tr"

    for (var i = 0; i < col.length; i++) {
        var th = document.createElement("th");      // tbody HEADER.
        var titleprefix = ""                        // prefix for the title

        // mark which column its sorted by
        if (col[i] == currentFilter["sortby"] & currentFilter["sortorder"] == "asc"){
            var titleprefix = "\u2193"
        }
        else if (col[i] == currentFilter["sortby"] && currentFilter["sortorder"] == "desc"){
            var titleprefix = "\u2191"
        }
        
        var a = document.createElement('a');
        var linkText = document.createTextNode(titleprefix+colname[col[i]]);
        a.href = "";
        a.id = col[i]
        a.onclick = function(){
            event.preventDefault();
            currentFilter = updateSort(currentFilter,this.id);
            getFilteredLiterature(JSON.stringify(currentFilter))};
        a.appendChild(linkText);
        th.appendChild(a);
        tr.appendChild(th); 
    }

    // ADD JSON DATA TO THE tbody AS ROWS.
    for (var i = 0; i < data.length; i++) {

        tr = tbody.insertRow(-1);

        for (var j = 0; j < col.length; j++) {
            var tabCell = tr.insertCell(-1);

            // different than main
            // create DELETE button 
            if (col[j] == "ID"){
                var a = document.createElement('a');
                a.classList.add("delete")
                a.href = base_url+"/delete/"+data[i][col[j]];
                var linkText = document.createTextNode("DELETE");
                a.appendChild(linkText);
                tabCell.appendChild(a);  
            }
            // create a button for the external URL
            else if (col[j] == "url"){
                if (data[i][col[j]] != "NaN"){
                    var a = document.createElement('a');
                    a.rel = "noopener noreferrer"
                    a.target = "_blank"
                    a.classList.add("externalUrl")
                    a.href = data[i][col[j]];
                    var linkText = document.createTextNode("Source");
                    a.appendChild(linkText);
                    tabCell.appendChild(a);
                };
            }

            // append json content into cell
            else {
                tabCell.innerHTML = data[i][col[j]];
            }
        }
        
    }

    // FINALLY ADD THE NEWLY CREATED tbody and table WITH JSON DATA TO A CONTAINER.
    var divContainer = document.getElementById("showData");
    if (data.length == 0) {
        divContainer.innerHTML = '<p style="font-style: italic;"> Unfortunately no literature met your criteria</p>';
    }
    else {
        divContainer.innerHTML = "";
        table.appendChild(colgroup)
        table.appendChild(tbody)
        divContainer.appendChild(table);
    }
    
}