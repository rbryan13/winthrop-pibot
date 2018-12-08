

function rezoom() {
    var userAgent = navigator.userAgent;
    var size = 0;
    if (userAgent.indexOf("Android") > 0) {
        if (userAgent.indexOf("SM-T230NU") > 0) {
            size = 2;
        }
    }
    if (size) {
        var outer = document.getElementsByTagName("html")[0];
        outer.style["font-size"] = "" + size + "em";
    }
}

document.addEventListener("DOMContentLoaded", function() {
    rezoom();
});

