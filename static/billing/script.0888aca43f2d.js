window.onload = function () {
    var footers = document.getElementsByTagName('footer');

    if (footers.length != 0) {
        footers[0].innerHTML = "Copyright © 2023 Silicon-goli. All rights reserved."
    }
    try {
        var cards = document.getElementsByClassName('card-body')
        if (cards.length != 0) {
            var stupid_text = cards[0].children[1]
            if ((stupid_text.childElementCount) === 0) {
                stupid_text.innerHTML = ""
            }
        }
    }
    catch (err) {
        console.log(err)
    }
    try {
        var client_save_btn = document.querySelector('#client_form > div > .col-lg-3 > div > div > div > input')
        client_save_btn.value = "Save & Add event"
    }
    catch (err) {
        console.log(err)
    }
    try {
        var inflow_save_btn = document.querySelector('#cashinflow_form > div > .col-lg-3 > div > div > div > input')
        var inflow_history_btn = document.querySelector('#cashinflow_form > div > .col-lg-3 > div > .object-tools > .btn-secondary')
        console.log(inflow_history_btn)
        if (inflow_history_btn != null) {
            inflow_save_btn.value = "Generate Updated Invoice"
            inflow_save_btn.addEventListener('click', function () { setTimeout(function () { window.location.replace(window.location.origin + '/admin/billing/cashinflow') }, 15000) })
        }
        else {
            inflow_save_btn.value = "Continue to Add Amount"
        }
    }
    catch (err) {
        console.log(err)
    }
    try {
        var client_save_btn = document.querySelector('#event_form > div > .col-lg-3 > div > div > div > input')
        client_save_btn.value = "Save & Generate Invoice"
        client_save_btn.addEventListener('click', function () { setTimeout(function () { window.location.replace(window.location.origin + '/admin/billing/event') }, 15000) })
    }
    catch (err) {
        console.log(err)
    }

}

function CopyUrl(element) {
    var copyText = element.href;
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = copyText;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
}

function CopyUrlOnly(link, id) {
    var copyText = window.location.origin + link.link;
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = copyText;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
    var tooltip = document.getElementById(id)
    tooltip.innerHTML = "Copied!"
}