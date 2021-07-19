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
        coin = list[6*j].toString()
        exchange = list[6*j+1].toString()
        percent = list[6*j+2] + "%"
        cmc_value = '$' + list[6*j+3].toString()
        e_v = '$' + list[6*j+4].toString()
        liquidity = '$' + list[6*j+5].toString()
        color = parseFloat(list[6*j+2]) > 0 ? "text-green-500" : "text-red-500"

        let content = '<tr><th scope="row">' + row + '</th><td>' + coin + '</td><td>' + exchange + '</td><td>' + 
            cmc_value + '</td><td>' + e_v + '</td><td><span class=' +
            color + '></i>' + percent + '</span></td><td>' + liquidity + '</td></tr>'

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
    let list = res.split(',')
    let numRows = list.length/6

    for(j=0;j<numRows;j++){
        for(i=0;i<6;i++){
            list[i+j*6] = list[i+j*6].replace(/[^0-9.a-z-]/gi, '')
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
        sendRequest("http://ec2-18-223-102-251.us-east-2.compute.amazonaws.com")
        setInterval("sendRequest('http://18.223.102.251');",5*1000);
    }
}



