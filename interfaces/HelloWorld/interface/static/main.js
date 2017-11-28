$(function () {
    $.ajax({
       'async': false,
       'type': "GET",
       'global': false,
       'headers': { "Authorization": 'Bearer ' + sessionStorage.getItem('accessToken')},
       'url': "interfaces/HelloWorld/metrics",
       'success': function(data) {
            for (const action in data) {
                console.log(action)
                console.log(data[action])
                $('#results').append(`
                    <tr>
                        <td>${action}</td>
                        <td>${data[action]}</td>
                    </tr>
                `)
            }
       },
       'error': function(e) {
            console.log(e)
       }
    })
})