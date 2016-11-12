/* globals Edit */
var textarea = document.querySelector('textarea#id_content');
textarea.hidden = true;
textarea.onkeydown = function(event) {
	if (event.keyCode == 9 && !event.shiftKey && !event.ctrlKey) { // KeyEvent.DOM_VK_TAB
		event.preventDefault();
		var s = this.selectionStart;
		var e = this.selectionEnd;
		this.value = this.value.substring(0, s) + '\t' + this.value.substring(e);
		this.selectionStart = this.selectionEnd = s + 1;
	}
};

var iframe = document.createElement('iframe');
iframe.id = 'richarea';
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
	if (textarea.hidden) {
		write_output();
	}
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
function swap() {
	if (textarea.hidden) {
		write_output();
		textarea.hidden = false;
		iframe.hidden = true;
	} else {
		read_input();
		textarea.hidden = true;
		iframe.hidden = false;
	}
}
