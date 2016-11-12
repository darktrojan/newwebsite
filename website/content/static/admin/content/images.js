var imageareabg = document.getElementById('imageareabg');
imageareabg.onclick = function() {
	imageareabg.style.display = null;
	imagearea.style.display = null;
	linkarea.style.display = null;
};
var imagearea = document.getElementById('imagearea');
fetch('/admin/all_images', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	var inner = imagearea.querySelector('div');
	for (var i of json) {
		var div = document.createElement('div');
		div.classList.add('image');
		div.dataset.src = i.url;
		div.title = i.url.substring(i.url.lastIndexOf('/') + 1);
		var img = document.createElement('img');
		if (i.thumb) {
			img.src = i.thumb;
		} else {
			img.onload = load_next_thumb;
		}
		div.appendChild(img);
		inner.appendChild(div);
	}

	load_next_thumb();
	function load_next_thumb() {
		var next = inner.querySelector('img:not([src])');
		if (next) {
			var name = next.parentNode.dataset.src.substring(7); // length of '/media/'
			next.src = '/admin/get_thumbnail?f=' + encodeURIComponent(name);
		}
	}
});
imagearea.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLImageElement) {
		target = target.parentNode;
	}
	if (target instanceof HTMLDivElement && target.classList.contains('image')) {
		var thumb = imageform.querySelector('img');
		thumb.onload = function() {
			imageform.width.value = this.naturalWidth;
			imageform.height.value = this.naturalHeight;
		};
		thumb.src = imageform.src.value = target.dataset.src;
		var name = imageform.querySelector('div');
		name.textContent = target.dataset.src.substring(target.dataset.src.lastIndexOf('/') + 1);
	}
};
var imageform = imagearea.querySelector('form');
imageform.onsubmit = function() {
	try {
		Edit.Actions.imageAction({
			src: this.src.value, width: this.width.value, height: this.height.value
		});
	} catch (ex) {
		console.error(ex);
	} finally {
		imageareabg.style.display = null;
		imagearea.style.display = null;
		Edit.currentWindow.focus();
		return false;
	}
};
Edit.imageCallback = function() {
	imageareabg.style.display = 'block';
	imagearea.style.display = 'flex';
};

var linkarea = document.getElementById('linkarea');
fetch('/admin/all_pages', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	for (var i of json) {
		var div = document.createElement('div');
		div.classList.add('link');
		div.dataset.href = i.url;
		div.textContent = i.title;
		linkarea.appendChild(div);
	}
});
linkarea.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLDivElement) {
		linkform.href.value = target.dataset.href;
	}
};
var linkform = linkarea.querySelector('form');
linkform.onsubmit = function() {
	try {
		Edit.Actions.linkAction({
			href: this.href.value,
			target: this.target.value
		});
	} catch (ex) {
		console.error(ex);
	} finally {
		imageareabg.style.display = null;
		linkarea.style.display = null;
		setTimeout(function() {
			Edit.currentWindow.focus();
		}, 0);
		return false;
	}
};
Edit.linkCallback = function() {
	imageareabg.style.display = 'block';
	linkarea.style.display = 'block';
};
