var imageareabg = document.getElementById('imageareabg');
imageareabg.onclick = function() {
	imageareabg.style.display = null;
	imagearea.style.display = null;
};
var imagearea = document.getElementById('imagearea');
fetch('/admin/all_images', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	for (var i of json) {
		var div = document.createElement('button');
		div.type = 'button';
		div.classList.add('image');
		div.dataset.src = i.url;
		var img = document.createElement('img');
		img.src = i.thumb;
		div.appendChild(img);
		imagearea.appendChild(div);
	}
});
imagearea.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLImageElement) {
		target = target.parentNode;
	}
	if (target instanceof HTMLButtonElement && target.classList.contains('image')) {
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
		imageareabg.style.display = null;
		imagearea.style.display = null;
	} catch (ex) {
		console.error(ex);
	} finally {
		return false;
	}
};
Edit.imageCallback = function() {
	imageareabg.style.display = 'block';
	imagearea.style.display = 'block';
};
