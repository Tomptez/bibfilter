var originalFilter = {"title":"","author":"", "timestart": "", "until": "", "type": "all","sortby":"_date_created_str","sortorder":"desc"};

function setUpUpload() {
    // Select your input type file and store it in a variable
    const input = document.getElementById("fileinput");

    uploadForm.addEventListener("submit", function (e){
        e.preventDefault();

        var data = new FormData();
        data.append('file', input.files[0]);
        const uploadForm = document.getElementById("uploadForm");
        
        fetch(base_url+"/file-upload", {
            method: 'POST',
            body: data
            }).then(function (response) {
                return response.json();
            }).then(function (response_text){
                alert(response_text["message"]);
                window.location.href=base_url+"/admin";
            }).catch(function (error){
                console.error(error);
                alert("A Network Error occured. Please contact the Website administrator or try again later.")
            });
        });
}

// Function to add an article
async function deleteTimePeriod(from,until){
    fetch(base_url+"/deleteTimePeriod/"+from+"/"+until, {
            method: 'GET',
            }).then(function (response) {
                return response.text();
            }).then(function (response_text){
                alert("Deleted "+response_text+" Articles");
                window.location.href=base_url+"/admin";
            }).catch(function (error){
                console.error(error);
                alert("A Network Error occured. Please contact the Website administrator or try again later.")
            });
}

function timeDelete() {
    const deleteArticlesForm = document.getElementById("deleteArticlesForm");

    deleteArticlesForm.addEventListener("submit", function (e){
        e.preventDefault();

        var dateFrom = document.getElementById('dateFrom').value;
        var dateUntil = document.getElementById('dateUntil').value;

        if (dateFrom.length == 0 || dateUntil.length == 0) {
            alert('Please enter dates between which creation dates you want to delete all articles');
            return false;
        }

        var r = confirm("Do you reall want to delete all Articles that were added \n between (including) "+dateFrom+" and "+dateUntil+"?");
        if (r == true) {
            deleteTimePeriod(dateFrom, dateUntil);
        } 
    });
}

// load setUpFilter() and get the articles when loading the page after importing all Javascript functions
window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter));
    setUpFilter();
    timeDelete();
    setUpUpload();
}