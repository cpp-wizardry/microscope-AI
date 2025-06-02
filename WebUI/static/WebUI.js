function submitForm(action) {
  const form = document.getElementById('motorForm');
  form.action = action;
  form.submit();
}
