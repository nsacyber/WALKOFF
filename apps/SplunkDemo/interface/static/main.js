$(function () {
	const PROCESS_STEP_NAME = 'get process info';
	const FILE_STEP_NAME = 'stats';
	const APP_NAME = 'SplunkDemo';
	let authToken = sessionStorage.getItem('access_token');

	refreshJwtAjax({
		'async': false,
		'type': "GET",
		'global': false,
		'headers': { "Authorization": 'Bearer ' + sessionStorage.getItem('refresh_token') },
		'url': "/apps/" + APP_NAME + "/data",
		'success': function (data) {
			initPage(data);
		},
		'error': function (e) {
			console.log(e);
		}
	});

	function refreshJwtAjax(request) {
		if (!window.parent.JwtHelper.isTokenExpired(authToken, 300)) {
			$.ajax(request);
			return;
		}

		var refreshToken = sessionStorage.getItem('refresh_token');

		if (!refreshToken) location.href = '/login';

		$.ajax({
			'async': false,
			'type': "POST",
			'global': false,
			'headers': { "Authorization": 'Bearer ' + refreshToken },
			'url': "/api/auth/refresh",
			'success': function (data) {
				sessionStorage.setItem('access_token', data['access_token']);
				authToken = data['access_token'];
				request['headers']['Authorization'] = 'Bearer ' + authToken;
				$.ajax(request);
			},
			'error': function (e) {
				console.log(e);
			}
		});
	}

	function viewPCAP(pcap_name) {
		refreshJwtAjax({
			'async': false,
			'type': "GET",
			'global': false,
			'headers': { "Authorization": 'Bearer ' + sessionStorage.getItem('refresh_token') },
			'url': `/apps/${APP_NAME}/view_pcap`,
			'success': function (data) {
				console.log('Opening wireshark locally...');
			},
			'error': function (e) {
				console.log(e);
			}
		});
	}

	// let data = {
	// 	workflow_results: [{
	// 		timestamp: '2017-09-20 14:10:21.702320',
	// 		action: PROCESS_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'HELLO WORLD'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:15:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'remote',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'GOODBYE WORLD'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:25:21.702320',
	// 		action: 'some_action',
	// 		type: 'FAILURE',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'ERROR'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:30:21.702320',
	// 		action: 'some_other_action',
	// 		location: 'remote',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'some other result'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:45:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:45:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'FAILURE',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:50:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'remote',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'remote',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'remote',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	},
	// 	{
	// 		timestamp: '2017-09-20 14:55:21.702320',
	// 		action: FILE_STEP_NAME,
	// 		type: 'SUCCESS',
	// 		location: 'local',
	// 		result: "{u'result': {u'status': u'Success', u'result': {u'message': u'something else'}}}"
	// 	}],
	// 	source_ip: '165.257.22.34',
	// 	source_latitude: -31.32,
	// 	source_longitude: 23.32,
	// 	target_ip: '10.200.255.212',
	// 	target_latitude: 37.618889,
	// 	target_longitude: -122.375,
	// 	pcap_name: 'test.pcap',
	// 	exe_name: 'notavirus.py',
	// };

	// initPage(data);

	function initPage(data) {
		$('#source_ip').text(data.source_ip);
		$('#target_ip').text(data.target_ip);
		$('#pcap_link').text(data.pcap_name);
		$('#pcap_link').attr('href', 'apps/' + APP_NAME + '/data/' + data.pcap_name);
		$('#view_pcap_link').click(function () {
			viewPCAP(data.pcap_name);
		});
		$('#exe_link').text(data.exe_name);
		$('#exe_link').attr('href', 'apps/' + APP_NAME + '/data/' + data.exe_name);

		var map = new Datamap({
			element: document.getElementById('mapContainer'),
			fills: {
				defaultFill: "#333",
				source: '#C60000',
				target: '#477EFF'
			},
			geographyConfig: {
				highlightFillColor: 'rgb(221, 28, 119)',
				highlightBorderColor: 'white',
				highlightBorderWidth: 3,
			},
			bubblesConfig: {
				highlightFillColor: 'rgb(221, 28, 119)',
				highlightBorderColor: 'white',
				highlightBorderWidth: 3,
			}
		});

		map.bubbles(
			[
				{ name: 'Source IP: ' + data.source_ip, latitude: data.source_latitude, longitude: data.source_longitude, radius: 15, fillKey: 'source' },
				{ name: 'Target IP: ' + data.target_ip, latitude: data.target_latitude, longitude: data.target_longitude, radius: 15, fillKey: 'target' },
			],
			{
				popupTemplate: function (geo, data) {
					return "<div class='hoverinfo'>" + data.name + "</div>";
				}
			}
		);

		map.arc([
			{
				origin: {
					latitude: data.source_latitude,
					longitude: data.source_longitude
				},
				destination: {
					latitude: data.target_latitude,
					longitude: data.target_longitude
				}
			}
		]);

		let processResult = data.workflow_results.find(function (wr) {
			return wr.action === PROCESS_STEP_NAME;
		});
		let fileResult = data.workflow_results.find(function (wr) {
			return wr.action === FILE_STEP_NAME;
		});

		if (processResult) {
			// processResult.result = JSON.parse(processResult.result.replace(/u'/g, "'").replace(/'/g, '"')).result.result;
			Object.keys(processResult.result.result).forEach(function (key) {
				$('#processInformationTable > tbody:last-child').append('<tr><td>' + key + '</td><td>' + processResult.result.result[key] + '</td></tr>');
			});
		} 
		if (fileResult) {
			// fileResult.result = JSON.parse(fileResult.result.replace(/u'/g, "'").replace(/'/g, '"')).result.result;
			Object.keys(fileResult.result.result).forEach(function (key) {
				$('#fileInformationTable > tbody:last-child').append('<tr><td>' + key + '</td><td>' + fileResult.result.result[key] + '</td></tr>');
			});
		}

		///TIMELINE STUFF
		data.workflow_results.forEach(function (wr) {
			$('.timeline ol').append(
				`<li class="${wr.type !== 'SUCCESS' ? 'error' : ''} ${wr.location}">
					<div>
						<time>${wr.timestamp}</time>
						<span>${wr.app} - ${wr.action} <i>(${wr.location})</i></span>
					</div>
				</li>`
			);
		});

		// VARIABLES
		const timeline = document.querySelector(".timeline ol"),
			elH = document.querySelectorAll(".timeline li > div"),
			arrows = document.querySelectorAll(".timeline .arrows .arrow"),
			arrowPrev = document.querySelector(".timeline .arrows .arrow__prev"),
			arrowNext = document.querySelector(".timeline .arrows .arrow__next"),
			firstItem = document.querySelector(".timeline li:first-child"),
			lastItem = document.querySelector(".timeline li:last-child"),
			xScrolling = 280,
			disabledClass = "disabled";

		// START
		init();

		function init() {
			setEqualHeights(elH);
			animateTl(xScrolling, arrows, timeline);
			setKeyboardFn(arrowPrev, arrowNext);
		}

		// SET EQUAL HEIGHTS
		function setEqualHeights(el) {
			let counter = 0;
			for (let i = 0; i < el.length; i++) {
				const singleHeight = el[i].offsetHeight;

				if (counter < singleHeight) {
					counter = singleHeight;
				}
			}

			for (let i = 0; i < el.length; i++) {
				el[i].style.height = `${counter}px`;
			}
		}

		// CHECK IF AN ELEMENT IS IN VIEWPORT
		// http://stackoverflow.com/questions/123999/how-to-tell-if-a-dom-element-is-visible-in-the-current-viewport
		function isElementInViewport(el) {
			const rect = el.getBoundingClientRect();
			return (
				rect.top >= 0 &&
				rect.left >= 0 &&
				rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
				rect.right <= (window.innerWidth || document.documentElement.clientWidth)
			);
		}

		// SET STATE OF PREV/NEXT ARROWS
		function setBtnState(el, flag = true) {
			if (flag) {
				el.classList.add(disabledClass);
			} else {
				if (el.classList.contains(disabledClass)) {
					el.classList.remove(disabledClass);
				}
				el.disabled = false;
			}
		}

		// ANIMATE TIMELINE
		function animateTl(scrolling, el, tl) {
			let counter = 0;
			for (let i = 0; i < el.length; i++) {
				el[i].addEventListener("click", function () {
					if (!arrowPrev.disabled) {
						arrowPrev.disabled = true;
					}
					if (!arrowNext.disabled) {
						arrowNext.disabled = true;
					}
					const sign = (this.classList.contains("arrow__prev")) ? "" : "-";
					if (counter === 0) {
						tl.style.transform = `translateX(-${scrolling}px)`;
					} else {
						const tlStyle = getComputedStyle(tl);
						// add more browser prefixes if needed here
						const tlTransform = tlStyle.getPropertyValue("-webkit-transform") || tlStyle.getPropertyValue("transform");
						const values = parseInt(tlTransform.split(",")[4]) + parseInt(`${sign}${scrolling}`);
						tl.style.transform = `translateX(${values}px)`;
					}

					setTimeout(() => {
						isElementInViewport(firstItem) ? setBtnState(arrowPrev) : setBtnState(arrowPrev, false);
						isElementInViewport(lastItem) ? setBtnState(arrowNext) : setBtnState(arrowNext, false);
					}, 1100);

					counter++;
				});
			}
		}

		// ADD BASIC KEYBOARD FUNCTIONALITY
		function setKeyboardFn(prev, next) {
			document.addEventListener("keydown", (e) => {
				if ((e.which === 37) || (e.which === 39)) {
					const timelineOfTop = timeline.offsetTop;
					const y = window.pageYOffset;
					if (timelineOfTop !== y) {
						window.scrollTo(0, timelineOfTop);
					}
					if (e.which === 37) {
						prev.click();
					} else if (e.which === 39) {
						next.click();
					}
				}
			});
		}
	}
});