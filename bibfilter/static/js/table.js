let originalFilter = {"search":"","title":"","author":"", "content":"", "timestart": "", "until": "", "type": "all","sortby":"authorlast","sortorder":"asc", "manualsort": false};
colname = {"title": "Title", "authorlast": "Author", "year": "Year", "url": "URL", "publication": "Publication", "importantWordsCount":"Occur", "icon": ""}


function showHideRow(row) { 
 
    $('.hidden_row').hide();

    $("#" + row).toggle(); 
}

function sortOccurences() {
    var table, rows, switching, i, x, y, shouldSwitch;
    table = document.getElementById("LitTable");
    
    // If table empty e.g. no search results, return immediately
    if (table == null){
        return
    }
    
    debugger;
    for (let col in colname){
        
        let cell = document.getElementById(col);
        cell.textContent = colname[col]
    }

    switching = true;
    /*Make a loop that will continue until
    no switching has been done:*/
    while (switching) {
        //start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        
        /*Loop through all table rows (except the
        first, which contains table headers):*/
        for (i = 1; i < (rows.length - 1); i+=2) {
            //start by saying there should be no switching:
            shouldSwitch = false;
            /*Get the two elements you want to compare,
            one from current row and one from the next:*/
            x = rows[i].getElementsByTagName("TD")[6];
            
            if (rows.length > i+2){
                // +2 instead of +1 due to hiddenrows
                y = rows[i + 2].getElementsByTagName("TD")[6];
            }
            else {
                break;
            }
            //check if the two rows should switch place:
            if (Number(x.innerHTML) < Number(y.innerHTML)) {
                //if so, mark as a switch and break the loop:
                shouldSwitch = true;
                break;
            }
        }
        
        if (shouldSwitch) {
            /*If a switch has been marked, make the switch
            and mark that a switch has been done:*/
            rows[i].parentNode.insertBefore(rows[i + 2], rows[i]);

            // This line is needed to move the hidden rows as well
            rows[i+1].parentNode.insertBefore(rows[i + 3], rows[i+1]);
            switching = true;
        }
    }
}

async function CreateTableFromJSON(data) {
    console.log("Start CreateTableFromJSON()")

    // Lemmatize content searchterms which is needed for measuring relevance
    
    termlist = await lemma(JSON.stringify(currentFilter));
    termlist = termlist["terms"]

    console.log(termlist)

    // EXTRACT VALUE FOR HTML HEADER. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    let col = [];
    for (let i = 0; i < data.length; i++) {
        for (let key in data[i]) {
            if (col.indexOf(key) === -1) {
                col.push(key);
            }
        }
    }

    // CREATE DYNAMIC TABLE.
    const table = document.createElement("table");
    table.id = "LitTable"
    const tbody = document.createElement("tbody")
    const colgroup = document.createElement("colgroup")

    // create cols with width
    for (let i = 0; i < col.length; i++){
        const newcol = document.createElement("col")
        newcol.id = "col_" + col[i]
        colgroup.appendChild(newcol)
    }

    // CREATE HTML TABLE HEADER ROW USING THE EXTRACTED HEADERS ABOVE.

    let tr = tbody.insertRow(-1);                   // tbody ROW.
    tr.className = "tr"
    tr.id = "tablehead"                  // add id for css

    for (let i = 0; i < col.length; i++) {

        // skip abstract data
        if (col[i] == "abstract" || col[i] == "importantWordsLocation") {
            continue;
        }
        const th = document.createElement("th");      // tbody HEADER.
        let titleprefix = ""                        // prefix for the title arrows

        // mark which column its sorted by
        if (col[i] == currentFilter["sortby"] && currentFilter["sortorder"] == "asc"){
            titleprefix = "\u2193"
        }
        else if (col[i] == currentFilter["sortby"] && currentFilter["sortorder"] == "desc"){
            titleprefix = "\u2191"
        }
        
        const a = document.createElement('a');
        const linkText = document.createTextNode(titleprefix+colname[col[i]]);
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
    // loop through each article / row
    for (let i = 0; i < data.length; i++) {

        tr = tbody.insertRow(-1);

        let hiddenContent = "";

        // Loop through each cell
        for (let j = 0; j < col.length; j++) {
            

            // create a button for the external URL
            if (col[j] == "url"){
                let tabCell = tr.insertCell(-1);
                if (data[i][col[j]] != "NaN"){
                    const a = document.createElement('a');
                    a.classList.add("externalUrl")
                    a.rel = "noopener noreferrer"
                    a.target = "_blank"
                    a.href = data[i][col[j]];
                    const linkText = document.createTextNode("Source");
                    a.appendChild(linkText);
                    tabCell.appendChild(a);
                };
            }

            // create icons
            else if (col[j] == "icon"){
                let tabCell = tr.insertCell(-1);
                let imgpath = "";
                if (data[i][col[j]] == "book"){
                    imgpath = base_url+"/static/img/book.png";
                }
                else if (data[i][col[j]] == "article"){
                    imgpath = base_url+"/static/img/article.png";
                }
                else {
                    imgpath = base_url+"/static/img/other.png";
                }
                const img = document.createElement('img');
                img.src = imgpath;
                img.classList.add("typeicon");
                tabCell.appendChild(img);
            }

            // handle abstract to put it in hidden row
            else if (col[j] == "abstract"){
                hiddenContent = data[i][col[j]];
            }

            // Get quotes of the articles where the searchterm is used.
            else if (col[j] == "importantWordsLocation"){
                // termlist has been lemmatized before
                if (currentFilter["content"] != ""){
                    hiddenContent = hiddenContent + "<br><br><b>Search Results:</b><br>" + data[i][col[j]][termlist[0]];
                }
            }

            // How relevant is the result based on the content search
            else if (col[j] == "importantWordsCount"){
                let tabCell = tr.insertCell(-1);
                relevance = 0

                if (currentFilter["content"] != ""){
                    // termlist has been lemmatized before
                    for (let term in termlist) {
                        relevance = relevance + data[i][col[j]][termlist[term]]
                    }
                }    
                tabCell.innerHTML = relevance;
            }

            // append json content into cell
            else {
                let tabCell = tr.insertCell(-1);
                tabCell.innerHTML = data[i][col[j]];
            }
        }
        
        // Show more information for items if hidden Content is available
        if (hiddenContent != ""){
            tr.onclick = function() { showHideRow('hidden_row'+i)};
            tr.classList.add("clickable");
        }

        tr = tbody.insertRow(-1);
        tr.id = "hidden_row" + i;
        tr.className = "hidden_row";

        // handle empty 
        if (hiddenContent == ""){
            tr.classList.add("hidden_row_empty");
        }
        let tabCell = tr.insertCell(-1);

        var div = document.createElement("div");
        div.className = "hidden_content"
        div.innerHTML = "<b> Abstract </b><br>" + hiddenContent
        tabCell.appendChild(div)
        tabCell.colSpan = 7;

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

    if (currentFilter["content"] != "" && currentFilter["manualsort"] == false) {
        sortOccurences();
    }
    
}

// load setUpFilter() and get the articles when loading the page after importing all Javascript functions
window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter));
    setUpFilter();
}