var currentFilter = {"title":"","author":"", "timestart": "", "until": "", "type": "all","sortby":"year","sortorder":"asc"}

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
                var divContainer = document.getElementById("showData");
                divContainer.innerHTML = '<p style="font-style: italic;"> A Neetwork Error occured. Please contact the Website administrator or try again later.</p>';
            });
}

async function downloadBib(){
    var json = JSON.stringify(currentFilter)
    fetch('http://127.0.0.1:5000/bibfile', {
            method: 'POST',
            body: json, // string or object
            headers: {
                'Content-Type': 'application/json'
            }
            }).then(function (response) {
                return response.blob();
            }).then(function (blob){
                download(blob, "bibliography.bib", "text/plain");
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
    console.log("resetPage()");
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
        console.log(currentFilter)
        var json = JSON.stringify(filter);
        getFilteredLiterature(json);
    });
}

function CreateTableFromJSON(data) {
    console.log("Start CreateTableFromJSON()")
    
    // EXTRACT VALUE FOR HTML HEADER. 
    // ('Book ID', 'Book Name', 'Category' and 'Price')
    var col = [];
    colname = {"title": "Title", "author": "Author", "year": "Year"}
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
        var linkText = document.createTextNode(colname[col[i]]);
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
    if (data.length == 0) {
        divContainer.innerHTML = '<p style="font-style: italic;"> Unfortunately no literature met your criteria</p>';
    }
    else {
        divContainer.innerHTML = "";
    divContainer.appendChild(table);
    }
    
}

//download.js v4.2, by dandavis; 2008-2016. [CCBY2] see http://danml.com/download.html for tests/usage
// v1 landed a FF+Chrome compat way of downloading strings to local un-named files, upgraded to use a hidden frame and optional mime
// v2 added named files via a[download], msSaveBlob, IE (10+) support, and window.URL support for larger+faster saves than dataURLs
// v3 added dataURL and Blob Input, bind-toggle arity, and legacy dataURL fallback was improved with force-download mime and base64 support. 3.1 improved safari handling.
// v4 adds AMD/UMD, commonJS, and plain browser support
// v4.1 adds url download capability via solo URL argument (same domain/CORS only)
// v4.2 adds semantic variable names, long (over 2MB) dataURL support, and hidden by default temp anchors
// https://github.com/rndme/download

