const burgerMenu = document.querySelector('.burger-menu');
const sidebar = document.querySelector('.sidebar');

burgerMenu.addEventListener('click', () => {
    burgerMenu.classList.toggle('active');
    sidebar.classList.toggle('open');
});
