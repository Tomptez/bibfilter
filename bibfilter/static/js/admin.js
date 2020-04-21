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

// Function to delete Articles in a timeperiod
// Explanation how to assign fetch values = https://stackoverflow.com/questions/54034875/how-can-i-acces-the-values-of-my-async-fetch-function
async function deleteTimePeriod(from,until,dry){
    console.log(dry)
    const respText = await fetch(base_url+"/deleteTimePeriod/"+from+"/"+until+"/"+dry, {
            method: 'GET',
            }).then(function (response) {
                return response.text();
            }).catch(function (error){
                console.error(error);
                alert("A Network Error occured. Please contact the Website administrator or try again later.")
            });
    return respText;
}

function timeDelete() {
    const deleteArticlesForm = document.getElementById("deleteArticlesForm");

    deleteArticlesForm.addEventListener("submit", async function (e){
        e.preventDefault();

        var dateFrom = document.getElementById('dateFrom').value;
        var dateUntil = document.getElementById('dateUntil').value;

        if (dateFrom.length == 0 || dateUntil.length == 0) {
            alert('Please enter the two adding-dates between which(including those dates) you want to delete all created articles');
            return false;
        }
        
        var cnt_delete = await deleteTimePeriod(dateFrom, dateUntil, "dry");

        var r = confirm("Do you really want to delete all "+ cnt_delete +" Articles that were added \n between (including) "+dateFrom+" and "+dateUntil+"?");
        if (r == true) {
            var response_text = await deleteTimePeriod(dateFrom, dateUntil, "delete");
            alert("Deleted "+response_text+" Articles");
            window.location.href=base_url+"/admin";
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