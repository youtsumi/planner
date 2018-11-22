if (! location.search.match(/\beventid=/)) {
	location.search = '?eventid=Click one "eventid" from "Event list"';
}

$.getJSON('processor.py' +  location.search, function(data) {
		var ary = data;
		var wak = "";
		for (i = 0; i < ary.length; i++) {
		wak += "<tr>";
		for (j = 0; j < ary[i].length; j++) {
		wak += "<td>" + ary[i][j] + "</td>";
		}
		wak += "</tr>";
		}
		$("#listbox").append('<table>' + wak + '</table>');
		var getUrlParameter = function getUrlParameter(sParam) {
		var sPageURL = decodeURIComponent(window.location.search.substring(1)),
		sURLVariables = sPageURL.split('&'),
		sParameterName,
		i;

		for (i = 0; i < sURLVariables.length; i++) {
		sParameterName = sURLVariables[i].split('=');

		if (sParameterName[0] === sParam) {
			return sParameterName[1] === undefined ? true : sParameterName[1];
		}
		}
		};
		var eventid = getUrlParameter('eventid');
		var mainhtml = "main.html";
		$('#normalh2').text(getUrlParameter('mode')+' : '+eventid);
		$('#candidates').attr('href', mainhtml+'?eventid=' + eventid + '&mode=candidate');
		$('#log').attr('href', mainhtml+'?eventid=' + eventid + '&mode=log');
		$('#event').attr('href', mainhtml+'?eventid=' + eventid + '&mode=event');
		$('#group').attr('href', mainhtml+'?eventid=' + eventid + '&mode=group');
		$('#admin').attr('href', mainhtml+'?eventid=' + eventid + '&mode=admin');
		$('#json').attr('href', 'processor.py?'+window.location.search.substring(1));
});

$(document).on('click', 'td', function() {
		var getUrlParameter = function getUrlParameter(sParam) {
		var sPageURL = decodeURIComponent(window.location.search.substring(1)),
		sURLVariables = sPageURL.split('&'),
		sParameterName,
		i;

		for (i = 0; i < sURLVariables.length; i++) {
		sParameterName = sURLVariables[i].split('=');

		if (sParameterName[0] === sParam) {
		return sParameterName[1] === undefined ? true : sParameterName[1];
		}
		}
		};

		var tr = $(this).closest('tr');
		var colIndex = tr.children().index(this);
		var table = $(this).closest('table');
		var header = table.find('tr').eq(0);
		var colName = header.children().eq(colIndex).text();
		var state = getUrlParameter('mode');
		if (colName == 'eventid') {
			var eventid = $(this).text();
			if ( state == 'admin' ) {
				var inserted = tr.children('td:eq(1)').text();
				location.search = (location.search + '&').replace(/\beventid=.*?&/, 'eventid=' + eventid + '&state=Ignore&inserted=' + inserted + '&' ).replace(/&&+/, '&').replace(/&$/, '');
			} else {
				location.search = (location.search + '&').replace(/\beventid=.*?&/, 'eventid=' + eventid + '&').replace(/&&+/, '&').replace(/&$/, '');
			}
		}
});


function disp(){
	var now = new Date();
	var watch1 = now.toUTCString();
	document.form1.field1.value = watch1;
	setTimeout("disp()", 1000);
}

