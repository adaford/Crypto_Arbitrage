/*var sidebar = document.getElementById('sidebar');

function sidebarToggle() {
    if (sidebar.style.display === "none") {
        sidebar.style.display = "block";
    } else {
        sidebar.style.display = "none";
    }
}

var profileDropdown = document.getElementById('ProfileDropDown');

function profileToggle() {
    if (profileDropdown.style.display === "none") {
        profileDropdown.style.display = "block";
    } else {
        profileDropdown.style.display = "none";
    }
}


/**
 * ### Modals ###
 

function toggleModal(action, elem_trigger)
{
    elem_trigger.addEventListener('click', function () {
        if (action == 'add') {
            let modal_id = this.dataset.modal;
            document.getElementById(`${modal_id}`).classList.add('modal-is-open');
        } else {
            // Automaticlly get the opned modal ID
            let modal_id = elem_trigger.closest('.modal-wrapper').getAttribute('id');
            document.getElementById(`${modal_id}`).classList.remove('modal-is-open');
        }
    });
}


// Check if there is modals on the page
if (document.querySelector('.modal-wrapper'))
{
    // Open the modal
    document.querySelectorAll('.modal-trigger').forEach(btn => {
        toggleModal('add', btn);
    });
    
    // close the modal
    document.querySelectorAll('.close-modal').forEach(btn => {
        toggleModal('remove', btn);
    });
}*/

function buildRows(numRows,list) {
    $('#Table').find('tbody>tr').remove()
    for(j=0;j<numRows;j++) {
        row = (j+1).toString()
        coin = list[7*j].toString()
        exchange = list[7*j+1].toString()
        percent = list[7*j+2] + "%"
        cmc_value = '$' + list[7*j+3].toString()
        e_v = '$' + list[7*j+4].toString()
        liquidity_exchange = '$' + list[7*j+5].toString()
        liqudity_gate = '$' + list[7*j+6].toString()
        color = parseFloat(list[7*j+2]) > 0 ? "text-green-500" : "text-red-500"

        let content = '<tr><th scope="row">' + row + '</th><td>' + coin + '</td><td>' + exchange + '</td><td>' + 
            cmc_value + '</td><td>' + e_v + '</td><td><span class=' +
            color + '></i>' + percent + '</span></td><td>' + liquidity_exchange + '</td><td>' + liqudity_gate + '</td></tr>'

        $('#Table').find('tbody').append(content)  
    }
        
}

    /*else if (currentLength < newLength){
        for(i=0;i<(newLength-currentLength);i++){
            $('#Table').find('tbody').append('<tr><th scope="row">' + (currentLength+i+1).toString() + '</th></tr>')
            console.log($('#Table').find('tbody>tr').length)
        }
    }

    for(i=0;i<newLength;i++){
        $('#Table').find('tbody')[i] = 1
    }*/

function parseResponseText(res) {
    if (!res.includes(',')) {
        buildRows(1,[0,0,0,0,0,0,0])
        return
    }
    let list = res.split(',')
    let numRows = list.length/7
    for(j=0;j<numRows;j++){
        for(i=0;i<7;i++){
            if (list[i+j*7].includes(':')) {
                list[i+j*7] = list[i+j*7].split(":")[1]
            }         
            list[i+j*7] = list[i+j*7].replace(/[^0-9.a-z-]/gi, '') 
        }
    }
    buildRows(numRows,list)
}

function sendRequest(url){
    var xhttp = new XMLHttpRequest();
    xhttp.onload = function () {
        if (xhttp.readyState === xhttp.DONE) {
            if (xhttp.status === 200) {
                parseResponseText(xhttp.responseText)
            }
        }
    };
    //var xhttp = new XMLHttpRequest();
    xhttp.open("GET", url, true);
    xhttp.send();
    //parseResponseText(xhttp)
}

// execute function when page is loaded
window.onload=function(){
    if(document.createElement&&document.createTextNode){
        // send get request every 2 seconds
        sendRequest("http://ec2-3-141-6-61.us-east-2.compute.amazonaws.com")
        setInterval("sendRequest('http://3.141.6.61');",5*1000);
    }
}



