function showHideRow(row) { 
    //$('.hidden_row').hide();
    $("#" + row).toggle(); 
}

// This function takes the hidden cells (marked with class hiddenRowContent) and puts them in a 
// hidden row below that can be toggled via showHideRow()

function insertHiddenRows() {
    var table = document.getElementById("literature");
    rows = table.rows;
    
    //  Make rows clickable to toggle hidden rows for abstract etc.
    // let is needed otherswise the onclick function doesn't work properly
    for (let i = 1; i < rows.length; i++) {
        $("#" + row).toggle(); 
        if (rows[i].className == "clickable"){
            rows[i].onclick = function() { 
                showHideRow('hidden_row'+i)};
            // rows[i].onclick = function(j) { return function() {showHideRow('hidden_row'+j); }; }(i);
        }
    }

    //  Create hidden rows
    li = document.getElementsByClassName("hiddenRowContent");
    // Reverse order to not run into problems when trying to insert at the right place
    for (let i=li.length; i > 1; i--){
        if (li[i-1].innerHTML != ""){
            var row = table.insertRow(i);
            row.id = "hidden_row" + String((i-1));
            row.className = "hidden_row";
            // Optional, first empty column width of the icon colum
            var cell = row.insertCell(0);
            cell.className = "hidden_left"
            var cell = row.insertCell(1);
            cell.innerHTML = li[i-1].innerHTML;
            cell.colSpan = 5;
        }
    }
}

window.onload = function(){
    insertHiddenRows()
}

// Creates the button to sort by relevance
// Old code, only here for reference
// function showButton(){
//     if (document.getElementById("relevanceButton") == null) {
//         var newButton = document.createElement("a");
//         // Version to delete the button afterwards
//         // newButton.setAttribute("onclick", "sortOccurences();this.parentNode.removeChild(this)");
//         newButton.setAttribute("onclick", "sortOccurences()");
//         newButton.setAttribute("id", "relevanceButton");
//         newButton.textContent = "Sort by Relevance";
//         newButton.classList.add("linkbutton");
//         var buttonDiv = document.getElementById("sortrelevance");
//         buttonDiv.appendChild(newButton);
//     }
// }