var textarea = document.querySelector('textarea');
textarea.style.marginLeft = '170px';

var richarea = document.createElement('div');
richarea.id = 'richarea';
textarea.parentNode.insertBefore(richarea, textarea);
new Edit.EditArea(richarea);
richarea.editArea.input(textarea.value);

// var button = createElement('button', 'Update textarea', { type: 'button' });
// textarea.parentNode.insertBefore(button, textarea);
// button.onclick = 
textarea.form.onsubmit = function() {
	textarea.value = richarea.editArea.output();
};
