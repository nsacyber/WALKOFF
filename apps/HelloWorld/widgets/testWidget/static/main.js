x = ['x',0];
data1 = ['data1',0];
data2 = ['data2',0];
xmin=0;
range=5;
on = false;

var chart1 = c3.generate({
    bindto: '#chart1',
    data: {
        x: 'x',
        columns: [
            x, data1, data2
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
            min: xmin,
            max: xmin+range,
            tick: {
              culling: false
            }
        }
    }
});


sse1 = new EventSource('apps/HelloWorld/testWidget/stream/counter');
sse1.onmessage = function(message) {
    x.push(message.data)
}



sse2 = new EventSource('apps/HelloWorld/testWidget/stream/data-1');
sse2.onmessage = function(message) {
    data1.push(message.data);
}



sse3 = new EventSource('apps/HelloWorld/testWidget/stream/data-2');
sse3.onmessage = function(message) {
    data2.push(message.data);
}

$("#toggleStreamButton").on("click", function(){
        if(on){
            on = false;
            $("#toggleStreamButton").text("Turn Stream On");
        }else{
            on = true;
            $("#toggleStreamButton").text("Turn Stream Off");
        }

});


setInterval(function () {
    if(on){
        chart1.axis.range({max: {x: xmin+range}, min: {x: xmin}});
        forward = 0
        if(xmin < x.length){
            forward = 1
            xmin +=1;
            chart1.flow({
                columns: [
                    x,data1,data2
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


