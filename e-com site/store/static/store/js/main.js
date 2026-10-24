document.addEventListener('DOMContentLoaded', () => {
  const menuButton = document.querySelector('.mobile-menu-toggle');
  const navigation = document.getElementById('primary-navigation');
  if (menuButton && navigation) {
    menuButton.addEventListener('click', () => {
      const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
      menuButton.setAttribute('aria-expanded', String(!isOpen));
      menuButton.setAttribute('aria-label', isOpen ? 'Open menu' : 'Close menu');
      navigation.classList.toggle('is-open', !isOpen);
    });
    navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.setAttribute('aria-label', 'Open menu');
      navigation.classList.remove('is-open');
    }));
  }

  document.querySelectorAll('.add-form, .detail-add').forEach(form => {
    form.addEventListener('submit', event => {
      const button = form.querySelector('button');
      if (button && !button.disabled) {
        button.dataset.label = button.textContent;
        button.textContent = 'Adding…';
      }
    });
  });
});
