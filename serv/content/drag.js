// drag.js

'use strict';

function rforeach(seq, fn) {
    var i1, n = seq.length;
    for (i1 = 0; i1 < n; i1 += 1) {
        fn(seq[i1]);
    }
}

function rmap(seq, fn) {
    var i2, n = seq.length;
    var res = [], val;
    for (i2 = 0; i2 < n; i2++) {
        val = fn(seq[i2]);
        res.push(val);
    }
    return res;
}

function rcontains(seq, item) {
    var i3, n = seq.length;
    for (i3 = 0; i3 < n; i3 += 1) {
        if (seq[i3] === item) {
            return true;
        }
    }
    return false;
}

// ****************************************

var Dragger =  {
        dragState: null,
        startDrag: function startDrag(event, x, y, touch, followups, evtFunctions) {
           var listener = function(event) { Dragger.dispatch(event, evtFunctions); };
           rforeach(followups, function(e) {
               window.addEventListener(e, listener);
           });
           Dragger.dragState = {
               target: event.target,
               touch: touch, listener: listener,
           };
       },
       endDrag: function endDrag(event, x, y) {
            Dragger.remove();
       },
       touchXY: function touchXY(event) {
            var touch;
            for (var i = 0; i < event.changedTouches.length; i++) {
                var t = event.changedTouches[i];
                if (t.identifier === Dragger.dragState.touch) {
                    touch = t;
                    break;
                }
            }
            if (touch) {
                return [touch.pageX, touch.pageY];
            } else return null;
        },
       remove: function remove() {
            var dragState = Dragger.dragState;
            if (dragState) {
                rforeach("mousemove mouseup touchmove touchend touchcancel".split(" "), function(e) {
                    window.removeEventListener(e, dragState.listener);
                });
                Dragger.dragState = null;
            }
       },
       dispatch: function dispatch(event, evtFunctions) {
            event.preventDefault();
            var dragTarget = Dragger.dragState && Dragger.dragState.target;
            switch (event.type) {
                case "mousedown":
                    var x = event.clientX, y = event.clientY;
                    Dragger.startDrag(event, x, y, 0, ["mousemove", "mouseup"], evtFunctions);
                    //console.log("evt x", x, "y", y);
                    if (evtFunctions && evtFunctions.onstart) evtFunctions.onstart(Dragger.dragState.target, x, y);
                    break;
                case "mousemove":
                    var x = event.clientX, y = event.clientY;
                    //console.log("yo", x, y);
                    if (evtFunctions && evtFunctions.onmove) evtFunctions.onmove(dragTarget, x, y);
                    break;
                case "mouseup":
                    var x = event.clientX, y = event.clientY;
                    Dragger.endDrag(event, x, y);
                    if (evtFunctions && evtFunctions.onend) evtFunctions.onend(dragTarget, x, y);
                    break;
                case "touchstart":
                    var touch = event.changedTouches[0];
                    var x = touch.pageX, y = touch.pageY;
                    Dragger.startDrag(event, x, y, touch.identifier, ["touchmove", "touchend", "touchcancel"], evtFunctions);
                    if (evtFunctions && evtFunctions.onstart) evtFunctions.onstart(Dragger.dragState.target, x, y);
                    break;
                case "touchmove":
                    var xy = Dragger.touchXY(event);
                    if (xy && evtFunctions && evtFunctions.onmove) evtFunctions.onmove(dragTarget, xy[0], xy[1]);
                    break;
                case "touchend":
                case "touchcancel":
                    var xy = Dragger.touchXY(event);
                    if (xy) {
                        Dragger.endDrag(event, xy[0], xy[1]);
                    }
                    Dragger.remove();
                    if (xy && evtFunctions && evtFunctions.onend) evtFunctions.onend(dragTarget, xy[0], xy[1]);
                    break;
                default:
                    console.log("unhandled evt", event);
                    break;
            }
       },
};

function doDrag(event, evtFunctions) {
    Dragger.dispatch(event, evtFunctions);
}
