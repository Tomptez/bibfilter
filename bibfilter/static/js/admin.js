function lastZoteroSync() {
    const syncTextField = document.getElementById("zoteroSyncNotification");

    fetch(base_url+"/zotero_sync", {
        method: 'GET'
        }).then(function (response) {
            return response.text();
        }).then(function (response_text){
            const update_str = response_text;
            const [date, time] = update_str.split(" ")
            const update_note = "<b>Database was last synced with Zotero on:</b><br><br><b>Date:</b> "+date+"<br><b>Time:</b> "+time
            syncTextField.innerHTML = update_note;
        }).catch(function (error){
            console.error(error);
            alert("A Network Error occured. Please contact the Website administrator or try again later.")
        });
}


// load setUpFilter() and get the articles when loading the page after importing all Javascript functions
window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter));
    setUpFilter();
    lastZoteroSync();
}