(function (root, factory) {
	if (typeof define === 'function' && define.amd) {
		// AMD. Register as an anonymous module.
		define([], factory);
	} else if (typeof exports === 'object') {
		// Node. Does not work with strict CommonJS, but
		// only CommonJS-like environments that support module.exports,
		// like Node.
		module.exports = factory();
	} else {
		// Browser globals (root is window)
		root.download = factory();
    }
}(this, function () {

	return function download(data, strFileName, strMimeType) {

		var self = window, // this script is only for browsers anyway...
			defaultMime = "application/octet-stream", // this default mime also triggers iframe downloads
			mimeType = strMimeType || defaultMime,
			payload = data,
			url = !strFileName && !strMimeType && payload,
			anchor = document.createElement("a"),
			toString = function(a){return String(a);},
			myBlob = (self.Blob || self.MozBlob || self.WebKitBlob || toString),
			fileName = strFileName || "download",
			blob,
			reader;
			myBlob= myBlob.call ? myBlob.bind(self) : Blob ;
        
            if(String(this)==="true"){ //reverse arguments, allowing download.bind(true, "text/xml", "export.xml") to act as a callback
			payload=[payload, mimeType];
			mimeType=payload[0];
			payload=payload[1];
		}


		if(url && url.length< 2048){ // if no filename and no mime, assume a url was passed as the only argument
			fileName = url.split("/").pop().split("?")[0];
			anchor.href = url; // assign href prop to temp anchor
		  	if(anchor.href.indexOf(url) !== -1){ // if the browser determines that it's a potentially valid url path:
                var ajax=new XMLHttpRequest();
                ajax.open( "GET", url, true);
                ajax.responseType = 'blob';
                ajax.onload= function(e){ 
                    download(e.target.response, fileName, defaultMime);
                };
                setTimeout(function(){ ajax.send();}, 0); // allows setting custom ajax headers using the return:
                return ajax;
			} // end if valid url?
		} // end if url?


		//go ahead and download dataURLs right away
		if(/^data\:[\w+\-]+\/[\w+\-]+[,;]/.test(payload)){
		
			if(payload.length > (1024*1024*1.999) && myBlob !== toString ){
				payload=dataUrlToBlob(payload);
				mimeType=payload.type || defaultMime;
			}else{			
				return navigator.msSaveBlob ?  // IE10 can't do a[download], only Blobs:
					navigator.msSaveBlob(dataUrlToBlob(payload), fileName) :
					saver(payload) ; // everyone else can save dataURLs un-processed
			}
			
		}//end if dataURL passed?

		blob = payload instanceof myBlob ?
			payload :
			new myBlob([payload], {type: mimeType}) ;


		function dataUrlToBlob(strUrl) {
			var parts= strUrl.split(/[:;,]/),
			type= parts[1],
			decoder= parts[2] == "base64" ? atob : decodeURIComponent,
			binData= decoder( parts.pop() ),
			mx= binData.length,
			i= 0,
			uiArr= new Uint8Array(mx);

			for(i;i<mx;++i) uiArr[i]= binData.charCodeAt(i);

			return new myBlob([uiArr], {type: type});
		}

		function saver(url, winMode){

			if ('download' in anchor) { //html5 A[download]
				anchor.href = url;
				anchor.setAttribute("download", fileName);
				anchor.className = "download-js-link";
				anchor.innerHTML = "downloading...";
				anchor.style.display = "none";
				document.body.appendChild(anchor);
				setTimeout(function() {
					anchor.click();
					document.body.removeChild(anchor);
					if(winMode===true){setTimeout(function(){ self.URL.revokeObjectURL(anchor.href);}, 250 );}
				}, 66);
				return true;
			}

			// handle non-a[download] safari as best we can:
			if(/(Version)\/(\d+)\.(\d+)(?:\.(\d+))?.*Safari\//.test(navigator.userAgent)) {
				url=url.replace(/^data:([\w\/\-\+]+)/, defaultMime);
				if(!window.open(url)){ // popup blocked, offer direct download:
					if(confirm("Displaying New Document\n\nUse Save As... to download, then click back to return to this page.")){ location.href=url; }
				}
				return true;
			}

			//do iframe dataURL download (old ch+FF):
			var f = document.createElement("iframe");
			document.body.appendChild(f);

			if(!winMode){ // force a mime that will download:
				url="data:"+url.replace(/^data:([\w\/\-\+]+)/, defaultMime);
			}
			f.src=url;
			setTimeout(function(){ document.body.removeChild(f); }, 333);

		}//end saver

		if (navigator.msSaveBlob) { // IE10+ : (has Blob, but not a[download] or URL)
			return navigator.msSaveBlob(blob, fileName);
		}

		if(self.URL){ // simple fast and modern way using Blob and URL:
			saver(self.URL.createObjectURL(blob), true);
		}else{
			// handle non-Blob()+non-URL browsers:
			if(typeof blob === "string" || blob.constructor===toString ){
				try{
					return saver( "data:" +  mimeType   + ";base64,"  +  self.btoa(blob)  );
				}catch(y){
					return saver( "data:" +  mimeType   + "," + encodeURIComponent(blob)  );
				}
			}

			// Blob but not URL support:
			reader=new FileReader();
			reader.onload=function(e){
				saver(this.result);
			};
			reader.readAsDataURL(blob);
		}
		return true;
	}; /* end download() */
}));

window.onload = function(){
    getFilteredLiterature(JSON.stringify(currentFilter))
    setUpFilter();
}