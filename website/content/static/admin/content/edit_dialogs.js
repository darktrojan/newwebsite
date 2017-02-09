/* globals Edit */
/* jshint -W004 */
var PickerBackground = {
	area: document.getElementById('pickerbackground'),
	show: function() {
		this.area.style.display = null;
	},
	hide: function() {
		this.area.style.display = 'none';
	}
};
var ImagePicker = {
	loaded: false,
	area: document.getElementById('imagearea'),

	init: function() {
		this.inner = this.area.querySelector('div');
		this.form = this.area.querySelector('form');
		this.thumbnail = this.form.querySelector('img');
		this.nameLabel = this.form.querySelector('div');
		this.submitButton = this.form.querySelector('button');
	},
	load: function() {
		this.loaded = true;
		fetch('/admin/content/all_images', {credentials: 'same-origin'}).then(function(result) {
			return result.json();
		}).then(function(json) {
			function show_folder(folder, parentFolder) {
				var folderinner = document.createElement('div');
				folderinner.classList.add('folderinner');
				folderinner.dataset.dirname = folder.path;
				ImagePicker.inner.appendChild(folderinner);

				if (parentFolder) {
					var div = document.createElement('div');
					var a = document.createElement('a');
					a.href = '#';
					a.classList.add('folder');
					a.dataset.path = parentFolder.path;
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
						if (parentFolder) {
							div.dataset.thumb = i.thumb;
						} else {
							img.src = i.thumb;
						}
					} else {
						img.onload = ImagePicker.load_next_thumb;
					}
					div.appendChild(img);
					folderinner.appendChild(div);
				}
				for (var f of folder.folders) {
					show_folder(f, folder);
				}
			}

			show_folder(json);
			ImagePicker.load_next_thumb();
		});
	},
	load_next_thumb: function() {
		var next = ImagePicker.inner.querySelector('div.folderinner:not([hidden]) img:not([src])');
		if (next) {
			var data = next.parentNode.dataset;
			if (data.thumb) {
				next.src = data.thumb;
				ImagePicker.load_next_thumb();
			} else {
				var name = data.src.substring(7); // length of '/media/'
				next.src = '/admin/content/get_thumbnail?f=' + encodeURIComponent(name);
			}
		}
	},
	show: function() {
		PickerBackground.show();
		this.area.style.display = null;
		this.inner.focus();

		if (!this.loaded) {
			this.load();
		}
	},
	hide: function() {
		this.area.style.display = 'none';
		PickerBackground.hide();
	}
};
var LinkPicker = {
	loaded: false,
	area: document.getElementById('linkarea'),

	init: function() {
		this.form = this.area.querySelector('form');
		this.submitButton = this.form.querySelector('button');
		this.list = this.area.querySelector('select');
	},
	load: function() {
		fetch('/admin/content/all_pages', {credentials: 'same-origin'}).then(function(result) {
			return result.json();
		}).then(function(json) {
			for (var i of json) {
				var div = document.createElement('option');
				div.classList.add('link');
				div.value = i.url;
				div.textContent = i.title;
				LinkPicker.list.appendChild(div);
			}
		});
	},
	show: function() {
		PickerBackground.show();
		this.area.style.display = null;
		this.list.focus();

		if (!this.loaded) {
			this.load();
		}
	},
	hide: function() {
		this.area.style.display = 'none';
		PickerBackground.hide();
	}
};

PickerBackground.area.onclick = function() {
	ImagePicker.hide();
	LinkPicker.hide();
};

ImagePicker.init();
ImagePicker.area.onclick = function(event) {
	var target = event.target;
	if (target instanceof HTMLImageElement) {
		target = target.parentNode;
	}
	if (target instanceof HTMLAnchorElement && target.classList.contains('folder')) {
		var folders = ImagePicker.area.querySelectorAll('div.folderinner');
		for (var i of folders) {
			if (i.dataset.dirname == target.dataset.path) {
				i.removeAttribute('hidden');
			} else {
				i.setAttribute('hidden', '');
			}
		}
		ImagePicker.load_next_thumb();
		return false;
	} else if (target instanceof HTMLDivElement && target.classList.contains('image')) {
		var selected = ImagePicker.area.querySelector('div.image.selected');
		if (selected) {
			selected.classList.remove('selected');
		}
		target.classList.add('selected');
		ImagePicker.thumbnail.onload = function() {
			ImagePicker.form.width.value = this.naturalWidth;
			ImagePicker.form.height.value = this.naturalHeight;
			ImagePicker.thumbnail.onload = null;
		};
		ImagePicker.thumbnail.src = ImagePicker.form.src.value = target.dataset.src;
		ImagePicker.nameLabel.textContent = target.dataset.src.substring(target.dataset.src.lastIndexOf('/') + 1);
		ImagePicker.submitButton.disabled = false;
	}
};
ImagePicker.form.onsubmit = function() {
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
ImagePicker.form.onreset = function() {
	ImagePicker.hide();
	var selected = ImagePicker.area.querySelector('div.image.selected');
	if (selected) {
		selected.classList.remove('selected');
	}
	ImagePicker.thumbnail.src = '';
	ImagePicker.nameLabel.textContent = null;
	ImagePicker.form.reset();
	ImagePicker.submitButton.disabled = true;
	Edit.currentWindow.focus();
};
ImagePicker.form.width.oninput = function() {
	ImagePicker.form.height.value = Math.round(
		this.value / ImagePicker.thumbnail.naturalWidth * ImagePicker.thumbnail.naturalHeight
	);
};
ImagePicker.form.height.oninput = function() {
	ImagePicker.form.width.value = Math.round(
		this.value / ImagePicker.thumbnail.naturalHeight * ImagePicker.thumbnail.naturalWidth
	);
};

Edit.imageCallback = function(existing) {
	ImagePicker.show();

	if (existing) {
		ImagePicker.thumbnail.src = ImagePicker.form.src.value = existing.getAttribute('src');
		ImagePicker.form.width.value = existing.getAttribute('width');
		ImagePicker.form.height.value = existing.getAttribute('height');
		ImagePicker.submitButton.disabled = false;
		ImagePicker.submitButton.textContent = 'Update';
	} else {
		ImagePicker.submitButton.textContent = 'Insert';
	}
};

LinkPicker.init();
LinkPicker.list.onchange = function() {
	LinkPicker.form.href.value = this.value;
	LinkPicker.submitButton.disabled = false;
};
LinkPicker.form.onsubmit = function() {
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
LinkPicker.form.onreset = function() {
	LinkPicker.hide();
	LinkPicker.list.selectedIndex = -1;
	LinkPicker.submitButton.disabled = true;
	setTimeout(function() {
		Edit.currentWindow.focus();
	}, 0);
};

Edit.linkCallback = function() {
	LinkPicker.show();
};
