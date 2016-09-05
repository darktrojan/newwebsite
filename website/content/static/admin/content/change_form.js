/* globals Edit */
var textarea = document.querySelector('textarea');
textarea.style.marginLeft = '170px';

var richarea = document.createElement('div');
richarea.id = 'richarea';
textarea.parentNode.insertBefore(richarea, textarea);
new Edit.EditArea(richarea);
read_input();

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
	Edit.Actions.imageAction({
		src: this.src.value, width: this.width.value, height: this.height.value
	});
	imagearea.style.display = null;
	return false;
};

textarea.form.onsubmit = function() {
	write_output();
};
Edit.linkCallback = function() {
	return '/media/files/Above_Gotham.jpg';
};
Edit.imageCallback = function() {
	imagearea.style.display = 'block';
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
	var content = richarea.editArea.content.cloneNode(true);

	// Sanitise here.

	textarea.value = Edit.Serializer.serialize(content);
}
