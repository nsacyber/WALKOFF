$(function(){
    var xData = ['xData',0];
    var data1 = ['data1',0];
    var data2 = ['data2',0];
    var xmin=0;
    var range=10;
    var on = false;

    var chart1 = c3.generate({
        bindto: '#chart1',
        data: {
            x: 'xData',
            columns: [
                xData, data1, data2
            ]
        },
        grid: {
            x: {
                show: true
            },
            y: {
                show: true
            }
        },
        axis: {
            y: {
                label: {
                text: 'Magnitude',
                position: 'outer-middle'
                },
            },
            x: {
                tick: {
                  culling: false
                }
            }
        }
    });


    var sse1 = new EventSource('apps/HelloWorld/testWidget/stream/counter');
    var sse2 = new EventSource('apps/HelloWorld/testWidget/stream/data-1');
    var sse3 = new EventSource('apps/HelloWorld/testWidget/stream/data-2');
    sse1.onmessage = function(message) {
        xData.push(message.data)
    }
    sse1.onerror = function(){
        sse1.close();
        sse2.close();
        sse3.close();
        $("#toggleStreamButton").text("Stream Closed");
        $("#toggleStreamButton").prop("disabled",true);
    }



    sse2.onmessage = function(message) {
        data1.push(message.data);
    }
    sse2.onerror = function(){
        sse1.close();
        sse2.close();
        sse3.close();
        $("#toggleStreamButton").text("Stream Closed");
        $("#toggleStreamButton").prop("disabled",true);
    }



    sse3.onmessage = function(message) {
        data2.push(message.data);
    }
    sse3.onerror = function(){
        sse1.close();
        sse2.close();
        sse3.close();
        $("#toggleStreamButton").text("Stream Closed");
        $("#toggleStreamButton").prop("disabled",true);
    }

    $("#toggleStreamButton").on("click", function(){
            if(on){
                on = false;
                $("#toggleStreamButton").text("Turn Stream On");
                sse1.close();
                sse2.close();
                sse3.close();
            }else{
                on = true;
                $("#toggleStreamButton").text("Turn Stream Off");
                sse1 = new EventSource('apps/HelloWorld/testWidget/stream/counter');
                sse2 = new EventSource('apps/HelloWorld/testWidget/stream/data-1');
                sse3 = new EventSource('apps/HelloWorld/testWidget/stream/data-2');
            }

    });


    setInterval(function () {
        if(on){
            forward = 0
            if(xmin < xData.length){
                forward = 1
                chart1.axis.range({max: {x: xmin+range}, min: {x: xmin}});
                xmin +=1;
                chart1.flow({
                    columns: [
                        xData,data1,data2
                    ],
                    length: forward
                });
            }


        }
    }, 1000);

    $("#contentWrapper").on("remove", function(){
        sse1.close();
        sse2.close();
        sse3.close();
    });

});
