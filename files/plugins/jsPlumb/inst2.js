jsPlumb.ready(function () {

    var instance = window.jsp = jsPlumb.getInstance({
        // default drag options
        DragOptions: { cursor: 'pointer', zIndex: 2000 },
        // the overlays to decorate each connection with.  note that the label overlay uses a function to generate the label text; in this
        // case it returns the 'labelText' member that we set on each connection in the 'init' method below.
        ConnectionOverlays: [
            [ "Arrow", {
                location: 1,
                visible:true,
                id:"ARROW",
                events:{
                    click:function() {$("#dialog").dialog('open');}
                }
            } ],
            [ "Label", {
                //label: "NEW ACTION",
                location: 0.1,
                id: "label",
                cssClass: "aLabel",
                events:{
                    tap:function() {$("#dialog").dialog('open');}
                }
            }]
        ],
        editable: true,
        Container: "canvas"
    });

    var basicType = {
        connector: "StateMachine",
        paintStyle: { strokeStyle: "red", lineWidth: 4 },
        hoverPaintStyle: { strokeStyle: "blue" },
        overlays: [
            "Arrow"
        ]
    };
    instance.registerConnectionType("basic", basicType);

    // this is the paint style for the connecting lines..
    var connectorPaintStyle = {
            lineWidth: 3,
            strokeStyle: "#5c96bc",
            joinstyle: "round",
            outlineColor: "white",
            outlineWidth: 1
        },
    // .. and this is the hover style.
        connectorHoverStyle = {
            lineWidth: 3,
            strokeStyle: "#7eb62f",
            outlineWidth: 2,
            outlineColor: "white"
        },
        endpointHoverStyle = {
            fillStyle: "#7eb62f",
            strokeStyle: "#7eb62f"
        },
    // the definition of source endpoints (the small blue ones)
        sourceEndpoint = {
            endpoint: "Dot",
            paintStyle: {
                strokeStyle: "#7AB02C",
                fillStyle: "transparent",
                radius: 5,
                lineWidth: 3
            },
            isSource: true,
            connector: [ "Flowchart", { stub: [40, 60], gap: 10, cornerRadius: 5, alwaysRespectStubs: true } ],
            connectorStyle: connectorPaintStyle,
            hoverPaintStyle: endpointHoverStyle,
            connectorHoverStyle: connectorHoverStyle,
            dragOptions: {},
            overlays: [
                [ "Label", {
                    location: [0.5, 1.5],
                    label: "Drag",
                    cssClass: "endpointSourceLabel",
                    visible:false
                } ]
            ]
        },
    // the definition of target endpoints (will appear when the user drags a connection)
        targetEndpoint = {
            endpoint: "Dot",
            paintStyle: { fillStyle: "#7AB02C", radius: 5 },
            hoverPaintStyle: endpointHoverStyle,
            maxConnections: -1,
            dropOptions: { hoverClass: "hover", activeClass: "active" },
            isTarget: true,
            overlays: [
                [ "Label", { location: [0.5, -0.5], label: "Drop", cssClass: "endpointTargetLabel", visible:false } ]
            ]
        },
        init = function (connection) {
            //console.log(connection.getOverlay("label").labelText);
            if (connection.isEditable()){
              var label = prompt("Does this flow have a condition?", "True, False, None");
              connection.getOverlay("label").setLabel(label);
            }
            //console.log('Connecting ' + connection.getOverlay("label"));
        };

    var _addEndpoints = function (toId, sourceAnchors, targetAnchors) {
        for (var i = 0; i < sourceAnchors.length; i++) {
            var sourceUUID = toId + sourceAnchors[i];
            instance.addEndpoint("flowchart" + toId, sourceEndpoint, {
                anchor: sourceAnchors[i], uuid: sourceUUID
            });
        }
        for (var j = 0; j < targetAnchors.length; j++) {
            var targetUUID = toId + targetAnchors[j];
            instance.addEndpoint("flowchart" + toId, targetEndpoint, { anchor: targetAnchors[j], uuid: targetUUID });
        }
    };

    function setnewOverlay(newConnection, newLabel){
      newConnection.addOverlay(
             ["Label",
             {label: newLabel,
             location: 0.1,
             cssClass: 'aLabel',
             events:{
                 tap:function() { $("#dialog").dialog('open');}
             }},
             true]
      );
    }
    // suspend drawing and initialise.
    instance.batch(function () {

        _addEndpoints("Window1", ["RightMiddle","TopCenter", "BottomCenter"], ["LeftMiddle"]);
        _addEndpoints("Window2", ["RightMiddle"], ["LeftMiddle","TopCenter", "BottomCenter"]);
        _addEndpoints("Window3", ["RightMiddle"], ["LeftMiddle","TopCenter", "BottomCenter"]);
        _addEndpoints("Window4", ["RightMiddle", "BottomCenter"], ["TopCenter", "LeftMiddle"]);
        _addEndpoints("Window5", ["RightMiddle", "BottomCenter"], ["TopCenter", "LeftMiddle"]);

        // listen for new connections; initialise them the same way we initialise the connections at startup.
        instance.bind("connection", function (connInfo, originalEvent) {
            init(connInfo.connection, null);
        });

        // make all the window divs draggable
        instance.draggable(jsPlumb.getSelector(".flowchart-demo .window"), { grid: [20, 20] });
        // THIS DEMO ONLY USES getSelector FOR CONVENIENCE. Use your library's appropriate selector
        // method, or document.querySelectorAll:
        //jsPlumb.draggable(document.querySelectorAll(".window"), { grid: [20, 20] });

        // connect a few up

        setnewOverlay(instance.connect({uuids: ["Window1TopCenter", "Window3TopCenter"], editable: false}),"YES");
        console.log("Connected First nodes.")
        setnewOverlay(instance.connect({uuids: ["Window1RightMiddle", "Window2LeftMiddle"], editable: false}), "NO");
        setnewOverlay(instance.connect({uuids: ["Window2RightMiddle", "Window3LeftMiddle"], editable: false}), "ACTION<br>COMPLETE");
        setnewOverlay(instance.connect({uuids: ["Window3RightMiddle", "Window4LeftMiddle"], editable: false}), "ACTION<br>COMPLETE");
        setnewOverlay(instance.connect({uuids: ["Window4RightMiddle", "Window5LeftMiddle"], editable: false}), "NO");

        //

        //
        // listen for clicks on connections, and offer to delete connections on click.
        //
        instance.bind("click", function (conn, originalEvent) {
           // if (confirm("Delete connection from " + conn.sourceId + " to " + conn.targetId + "?"))
             //   instance.detach(conn);
            //conn.toggleType("basic");
        });

        instance.bind("connectionDrag", function (connection) {
            console.log("connection " + connection.id + " is being dragged. suspendedElement is ", connection.suspendedElement, " of type ", connection.suspendedElementType);
        });

        instance.bind("connectionDragStop", function (connection) {
            console.log("connection " + connection.id + " was dragged");
        });

        instance.bind("connectionMoved", function (params) {
            console.log("connection " + params.connection.id + " was moved");
        });
    });

    jsPlumb.fire("jsPlumbDemoLoaded", instance);

});
