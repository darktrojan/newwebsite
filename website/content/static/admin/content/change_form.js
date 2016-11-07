/* globals Edit */
var textarea = document.querySelector('textarea');
textarea.style.marginLeft = '170px';
textarea.style.display = 'none';

var iframe = document.createElement('iframe');
iframe.style.width = '100%';
iframe.style.height = '80vh';
textarea.parentNode.insertBefore(iframe, textarea);

var richarea;
iframe.contentWindow.onload = function() {
	richarea = iframe.contentDocument.body;
	var link = document.createElement('link');
	link.rel = 'stylesheet';
	link.href = '/static/admin/content/iframe.css';
	link.type = 'text/css';
	iframe.contentDocument.head.appendChild(link);
	read_input();
	new Edit.EditArea(richarea);
};
if (iframe.contentDocument.readyState == 'complete') { // chrome
	iframe.contentWindow.onload();
}


textarea.form.onsubmit = function() {
	write_output();
};

Edit.linkCallback = function() {
	return '/media/files/Above_Gotham.jpg';
};

function read_input() {
	var div = document.createElement('div');
	div.innerHTML = textarea.value;

	// Sanitise here.

	richarea.innerHTML = '';
	while (div.firstChild) {
		richarea.appendChild(div.firstChild);
	}
	richarea.classList.remove('edit_placeholder');
}
function write_output() {
	if (richarea.editArea.content._placeholder) {
		textarea.value = '';
		return;
	}

	var content = richarea.editArea.content.cloneNode(true);

	// Sanitise here.

	textarea.value = Edit.Serializer.serialize(content);
}
