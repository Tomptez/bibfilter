let originalFilter = {"search":"","title":"","author":"", "content":"", "timestart": "", "until": "", "type": "all","sortby":"authorlast","sortorder":"asc"};

function showHideRow(row) { 
 
    $('.hidden_row').hide();

    $("#" + row).toggle(); 
} 

async function CreateTableFromJSON(data) {
    console.log("Start CreateTableFromJSON()")

    // Lemmatize content searchterms which is needed for measuring relevance
    
    termlist = await lemma(JSON.stringify(currentFilter));
    
    console.log(termlist)

    // EXTRACT VALUE FOR HTML HEADER. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    let col = [];
    colname = {"title": "Title", "authorlast": "Author", "year": "Year", "url": "URL", "publication": "Publication", "importantWordsCount":"Occur", "ID": "Delete", "icon": ""}
    for (let i = 0; i < data.length; i++) {
        for (let key in data[i]) {
            if (col.indexOf(key) === -1) {
                col.push(key);
            }
        }
    }

    // CREATE DYNAMIC TABLE.
    const table = document.createElement("table");
    const tbody = document.createElement("tbody")
    const colgroup = document.createElement("colgroup")

    // create cols with width
    for (let i = 0; i < col.length; i++){
        const newcol = document.createElement("col")
        newcol.id = col[i]
        colgroup.appendChild(newcol)
    }

    // CREATE HTML TABLE HEADER ROW USING THE EXTRACTED HEADERS ABOVE.

    let tr = tbody.insertRow(-1);                   // tbody ROW.
    tr.className = "tr"
    tr.classList.add("articlerow")                  // add class for css

    for (let i = 0; i < col.length; i++) {

        // skip abstract data
        if (col[i] == "abstract") {
            continue;
        }
        const th = document.createElement("th");      // tbody HEADER.
        let titleprefix = ""                        // prefix for the title arrows

        // mark which column its sorted by
        if (col[i] == currentFilter["sortby"] & currentFilter["sortorder"] == "asc"){
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
        tr.onclick = function() { showHideRow('hidden_row'+i)};

        let hiddenContent = "";

        // Loop through each cell
        for (let j = 0; j < col.length; j++) {
            let tabCell = tr.insertCell(-1);

            // create a button for the external URL
            if (col[j] == "url"){
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

            // How relevant is the result based on the content search
            else if (col[j] == "importantWordsCount"){
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
                tabCell.innerHTML = data[i][col[j]];
            }
        }
        

        tr = tbody.insertRow(-1);
        tr.id = "hidden_row" + i;
        tr.className = "hidden_row";
        let hiddenCell = tr.insertCell(-1);

        var div = document.createElement("div");
        div.className = "hidden_content"
        div.innerText = hiddenContent
        hiddenCell.appendChild(div)
        hiddenCell.colSpan = 6;

        
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

// load setUpFilter() and get the articles when loading the page after importing all Javascript functions
window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter));
    setUpFilter();
}