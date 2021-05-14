function showHideRow(row) { 
 
    $('.hidden_row').hide();

    $("#" + row).toggle(); 
}

// This function takes the hidden cells (marked with class hiddenRowContent) and puts them in a 
// hidden row below that can be toggled via showHideRow()

function insertHiddenRows() {
    var table = document.getElementById("literature");
    rows = table.rows;
    
    // let is needed otherswise the onclick function doesn't work properly
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].className == "clickable"){
            console.log(i-1)
            rows[i].onclick = function() { showHideRow('hidden_row'+i)};
            // rows[i].onclick = function(j) { return function() {showHideRow('hidden_row'+j); }; }(i);
        }
    }

    li = document.getElementsByClassName("hiddenRowContent")
    // Reverse order to not run into problems when trying to insert at the right place
    for (let i=li.length; i > 1; i--){
        if (li[i-1].innerHTML != ""){
            var row = table.insertRow(i);
            row.id = "hidden_row" + String((i-1));
            row.className = "hidden_row";
            var cell = row.insertCell(0);
            cell.innerHTML = li[i-1].innerHTML;
            cell.colSpan = 6;
        }
    }
}

window.onload = function(){
    insertHiddenRows();
}