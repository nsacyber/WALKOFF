$(function(){
    var xData = ['xData','0'];
    var data1 = ['data1','0'];
    var data2 = ['data2','0'];
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
    var sse2 = new EventSource('apps/HelloWorld/testWidget/stream/random-number');
    sse1.onmessage = function(message) {

        xData.push(message.data)
        if(xData.length >= range){
          data2.splice(1, 1);
        }
    }
    sse1.onerror = function(){
        sse1.close();
        sse2.close();
        $("#toggleStreamButton").text("Stream Closed");
        $("#toggleStreamButton").prop("disabled",true);
    }



    sse2.onmessage = function(message) {

        data1.push(message.data);
        if(data1.length >= range){
            data2.splice(1, 1);
        }
    }
    sse2.onerror = function(){
        sse1.close();
        sse2.close();
        $("#toggleStreamButton").text("Stream Closed");
        $("#toggleStreamButton").prop("disabled",true);
    }

    setInterval(function () {
        if(on){
            forward = 0

            if(xmin < xData.length){
                data1 = data1.slice(0, xData.length);
                data2 = data2.slice(0, xData.length);
                console.log(xData.length, data1.length, data2.length, xmin);
                forward = 1;
                xmin +=1;
                chart1.axis.range({min: {x: xmin}, max: {x: xmin+range}});
                chart1.flow({
                    columns: [
                        xData,data1, data2
                    ],
                    length: forward,
                    done: function(){

                    }
                });
            }


        }
    }, 1000);

    $("#contentWrapper").on("remove", function(){
        sse1.close();
        sse2.close();
    });

});
