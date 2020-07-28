function lastZoteroSync() {
    const syncTextField = document.getElementById("zoteroSyncText");

    fetch(base_url+"/zotero_sync", {
        method: 'GET'
        }).then(function (response) {
            return response.text();
        }).then(function (response_text){
            const update_str = response_text;
            const [date, time] = update_str.split(" ")
            const update_note = "<b>Database was last synced with Zotero</b><br><br><b>Date:</b> "+date+"<br><b>Time:</b> "+time
            syncTextField.innerHTML = update_note;
        }).catch(function (error){
            console.error(error);
            alert("A Network Error occured. Please contact the Website administrator or try again later.")
        });
}

function setUpUpload() {
    // Select your input type file and store it in a constiable
    const input = document.getElementById("fileinput");

    uploadForm.addEventListener("submit", function (e){
        e.preventDefault();

        const data = new FormData();
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
// Function to ad an article
async function addArticle(mydoi){
    fetch(base_url+"/add/"+mydoi, {
            method: 'GET',
            }).then(function (response) {
                return response.text();
            }).then(function (response_text){
                alert(response_text);
                window.location.href=base_url;
            }).catch(function (error){
                console.error(error);
                alert("A Network Error occured. Please contact the Website administrator or try again later.")
            });
}

function addArticleSetUp() {
    const addArticleForm = document.getElementById("addArticleForm");

        addArticleForm.addEventListener("submit", function (e){
            e.preventDefault();

            var doicontent = document.getElementById('mydoi').value;
            var copy = doicontent;
            var slashcount = copy.replace(/[^\/]/g, "").length;
            if (slashcount  != 1 && slashcount  != 2 && slashcount != 3) {
                alert("DOI format is not compatible. Please check if entered correctly.");
                return false;
            };
            // Replace all Slashes '/' with '&&sl' to forward the doi as a single parameter to the API
            var doi = doicontent.replace(/\//g,"&&sl")
            addArticle(doi);
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

        const dateFrom = document.getElementById('dateFrom').value;
        const dateUntil = document.getElementById('dateUntil').value;

        if (dateFrom.length == 0 || dateUntil.length == 0) {
            alert('Please enter the two adding-dates between which(including those dates) you want to delete all created articles');
            return false;
        }
        
        const cnt_delete = await deleteTimePeriod(dateFrom, dateUntil, "dry");

        const r = confirm("Do you really want to delete all "+ cnt_delete +" Articles that were added \n between (including) "+dateFrom+" and "+dateUntil+"?");
        if (r == true) {
            const response_text = await deleteTimePeriod(dateFrom, dateUntil, "delete");
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
    addArticleSetUp();
    lastZoteroSync();
}