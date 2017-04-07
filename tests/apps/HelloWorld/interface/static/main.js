
//-----------------------------------------------------------------------------
// Chart #1
//-----------------------------------------------------------------------------

$(function(){
    var x = ['x'];
    var data1 = ['data1'];
    var data2 = ['data2'];

    var N = 100;
    for (var i=0;i<N; ++i) {
        x.push(i);
        data1.push(10*Math.random());
        data2.push(10*Math.random() + 12);
    }

    var xmin=0;
    var range=5;

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
                text: 'Cost',
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

    setInterval(function () {
        chart1.axis.range({max: {x: xmin+range}, min: {x: xmin}});
        xmin += 1;
        if (xmin > N-range)
            xmin = 0;
    }, 1000);
});


//-----------------------------------------------------------------------------
// Chart #2
//-----------------------------------------------------------------------------

$(function(){
    var N = 5;
    var x = ['data1'];
    for (var i=-N;i<=N; i+=0.2) {
        var val = Math.exp(-i*i/2) + 0.1*Math.random();
        x.push(val);
    }

    c3.generate({
         bindto: '#chart2',
        data: {
            columns: [
                x
            ],
            type: 'bar'
        },
        bar: {
            width: 5 // bar width in pixels
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
                    text: 'Size',
                    position: 'outer-middle'
                }
            }
        }
    });
});

//-----------------------------------------------------------------------------
// Chart #3
//-----------------------------------------------------------------------------

$(function(){
    var chart3 = c3.generate({
        bindto: '#chart3',
        data: {
            columns: [
                ['data1', 30],
                ['data2', 120],
                ['data3', 120],
            ],
            type : 'pie'
        },
        donut: {
            title: "Width"
        }
    });

    chart3.load({
        columns: [
            ["data1", 0.2, 0.2, 0.2, 0.2, 0.2, 0.4, 0.3, 0.2, 0.2, 0.1, 0.2, 0.2, 0.1, 0.1, 0.2, 0.4, 0.4, 0.3, 0.3, 0.3, 0.2, 0.4, 0.2, 0.5, 0.2, 0.2, 0.4, 0.2, 0.2, 0.2, 0.2, 0.4, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.2, 0.2, 0.3, 0.3, 0.2, 0.6, 0.4, 0.3, 0.2, 0.2, 0.2, 0.2],
            ["data2", 1.4, 1.5, 1.5, 1.3, 1.5, 1.3, 1.6, 1.0, 1.3, 1.4, 1.0, 1.5, 1.0, 1.4, 1.3, 1.4, 1.5, 1.0, 1.5, 1.1, 1.8, 1.3, 1.5, 1.2, 1.3, 1.4, 1.4, 1.7, 1.5, 1.0, 1.1, 1.0, 1.2, 1.6, 1.5, 1.6, 1.5, 1.3, 1.3, 1.3, 1.2, 1.4, 1.2, 1.0, 1.3, 1.2, 1.3, 1.3, 1.1, 1.3],
            ["data3", 2.5, 1.9, 2.1, 1.8, 2.2, 2.1, 1.7, 1.8, 1.8, 2.5, 2.0, 1.9, 2.1, 2.0, 2.4, 2.3, 1.8, 2.2, 2.3, 1.5, 2.3, 2.0, 2.0, 1.8, 2.1, 1.8, 1.8, 1.8, 2.1, 1.6, 1.9, 2.0, 2.2, 1.5, 1.4, 2.3, 2.4, 1.8, 1.8, 2.1, 2.4, 2.3, 1.9, 2.3, 2.5, 2.3, 1.9, 2.0, 2.3, 1.8],
        ]
    });
});


//-----------------------------------------------------------------------------
// Chart #4
//-----------------------------------------------------------------------------

