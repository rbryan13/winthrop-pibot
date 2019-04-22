// grassy-drive.js

function phoneHome(text) {
    var url = "/phonehome/?" + encodeURI(text);
    sendAjaxGet(url);
}

function sendAjaxGet(url, okfn, errfn) {
    var errors = document.getElementById("errors");
    errors.innerText = "";
    if (!errfn) errfn = ajaxErrFn;
    var loadedfn = function loadedfn(evt) {
	if (evt.target.status !== 0 && evt.target.status !== 200) {
	    errfn(evt);
	} else if (okfn) okfn(evt);
    };
    var req = new XMLHttpRequest();
    req.responseType = "text";
    req.open("GET", url);
    req.addEventListener("load", loadedfn);
    req.addEventListener("error", errfn);
    req.addEventListener("abort", errfn);
    req.send();
}

function ajaxErrFn(evt) {
    console.log("ajax error", evt.target);
    var errors = document.getElementById("errors");
    errors.innerText = "Trouble contacting server";
}

function lerp(x, x0, x1, y0, y1) {
    var frac = (x - x0) / (x1 - x0);
    var y =  y0 + frac * (y1 - y0);
    //console.log(`lerp x ${x} x0 ${x0} x1 ${x1} y0 ${y0} y1 ${y1} ==> ${y}`);
    return y;
}

function round3(x) { return Math.round(1000*x) / 1000; }

function onStart(target, x, y) {
    //console.log("onStart x", x, "y", y);
    var f = posFraction(x, y);
    maybeSendMotion(f.x, f.y);
}
function onMove(target, x, y) {
    var f = posFraction(x, y);
    maybeSendMotion(f.x, f.y);
}
function onEnd(target, x, y) {
    maybeSendMotion(0.5, 0.5);
    //sendAjaxGet("/stop");
}

var onFunctions = {onstart: onStart, onmove: onMove, onend: onEnd};

function arenaClick(evt) {
    doDrag(evt, onFunctions);
}
function arenaTouch(evt) {
    doDrag(evt, onFunctions);
}

var servoChannels = {
    throttle: 0,
	      steering: 1,
};
var deadZone = { steering: {low: 0.4, high: 0.6}, throttle: {low: 0.4, high: 0.6}};

var desiredSetting = {
    steering: {direction: null, speed: 0},
    throttle: {direction: null, speed: 0}
};
var recentSetting = {
    steering: {direction: null, speed: 0},
    throttle: {direction: null, speed: 0},
    inprogress: false,
};

var fullThrottlePWM = 1.0;

// ****************************************
// This function is supplied by the caller (motors.html, cart.html)
// function maybeSendMotion(fx, fy) { ... }
// ****************************************

// While a request is in progress, don't send another until the response
// to the current one comes back.
function queueMotion() {
    if (recentSetting.inprogress) {
	// Any change will be handled when the current in-progress request completes.
	//phoneHome("in progress");
	return;
    }
    var changed = false;
    rforeach(["steering", "throttle"], function(motor) {
	rforeach(["direction", "speed"], function(axis) {
	    if (desiredSetting[motor][axis] != recentSetting[motor][axis]) {
		changed = true;
	    } else {
		//var msg = "n/c " + motor+"."+axis + " " + desiredSetting[motor][axis] + " vs " + recentSetting[motor][axis];
		//phoneHome(msg);
	    }
	});
    });
    if (!changed) {
	// ---This could keep track of when the last request went out,
	// and send out even a dup if it has been long enough (like 1.0 sec?)

	// Nothing to do
	//phoneHome("no change");
	return;
    } else {
	//phoneHome("yay change");
    }

    // direction (A or B)
    // channel (0 or 1, probably)
    // PWM value (0.0 to 1.0)
    // One triple for steering, then one for throttle
    var urlparts = function urlparts(motor) {
	var parts = [desiredSetting[motor].direction, servoChannels[motor], desiredSetting[motor].speed];
	return parts.join("-");
    };

    var steeringParts = urlparts("steering");
    var throttleParts = urlparts("throttle");
    var url = ["/motor", steeringParts, throttleParts].join("/");
    rforeach(["steering", "throttle"], function(motor) {
	rforeach(["direction", "speed"], function(axis) {
	    recentSetting[motor][axis] = desiredSetting[motor][axis];
	});
    });

    recentSetting.inprogress = true;
    var okfn = function okfn(evt) {
	recentSetting.inprogress = false;
	queueMotion();
    };
    var errfn = function errfn(evt) {
	recentSetting.inprogress = false;
	ajaxErrFn(evt);
    };
    sendAjaxGet(url, okfn, errfn);
}

function posFraction(x, y) {
    var arena = document.getElementById("arena");
    var left = arena.offsetLeft;
    var top = arena.offsetTop;
    var width = arena.offsetWidth;
    var height = arena.offsetHeight;
    var dx = x - left;
    var dy = y - top;
    var fx = round3(Math.max(0.0, Math.min(1.0, dx * 1.0 / width)));
    var fy = round3(Math.max(0.0, Math.min(1.0, dy * 1.0 / height)));
    //console.log("left", left, "top", top, "width", width, "height", height);
    //console.log("x", x, "y", y, "dx", dx, "dy", dy, "fx", fx, "fy", fy);
    return {x: fx, y: fy};
}
