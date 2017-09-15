(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
module.exports = function (cytoscape, cy, $) {
    
    // Needed because parent nodes cannot be moved!
    function moveTopDown(node, dx, dy) {
        var nodes = node.union(node.descendants());

        nodes.positions(function (i, node) {
            var pos = node.position();
            return {
                x: pos.x + dx,
                y: pos.y + dy
            };
        });
    }

    function getTopMostNodes(nodes) {
        var nodesMap = {};
        for (var i = 0; i < nodes.length; i++) {
            nodesMap[nodes[i].id()] = true;
        }
        var roots = nodes.filter(function (i, ele) {
            var parent = ele.parent()[0];
            while(parent != null){
                if(nodesMap[parent.id()]){
                    return false;
                }
                parent = parent.parent()[0];
            }
            return true;
        });

        return roots;
    }


    cytoscape( "collection", "align", function (horizontal, vertical, alignTo) {

        var eles = getTopMostNodes(this.nodes(":visible"));

        var modelNode = alignTo ? alignTo : eles[0];

        eles = eles.not(modelNode);

        horizontal = horizontal ? horizontal : "none";
        vertical = vertical ? vertical : "none";


        // 0 for center
        var xFactor = 0;
        var yFactor = 0;

        if (vertical == "left")
            xFactor = -1;
        else if (vertical == "right")
            xFactor = 1;

        if (horizontal == "top")
            yFactor = -1;
        else if (horizontal == "bottom")
            yFactor = 1;


        for (var i = 0; i < eles.length; i++) {
            var node = eles[i];
            var oldPos = $.extend({}, node.position());
            var newPos = $.extend({}, node.position());

            if (vertical != "none")
                newPos.x = modelNode.position("x") + xFactor * (modelNode.width() - node.width()) / 2;


            if (horizontal != "none")
                newPos.y = modelNode.position("y") + yFactor * (modelNode.height() - node.height()) / 2;

            moveTopDown(node, newPos.x - oldPos.x, newPos.y - oldPos.y);
        }

        return this;
    });

    if (cy.undoRedo) {
        function getNodePositions() {
            var positionsAndSizes = {};
            var nodes = cy.nodes();

            for (var i = 0; i < nodes.length; i++) {
                var ele = nodes[i];
                positionsAndSizes[ele.id()] = {
                    x: ele.position("x"),
                    y: ele.position("y")
                };
            }

            return positionsAndSizes;
        }

        function returnToPositions(nodesData) {
            var currentPositions = {};
            cy.nodes().positions(function (i, ele) {
                currentPositions[ele.id()] = {
                    x: ele.position("x"),
                    y: ele.position("y")
                };
                var data = nodesData[ele.id()];
                return {
                    x: data.x,
                    y: data.y
                };
            });

            return currentPositions
        }

        var ur = cy.undoRedo();

        ur.action("align", function (args) {

            var nodesData;
            if (args.firstTime){
                nodesData = getNodePositions();
                args.nodes.align(args.horizontal, args.vertical, args.alignTo);
            }
            else
                nodesData = returnToPositions(args);

            return nodesData;

        }, function (nodesData) {
            return returnToPositions(nodesData);
        });

    }



};
},{}],2:[function(require,module,exports){

var debounce = (function(){
    /**
     * lodash 3.1.1 (Custom Build) <https://lodash.com/>
     * Build: `lodash modern modularize exports="npm" -o ./`
     * Copyright 2012-2015 The Dojo Foundation <http://dojofoundation.org/>
     * Based on Underscore.js 1.8.3 <http://underscorejs.org/LICENSE>
     * Copyright 2009-2015 Jeremy Ashkenas, DocumentCloud and Investigative Reporters & Editors
     * Available under MIT license <https://lodash.com/license>
     */
    /** Used as the `TypeError` message for "Functions" methods. */
    var FUNC_ERROR_TEXT = 'Expected a function';

    /* Native method references for those with the same name as other `lodash` methods. */
    var nativeMax = Math.max,
        nativeNow = Date.now;

    /**
     * Gets the number of milliseconds that have elapsed since the Unix epoch
     * (1 January 1970 00:00:00 UTC).
     *
     * @static
     * @memberOf _
     * @category Date
     * @example
     *
     * _.defer(function(stamp) {
     *   console.log(_.now() - stamp);
     * }, _.now());
     * // => logs the number of milliseconds it took for the deferred function to be invoked
     */
    var now = nativeNow || function() {
            return new Date().getTime();
        };

    /**
     * Creates a debounced function that delays invoking `func` until after `wait`
     * milliseconds have elapsed since the last time the debounced function was
     * invoked. The debounced function comes with a `cancel` method to cancel
     * delayed invocations. Provide an options object to indicate that `func`
     * should be invoked on the leading and/or trailing edge of the `wait` timeout.
     * Subsequent calls to the debounced function return the result of the last
     * `func` invocation.
     *
     * **Note:** If `leading` and `trailing` options are `true`, `func` is invoked
     * on the trailing edge of the timeout only if the the debounced function is
     * invoked more than once during the `wait` timeout.
     *
     * See [David Corbacho's article](http://drupalmotion.com/article/debounce-and-throttle-visual-explanation)
     * for details over the differences between `_.debounce` and `_.throttle`.
     *
     * @static
     * @memberOf _
     * @category Function
     * @param {Function} func The function to debounce.
     * @param {number} [wait=0] The number of milliseconds to delay.
     * @param {Object} [options] The options object.
     * @param {boolean} [options.leading=false] Specify invoking on the leading
     *  edge of the timeout.
     * @param {number} [options.maxWait] The maximum time `func` is allowed to be
     *  delayed before it's invoked.
     * @param {boolean} [options.trailing=true] Specify invoking on the trailing
     *  edge of the timeout.
     * @returns {Function} Returns the new debounced function.
     * @example
     *
     * // avoid costly calculations while the window size is in flux
     * jQuery(window).on('resize', _.debounce(calculateLayout, 150));
     *
     * // invoke `sendMail` when the click event is fired, debouncing subsequent calls
     * jQuery('#postbox').on('click', _.debounce(sendMail, 300, {
     *   'leading': true,
     *   'trailing': false
     * }));
     *
     * // ensure `batchLog` is invoked once after 1 second of debounced calls
     * var source = new EventSource('/stream');
     * jQuery(source).on('message', _.debounce(batchLog, 250, {
     *   'maxWait': 1000
     * }));
     *
     * // cancel a debounced call
     * var todoChanges = _.debounce(batchLog, 1000);
     * Object.observe(models.todo, todoChanges);
     *
     * Object.observe(models, function(changes) {
     *   if (_.find(changes, { 'user': 'todo', 'type': 'delete'})) {
     *     todoChanges.cancel();
     *   }
     * }, ['delete']);
     *
     * // ...at some point `models.todo` is changed
     * models.todo.completed = true;
     *
     * // ...before 1 second has passed `models.todo` is deleted
     * // which cancels the debounced `todoChanges` call
     * delete models.todo;
     */
    function debounce(func, wait, options) {
        var args,
            maxTimeoutId,
            result,
            stamp,
            thisArg,
            timeoutId,
            trailingCall,
            lastCalled = 0,
            maxWait = false,
            trailing = true;

        if (typeof func != 'function') {
            throw new TypeError(FUNC_ERROR_TEXT);
        }
        wait = wait < 0 ? 0 : (+wait || 0);
        if (options === true) {
            var leading = true;
            trailing = false;
        } else if (isObject(options)) {
            leading = !!options.leading;
            maxWait = 'maxWait' in options && nativeMax(+options.maxWait || 0, wait);
            trailing = 'trailing' in options ? !!options.trailing : trailing;
        }

        function cancel() {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            if (maxTimeoutId) {
                clearTimeout(maxTimeoutId);
            }
            lastCalled = 0;
            maxTimeoutId = timeoutId = trailingCall = undefined;
        }

        function complete(isCalled, id) {
            if (id) {
                clearTimeout(id);
            }
            maxTimeoutId = timeoutId = trailingCall = undefined;
            if (isCalled) {
                lastCalled = now();
                result = func.apply(thisArg, args);
                if (!timeoutId && !maxTimeoutId) {
                    args = thisArg = undefined;
                }
            }
        }

        function delayed() {
            var remaining = wait - (now() - stamp);
            if (remaining <= 0 || remaining > wait) {
                complete(trailingCall, maxTimeoutId);
            } else {
                timeoutId = setTimeout(delayed, remaining);
            }
        }

        function maxDelayed() {
            complete(trailing, timeoutId);
        }

        function debounced() {
            args = arguments;
            stamp = now();
            thisArg = this;
            trailingCall = trailing && (timeoutId || !leading);

            if (maxWait === false) {
                var leadingCall = leading && !timeoutId;
            } else {
                if (!maxTimeoutId && !leading) {
                    lastCalled = stamp;
                }
                var remaining = maxWait - (stamp - lastCalled),
                    isCalled = remaining <= 0 || remaining > maxWait;

                if (isCalled) {
                    if (maxTimeoutId) {
                        maxTimeoutId = clearTimeout(maxTimeoutId);
                    }
                    lastCalled = stamp;
                    result = func.apply(thisArg, args);
                }
                else if (!maxTimeoutId) {
                    maxTimeoutId = setTimeout(maxDelayed, remaining);
                }
            }
            if (isCalled && timeoutId) {
                timeoutId = clearTimeout(timeoutId);
            }
            else if (!timeoutId && wait !== maxWait) {
                timeoutId = setTimeout(delayed, wait);
            }
            if (leadingCall) {
                isCalled = true;
                result = func.apply(thisArg, args);
            }
            if (isCalled && !timeoutId && !maxTimeoutId) {
                args = thisArg = undefined;
            }
            return result;
        }
        debounced.cancel = cancel;
        return debounced;
    }

    /**
     * Checks if `value` is the [language type](https://es5.github.io/#x8) of `Object`.
     * (e.g. arrays, functions, objects, regexes, `new Number(0)`, and `new String('')`)
     *
     * @static
     * @memberOf _
     * @category Lang
     * @param {*} value The value to check.
     * @returns {boolean} Returns `true` if `value` is an object, else `false`.
     * @example
     *
     * _.isObject({});
     * // => true
     *
     * _.isObject([1, 2, 3]);
     * // => true
     *
     * _.isObject(1);
     * // => false
     */
    function isObject(value) {
        // Avoid a V8 JIT bug in Chrome 19-20.
        // See https://code.google.com/p/v8/issues/detail?id=2291 for more details.
        var type = typeof value;
        return !!value && (type == 'object' || type == 'function');
    }

    return debounce;

})();

module.exports = debounce;
},{}],3:[function(require,module,exports){
module.exports = function (cy, snap) {

    var discreteDrag = {};

    var attachedNode;
    var draggedNodes;

    var startPos;
    var endPos;


    discreteDrag.onTapStartNode = function (e) {
        if (e.cyTarget.selected())
            draggedNodes = e.cy.$(":selected");
        else
            draggedNodes = e.cyTarget;

        startPos = e.cyPosition;

        attachedNode = e.cyTarget;
        attachedNode.lock();
        attachedNode.trigger("grab");
        cy.on("tapdrag", onTapDrag);
        cy.on("tapend", onTapEndNode);

    };

    var onTapEndNode = function (e) {
        //attachedNode.trigger("free");
        cy.off("tapdrag", onTapDrag);
        cy.off("tapend", onTapEndNode);
        attachedNode.unlock();
        e.preventDefault();
    };

    var getDist = function () {
        return {
            x: endPos.x - startPos.x,
            y: endPos.y - startPos.y
        }
    };

    function getTopMostNodes(nodes) {
        var nodesMap = {};

        for (var i = 0; i < nodes.length; i++) {
            nodesMap[nodes[i].id()] = true;
        }

        var roots = nodes.filter(function (i, ele) {
            var parent = ele.parent()[0];
            while (parent != null) {
                if (nodesMap[parent.id()]) {
                    return false;
                }
                parent = parent.parent()[0];
            }
            return true;
        });

        return roots;
    }

    var moveNodesTopDown = function (nodes, dx, dy) {

/*
        console.log(nodes.map(function (e) {
            return e.id();
        }));
        for (var i = 0; i < nodes.length; i++) {
            var node = nodes[i];
            var pos = node.position();
            if (!node.isParent()) {
                node.position({
                    x: pos.x + dx,
                    y: pos.y + dy
                });
                console.log(node.id() + " " + dx + " " + dy);
            }
            moveNodesTopDown(nodes.children(), dx, dy);
        }
*/
    };

    var onTapDrag = function (e) {

        var nodePos = attachedNode.position();
        endPos = e.cyPosition;
        endPos = snap.snapPos(endPos);
        var dist = getDist();
        if (dist.x != 0 || dist.y != 0) {
            attachedNode.unlock();
            //var topMostNodes = getTopMostNodes(draggedNodes);
            var nodes = draggedNodes.union(draggedNodes.descendants());

            nodes.positions(function (i, node) {
                var pos = node.position();
                return snap.snapPos({
                    x: pos.x + dist.x,
                    y: pos.y + dist.y
                });
            });

            startPos = endPos;
            attachedNode.lock();
            attachedNode.trigger("drag");
        }

    };

    return discreteDrag;


};
},{}],4:[function(require,module,exports){
module.exports = function (opts, cy, $, debounce) {

    var options = opts;

    var changeOptions = function (opts) {
      options = opts;
    };


    var $canvas = $( '<canvas></canvas>' );
    var $container = $( cy.container() );
    var ctx = $canvas[ 0 ].getContext( '2d' );
    $container.append( $canvas );

    var drawGrid = function() {
        clearDrawing();

        var zoom = cy.zoom();
        var canvasWidth = $container.width();
        var canvasHeight = $container.height();
        var increment = options.gridSpacing*zoom;
        var pan = cy.pan();
        var initialValueX = pan.x%increment;
        var initialValueY = pan.y%increment;

        ctx.strokeStyle = options.strokeStyle;
        ctx.lineWidth = options.lineWidth;

        if(options.zoomDash) {
            var zoomedDash = options.lineDash.slice();

            for(var i = 0; i < zoomedDash.length; i++) {
                zoomedDash[ i ] = options.lineDash[ i ]*zoom;
            }
            ctx.setLineDash( zoomedDash );
        } else {
            ctx.setLineDash( options.lineDash );
        }

        if(options.panGrid) {
            ctx.lineDashOffset = -pan.y;
        } else {
            ctx.lineDashOffset = 0;
        }

        for(var i = initialValueX; i < canvasWidth; i += increment) {
            ctx.beginPath();
            ctx.moveTo( i, 0 );
            ctx.lineTo( i, canvasHeight );
            ctx.stroke();
        }

        if(options.panGrid) {
            ctx.lineDashOffset = -pan.x;
        } else {
            ctx.lineDashOffset = 0;
        }

        for(var i = initialValueY; i < canvasHeight; i += increment) {
            ctx.beginPath();
            ctx.moveTo( 0, i );
            ctx.lineTo( canvasWidth, i );
            ctx.stroke();
        }
    };
    var clearDrawing = function() {
        var width = $container.width();
        var height = $container.height();

        ctx.clearRect( 0, 0, width, height );
    };

    var resizeCanvas = debounce(function() {
            $canvas
                .attr( 'height', $container.height() )
                .attr( 'width', $container.width() )
                .css( {
                    'position': 'absolute',
                    'top': 0,
                    'left': 0,
                    'z-index': options.gridStackOrder
                } );

            setTimeout( function() {
                var canvasBb = $canvas.offset();
                var containerBb = $container.offset();

                console.log(canvasBb, containerBb);
                $canvas
                    .attr( 'height', $container.height() )
                    .attr( 'width', $container.width() )
                    .css( {
                        'top': -( canvasBb.top - containerBb.top ),
                        'left': -( canvasBb.left - containerBb.left )
                    } );
                drawGrid();
            }, 0 );

    }, 250);




    return {
        initCanvas: resizeCanvas,
        resizeCanvas: resizeCanvas,
        clearCanvas: clearDrawing,
        drawGrid: drawGrid,
        changeOptions: changeOptions,
        sizeCanvas: drawGrid
    };
};
},{}],5:[function(require,module,exports){
module.exports = function (cy, snap, resize, discreteDrag, drawGrid, guidelines, parentPadding, $) {

    var feature = function (func) {
        return function (enable) {
            func(enable);
        };
    };

    var controller = {
        discreteDrag: new feature(setDiscreteDrag),
        resize: new feature(setResize),
        snapToGrid: new feature(setSnapToGrid),
        drawGrid: new feature(setDrawGrid),
        guidelines: new feature(setGuidelines),
        parentPadding: new feature(setParentPadding)
    };

    function applyToCyTarget(func, allowParent) {
        return function (e) {
            if (!e.cyTarget.is(":parent") || allowParent)
                func(e.cyTarget);
        }
    }

    function applyToActiveNodes(func, allowParent) {
        return function (e) {
            if (!e.cyTarget.is(":parent") || allowParent)
                if (e.cyTarget.selected())
                    func(e.cyTarget, e.cy.$(":selected"));
                else
                    func(e.cyTarget, e.cyTarget);
        }
    }

    function applyToAllNodesButNoParent(func) {
        return function () {
            cy.nodes().not(":parent").each(function (i, ele) {
                func(ele);
            });
        };
    }
    function applyToAllNodes(func) {
        return function () {
            cy.nodes().each(function (i, ele) {
                func(ele);
            });
        };
    }

    function eventStatus(enable) {
        return enable ? "on" : "off";
    }


    // Discrete Drag
    function setDiscreteDrag(enable) {
        cy[eventStatus(enable)]("tapstart", "node", discreteDrag.onTapStartNode);
    }

    // Resize
    var resizeAllNodes = applyToAllNodesButNoParent(resize.resizeNode);
    var resizeNode = applyToCyTarget(resize.resizeNode);
    var recoverAllNodeDimensions = applyToAllNodesButNoParent(resize.recoverNodeDimensions);

    function setResize(enable) {
        cy[eventStatus(enable)]("ready", resizeAllNodes);
      //  cy[eventStatus(enable)]("style", "node", resizeNode);
        enable ? resizeAllNodes() : recoverAllNodeDimensions();
    }

    // Snap To Grid
    var snapAllNodes = applyToAllNodes(snap.snapNodesTopDown);
    var recoverSnapAllNodes = applyToAllNodes(snap.recoverSnapNode);
    var snapCyTarget = applyToCyTarget(snap.snapNode, true);

    function setSnapToGrid(enable) {
        cy[eventStatus(enable)]("add", "node", snapCyTarget);
        cy[eventStatus(enable)]("ready", snapAllNodes);

        cy[eventStatus(enable)]("free", "node", snap.onFreeNode);

        if (enable) {
            snapAllNodes();
        } else {
            recoverSnapAllNodes();
        }
    }

    // Draw Grid
    var drawGridOnZoom = function () {
        if (currentOptions.zoomDash) drawGrid.drawGrid()
    };
    var drawGridOnPan = function () {
        if (currentOptions.panGrid) drawGrid.drawGrid()
    };

    function setDrawGrid(enable) {
        cy[eventStatus(enable)]('zoom', drawGridOnZoom);
        cy[eventStatus(enable)]('pan', drawGridOnPan);
        cy[eventStatus(enable)]('ready', drawGrid.resizeCanvas);

        if (enable) {
            drawGrid.initCanvas();
            $(window).on('resize', drawGrid.resizeCanvas);
        } else {
            drawGrid.clearCanvas();
            $(window).off('resize', drawGrid.resizeCanvas);
        }
    }

    // Guidelines

    function setGuidelines(enable) {
        cy[eventStatus(enable)]('zoom', guidelines.onZoom);
        cy[eventStatus(enable)]('drag', "node", guidelines.onDragNode);
        cy[eventStatus(enable)]('grab', "node", guidelines.onGrabNode);
        cy[eventStatus(enable)]('free', "node", guidelines.onFreeNode);

        if (enable) {
            $(window).on('resize', guidelines.resizeCanvas);
        } else {
            $(window).off('resize', guidelines.resizeCanvas);
        }
    }

    // Parent Padding
    var setAllParentPaddings = function (enable) {
        parentPadding.setPaddingOfParent(cy.nodes(":parent"), enable);
    };
    var enableParentPadding = function (node) {
        parentPadding.setPaddingOfParent(node, true);
    };


    function setParentPadding(enable) {

        setAllParentPaddings(enable);

        cy[eventStatus(enable)]('ready', setAllParentPaddings);
        cy[eventStatus(enable)]("add", "node:parent", applyToCyTarget(enableParentPadding, true));
    }

    // Sync with options: Enables/disables changed via options.
    var latestOptions = {};
    var currentOptions;

    var specialOpts = {
        drawGrid: ["gridSpacing", "zoomDash", "panGrid", "gridStackOrder", "strokeStyle", "lineWidth", "lineDash"],
        guidelines: ["gridSpacing", "guidelinesStackOrder", "guidelinesTolerance", "guidelinesStyle"],
        resize: ["gridSpacing"],
        parentPadding: ["gridSpacing", "parentSpacing"],
        snapToGrid: ["gridSpacing"]
    };

    function syncWithOptions(options) {
        currentOptions = $.extend(true, {}, options);
        for (var key in options)
            if (latestOptions[key] != options[key])
                if (controller.hasOwnProperty(key)) {
                    controller[key](options[key]);
                } else {
                    for (var optsKey in specialOpts) {
                        var opts = specialOpts[optsKey];
                        if (opts.indexOf(key) >= 0) {
                            if(optsKey == "drawGrid") {
                                drawGrid.changeOptions(options);
                                if (options.drawGrid)
                                    drawGrid.resizeCanvas();
                            }

                            if (optsKey == "snapToGrid"){
                                snap.changeOptions(options);
                                if (options.snapToGrid)
                                    snapAllNodes();
                            }

                            if(optsKey == "guidelines")
                                guidelines.changeOptions(options);

                            if (optsKey == "resize") {
                                resize.changeOptions(options);
                                if (options.resize)
                                    resizeAllNodes();
                            }

                            if (optsKey == "parentPadding")
                                parentPadding.changeOptions(options);

                                
                        }
                    }
                }
        latestOptions = $.extend(true, latestOptions, options);
    }

    return {
        init: syncWithOptions,
        syncWithOptions: syncWithOptions
    };

};

},{}],6:[function(require,module,exports){
module.exports = function (opts, cy, $, debounce) {

    var options = opts;

    var changeOptions = function (opts) {
        options = opts;
    };

    function calcDistance(p1, p2) {
        return Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
    }
    
    function getExtraDim(node, paddingDim) {

    }

    var dims = function (node) {

        var pos = node.renderedPosition();
        var width = node.renderedWidth();
        var height = node.renderedHeight();
        var padding = {
            left: Number(node.renderedStyle("padding-left").replace("px", "")),
            right: Number(node.renderedStyle("padding-right").replace("px", "")),
            top: Number(node.renderedStyle("padding-top").replace("px", "")),
            bottom: Number(node.renderedStyle("padding-bottom").replace("px", ""))
        };

        this.horizontal = {
            center: pos.x,
            left: pos.x - (padding.left + width / 2),
            right: pos.x + (padding.right + width / 2)
        };

        this.vertical = {
            center: pos.y,
            top: pos.y - (padding.top + height / 2),
            bottom: pos.y + (padding.bottom + height / 2)
        };

        return this;
    };

    var $canvas = $('<canvas></canvas>');
    var $container = $(cy.container());
    var ctx = $canvas[0].getContext('2d');
    $container.append($canvas);

    $canvas
        .attr('height', $container.height())
        .attr('width', $container.width())
        .css({
            'position': 'absolute',
            'top': 0,
            'left': 0,
            'z-index': options.guidelinesStackOrder
        });

    var canvasBb = $canvas.offset();
    var containerBb = $container.offset();

    $canvas
        .attr( 'height', $container.height() )
        .attr( 'width', $container.width() )
        .css( {
            'top': -( canvasBb.top - containerBb.top ),
            'left': -( canvasBb.left - containerBb.left )
        } );
    var clearDrawing = function () {
        var width = $container.width();
        var height = $container.height();

        ctx.clearRect(0, 0, width, height);
    };


    var pickedNode;

    function onGrabNode(e) {
        pickedNode = e.cyTarget;
        onDragNode(e);
    }

    var onDragNode = debounce(function(e) {
        if (pickedNode) {
            var node = pickedNode;

            var mainDims = new dims(node);

            var cy = e.cy;
            var nearests = {
                horizontal: {
                    distance: Number.MAX_VALUE
                },
                vertical: {
                    distance: Number.MAX_VALUE
                }
            };

            cy.nodes(":visible").not(node.ancestors()).not(node.descendants()).not(node).each(function (i, ele) {
                var nodeDims = new dims(ele);


                for (var dim in mainDims) {
                    var mainDim = mainDims[dim];
                    var nodeDim = nodeDims[dim];
                    var otherDim = dim == "horizontal" ? "y" : "x";
                    var eitherDim = otherDim == "x" ? "y" : "x";
                    for (var key in mainDim) {
                        for (var key2 in nodeDim) {
                            if (Math.abs(mainDim[key] - nodeDim[key2]) < options.guidelinesTolerance) {
                                var distance = calcDistance(node.renderedPosition(), ele.renderedPosition());
                                if (nearests[dim].distance > distance) {

                                    nearests[dim] = {
                                        to: ele.id(),
                                        toPos: {},
                                        from: node.id(),
                                        fromPos: {},
                                        distance: distance
                                    };
                                    nearests[dim].fromPos[eitherDim] = mainDim[key];
                                    nearests[dim].fromPos[otherDim] = node.renderedPosition(otherDim);
                                    nearests[dim].toPos[eitherDim] = nodeDim[key2];
                                    nearests[dim].toPos[otherDim] = ele.renderedPosition(otherDim);
                                }
                            }
                        }
                    }
                }
            });

            clearDrawing();
            for (var key in nearests) {
                var item = nearests[key];
                if (item.from) {
                    ctx.beginPath();
                    ctx.moveTo(item.fromPos.x, item.fromPos.y);
                    ctx.lineTo(item.toPos.x, item.toPos.y);

                    ctx.setLineDash(options.guidelinesStyle.lineDash);
                    for (var styleKey in options.guidelinesStyle)
                        ctx[styleKey] = options.guidelinesStyle[styleKey];

                    ctx.stroke();
                }
            }

        }
    }, 0, true);

    function onFreeNode() {
        pickedNode = undefined;
        clearDrawing();
    }
    var resizeCanvas = debounce(function() {
	    $canvas
	    .attr( 'height', $container.height() )
	    .attr( 'width', $container.width() )
	    .css( {
		    'position': 'absolute',
		    'top': 0,
		    'left': 0,
		    'z-index': options.guidelinesStackOrder
	    } );

	    setTimeout( function() {
		    var canvasBb = $canvas.offset();
		    var containerBb = $container.offset();

		    $canvas
		    .attr( 'height', $container.height() )
		    .attr( 'width', $container.width() )
		    .css( {
			    'top': -( canvasBb.top - containerBb.top ),
			    'left': -( canvasBb.left - containerBb.left )
		    } );
	    }, 0 );

    }, 250);

    resizeCanvas();

    return {
	    onDragNode: onDragNode,
		    onZoom: onDragNode,
		    onGrabNode: onGrabNode,
		    onFreeNode: onFreeNode,
		    changeOptions: changeOptions,
		    resizeCanvas: resizeCanvas
    }

};

},{}],7:[function(require,module,exports){
;(function(){ 'use strict';

    // registers the extension on a cytoscape lib ref
    var register = function( cytoscape ){

        if( !cytoscape ){ return; } // can't register if cytoscape unspecified


        var options = {
            // On/Off Modules
            snapToGrid: true, // Snap to grid functionality
            discreteDrag: true, // Discrete Drag
            guidelines: true, // Guidelines on dragging nodes
            resize: true, // Adjust node sizes to cell sizes
            parentPadding: true, // Adjust parent sizes to cell sizes by padding
            drawGrid: true, // Draw grid background

            // Other settings

            // General
            gridSpacing: 20, // Distance between the lines of the grid.

            // Draw Grid
            zoomDash: true, // Determines whether the size of the dashes should change when the drawing is zoomed in and out if grid is drawn.
            panGrid: true, // Determines whether the grid should move then the user moves the graph if grid is drawn.
            gridStackOrder: -1, // Namely z-index
            strokeStyle: '#dedede', // Color of grid lines
            lineWidth: 1.0, // Width of grid lines
            lineDash: [2.5, 4], // Defines style of dash. Read: https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/setLineDash

            // Guidelines
            guidelinesStackOrder: 4, // z-index of guidelines
            guidelinesTolerance: 2.00, // Tolerance distance for rendered positions of nodes' interaction.
            guidelinesStyle: { // Set ctx properties of line. Properties are here:
                strokeStyle: "#8b7d6b",
                lineDash: [3, 5]
            },

            // Parent Padding
            parentSpacing: -1 // -1 to set paddings of parents to gridSpacing
        };

        var _snap = require("./snap");
        var _discreteDrag = require("./discrete_drag");
        var _drawGrid = require("./draw_grid");
        var _resize = require("./resize");
        var _eventsController = require("./events_controller");
        var _guidelines = require("./guidelines");
        var _parentPadding = require("./parentPadding");
        var _alignment = require("./alignment");
        var debounce = require("./debounce");
        var snap, resize, discreteDrag, drawGrid, eventsController, guidelines, parentPadding, alignment;

        function getScratch(cy) {
            if (!cy.scratch("_gridGuide")) {
                cy.scratch("_gridGuide", { });

            }
            return cy.scratch("_gridGuide");
        }

        cytoscape( 'core', 'gridGuide', function(opts){
            var cy = this;
            $.extend(true, options, opts);

            if (!getScratch(cy).initialized) {
                snap = _snap(cy, options.gridSpacing);
                resize = _resize(options.gridSpacing);
                discreteDrag = _discreteDrag(cy, snap);
                drawGrid = _drawGrid(options, cy, $, debounce);
                guidelines = _guidelines(options, cy, $, debounce);
                parentPadding = _parentPadding(options, cy);

                eventsController = _eventsController(cy, snap, resize, discreteDrag, drawGrid, guidelines, parentPadding, $);

                alignment = _alignment(cytoscape, cy, $);

                eventsController.init(options);
                getScratch(cy).initialized = true;
            } else
                eventsController.syncWithOptions(options);


            return this; // chainability
        } ) ;


    };

    if( typeof module !== 'undefined' && module.exports ){ // expose as a commonjs module
        module.exports = register;
    }

    if( typeof define !== 'undefined' && define.amd ){ // expose as an amd/requirejs module
        define('cytoscape-grid-guide', function(){
            return register;
        });
    }

    if( typeof cytoscape !== 'undefined' ){ // expose to global cytoscape (i.e. window.cytoscape)
        register( cytoscape );
    }

})();

},{"./alignment":1,"./debounce":2,"./discrete_drag":3,"./draw_grid":4,"./events_controller":5,"./guidelines":6,"./parentPadding":8,"./resize":9,"./snap":10}],8:[function(require,module,exports){
module.exports = function (opts, cy) {

    var options = opts;
    var ppClass = "_gridParentPadding";

    function initPadding() {
        var padding = options.parentSpacing < 0 ? options.gridSpacing : options.parentSpacing;
        cy.style()
            .selector('.' + ppClass)
            .style("compound-sizing-wrt-labels", "exclude")
            .style("padding-left", padding)
            .style("padding-right", padding)
            .style("padding-top", padding)
            .style("padding-bottom", padding)
            .update();

    }

    function changeOptions(opts) {
        options = opts;
        padding = options.parentSpacing < 0 ? options.gridSpacing : options.parentSpacing;
        initPadding();
    }

    function setPaddingOfParent(node, enable) {
        if (enable)
            node.addClass(ppClass);
        else
            node.removeClass(ppClass);
    }

    return {
        changeOptions: changeOptions,
        setPaddingOfParent: setPaddingOfParent
    };
};
},{}],9:[function(require,module,exports){
module.exports = function (gridSpacing) {


    var changeOptions = function (opts) {
        gridSpacing = Number(opts.gridSpacing);
    };

    var getScratch = function (node) {
        if (!node.scratch("_gridGuide"))
            node.scratch("_gridGuide", {});

        return node.scratch("_gridGuide");
    };

    function resizeNode(node) {
        var width = node.width();
        var height = node.height();

        var newWidth = Math.round((width - gridSpacing) / (gridSpacing * 2)) * (gridSpacing * 2);
        var newHeight = Math.round((height - gridSpacing) / (gridSpacing * 2)) * (gridSpacing * 2);
        newWidth = newWidth > 0 ? newWidth + gridSpacing : gridSpacing;
        newHeight = newHeight > 0 ? newHeight + gridSpacing : gridSpacing;

        if (width != newWidth || height != newHeight) {
            node.style({
                "width": newWidth,
                "height": newHeight
            });
            getScratch(node).resize = {
                oldWidth: width,
                oldHeight: height
            };
        }
    }

    function recoverNodeDimensions(node) {
        var oldSizes = getScratch(node).resize;
        if (oldSizes) 
            node.style({
                "width": oldSizes.oldWidth,
                "height": oldSizes.oldHeight
            });


    }


    return {
        resizeNode: resizeNode,
        recoverNodeDimensions: recoverNodeDimensions,
        changeOptions: changeOptions
    };

};
},{}],10:[function(require,module,exports){
module.exports = function (cy, gridSpacing) {

    var snap = { };

    snap.changeOptions = function (opts) {
        gridSpacing = opts.gridSpacing;
    };

    var getScratch = function (node) {
        if (!node.scratch("_gridGuide"))
            node.scratch("_gridGuide", {});

        return node.scratch("_gridGuide");
    };


    function getTopMostNodes(nodes) {
        var nodesMap = {};

        for (var i = 0; i < nodes.length; i++) {
            nodesMap[nodes[i].id()] = true;
        }

        var roots = nodes.filter(function (i, ele) {
            var parent = ele.parent()[0];
            while(parent != null){
                if(nodesMap[parent.id()]){
                    return false;
                }
                parent = parent.parent()[0];
            }
            return true;
        });

        return roots;
    }

    snap.snapPos = function (pos) {
        var newPos = {
            x: (Math.floor(pos.x / gridSpacing) + 0.5) * gridSpacing,
            y: (Math.floor(pos.y / gridSpacing) + 0.5) * gridSpacing
        };

        return newPos;
    };

    snap.snapNode = function (node) {

        var pos = node.position();
        var newPos = snap.snapPos(pos);

        node.position(newPos);
    };

    function snapTopDown(nodes) {

        nodes.union(nodes.descendants()).positions(function (i, node) {
            var pos = node.position();
            return snap.snapPos(pos);
        });
        /*
        for (var i = 0; i < nodes.length; i++) {
            if (!nodes[i].isParent())
                snap.snapNode(nodes[i]);
            snapTopDown(nodes.children());
        }*/

    }

    snap.snapNodesTopDown = function (nodes) {
        // getTOpMostNodes -> nodes
        cy.startBatch();
        nodes.union(nodes.descendants()).positions(function (i, node) {
            var pos = node.position();
            return snap.snapPos(pos);
        });
        cy.endBatch();
    };

    snap.onFreeNode = function (e) {
        var nodes;
        if (e.cyTarget.selected())
            nodes = e.cy.$(":selected");
        else
            nodes = e.cyTarget;

        snap.snapNodesTopDown(nodes);

    };


    snap.recoverSnapNode = function (node) {
        var snapScratch = getScratch(node).snap;
        if (snapScratch) {
            node.position(snapScratch.oldPos);
        }
    };

    return snap;





};
},{}]},{},[7]);