$(function(){
    c3.generate({
        bindto: '#chart4',
        data: {
            columns: [
                ['data1', 30, 200, 100, 400, 150, 250],
                ['data2', 50, 20, 10, 40, 15, 25]
            ],
            axes: {
                data2: 'y2'
            },
            types: {
                data2: 'bar'
            }
        },
        axis: {
            y: {
                label: {
                    text: 'Y Label',
                    position: 'outer-middle'
                },
                tick: {
                    format: d3.format("$,")
                }
            },
            y2: {
                show: true,
                label: {
                    text: 'Y2 Label',
                    position: 'outer-middle'
                }
            }
        },
        grid: {
            x: {
                show: true
            },
            y: {
                show: true
            }
        },
        zoom: {
            enabled: false
        }
    });
});


//-----------------------------------------------------------------------------
// Chart #5
//-----------------------------------------------------------------------------
$(function(){
    $('#chart5').vectorMap({
        map: 'world_mill_en',
        normalizeFunction: 'polynomial',
        hoverOpacity: 0.7,
        hoverColor: false,
        backgroundColor: 'transparent',
        regionStyle: {
            initial: {
                fill: 'rgba(210, 214, 222, 1)',
                "fill-opacity": 1,
                stroke: 'none',
                "stroke-width": 0,
                "stroke-opacity": 1
            },
            hover: {
                "fill-opacity": 0.7,
                cursor: 'pointer'
            },
            selected: {
                fill: 'yellow'
            },
            selectedHover: {}
        },
        markerStyle: {
             initial: {
                fill: '#00a65a',
                stroke: '#111'
            }
        },
        markers: [
            {latLng: [41.90, 12.45], name: 'Vatican City'},
            {latLng: [43.73, 7.41], name: 'Monaco'},
            {latLng: [-0.52, 166.93], name: 'Nauru'},
            {latLng: [-8.51, 179.21], name: 'Tuvalu'},
            {latLng: [43.93, 12.46], name: 'San Marino'},
            {latLng: [47.14, 9.52], name: 'Liechtenstein'},
            {latLng: [7.11, 171.06], name: 'Marshall Islands'},
            {latLng: [17.3, -62.73], name: 'Saint Kitts and Nevis'},
            {latLng: [3.2, 73.22], name: 'Maldives'},
            {latLng: [35.88, 14.5], name: 'Malta'},
            {latLng: [12.05, -61.75], name: 'Grenada'},
            {latLng: [13.16, -61.23], name: 'Saint Vincent and the Grenadines'},
            {latLng: [13.16, -59.55], name: 'Barbados'},
            {latLng: [17.11, -61.85], name: 'Antigua and Barbuda'},
            {latLng: [-4.61, 55.45], name: 'Seychelles'},
            {latLng: [7.35, 134.46], name: 'Palau'},
            {latLng: [42.5, 1.51], name: 'Andorra'},
            {latLng: [14.01, -60.98], name: 'Saint Lucia'},
            {latLng: [6.91, 158.18], name: 'Federated States of Micronesia'},
            {latLng: [1.3, 103.8], name: 'Singapore'},
            {latLng: [1.46, 173.03], name: 'Kiribati'},
            {latLng: [-21.13, -175.2], name: 'Tonga'},
            {latLng: [15.3, -61.38], name: 'Dominica'},
            {latLng: [-20.2, 57.5], name: 'Mauritius'},
            {latLng: [26.02, 50.55], name: 'Bahrain'},
            {latLng: [0.33, 6.73], name: 'São Tomé and Príncipe'}
        ]
    });
});

$(function(){

})

$(function(){
    var sse1 = new EventSource('apps/HelloWorld/stream/counter');
    var sse2 = new EventSource('apps/HelloWorld/stream/random-number');

    var s = document.getElementById('counter_stream')
    sse1.onmessage = function(message) {
        s.innerHTML = '<li>'+message.data+'</li>'
    }
    sse1.onerror = function(){
        sse1.close();
        sse2.close();
    }

    var s = document.getElementById('rand_stream')
    sse2.onmessage = function(message) {
        s.innerHTML = '<li>'+message.data+'</li>'
    }
    sse2.onerror = function(){
        sse1.close();
        sse2.close();
    }
})