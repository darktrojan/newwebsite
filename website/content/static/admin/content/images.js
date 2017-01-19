var imageareabg = document.getElementById('imageareabg');
imageareabg.onclick = function() {
	imageareabg.style.display = null;
	imagearea.style.display = null;
	linkarea.style.display = null;
};
var imagearea = document.getElementById('imagearea');
var inner = imagearea.querySelector('div');
fetch('/admin/content/all_images', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	function show_folder(folder, parent) {
		var folderinner = document.createElement('div');
		folderinner.classList.add('folderinner');
		folderinner.dataset.dirname = folder.path;
		inner.appendChild(folderinner);

		if (parent) {
			var div = document.createElement('div');
			var a = document.createElement('a');
			a.href = '#';
			a.classList.add('folder');
			a.dataset.path = parent.path;
			a.textContent = ' Parent folder';
			var span = document.createElement('span');
			span.classList.add('folder-icon');
			a.insertBefore(span, a.firstChild);
			div.appendChild(a);
			folderinner.appendChild(div);
			folderinner.setAttribute('hidden', '');
		}
		for (var f of folder.folders) {
			var div = document.createElement('div');
			var a = document.createElement('a');
			a.href = '#';
			a.classList.add('folder');
			a.dataset.path = f.path;
			a.textContent = ' ' + f.path.substring(f.path.lastIndexOf('/') + 1);
			var span = document.createElement('span');
			span.classList.add('folder-icon');
			a.insertBefore(span, a.firstChild);
			div.appendChild(a);
			folderinner.appendChild(div);
		}
		for (var i of folder.images) {
			var div = document.createElement('div');
			div.classList.add('image');
			div.dataset.src = i.url;
			div.dataset.dirname = i.url.substring(14, i.url.lastIndexOf('/'));
			div.title = i.url.substring(i.url.lastIndexOf('/') + 1);
			var img = document.createElement('img');
			if (i.thumb) {
				img.src = i.thumb;
			} else {
				img.onload = load_next_thumb;
			}
			div.appendChild(img);
			folderinner.appendChild(div);
		}
		for (var f of folder.folders) {
			show_folder(f, folder);
		}
	}

	show_folder(json);
	load_next_thumb();
});
function load_next_thumb() {
	var next = inner.querySelector('div.folderinner:not([hidden]) img:not([src])');
	if (next) {
		var name = next.parentNode.dataset.src.substring(7); // length of '/media/'
		next.src = '/admin/content/get_thumbnail?f=' + encodeURIComponent(name);
	}
}
imagearea.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLImageElement) {
		target = target.parentNode;
	}
	if (target instanceof HTMLAnchorElement && target.classList.contains('folder')) {
		var folders = imagearea.querySelectorAll('div.folderinner');
		for (var i of folders) {
			if (i.dataset.dirname == target.dataset.path) {
				i.removeAttribute('hidden');
			} else {
				i.setAttribute('hidden', '');
			}
		}
		load_next_thumb();
		return false;
	} else if (target instanceof HTMLDivElement && target.classList.contains('image')) {
		var selected = imagearea.querySelector('div.image.selected');
		if (selected) {
			selected.classList.remove('selected');
		}
		target.classList.add('selected');
		var thumb = imageform.querySelector('img');
		thumb.onload = function() {
			imageform.width.value = this.naturalWidth;
			imageform.height.value = this.naturalHeight;
		};
		thumb.src = imageform.src.value = target.dataset.src;
		var name = imageform.querySelector('div');
		name.textContent = target.dataset.src.substring(target.dataset.src.lastIndexOf('/') + 1);
		imageform.querySelector('button').disabled = false;
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
		this.reset();
		return false;
	}
};
imageform.onreset = function() {
	imageareabg.style.display = null;
	imagearea.style.display = null;
	var selected = imagearea.querySelector('div.image.selected');
	if (selected) {
		selected.classList.remove('selected');
	}
	var thumb = imageform.querySelector('img');
	thumb.src = '';
	var name = imageform.querySelector('div');
	name.textContent = null;
	imageform.reset();
	imageform.querySelector('button[type="submit"]').disabled = true;
	Edit.currentWindow.focus();
};
Edit.imageCallback = function() {
	imageareabg.style.display = 'block';
	imagearea.style.display = 'flex';
	imagearea.querySelector('div').focus();
};

var linkarea = document.getElementById('linkarea');
fetch('/admin/content/all_pages', {credentials: 'same-origin'}).then(function(result) {
	return result.json();
}).then(function(json) {
	var list = linkarea.querySelector('select');
	for (var i of json) {
		var div = document.createElement('option');
		div.classList.add('link');
		div.value = i.url;
		div.textContent = i.title;
		list.appendChild(div);
	}
	list.onchange = function() {
		linkform.href.value = this.value;
		linkform.querySelector('button').disabled = false;
	};
});
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
		this.reset();
		return false;
	}
};
linkform.onreset = function() {
	imageareabg.style.display = null;
	linkarea.style.display = null;
	linkarea.querySelector('select').selectedIndex = -1;
	linkform.querySelector('button[type="submit"]').disabled = true;
	setTimeout(function() {
		Edit.currentWindow.focus();
	}, 0);
};
Edit.linkCallback = function() {
	imageareabg.style.display = 'block';
	linkarea.style.display = 'flex';
	linkarea.querySelector('select').focus();
};
