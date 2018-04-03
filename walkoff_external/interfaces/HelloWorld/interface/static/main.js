$(function () {
    $.ajax({
       'async': false,
       'type': "GET",
       'global': false,
       'headers': { "Authorization": 'Bearer ' + sessionStorage.getItem('access_token')},
       'url': "interfaces/HelloWorld/metrics",
       'success': function(data) {
            for (const action in data) {
                $('#results tbody').append(`
                    <tr>
                        <td>${action}</td>
                        <td>${data[action]}</td>
                    </tr>
                `);
            }
       },
       'error': function(e) {
            console.error(e);
       }
    });

    const eventSource = new EventSource('interfaces/HelloWorld/actionstream?access_token=' + sessionStorage.getItem('access_token'));

    function eventHandler(message) {
        let result = JSON.parse(message.data);
        
        $('#actionResults tbody').append(`
            <tr>
                <td>${result.sender_uid}</td>
                <td>${result.sender_name}</td>
                <td>${result.timestamp}</td>
                <td>${result.data.status}</td>
            </tr>
        `);
    }

    eventSource.addEventListener('action_success', eventHandler);
    eventSource.addEventListener('action_error', eventHandler);
    eventSource.addEventListener('error', (err) => {
        console.error(err);
    });
})