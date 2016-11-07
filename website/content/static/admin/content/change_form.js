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

/**
var imagearea = document.getElementById('imagearea');
fetch('/admin/all_images', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	for (var i of json) {
		var div = document.createElement('div');
		div.classList.add('image');
		var img = document.createElement('img');
		img.src = i.thumb;
		img.dataset.src = i.url;
		div.appendChild(img);
		imagearea.appendChild(div);
	}
});
imagearea.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLImageElement) {
		var thumb = imageform.querySelector('img');
		thumb.onload = function() {
			imageform.width.value = this.naturalWidth;
			imageform.height.value = this.naturalHeight;
		};
		thumb.src = imageform.src.value = target.dataset.src;
	}
};
var imageform = imagearea.querySelector('form');
imageform.onsubmit = function() {
	try {
		Edit.Actions.imageAction({
			src: this.src.value, width: this.width.value, height: this.height.value
		});
		imagearea.style.display = null;
	} finally {
		return false;
	}
};
**/

textarea.form.onsubmit = function() {
	write_output();
};

/**
Edit.linkCallback = function() {
	return '/media/files/Above_Gotham.jpg';
};
Edit.imageCallback = function() {
	imagearea.style.display = 'block';
};
**/

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
